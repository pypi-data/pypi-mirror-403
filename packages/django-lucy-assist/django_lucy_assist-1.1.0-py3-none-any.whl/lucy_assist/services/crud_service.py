"""
Service pour exécuter des opérations CRUD via Lucy Assist.

Ce service utilise les vues du projet hôte quand elles sont disponibles,
ce qui permet de bénéficier de toute la logique métier (services, logs, etc.)
présente dans les vues.

Si aucune vue n'est trouvée, il utilise un fallback direct sur les modèles.
"""
from typing import Dict, List, Optional, Any

from django.apps import apps
from django.db import transaction
from django.forms import modelform_factory
from django.test import RequestFactory
from django.urls import reverse, NoReverseMatch
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore

from lucy_assist.utils.log_utils import LogUtils
from lucy_assist.conf import lucy_assist_settings


class CRUDService:
    """
    Service pour les opérations CRUD pilotées par Lucy Assist.

    Utilise les vues du projet hôte via RequestFactory quand elles sont
    disponibles, sinon effectue les opérations directement sur les modèles.
    """

    def __init__(self, user):
        self.user = user
        self._request_factory = RequestFactory()
        self._config = None

    @property
    def config(self):
        """Lazy loading de la configuration."""
        if self._config is None:
            from lucy_assist.models import ConfigurationLucyAssist
            self._config = ConfigurationLucyAssist.get_config()
        return self._config

    def _create_request(self, method: str, path: str, data: Dict = None):
        """
        Crée une requête Django simulée avec l'utilisateur et la session.
        Inclut les attributs personnalisés que les middlewares du projet pourraient ajouter.
        """
        if method.upper() == 'POST':
            request = self._request_factory.post(path, data=data or {})
        else:
            request = self._request_factory.get(path, data=data or {})

        # Attacher l'utilisateur
        request.user = self.user

        # Configurer la session
        request.session = SessionStore()
        request.session.create()

        # Configurer les messages Django
        setattr(request, '_messages', FallbackStorage(request))

        # Simuler HTMX désactivé (on veut une réponse complète)
        request.htmx = False

        # Ajouter les attributs personnalisés du middleware du projet
        # Ces attributs sont souvent utilisés par les vues
        self._add_custom_middleware_attributes(request)

        return request

    def _add_custom_middleware_attributes(self, request):
        """
        Ajoute les attributs personnalisés que les middlewares du projet
        pourraient avoir ajoutés à la requête.

        Cette méthode copie les attributs personnalisés de l'utilisateur
        vers la requête, permettant aux vues d'y accéder normalement.
        """
        # Copier les attributs personnalisés de l'utilisateur vers la requête
        # Les projets peuvent avoir des middlewares qui ajoutent des attributs
        # comme 'tenant', 'organization', 'company', etc.
        custom_attrs = lucy_assist_settings.get('REQUEST_USER_ATTRS', [])
        for attr in custom_attrs:
            if hasattr(self.user, attr):
                setattr(request, attr, getattr(self.user, attr))

    def _get_thread_local_paths(self) -> list:
        """
        Retourne la liste des chemins possibles pour le module ThreadLocal.
        Utilise la configuration si disponible, sinon des chemins par défaut.
        """
        paths = []

        # Utiliser le chemin configuré en priorité
        configured_path = lucy_assist_settings.THREAD_LOCAL_MODULE
        if configured_path:
            paths.append((configured_path, 'set_current_user'))

        # Chemins par défaut
        paths.extend([
            ('alyse.middleware.middleware', 'set_current_user'),
            ('middleware.middleware', 'set_current_user'),
            ('core.middleware', 'set_current_user'),
        ])

        return paths

    def _setup_thread_local(self):
        """
        Configure le ThreadLocal pour les managers qui utilisent get_current_user().
        Essaie de trouver et utiliser la fonction set_current_user du projet.
        """
        for module_path, func_name in self._get_thread_local_paths():
            try:
                module = __import__(module_path, fromlist=[func_name])
                set_current_user = getattr(module, func_name, None)
                if set_current_user:
                    set_current_user(self.user)
                    LogUtils.info(f"[CRUD] ThreadLocal configuré via {module_path}")
                    return
            except (ImportError, AttributeError):
                continue

        # Fallback: essayer de définir directement dans threading.local
        # si le projet utilise cette approche
        LogUtils.info("[CRUD] Pas de set_current_user trouvé, ThreadLocal non configuré")

    def _cleanup_thread_local(self):
        """
        Nettoie le ThreadLocal après l'appel de la vue.
        """
        for module_path, func_name in self._get_thread_local_paths():
            try:
                module = __import__(module_path, fromlist=[func_name])
                set_current_user = getattr(module, func_name, None)
                if set_current_user:
                    set_current_user(None)
                    return
            except (ImportError, AttributeError):
                continue

    def _extract_messages(self, request) -> List[str]:
        """Extrait les messages Django de la requête."""
        messages = []
        if hasattr(request, '_messages'):
            for msg in request._messages:
                messages.append(str(msg))
        return messages

    def _call_view(
        self,
        model_name: str,
        action: str,
        data: Dict = None,
        object_id: int = None
    ) -> Optional[Dict]:
        """
        Appelle une vue du projet via RequestFactory.

        Args:
            model_name: Nom du modèle
            action: Action CRUD ('create', 'update', 'delete', 'list', 'detail')
            data: Données à envoyer (pour POST)
            object_id: ID de l'objet (pour update/delete/detail)

        Returns:
            Dict avec 'success', 'response', 'messages' ou None si pas de vue
        """
        view_info = self.config.get_crud_view_for_model(model_name, action)

        # Essayer aussi avec des variations du nom de modèle
        if not view_info:
            from lucy_assist.services.view_discovery_service import ViewDiscoveryService
            service = ViewDiscoveryService()
            view_info = service.get_view_info(model_name, action)

        if not view_info:
            LogUtils.info(f"[CRUD] Pas de vue trouvée pour {model_name}.{action}")
            return None

        url_name = view_info.get('url_name')
        method = view_info.get('method', 'GET')
        requires_pk = view_info.get('requires_pk', False)

        LogUtils.info(f"[CRUD] Appel vue {url_name} ({method}) pour {model_name}.{action}")

        try:
            # Construire l'URL
            if requires_pk and object_id:
                url = reverse(url_name, kwargs={'pk': object_id})
            else:
                url = reverse(url_name)

            # Préparer les données POST
            post_data = data.copy() if data else {}

            # Pour les vues formulaire, ajouter le pk si c'est une modification
            if action == 'update' and object_id:
                post_data['pk'] = object_id

            # Créer et exécuter la requête
            request = self._create_request(method, url, post_data if method == 'POST' else None)

            # Configurer le ThreadLocal pour les managers qui en dépendent
            self._setup_thread_local()

            # Résoudre et appeler la vue
            from django.urls import resolve
            match = resolve(url)
            view_func = match.func

            try:
                # Appeler la vue
                if hasattr(view_func, 'view_class'):
                    # Class-based view
                    view = view_func.view_class.as_view()
                    response = view(request, **match.kwargs)
                else:
                    # Function-based view
                    response = view_func(request, **match.kwargs)
            finally:
                # Nettoyer le ThreadLocal
                self._cleanup_thread_local()

            # Analyser la réponse
            success = response.status_code in [200, 201, 302]
            messages = self._extract_messages(request)

            # Détecter les erreurs dans la réponse
            if hasattr(response, 'content'):
                content = response.content.decode('utf-8', errors='replace')
                # Chercher des indicateurs d'erreur dans le HTML
                if 'class="error' in content or 'class="invalid' in content:
                    success = False

            return {
                'success': success,
                'status_code': response.status_code,
                'messages': messages,
                'redirect_url': response.get('Location') if response.status_code == 302 else None
            }

        except NoReverseMatch as e:
            LogUtils.warning(f"[CRUD] URL non trouvée pour {url_name}: {e}")
            return None
        except Exception as e:
            LogUtils.error(f"[CRUD] Erreur appel vue {url_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'messages': []
            }

    def _serialize_value(self, value):
        """
        Convertit une valeur en un format sérialisable JSON.
        """
        from datetime import datetime, date, time
        from decimal import Decimal
        import uuid

        if value is None:
            return None
        elif isinstance(value, (datetime,)):
            return value.isoformat()
        elif isinstance(value, (date,)):
            return value.isoformat()
        elif isinstance(value, (time,)):
            return value.isoformat()
        elif isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, uuid.UUID):
            return str(value)
        elif hasattr(value, 'pk'):
            # ForeignKey ou relation
            return {'id': value.pk, 'str': str(value)}
        elif hasattr(value, 'all'):
            # ManyToMany ou reverse FK - retourner juste le count
            return {'count': value.count()}
        elif isinstance(value, bytes):
            return value.decode('utf-8', errors='replace')
        else:
            # Essayer de retourner directement, sinon convertir en string
            try:
                # Types simples (str, int, float, bool, list, dict)
                import json
                json.dumps(value)
                return value
            except (TypeError, ValueError):
                return str(value)

    def can_perform_action(self, app_name: str, model_name: str, action: str) -> bool:
        """
        Vérifie si l'utilisateur peut effectuer l'action.

        Args:
            app_name: Nom de l'app Django
            model_name: Nom du modèle
            action: 'add', 'change', 'delete', 'view'

        Returns:
            True si autorisé
        """
        if self.user.is_superuser:
            return True

        permission = f"{app_name}.{action}_{model_name.lower()}"
        return self.user.has_perm(permission)

    def get_model(self, app_name: str, model_name: str):
        """Récupère une classe de modèle Django."""
        # Essayer d'abord avec app_name fourni
        try:
            model = apps.get_model(app_name, model_name)
            LogUtils.info(f"[CRUD] Modèle trouvé: {app_name}.{model_name}")
            return model
        except LookupError:
            pass

        # Essayer avec le préfixe PROJECT_APPS_PREFIX
        apps_prefix = lucy_assist_settings.PROJECT_APPS_PREFIX or ''
        if apps_prefix and not app_name.startswith(apps_prefix):
            try:
                full_app_name = f"{apps_prefix}{app_name}"
                model = apps.get_model(full_app_name, model_name)
                LogUtils.info(f"[CRUD] Modèle trouvé avec préfixe: {full_app_name}.{model_name}")
                return model
            except LookupError:
                pass

        # Chercher dans toutes les apps du projet
        for app_config in apps.get_app_configs():
            # Filtrer par préfixe si configuré
            if apps_prefix and not app_config.name.startswith(apps_prefix):
                continue

            try:
                model = app_config.get_model(model_name)
                LogUtils.info(f"[CRUD] Modèle trouvé par recherche: {app_config.label}.{model_name}")
                return model
            except LookupError:
                continue

        LogUtils.warning(f"[CRUD] Modèle non trouvé: {app_name}.{model_name}")
        return None

    def get_form_class(self, model):
        """Récupère ou crée une classe de formulaire pour le modèle."""
        app_label = model._meta.app_label
        model_name = model.__name__

        # Liste des chemins d'import possibles pour les formulaires
        apps_prefix = lucy_assist_settings.PROJECT_APPS_PREFIX or ''
        possible_paths = [
            f'{apps_prefix}{app_label}.forms',  # apps.client.forms
            f'{app_label}.forms',                # client.forms
            f'apps.{app_label}.forms',           # apps.client.forms (legacy)
        ]

        # Essayer de trouver un formulaire existant
        for path in possible_paths:
            try:
                forms_module = __import__(path, fromlist=[f'{model_name}Form'])
                form_class = getattr(forms_module, f'{model_name}Form', None)
                if form_class:
                    LogUtils.info(f"[CRUD] Formulaire trouvé: {path}.{model_name}Form")
                    return form_class
            except (ImportError, AttributeError, ModuleNotFoundError):
                continue

        # Créer un formulaire automatique
        LogUtils.info(f"[CRUD] Formulaire auto-généré pour {model_name}")
        return modelform_factory(model, fields='__all__')

    def get_required_fields(self, model) -> List[Dict]:
        """
        Retourne les champs requis pour créer un objet.

        Returns:
            Liste de dicts avec 'name', 'verbose_name', 'type', 'choices'
        """
        required = []

        for field in model._meta.get_fields():
            # Ignorer les relations inverses et les champs auto
            if not hasattr(field, 'blank'):
                continue

            if field.name in ['id', 'pk', 'created_date', 'updated_date', 'created_user', 'updated_user']:
                continue

            if not field.blank or (hasattr(field, 'null') and not field.null and not field.has_default()):
                field_info = {
                    'name': field.name,
                    'verbose_name': str(field.verbose_name) if hasattr(field, 'verbose_name') else field.name,
                    'type': field.get_internal_type() if hasattr(field, 'get_internal_type') else 'text',
                    'required': True
                }

                # Ajouter les choix si c'est un champ avec choices
                if hasattr(field, 'choices') and field.choices:
                    field_info['choices'] = [
                        {'value': c[0], 'label': c[1]} for c in field.choices
                    ]

                required.append(field_info)

        return required

    def get_optional_fields(self, model) -> List[Dict]:
        """Retourne les champs optionnels."""
        optional = []

        for field in model._meta.get_fields():
            if not hasattr(field, 'blank'):
                continue

            if field.name in ['id', 'pk', 'created_date', 'updated_date', 'created_user', 'updated_user']:
                continue

            if field.blank:
                field_info = {
                    'name': field.name,
                    'verbose_name': str(field.verbose_name) if hasattr(field, 'verbose_name') else field.name,
                    'type': field.get_internal_type() if hasattr(field, 'get_internal_type') else 'text',
                    'required': False
                }

                if hasattr(field, 'choices') and field.choices:
                    field_info['choices'] = [
                        {'value': c[0], 'label': c[1]} for c in field.choices
                    ]

                optional.append(field_info)

        return optional

    def create_object(
        self,
        app_name: str,
        model_name: str,
        data: Dict[str, Any]
    ) -> Dict:
        """
        Crée un nouvel objet en utilisant la vue du projet si disponible.

        Args:
            app_name: Nom de l'app
            model_name: Nom du modèle
            data: Données du formulaire

        Returns:
            Dict avec 'success', 'object_id', 'errors', 'messages'
        """
        LogUtils.info(f"[CRUD] create_object: {app_name}.{model_name}")

        # Essayer d'abord via la vue du projet
        view_result = self._call_view(model_name, 'create', data=data)

        if view_result is not None:
            if view_result.get('success'):
                # Essayer de récupérer l'ID de l'objet créé depuis la redirection
                redirect_url = view_result.get('redirect_url', '')
                object_id = self._extract_id_from_url(redirect_url)

                return {
                    'success': True,
                    'object_id': object_id,
                    'message': view_result.get('messages', [f'{model_name} créé avec succès.'])[0] if view_result.get('messages') else f'{model_name} créé avec succès.',
                    'messages': view_result.get('messages', []),
                    'via_view': True
                }
            else:
                return {
                    'success': False,
                    'errors': view_result.get('messages', []) or [view_result.get('error', 'Erreur lors de la création')],
                    'via_view': True
                }

        # Fallback: création directe via le modèle
        LogUtils.info(f"[CRUD] Fallback création directe pour {model_name}")
        return self._create_object_direct(app_name, model_name, data)

    @transaction.atomic
    def _create_object_direct(
        self,
        app_name: str,
        model_name: str,
        data: Dict[str, Any]
    ) -> Dict:
        """Création directe via le modèle (fallback)."""
        # Configurer le ThreadLocal pour les managers
        self._setup_thread_local()

        try:
            return self._create_object_direct_impl(app_name, model_name, data)
        finally:
            self._cleanup_thread_local()

    def _create_object_direct_impl(
        self,
        app_name: str,
        model_name: str,
        data: Dict[str, Any]
    ) -> Dict:
        """Implémentation de la création directe."""
        # Vérifier les permissions
        if not self.can_perform_action(app_name, model_name, 'add'):
            return {
                'success': False,
                'errors': ['Vous n\'avez pas les droits pour créer cet objet.']
            }

        # Récupérer le modèle
        model = self.get_model(app_name, model_name)
        if not model:
            return {
                'success': False,
                'errors': [f'Modèle {model_name} non trouvé.']
            }

        # Récupérer le formulaire
        form_class = self.get_form_class(model)

        try:
            form = form_class(data=data)

            if form.is_valid():
                obj = form.save(commit=False)

                # Ajouter l'utilisateur créateur si le champ existe
                if hasattr(obj, 'created_user'):
                    obj.created_user = self.user

                obj.save()
                form.save_m2m()  # Sauvegarder les relations many-to-many

                return {
                    'success': True,
                    'object_id': obj.pk,
                    'object_str': str(obj),
                    'message': f'{model_name} créé avec succès.',
                    'via_view': False
                }
            else:
                return {
                    'success': False,
                    'errors': [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()],
                    'via_view': False
                }

        except Exception as e:
            LogUtils.error(f"Erreur lors de la création de {model_name}: {e}")
            return {
                'success': False,
                'errors': [str(e)],
                'via_view': False
            }

    def update_object(
        self,
        app_name: str,
        model_name: str,
        object_id: int,
        data: Dict[str, Any]
    ) -> Dict:
        """
        Met à jour un objet en utilisant la vue du projet si disponible.

        Returns:
            Dict avec 'success', 'errors', 'messages'
        """
        LogUtils.info(f"[CRUD] update_object: {app_name}.{model_name} #{object_id}")

        # Essayer d'abord via la vue du projet
        view_result = self._call_view(model_name, 'update', data=data, object_id=object_id)

        if view_result is not None:
            if view_result.get('success'):
                return {
                    'success': True,
                    'object_id': object_id,
                    'message': view_result.get('messages', [f'{model_name} mis à jour avec succès.'])[0] if view_result.get('messages') else f'{model_name} mis à jour avec succès.',
                    'messages': view_result.get('messages', []),
                    'via_view': True
                }
            else:
                return {
                    'success': False,
                    'errors': view_result.get('messages', []) or [view_result.get('error', 'Erreur lors de la mise à jour')],
                    'via_view': True
                }

        # Fallback: mise à jour directe via le modèle
        LogUtils.info(f"[CRUD] Fallback mise à jour directe pour {model_name}")
        return self._update_object_direct(app_name, model_name, object_id, data)

    @transaction.atomic
    def _update_object_direct(
        self,
        app_name: str,
        model_name: str,
        object_id: int,
        data: Dict[str, Any]
    ) -> Dict:
        """Mise à jour directe via le modèle (fallback)."""
        # Configurer le ThreadLocal pour les managers
        self._setup_thread_local()

        try:
            return self._update_object_direct_impl(app_name, model_name, object_id, data)
        finally:
            self._cleanup_thread_local()

    def _update_object_direct_impl(
        self,
        app_name: str,
        model_name: str,
        object_id: int,
        data: Dict[str, Any]
    ) -> Dict:
        """Implémentation de la mise à jour directe."""
        # Vérifier les permissions
        if not self.can_perform_action(app_name, model_name, 'change'):
            return {
                'success': False,
                'errors': ['Vous n\'avez pas les droits pour modifier cet objet.']
            }

        # Récupérer le modèle et l'objet
        model = self.get_model(app_name, model_name)
        if not model:
            return {
                'success': False,
                'errors': [f'Modèle {model_name} non trouvé.']
            }

        try:
            obj = model.objects.get(pk=object_id)
        except model.DoesNotExist:
            return {
                'success': False,
                'errors': [f'{model_name} #{object_id} non trouvé.']
            }

        # Récupérer le formulaire
        form_class = self.get_form_class(model)

        try:
            form = form_class(data=data, instance=obj)

            if form.is_valid():
                obj = form.save(commit=False)

                # Mettre à jour l'utilisateur modificateur si le champ existe
                if hasattr(obj, 'updated_user'):
                    obj.updated_user = self.user

                obj.save()
                form.save_m2m()

                return {
                    'success': True,
                    'object_id': obj.pk,
                    'message': f'{model_name} mis à jour avec succès.',
                    'via_view': False
                }
            else:
                return {
                    'success': False,
                    'errors': [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()],
                    'via_view': False
                }

        except Exception as e:
            LogUtils.error(f"Erreur lors de la mise à jour de {model_name}: {e}")
            return {
                'success': False,
                'errors': [str(e)],
                'via_view': False
            }

    def delete_object(
        self,
        app_name: str,
        model_name: str,
        object_id: int
    ) -> Dict:
        """
        Supprime un objet en utilisant la vue du projet si disponible.

        Returns:
            Dict avec 'success', 'errors', 'messages'
        """
        LogUtils.info(f"[CRUD] delete_object: {app_name}.{model_name} #{object_id}")

        # Essayer d'abord via la vue du projet
        view_result = self._call_view(model_name, 'delete', object_id=object_id)

        if view_result is not None:
            if view_result.get('success'):
                return {
                    'success': True,
                    'message': view_result.get('messages', [f'{model_name} supprimé avec succès.'])[0] if view_result.get('messages') else f'{model_name} supprimé avec succès.',
                    'messages': view_result.get('messages', []),
                    'via_view': True
                }
            else:
                return {
                    'success': False,
                    'errors': view_result.get('messages', []) or [view_result.get('error', 'Erreur lors de la suppression')],
                    'via_view': True
                }

        # Fallback: suppression directe via le modèle
        LogUtils.info(f"[CRUD] Fallback suppression directe pour {model_name}")
        return self._delete_object_direct(app_name, model_name, object_id)

    @transaction.atomic
    def _delete_object_direct(
        self,
        app_name: str,
        model_name: str,
        object_id: int
    ) -> Dict:
        """Suppression directe via le modèle (fallback)."""
        # Configurer le ThreadLocal pour les managers
        self._setup_thread_local()

        try:
            return self._delete_object_direct_impl(app_name, model_name, object_id)
        finally:
            self._cleanup_thread_local()

    def _delete_object_direct_impl(
        self,
        app_name: str,
        model_name: str,
        object_id: int
    ) -> Dict:
        """Implémentation de la suppression directe."""
        # Vérifier les permissions
        if not self.can_perform_action(app_name, model_name, 'delete'):
            return {
                'success': False,
                'errors': ['Vous n\'avez pas les droits pour supprimer cet objet.']
            }

        # Récupérer le modèle
        model = self.get_model(app_name, model_name)
        if not model:
            return {
                'success': False,
                'errors': [f'Modèle {model_name} non trouvé.']
            }

        try:
            obj = model.objects.get(pk=object_id)
            obj_str = str(obj)
            obj.delete()

            return {
                'success': True,
                'message': f'{model_name} "{obj_str}" supprimé avec succès.',
                'via_view': False
            }

        except model.DoesNotExist:
            return {
                'success': False,
                'errors': [f'{model_name} #{object_id} non trouvé.'],
                'via_view': False
            }
        except Exception as e:
            LogUtils.error(f"Erreur lors de la suppression de {model_name}: {e}")
            return {
                'success': False,
                'errors': [str(e)],
                'via_view': False
            }

    def get_object(
        self,
        app_name: str,
        model_name: str,
        object_id: int
    ) -> Optional[Dict]:
        """
        Récupère les détails d'un objet.

        Returns:
            Dict avec les données de l'objet ou None
        """
        LogUtils.info(f"[CRUD] get_object: {app_name}.{model_name} #{object_id}")

        # Configurer le ThreadLocal pour les managers
        self._setup_thread_local()

        try:
            return self._get_object_impl(app_name, model_name, object_id)
        finally:
            self._cleanup_thread_local()

    def _get_object_impl(
        self,
        app_name: str,
        model_name: str,
        object_id: int
    ) -> Optional[Dict]:
        """Implémentation de la récupération d'objet."""
        # Vérifier les permissions
        if not self.can_perform_action(app_name, model_name, 'view'):
            LogUtils.info(f"[CRUD] get_object: permission refusée pour {model_name}")
            return None

        model = self.get_model(app_name, model_name)
        if not model:
            LogUtils.warning(f"[CRUD] get_object: modèle {model_name} non trouvé")
            return None

        try:
            # Utiliser objects.all() pour éviter les problèmes avec les managers customs
            obj = model.objects.all().get(pk=object_id)

            # Construire un dict avec les données
            data = {'id': obj.pk, 'str': str(obj)}

            for field in model._meta.get_fields():
                if hasattr(field, 'verbose_name'):
                    try:
                        value = getattr(obj, field.name)
                        data[field.name] = self._serialize_value(value)
                    except Exception:
                        pass

            LogUtils.info(f"[CRUD] get_object: {model_name} #{object_id} récupéré avec succès")
            return data

        except model.DoesNotExist:
            LogUtils.info(f"[CRUD] get_object: {model_name} #{object_id} non trouvé")
            return None
        except Exception as e:
            LogUtils.error(f"[CRUD] get_object: erreur pour {model_name} #{object_id}: {e}")
            return None

    def get_deletion_impact(
        self,
        app_name: str,
        model_name: str,
        object_id: int
    ) -> Dict:
        """
        Analyse l'impact d'une suppression et retourne toutes les conséquences.

        Utilise le Collector Django pour simuler la suppression et identifier
        tous les objets qui seront affectés (CASCADE, SET_NULL, PROTECT, etc.)

        Returns:
            Dict avec 'can_delete', 'cascade_deletions', 'set_null', 'protected', 'summary'
        """
        LogUtils.info(f"[CRUD] get_deletion_impact: {app_name}.{model_name} #{object_id}")

        # Configurer le ThreadLocal pour les managers
        self._setup_thread_local()

        try:
            return self._get_deletion_impact_impl(app_name, model_name, object_id)
        finally:
            self._cleanup_thread_local()

    def _get_deletion_impact_impl(
        self,
        app_name: str,
        model_name: str,
        object_id: int
    ) -> Dict:
        """Implémentation de l'analyse d'impact de suppression."""
        from django.db.models import ProtectedError
        from django.db.models.deletion import Collector

        result = {
            'can_delete': True,
            'object_str': None,
            'cascade_deletions': [],  # Objets qui seront supprimés en cascade
            'set_null': [],           # Objets dont la FK sera mise à NULL
            'set_default': [],        # Objets dont la FK sera mise à la valeur par défaut
            'protected': [],          # Objets qui bloquent la suppression
            'restricted': [],         # Objets avec RESTRICT
            'summary': {},            # Résumé par modèle
            'total_deletions': 0,
            'warnings': []
        }

        # Vérifier les permissions
        if not self.can_perform_action(app_name, model_name, 'view'):
            result['can_delete'] = False
            result['warnings'].append("Permission insuffisante pour voir cet objet.")
            return result

        # Récupérer le modèle et l'objet
        model = self.get_model(app_name, model_name)
        if not model:
            result['can_delete'] = False
            result['warnings'].append(f"Modèle {model_name} non trouvé.")
            return result

        try:
            obj = model.objects.all().get(pk=object_id)
            result['object_str'] = str(obj)
        except model.DoesNotExist:
            result['can_delete'] = False
            result['warnings'].append(f"{model_name} #{object_id} non trouvé.")
            return result

        # Utiliser le Collector Django pour simuler la suppression
        try:
            from django.db import router
            using = router.db_for_write(model, instance=obj)
            collector = Collector(using=using)

            try:
                collector.collect([obj])
            except ProtectedError as e:
                result['can_delete'] = False
                # Extraire les objets protégés
                protected_objects = list(e.protected_objects)
                for protected_obj in protected_objects[:20]:  # Limiter à 20
                    result['protected'].append({
                        'model': protected_obj.__class__.__name__,
                        'id': protected_obj.pk,
                        'str': str(protected_obj)[:100]
                    })
                result['warnings'].append(
                    f"Suppression impossible: {len(protected_objects)} objet(s) protégé(s) référencent cet élément."
                )
                return result

            # Analyser les objets collectés pour suppression
            # collector.data contient {model: set(instances)}
            for collected_model, instances in collector.data.items():
                if collected_model == model and len(instances) == 1:
                    # C'est l'objet principal, on le skip
                    continue

                model_name_collected = collected_model.__name__
                count = len(instances)

                # Ajouter au résumé
                if model_name_collected not in result['summary']:
                    result['summary'][model_name_collected] = 0
                result['summary'][model_name_collected] += count
                result['total_deletions'] += count

                # Ajouter les détails (limité à 10 par modèle)
                for instance in list(instances)[:10]:
                    result['cascade_deletions'].append({
                        'model': model_name_collected,
                        'id': instance.pk,
                        'str': str(instance)[:100]
                    })

            # Analyser les champs qui seront mis à NULL (SET_NULL)
            # et ceux avec SET_DEFAULT
            self._analyze_on_delete_actions(obj, result)

        except Exception as e:
            LogUtils.error(f"[CRUD] Erreur analyse impact suppression: {e}")
            result['warnings'].append(f"Erreur lors de l'analyse: {str(e)}")

        return result

    def _analyze_on_delete_actions(self, obj, result: Dict):
        """
        Analyse les relations pour identifier les actions SET_NULL, SET_DEFAULT, etc.
        """
        from django.db.models import SET_NULL, SET_DEFAULT, DO_NOTHING
        from django.db.models.fields.related import ForeignKey, OneToOneField

        model = obj.__class__

        # Parcourir les relations inverses (objets qui pointent vers cet objet)
        for related in model._meta.get_fields():
            if not hasattr(related, 'remote_field'):
                continue
            if not hasattr(related, 'related_model'):
                continue

            # C'est une relation inverse
            related_model = related.related_model
            if related_model == model:
                continue

            # Trouver le champ FK dans le modèle lié
            for field in related_model._meta.get_fields():
                if not isinstance(field, (ForeignKey, OneToOneField)):
                    continue
                if field.related_model != model:
                    continue

                on_delete = field.remote_field.on_delete
                field_name = field.name

                try:
                    # Compter les objets liés
                    related_objects = related_model.objects.filter(**{field_name: obj})
                    count = related_objects.count()

                    if count == 0:
                        continue

                    # Identifier l'action on_delete
                    if on_delete == SET_NULL:
                        result['set_null'].append({
                            'model': related_model.__name__,
                            'field': field_name,
                            'count': count,
                            'action': f"Le champ '{field_name}' sera mis à NULL"
                        })
                    elif on_delete == SET_DEFAULT:
                        default_value = field.default
                        result['set_default'].append({
                            'model': related_model.__name__,
                            'field': field_name,
                            'count': count,
                            'action': f"Le champ '{field_name}' sera mis à la valeur par défaut ({default_value})"
                        })
                    elif on_delete == DO_NOTHING:
                        result['warnings'].append(
                            f"{count} {related_model.__name__}(s) ont DO_NOTHING sur '{field_name}' - "
                            "cela pourrait causer des erreurs d'intégrité référentielle."
                        )

                except Exception as e:
                    LogUtils.info(f"[CRUD] Erreur analyse relation {related_model.__name__}: {e}")

    def format_deletion_impact_message(self, impact: Dict) -> str:
        """
        Formate l'impact de suppression en message lisible.
        """
        lines = []

        if not impact.get('can_delete'):
            lines.append("**SUPPRESSION IMPOSSIBLE**")
            for warning in impact.get('warnings', []):
                lines.append(f"- {warning}")
            if impact.get('protected'):
                lines.append("\nObjets protégés :")
                for item in impact['protected'][:10]:
                    lines.append(f"  - {item['model']} #{item['id']}: {item['str']}")
            return '\n'.join(lines)

        # Objet principal
        lines.append(f"**Suppression de:** {impact.get('object_str', 'Objet')}")

        # Résumé des suppressions en cascade
        if impact.get('total_deletions', 0) > 0:
            lines.append(f"\n**Suppressions en cascade:** {impact['total_deletions']} objet(s)")
            lines.append("\nDétail par type :")
            for model_name, count in sorted(impact.get('summary', {}).items()):
                lines.append(f"  - {model_name}: {count}")

            # Détails des objets (limités)
            if impact.get('cascade_deletions'):
                lines.append("\nObjets qui seront supprimés :")
                for item in impact['cascade_deletions'][:15]:
                    lines.append(f"  - {item['model']} #{item['id']}: {item['str']}")
                if len(impact['cascade_deletions']) > 15:
                    lines.append(f"  ... et {len(impact['cascade_deletions']) - 15} autres")
        else:
            lines.append("\nAucune suppression en cascade.")

        # Objets qui seront mis à NULL
        if impact.get('set_null'):
            lines.append("\n**Champs mis à NULL :**")
            for item in impact['set_null']:
                lines.append(f"  - {item['count']} {item['model']}(s): {item['action']}")

        # Objets qui seront mis à default
        if impact.get('set_default'):
            lines.append("\n**Champs mis à valeur par défaut :**")
            for item in impact['set_default']:
                lines.append(f"  - {item['count']} {item['model']}(s): {item['action']}")

        # Avertissements
        if impact.get('warnings'):
            lines.append("\n**Avertissements :**")
            for warning in impact['warnings']:
                lines.append(f"  - {warning}")

        return '\n'.join(lines)

    def _extract_id_from_url(self, url: str) -> Optional[int]:
        """
        Extrait un ID d'objet depuis une URL de redirection.

        Args:
            url: URL (ex: '/client/detail/123/')

        Returns:
            ID extrait ou None
        """
        if not url:
            return None

        import re
        # Chercher un nombre dans l'URL
        match = re.search(r'/(\d+)/?', url)
        if match:
            return int(match.group(1))
        return None
