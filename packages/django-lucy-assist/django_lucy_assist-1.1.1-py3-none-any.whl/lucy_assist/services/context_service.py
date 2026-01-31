"""
Service de détection et construction du contexte de page.
"""
import re
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

from django.urls import resolve, Resolver404
from django.apps import apps

from lucy_assist.utils.log_utils import LogUtils
from lucy_assist.conf import lucy_assist_settings


class ContextService:
    """Service pour construire le contexte de la page courante."""

    # Patterns pour détecter les dates dans les requêtes
    DATE_PATTERNS = [
        (r'(\d{1,2})/(\d{1,2})/(\d{4})', '%d/%m/%Y'),  # 18/10/2025
        (r'(\d{1,2})-(\d{1,2})-(\d{4})', '%d-%m-%Y'),  # 18-10-2025
        (r'(\d{4})/(\d{1,2})/(\d{1,2})', '%Y/%m/%d'),  # 2025/10/18
        (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),  # 2025-10-18
    ]

    def __init__(self, user):
        self.user = user

    def _extract_date_from_query(self, query: str) -> Optional[datetime]:
        """
        Extrait une date d'une requête texte.
        Supporte les formats: 18/10/2025, 18-10-2025, 2025/10/18, 2025-10-18
        """
        for pattern, date_format in self.DATE_PATTERNS:
            match = re.search(pattern, query)
            if match:
                try:
                    date_str = match.group(0)
                    return datetime.strptime(date_str, date_format)
                except ValueError:
                    continue
        return None

    def _remove_date_from_query(self, query: str) -> str:
        """Supprime la date de la requête pour garder les autres mots-clés."""
        for pattern, _ in self.DATE_PATTERNS:
            query = re.sub(pattern, '', query)
        return query.strip()

    def get_page_context(self, url_path: str) -> Dict:
        """
        Construit le contexte complet d'une page.

        Args:
            url_path: URL de la page (ex: /membre/list)

        Returns:
            Dict avec les informations de contexte
        """
        context = {
            'url': url_path,
            'app_name': None,
            'view_name': None,
            'model_name': None,
            'object_id': None,
            'action': None,
            'available_actions': [],
            'help_text': None
        }

        if not url_path:
            return context

        # Parser l'URL
        parsed = urlparse(url_path)
        path = parsed.path

        try:
            # Résoudre l'URL Django
            match = resolve(path)

            context['app_name'] = match.app_name
            context['view_name'] = match.url_name

            # Extraire l'ID d'objet si présent
            if 'pk' in match.kwargs:
                context['object_id'] = match.kwargs['pk']
            elif 'id' in match.kwargs:
                context['object_id'] = match.kwargs['id']

            # Déterminer l'action
            context['action'] = self._detect_action(match.url_name)

            # Trouver le modèle associé
            context['model_name'] = self._find_model_name(match)

            # Déterminer les actions disponibles
            context['available_actions'] = self._get_available_actions(
                match.app_name,
                context['model_name']
            )

            # Générer le texte d'aide
            context['help_text'] = self._generate_help_text(context)

        except Resolver404:
            LogUtils.info(f"URL non résolue: {path}")
            # Essayer d'extraire les infos depuis le path
            context.update(self._parse_url_manually(path))

        return context

    def _detect_action(self, url_name: str) -> Optional[str]:
        """Détecte l'action à partir du nom de l'URL."""
        if not url_name:
            return None

        url_name_lower = url_name.lower()

        if 'list' in url_name_lower:
            return 'list'
        elif 'form' in url_name_lower or 'create' in url_name_lower or 'add' in url_name_lower:
            return 'create_or_edit'
        elif 'detail' in url_name_lower or 'view' in url_name_lower:
            return 'detail'
        elif 'delete' in url_name_lower:
            return 'delete'
        elif 'edit' in url_name_lower or 'update' in url_name_lower:
            return 'edit'

        return 'unknown'

    def _find_model_name(self, match) -> Optional[str]:
        """Trouve le nom du modèle à partir de la vue."""
        if not match.url_name:
            return None

        # Extraire le nom du modèle depuis le nom de l'URL
        # Pattern: model-action (ex: membre-list, paiement-form)
        parts = match.url_name.split('-')
        if parts:
            model_name = parts[0].capitalize()

            # Vérifier si le modèle existe
            if match.app_name:
                try:
                    app_config = apps.get_app_config(match.app_name.split(':')[-1])
                    for model in app_config.get_models():
                        if model.__name__.lower() == parts[0].lower():
                            return model.__name__
                except LookupError:
                    pass

            return model_name

        return None

    def _get_available_actions(self, app_name: str, model_name: str) -> List[Dict]:
        """Retourne les actions disponibles pour l'utilisateur."""
        actions = []

        if not app_name or not model_name:
            return actions

        model_lower = model_name.lower()
        app_simple = app_name.split(':')[-1] if app_name else ''

        # Vérifier les permissions
        permission_map = {
            'view': f'{app_simple}.view_{model_lower}',
            'add': f'{app_simple}.add_{model_lower}',
            'change': f'{app_simple}.change_{model_lower}',
            'delete': f'{app_simple}.delete_{model_lower}',
        }

        for action, perm in permission_map.items():
            has_perm = self.user.has_perm(perm) if self.user else False
            actions.append({
                'action': action,
                'permission': perm,
                'allowed': has_perm or (self.user and self.user.is_superuser)
            })

        return actions

    def _generate_help_text(self, context: Dict) -> str:
        """Génère un texte d'aide contextuel."""
        action = context.get('action')
        model = context.get('model_name', 'élément')

        help_texts = {
            'list': f"Vous êtes sur la liste des {model}s. Vous pouvez filtrer, rechercher ou créer un nouveau {model}.",
            'create_or_edit': f"Vous êtes sur le formulaire de {model}. Remplissez les champs requis et cliquez sur Enregistrer.",
            'detail': f"Vous consultez les détails d'un {model}. Vous pouvez le modifier ou le supprimer si vous avez les droits.",
            'delete': f"Vous allez supprimer ce {model}. Cette action est irréversible.",
            'edit': f"Vous modifiez un {model} existant. Les modifications seront enregistrées après validation.",
        }

        return help_texts.get(action, f"Vous êtes sur la page {context.get('view_name', 'inconnue')}.")

    def _parse_url_manually(self, path: str) -> Dict:
        """Parse l'URL manuellement si Django ne peut pas la résoudre."""
        result = {
            'app_name': None,
            'view_name': None,
            'action': None
        }

        parts = path.strip('/').split('/')
        if parts:
            result['app_name'] = parts[0]

            if len(parts) > 1:
                action_part = parts[1]
                if 'list' in action_part:
                    result['action'] = 'list'
                elif 'form' in action_part:
                    result['action'] = 'create_or_edit'
                elif 'detail' in action_part:
                    result['action'] = 'detail'

                result['view_name'] = action_part

        return result

    def get_form_info(self, app_name: str, model_name: str) -> Optional[Dict]:
        """
        Récupère les informations sur un formulaire.

        Returns:
            Dict avec 'fields', 'required_fields', 'help_texts'
        """
        if not app_name or not model_name:
            return None

        try:
            # Trouver le modèle
            app_simple = app_name.split(':')[-1]
            model = apps.get_model(app_simple, model_name)

            # Extraire les informations des champs
            fields = []
            required_fields = []

            for field in model._meta.get_fields():
                if hasattr(field, 'verbose_name'):
                    field_info = {
                        'name': field.name,
                        'verbose_name': str(field.verbose_name),
                        'type': field.get_internal_type() if hasattr(field, 'get_internal_type') else 'Unknown',
                        'required': not getattr(field, 'blank', True),
                        'help_text': str(field.help_text) if hasattr(field, 'help_text') else ''
                    }
                    fields.append(field_info)

                    if field_info['required']:
                        required_fields.append(field_info['verbose_name'])

            return {
                'model': model_name,
                'fields': fields,
                'required_fields': required_fields
            }

        except LookupError:
            LogUtils.info(f"Modèle non trouvé: {app_name}.{model_name}")
            return None

    def search_objects(
        self,
        query: str,
        model_name: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Recherche des objets dans la base de données.

        Args:
            query: Terme de recherche
            model_name: Nom du modèle (optionnel, cherche dans tous si None)
            limit: Nombre max de résultats

        Returns:
            Liste de résultats avec 'model', 'id', 'str', 'url'
        """
        results = []

        # Liste des modèles à rechercher
        models_to_search = []

        if model_name:
            # Chercher le modèle spécifique
            for app_config in apps.get_app_configs():
                try:
                    model = app_config.get_model(model_name)
                    models_to_search.append(model)
                    break
                except LookupError:
                    continue
        else:
            # Découvrir dynamiquement les modèles du projet
            apps_prefix = lucy_assist_settings.PROJECT_APPS_PREFIX

            for app_config in apps.get_app_configs():
                # Filtrer par préfixe si configuré
                if apps_prefix and not app_config.name.startswith(apps_prefix):
                    continue

                # Exclure les apps système et lucy_assist
                if app_config.name.startswith('django.') or app_config.name == 'lucy_assist':
                    continue

                # Ajouter les modèles de cette app (limiter à 3 par app)
                app_models = list(app_config.get_models())[:3]
                models_to_search.extend(app_models)

                # Limiter le nombre total de modèles à rechercher
                if len(models_to_search) >= 10:
                    break

        # Log des modèles découverts pour debug
        LogUtils.info(f"[search_objects] Recherche '{query}' dans {len(models_to_search)} modèles: {[m.__name__ for m in models_to_search]}")

        # Extraire une date de la requête si présente
        search_date = self._extract_date_from_query(query)
        text_query = self._remove_date_from_query(query) if search_date else query

        if search_date:
            LogUtils.info(f"[search_objects] Date détectée: {search_date.date()}")

        # Rechercher dans chaque modèle
        for model in models_to_search:
            try:
                # Trouver les champs texte et date pour la recherche
                search_fields = []
                date_fields = []  # DateField (comparaison directe)
                datetime_fields = []  # DateTimeField (utilise __date)
                for field in model._meta.get_fields():
                    if hasattr(field, 'get_internal_type'):
                        field_type = field.get_internal_type()
                        if field_type in ['CharField', 'TextField']:
                            search_fields.append(field.name)
                        elif field_type == 'DateField':
                            date_fields.append(field.name)
                        elif field_type == 'DateTimeField':
                            datetime_fields.append(field.name)

                # Construire la requête
                from django.db.models import Q
                q_objects = None
                has_criteria = False

                # Si on a une date, chercher dans les champs date
                if search_date and (date_fields or datetime_fields):
                    date_q = Q()
                    search_date_only = search_date.date()

                    # DateField: comparaison directe
                    for field_name in date_fields:
                        date_q |= Q(**{field_name: search_date_only})

                    # DateTimeField: utiliser __date
                    for field_name in datetime_fields:
                        date_q |= Q(**{f'{field_name}__date': search_date_only})

                    q_objects = date_q
                    has_criteria = True
                    LogUtils.info(f"[search_objects] {model.__name__}: recherche date dans DateField={date_fields}, DateTimeField={datetime_fields}")

                # Si on a du texte, chercher dans les champs texte
                if text_query.strip() and search_fields:
                    query_words = text_query.strip().split()
                    text_q = Q()

                    if len(query_words) > 1:
                        # Recherche multi-mots: chaque mot doit matcher au moins un champ
                        for word in query_words:
                            word_q = Q()
                            for field_name in search_fields[:5]:
                                word_q |= Q(**{f'{field_name}__icontains': word})
                            text_q &= word_q
                    else:
                        # Recherche simple
                        for field_name in search_fields[:5]:
                            text_q |= Q(**{f'{field_name}__icontains': text_query})

                    if q_objects is not None:
                        q_objects &= text_q
                    else:
                        q_objects = text_q
                    has_criteria = True

                # Si pas de critère de recherche valide, skip
                if not has_criteria:
                    if not search_fields and not date_fields and not datetime_fields:
                        LogUtils.info(f"[search_objects] {model.__name__}: aucun champ recherchable")
                    continue

                # Filtrer par permissions si possible
                # Note: certains modèles utilisent des managers customs qui
                # dépendent de ThreadLocal/middleware pour l'utilisateur courant
                try:
                    queryset = model.objects.all()
                    count = queryset.count()
                    LogUtils.info(f"[search_objects] {model.__name__}: {count} objets en base")
                    objects = queryset.filter(q_objects)[:limit]
                except AttributeError as e:
                    # Si le manager a besoin d'un utilisateur non disponible, skip ce modèle
                    LogUtils.info(f"[search_objects] {model.__name__}: skip (AttributeError: {e})")
                    continue

                for obj in objects:
                    result = {
                        'model': model.__name__,
                        'id': obj.pk,
                        'str': str(obj),
                        'url': self._get_object_url(model, obj)
                    }
                    results.append(result)

                    if len(results) >= limit:
                        return results

            except Exception as e:
                LogUtils.info(f"[search_objects] Erreur recherche dans {model.__name__}: {e}")
                continue

        return results

    def _get_object_url(self, model, obj) -> Optional[str]:
        """Génère l'URL de détail d'un objet."""
        try:
            from django.urls import reverse
            app_label = model._meta.app_label
            model_name = model.__name__.lower()

            # Essayer différents patterns d'URL
            url_patterns = [
                f'{app_label}:{model_name}-detail',
                f'{app_label}:{model_name}-form',
                f'{model_name}-detail',
            ]

            for pattern in url_patterns:
                try:
                    return reverse(pattern, kwargs={'pk': obj.pk})
                except Exception:
                    continue

            return None

        except Exception:
            return None
