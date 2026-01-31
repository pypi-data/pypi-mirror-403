"""
Service de gestion du contexte projet avec cache intelligent.

Optimise l'utilisation des tokens Claude en cachant:
- La structure du projet
- Les résumés des apps
- Les patterns de code communs
- Les informations sur les modèles/vues
"""
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from django.db import transaction

from lucy_assist.utils.log_utils import LogUtils
from lucy_assist.models import ProjectContextCache
from lucy_assist.services.gitlab_service import GitLabService


@dataclass
class CachedContext:
    """Représente un contexte mis en cache."""
    key: str
    data: Dict
    from_cache: bool
    tokens_estimated: int


class ProjectContextService:
    """
    Service pour gérer le contexte projet de manière optimisée.

    Stratégies d'optimisation:
    1. Cache hiérarchique (Redis/Django cache -> BDD)
    2. Pré-calcul des résumés de structure
    3. Indexation des patterns communs
    4. Compression du contexte pour réduire les tokens
    """

    # Estimation des tokens par type de contenu
    TOKENS_PER_CHAR = 0.25  # ~4 caractères par token en moyenne

    # TTL par type de cache (en heures)
    CACHE_TTL = {
        'project_structure': 168,  # 7 jours - change rarement
        'app_summary': 72,         # 3 jours
        'model_info': 48,          # 2 jours
        'view_info': 24,           # 1 jour
        'recent_changes': 1,       # 1 heure - change souvent
    }

    def __init__(self):
        self.gitlab_service = GitLabService()

    def _estimate_tokens(self, content: Any) -> int:
        """Estime le nombre de tokens pour un contenu."""
        if isinstance(content, dict) or isinstance(content, list):
            content = json.dumps(content, ensure_ascii=False)
        return int(len(str(content)) * self.TOKENS_PER_CHAR)

    def get_project_structure(self, force_refresh: bool = False) -> CachedContext:
        """
        Récupère la structure du projet (apps, modèles principaux).

        Cette information change rarement et peut être cachée longtemps.
        """
        cache_key = "project_structure"

        if not force_refresh:
            cached = ProjectContextCache.get_cached_content(cache_key)
            if cached:
                tokens_saved = self._estimate_tokens(cached)
                # Incrémenter le compteur
                try:
                    cache_obj = ProjectContextCache.objects.get(cache_key=cache_key)
                    cache_obj.increment_hit(tokens_saved)
                except ProjectContextCache.DoesNotExist:
                    pass

                return CachedContext(
                    key=cache_key,
                    data=cached,
                    from_cache=True,
                    tokens_estimated=tokens_saved
                )

        # Construire la structure depuis GitLab
        structure = self._build_project_structure()

        # Sauvegarder en cache
        content_hash = ProjectContextCache.compute_hash(structure)
        ProjectContextCache.set_cached_content(
            cache_key=cache_key,
            contenu=structure,
            content_hash=content_hash,
            ttl_hours=self.CACHE_TTL['project_structure']
        )

        return CachedContext(
            key=cache_key,
            data=structure,
            from_cache=False,
            tokens_estimated=self._estimate_tokens(structure)
        )

    def _build_project_structure(self) -> Dict:
        """Construit un résumé de la structure du projet."""
        # Rechercher les apps Django
        apps_search = self.gitlab_service.search_code("class.*Config.*AppConfig")

        apps = []
        for result in apps_search[:15]:  # Limiter à 15 apps
            filename = result.get('filename', '')
            if 'apps.py' in filename:
                app_name = filename.split('/')[1] if '/' in filename else filename.replace('/apps.py', '')
                apps.append({
                    'name': app_name,
                    'path': f"apps/{app_name}/"
                })

        # Résumé compact
        return {
            'type': 'django_project',
            'apps': apps,
            'summary': f"Projet Django avec {len(apps)} applications",
            'main_apps': [a['name'] for a in apps[:5]]  # Les 5 premières
        }

    def get_app_summary(self, app_name: str, force_refresh: bool = False) -> CachedContext:
        """
        Récupère le résumé d'une application.

        Inclut: modèles, vues principales, patterns utilisés.
        """
        cache_key = f"app_summary_{app_name}"

        if not force_refresh:
            cached = ProjectContextCache.get_cached_content(cache_key)
            if cached:
                return CachedContext(
                    key=cache_key,
                    data=cached,
                    from_cache=True,
                    tokens_estimated=self._estimate_tokens(cached)
                )

        # Construire le résumé de l'app
        summary = self._build_app_summary(app_name)

        ProjectContextCache.set_cached_content(
            cache_key=cache_key,
            contenu=summary,
            ttl_hours=self.CACHE_TTL['app_summary']
        )

        return CachedContext(
            key=cache_key,
            data=summary,
            from_cache=False,
            tokens_estimated=self._estimate_tokens(summary)
        )

    def _build_app_summary(self, app_name: str) -> Dict:
        """Construit un résumé d'une application Django."""
        summary = {
            'name': app_name,
            'models': [],
            'views': [],
            'urls_patterns': []
        }

        # Rechercher les modèles
        model_search = self.gitlab_service.search_code(f"class.*Model.*apps/{app_name}/models")
        for result in model_search[:10]:
            # Extraire le nom du modèle du data
            data = result.get('data', '')
            if 'class ' in data:
                model_name = data.split('class ')[1].split('(')[0].strip()
                summary['models'].append(model_name)

        # Rechercher les vues principales
        view_search = self.gitlab_service.search_code(f"class.*View.*apps/{app_name}/views")
        for result in view_search[:10]:
            data = result.get('data', '')
            if 'class ' in data:
                view_name = data.split('class ')[1].split('(')[0].strip()
                summary['views'].append(view_name)

        return summary

    def get_model_info(
        self,
        model_name: str,
        include_code: bool = False,
        force_refresh: bool = False
    ) -> CachedContext:
        """
        Récupère les informations sur un modèle.

        Args:
            model_name: Nom du modèle
            include_code: Inclure le code source (plus de tokens)
            force_refresh: Forcer le rafraîchissement
        """
        cache_key = f"model_info_{model_name}_{include_code}"

        if not force_refresh:
            cached = ProjectContextCache.get_cached_content(cache_key)
            if cached:
                return CachedContext(
                    key=cache_key,
                    data=cached,
                    from_cache=True,
                    tokens_estimated=self._estimate_tokens(cached)
                )

        # Récupérer les infos du modèle
        model_data = self.gitlab_service.find_model_and_form(model_name)

        info = {
            'name': model_name,
            'model_file': model_data.get('model_file'),
            'form_file': model_data.get('form_file'),
            'has_form': model_data.get('form_code') is not None
        }

        if include_code:
            # Compresser le code en ne gardant que les parties essentielles
            model_code = model_data.get('model_code', '')
            if model_code:
                info['model_fields'] = self._extract_model_fields(model_code, model_name)

        ProjectContextCache.set_cached_content(
            cache_key=cache_key,
            contenu=info,
            ttl_hours=self.CACHE_TTL['model_info']
        )

        return CachedContext(
            key=cache_key,
            data=info,
            from_cache=False,
            tokens_estimated=self._estimate_tokens(info)
        )

    def _extract_model_fields(self, code: str, model_name: str) -> List[str]:
        """Extrait les champs d'un modèle (version compressée)."""
        import re

        fields = []
        # Pattern pour trouver les champs Django
        field_pattern = r'(\w+)\s*=\s*models\.(\w+)'
        matches = re.findall(field_pattern, code)

        for field_name, field_type in matches[:20]:  # Limiter à 20 champs
            fields.append(f"{field_name}: {field_type}")

        return fields

    def get_optimized_context(
        self,
        page_url: str,
        user_question: str,
        conversation_history: List[Dict] = None
    ) -> Dict:
        """
        Construit un contexte optimisé pour Claude.

        Sélectionne intelligemment les informations pertinentes
        en fonction de la question et de la page.

        Returns:
            Dict avec le contexte optimisé et les stats
        """
        context = {
            'page': page_url,
            'relevant_info': {},
            'stats': {
                'tokens_from_cache': 0,
                'tokens_fresh': 0,
                'cache_hits': 0
            }
        }

        # 1. Toujours inclure un résumé léger du projet
        project = self.get_project_structure()
        if project.from_cache:
            context['stats']['tokens_from_cache'] += project.tokens_estimated
            context['stats']['cache_hits'] += 1
        else:
            context['stats']['tokens_fresh'] += project.tokens_estimated

        context['relevant_info']['project'] = {
            'apps': project.data.get('main_apps', []),
            'summary': project.data.get('summary', '')
        }

        # 2. Détecter l'app concernée par la page
        app_name = self._detect_app_from_url(page_url)
        if app_name:
            app_summary = self.get_app_summary(app_name)
            if app_summary.from_cache:
                context['stats']['tokens_from_cache'] += app_summary.tokens_estimated
                context['stats']['cache_hits'] += 1
            else:
                context['stats']['tokens_fresh'] += app_summary.tokens_estimated

            context['relevant_info']['current_app'] = {
                'name': app_name,
                'models': app_summary.data.get('models', [])[:5],
                'views': app_summary.data.get('views', [])[:5]
            }

        # 3. Si la question mentionne un modèle spécifique
        model_name = self._detect_model_from_question(user_question)
        if model_name:
            model_info = self.get_model_info(model_name)
            if model_info.from_cache:
                context['stats']['tokens_from_cache'] += model_info.tokens_estimated
                context['stats']['cache_hits'] += 1

            context['relevant_info']['model'] = model_info.data

        return context

    def _detect_app_from_url(self, url: str) -> Optional[str]:
        """Détecte l'application Django depuis l'URL."""
        parts = url.strip('/').split('/')
        if parts:
            return parts[0]
        return None

    def _detect_model_from_question(self, question: str) -> Optional[str]:
        """Détecte si la question mentionne un modèle."""
        # Mots-clés courants et leurs modèles associés
        model_keywords = {
            'membre': 'Membre',
            'adhésion': 'Adhesion',
            'cotisation': 'Cotisation',
            'utilisateur': 'Utilisateur',
            'user': 'Utilisateur',
            'paiement': 'Paiement',
            'facture': 'Facture',
            'structure': 'Structure',
        }

        question_lower = question.lower()
        for keyword, model in model_keywords.items():
            if keyword in question_lower:
                return model

        return None

    def summarize_conversation(
        self,
        messages: List[Dict],
        max_tokens: int = 500
    ) -> str:
        """
        Résume une conversation longue pour économiser des tokens.

        Au lieu d'envoyer tout l'historique, crée un résumé
        des points clés de la conversation.
        """
        if not messages or len(messages) <= 4:
            # Conversation courte, pas besoin de résumer
            return None

        # Garder les 2 premiers et 2 derniers messages
        # Résumer le milieu
        first_messages = messages[:2]
        last_messages = messages[-2:]
        middle_messages = messages[2:-2]

        if not middle_messages:
            return None

        # Créer un résumé textuel simple
        summary_parts = []

        for msg in middle_messages:
            role = "Utilisateur" if msg.get('role') == 'user' else "Assistant"
            content = msg.get('content', '')[:100]  # Tronquer
            summary_parts.append(f"- {role}: {content}...")

        summary = "Résumé des échanges précédents:\n" + "\n".join(summary_parts)

        # Retourner le format optimisé
        return {
            'type': 'conversation_summary',
            'first_messages': first_messages,
            'summary': summary,
            'last_messages': last_messages,
            'original_count': len(messages),
            'tokens_saved_estimate': self._estimate_tokens(middle_messages) - self._estimate_tokens(summary)
        }

    @transaction.atomic
    def cleanup_expired_caches(self) -> int:
        """Nettoie les caches expirés."""
        from django.utils import timezone

        deleted_count, _ = ProjectContextCache.objects.filter(
            expire_at__lt=timezone.now()
        ).delete()

        return deleted_count

    def get_cache_stats(self) -> Dict:
        """Retourne les statistiques de cache."""
        return ProjectContextCache.get_stats()
