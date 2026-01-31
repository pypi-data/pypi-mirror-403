"""
Service de découverte automatique des vues CRUD du projet.

Parcourt les URL patterns Django pour identifier les vues CRUD
et construire un mapping utilisable par Lucy Assist.
"""
import re
from typing import Dict, List, Optional, Tuple
from django.urls import URLPattern, URLResolver, get_resolver
from django.urls.resolvers import RoutePattern

from lucy_assist.utils.log_utils import LogUtils
from lucy_assist.conf import lucy_assist_settings


class ViewDiscoveryService:
    """
    Service pour découvrir automatiquement les vues CRUD d'un projet Django.
    """

    # Patterns de nommage courants pour les vues CRUD
    # L'ordre est important : les patterns plus spécifiques doivent être en premier
    CRUD_PATTERNS = {
        'list': [
            r'-list$', r'-liste$', r'-gestion$', r'-index$',
            r'_list$', r'_liste$', r'_gestion$', r'_index$',
            r'list$', r'liste$', r'gestion$'
        ],
        'create': [
            r'-create$', r'-add$', r'-nouveau$', r'-new$',
            r'_create$', r'_add$', r'_nouveau$', r'_new$',
            r'create$', r'add$', r'nouveau$'
        ],
        'detail': [
            r'-detail$', r'-view$', r'-show$', r'-fiche$', r'-consulter$',
            r'_detail$', r'_view$', r'_show$', r'_fiche$',
            r'detail$', r'view$', r'fiche$'
        ],
        'update': [
            r'-update$', r'-edit$', r'-modifier$', r'-modification$',
            r'_update$', r'_edit$', r'_modifier$',
            r'update$', r'edit$', r'modifier$'
        ],
        'delete': [
            r'-delete$', r'-suppression$', r'-supprimer$', r'-remove$',
            r'_delete$', r'_suppression$', r'_supprimer$', r'_remove$',
            r'delete$', r'suppression$', r'supprimer$'
        ],
        # Formulaire peut être create ou update selon le contexte
        'formulaire': [
            r'-formulaire$', r'_formulaire$', r'formulaire$',
            r'-form$', r'_form$', r'form$'
        ]
    }

    # Patterns d'URL pour détecter les paramètres
    URL_PARAM_PATTERNS = [
        (r'<int:pk>', 'pk'),
        (r'<pk>', 'pk'),
        (r'<int:id>', 'id'),
        (r'<id>', 'id'),
        (r'<slug:slug>', 'slug'),
    ]

    def __init__(self):
        self.apps_prefix = lucy_assist_settings.PROJECT_APPS_PREFIX or ''

    def discover_crud_views(self) -> Dict:
        """
        Découvre toutes les vues CRUD du projet.

        Returns:
            Dict avec le mapping modèle -> actions -> infos vue
        """
        LogUtils.info("[ViewDiscovery] Début de la découverte des vues CRUD")

        crud_mapping = {}
        resolver = get_resolver()

        # Parcourir tous les URL patterns
        self._scan_url_patterns(resolver.url_patterns, '', '', crud_mapping)

        LogUtils.info(f"[ViewDiscovery] {len(crud_mapping)} modèles découverts")
        for model, actions in crud_mapping.items():
            LogUtils.info(f"[ViewDiscovery] {model}: {list(actions.keys())}")

        return crud_mapping

    def _scan_url_patterns(
        self,
        patterns: List,
        namespace: str,
        url_prefix: str,
        crud_mapping: Dict
    ):
        """
        Parcourt récursivement les URL patterns.
        """
        for pattern in patterns:
            if isinstance(pattern, URLResolver):
                # C'est un include() - descendre récursivement
                new_namespace = pattern.namespace
                if namespace and new_namespace:
                    new_namespace = f"{namespace}:{new_namespace}"
                elif namespace:
                    new_namespace = namespace

                # Construire le préfixe URL
                pattern_str = self._get_pattern_string(pattern.pattern)
                new_url_prefix = url_prefix + pattern_str

                # Filtrer par préfixe d'apps si configuré
                app_name = getattr(pattern, 'app_name', '') or ''
                if self.apps_prefix:
                    # Vérifier si c'est une app du projet
                    if app_name and not app_name.startswith(self.apps_prefix.rstrip('.')):
                        # Permettre aussi les apps dont le namespace correspond
                        if new_namespace and not any(
                            new_namespace.startswith(prefix)
                            for prefix in ['admin', 'lucy_assist']
                        ):
                            pass  # Continuer l'exploration
                        else:
                            continue

                self._scan_url_patterns(
                    pattern.url_patterns,
                    new_namespace or '',
                    new_url_prefix,
                    crud_mapping
                )

            elif isinstance(pattern, URLPattern):
                # C'est une vue finale
                self._process_url_pattern(
                    pattern,
                    namespace,
                    url_prefix,
                    crud_mapping
                )

    def _process_url_pattern(
        self,
        pattern: URLPattern,
        namespace: str,
        url_prefix: str,
        crud_mapping: Dict
    ):
        """
        Analyse un URL pattern pour détecter s'il s'agit d'une vue CRUD.
        """
        url_name = pattern.name
        if not url_name:
            return

        # Construire l'URL complète
        pattern_str = self._get_pattern_string(pattern.pattern)
        full_url = '/' + url_prefix + pattern_str
        full_url = re.sub(r'/+', '/', full_url)  # Normaliser les slashes

        # Construire le nom complet de la vue
        full_name = f"{namespace}:{url_name}" if namespace else url_name

        # Détecter le modèle et l'action depuis le nom de l'URL
        model_name, action = self._detect_model_and_action(url_name)

        if not model_name or not action:
            return

        # Détecter si l'URL nécessite un paramètre (pk, id, etc.)
        requires_pk = self._url_requires_pk(full_url)

        # Déterminer la méthode HTTP
        http_method = self._detect_http_method(pattern, action)

        # Ajouter au mapping
        model_lower = model_name.lower()
        if model_lower not in crud_mapping:
            crud_mapping[model_lower] = {}

        # Les vues "formulaire" gèrent généralement create ET update
        if action == 'formulaire':
            crud_mapping[model_lower]['create'] = {
                'url_name': full_name,
                'url': full_url,
                'method': 'POST',
                'requires_pk': False
            }
            crud_mapping[model_lower]['update'] = {
                'url_name': full_name,
                'url': full_url,
                'method': 'POST',
                'requires_pk': True  # pk passé en POST ou GET
            }
            return

        # Pour les autres actions create/update
        if action == 'create' and requires_pk:
            # C'est probablement une vue qui gère create et update
            action = 'update'

        crud_mapping[model_lower][action] = {
            'url_name': full_name,
            'url': full_url,
            'method': http_method,
            'requires_pk': requires_pk
        }

    def _detect_model_and_action(self, url_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Détecte le nom du modèle et l'action CRUD depuis le nom de l'URL.

        Args:
            url_name: Nom de l'URL (ex: 'client-list', 'reservation-formulaire', 'client-b2b-gestion')

        Returns:
            Tuple (model_name, action) ou (None, None)
        """
        url_name_lower = url_name.lower()

        # Chercher l'action dans le nom
        detected_action = None
        matched_pattern = None

        for action, patterns in self.CRUD_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url_name_lower):
                    detected_action = action
                    matched_pattern = pattern
                    break
            if detected_action:
                break

        if not detected_action:
            return None, None

        # Extraire le nom du modèle en retirant le pattern d'action trouvé
        model_name = re.sub(matched_pattern, '', url_name_lower)

        # Nettoyer le nom du modèle
        model_name = model_name.strip('-_')

        # Convertir les tirets en underscores pour la cohérence
        # mais garder aussi la version avec tirets pour le mapping
        model_name_normalized = model_name.replace('-', '_')

        if not model_name:
            return None, None

        # Retourner la version normalisée (avec underscores)
        return model_name_normalized, detected_action

    def _get_pattern_string(self, pattern) -> str:
        """
        Extrait la chaîne de pattern depuis un RoutePattern ou RegexPattern.
        """
        if hasattr(pattern, '_route'):
            return pattern._route
        elif hasattr(pattern, '_regex'):
            # Convertir le regex en quelque chose de lisible
            regex = pattern._regex
            # Simplifier les captures
            regex = re.sub(r'\(\?P<(\w+)>[^)]+\)', r'<\1>', regex)
            regex = regex.strip('^$')
            return regex
        return ''

    def _url_requires_pk(self, url: str) -> bool:
        """
        Vérifie si l'URL nécessite un paramètre pk/id.
        """
        pk_patterns = ['<pk>', '<int:pk>', '<id>', '<int:id>', '<slug>']
        return any(p in url for p in pk_patterns)

    def _detect_http_method(self, pattern: URLPattern, action: str) -> str:
        """
        Détecte la méthode HTTP appropriée pour une action.
        """
        # Pour les vues basées sur des classes, on peut essayer de détecter
        # les méthodes supportées, mais par défaut on utilise les conventions

        method_map = {
            'list': 'GET',
            'detail': 'GET',
            'create': 'POST',
            'update': 'POST',  # Souvent POST dans Django (pas PUT)
            'delete': 'POST',  # Souvent POST dans Django (pas DELETE)
        }

        return method_map.get(action, 'GET')

    def get_view_info(self, model_name: str, action: str) -> Optional[Dict]:
        """
        Récupère les informations d'une vue pour un modèle et une action.

        Args:
            model_name: Nom du modèle
            action: Action CRUD ('list', 'create', 'detail', 'update', 'delete')

        Returns:
            Dict avec 'url_name', 'url', 'method', 'requires_pk' ou None
        """
        from lucy_assist.models import ConfigurationLucyAssist
        config = ConfigurationLucyAssist.get_config()

        if not config.crud_views_mapping:
            config.refresh_crud_views_mapping()

        model_lower = model_name.lower()

        # Essayer plusieurs variations du nom de modèle
        variations = [
            model_lower,
            model_lower.replace('_', '-'),  # client_b2b -> client-b2b
            model_lower.replace('-', '_'),  # client-b2b -> client_b2b
            model_lower.replace('_', ''),   # client_b2b -> clientb2b
        ]

        for variant in variations:
            model_views = config.crud_views_mapping.get(variant, {})
            if model_views and action in model_views:
                return model_views.get(action)

        return None

    def get_all_discovered_models(self) -> List[str]:
        """
        Retourne la liste de tous les modèles découverts avec des vues CRUD.

        Returns:
            Liste des noms de modèles
        """
        from lucy_assist.models import ConfigurationLucyAssist
        config = ConfigurationLucyAssist.get_config()

        if not config.crud_views_mapping:
            config.refresh_crud_views_mapping()

        return list(config.crud_views_mapping.keys())
