"""
Service d'intégration avec GitLab pour l'analyse de code.
"""
import re
from typing import Dict, List, Optional
from urllib.parse import quote

from django.conf import settings

import requests

from lucy_assist.utils.log_utils import LogUtils


class GitLabService:
    """Service pour interagir avec l'API GitLab."""

    def __init__(self):
        self.token = getattr(settings, 'GITLAB_TOKEN', None)
        self.base_url = getattr(settings, 'GITLAB_URL', 'https://gitlab.com')
        self.project_id = getattr(settings, 'GITLAB_PROJECT_ID', None)

        if not self.token:
            LogUtils.error("GITLAB_TOKEN non configuré")

    @property
    def headers(self) -> Dict[str, str]:
        """Headers pour les requêtes API."""
        return {
            'PRIVATE-TOKEN': self.token,
            'Content-Type': 'application/json'
        }

    def _api_url(self, endpoint: str) -> str:
        """Construit l'URL de l'API."""
        return f"{self.base_url}/api/v4{endpoint}"

    def search_code(
            self,
            query: str,
            scope: str = 'blobs',
            per_page: int = 10
    ) -> List[Dict]:
        """
        Recherche dans le code source du projet.

        Args:
            query: Terme de recherche
            scope: 'blobs' (fichiers), 'commits', 'issues'
            per_page: Nombre de résultats

        Returns:
            Liste des résultats de recherche
        """
        if not self.token or not self.project_id:
            LogUtils.error("GitLab non configuré pour la recherche de code")
            return []

        try:
            url = self._api_url(f"/projects/{self.project_id}/search")
            params = {
                'scope': scope,
                'search': query,
                'per_page': per_page
            }

            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:
            LogUtils.error(f"Erreur lors de la recherche GitLab: {e}")
            return []

    def get_file_content(
            self,
            file_path: str,
            ref: str = 'main'
    ) -> Optional[str]:
        """
        Récupère le contenu d'un fichier.

        Args:
            file_path: Chemin du fichier dans le repo
            ref: Branche ou tag

        Returns:
            Contenu du fichier ou None
        """
        if not self.token or not self.project_id:
            return None

        try:
            encoded_path = quote(file_path, safe='')
            url = self._api_url(
                f"/projects/{self.project_id}/repository/files/{encoded_path}/raw"
            )
            params = {'ref': ref}

            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()

            return response.text

        except requests.RequestException as e:
            LogUtils.error(f"Erreur lors de la récupération du fichier {file_path}: {e}")
            return None

    def get_file_blame(
            self,
            file_path: str,
            ref: str = 'main'
    ) -> List[Dict]:
        """
        Récupère le blame d'un fichier (qui a modifié quoi).

        Returns:
            Liste des blocs de blame
        """
        if not self.token or not self.project_id:
            return []

        try:
            encoded_path = quote(file_path, safe='')
            url = self._api_url(
                f"/projects/{self.project_id}/repository/files/{encoded_path}/blame"
            )
            params = {'ref': ref}

            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:
            LogUtils.error(f"Erreur lors du blame du fichier {file_path}: {e}")
            return []

    def find_view_for_url(self, url_path: str) -> Optional[Dict]:
        """
        Trouve la vue Django correspondant à une URL.

        Args:
            url_path: Chemin de l'URL (ex: /membre/list)

        Returns:
            Dict avec 'file_path', 'view_name', 'code' ou None
        """
        # Extraire le nom de l'app et la vue potentielle
        parts = url_path.strip('/').split('/')
        if not parts:
            return None

        app_name = parts[0]

        # Chercher dans les fichiers urls.py et views.py
        search_results = self.search_code(f"path.*{parts[-1] if len(parts) > 1 else app_name}")

        for result in search_results:
            if 'urls.py' in result.get('filename', ''):
                # Trouver le nom de la vue associée
                content = self.get_file_content(result['filename'])
                if content:
                    # Chercher la vue correspondante
                    view_match = re.search(
                        rf'path\(["\'][^"\']*{re.escape(parts[-1] if len(parts) > 1 else "")}["\'][^)]*views\.(\w+)',
                        content
                    )
                    if view_match:
                        view_name = view_match.group(1)
                        # Chercher le fichier de la vue
                        views_path = result['filename'].replace('urls.py', f'views/{view_name.lower()}_views.py')
                        view_content = self.get_file_content(views_path)

                        if not view_content:
                            # Essayer le fichier views.py principal
                            views_path = result['filename'].replace('urls.py', 'views.py')
                            view_content = self.get_file_content(views_path)

                        return {
                            'file_path': views_path,
                            'view_name': view_name,
                            'code': view_content
                        }

        return None

    def find_model_and_form(self, model_name: str) -> Dict:
        """
        Trouve le modèle et le formulaire correspondant.

        Returns:
            Dict avec 'model_file', 'model_code', 'form_file', 'form_code'
        """
        result = {
            'model_file': None,
            'model_code': None,
            'form_file': None,
            'form_code': None
        }

        # Chercher le modèle
        model_search = self.search_code(f"class {model_name}(")
        for item in model_search:
            if 'models' in item.get('filename', ''):
                result['model_file'] = item['filename']
                result['model_code'] = self.get_file_content(item['filename'])
                break

        # Chercher le formulaire
        form_search = self.search_code(f"class {model_name}Form(")
        for item in form_search:
            if 'forms' in item.get('filename', ''):
                result['form_file'] = item['filename']
                result['form_code'] = self.get_file_content(item['filename'])
                break

        return result

    def get_recent_commits(self, per_page: int = 10) -> List[Dict]:
        """
        Récupère les commits récents.

        Returns:
            Liste des commits avec 'id', 'message', 'author', 'date'
        """
        if not self.token or not self.project_id:
            return []

        try:
            url = self._api_url(f"/projects/{self.project_id}/repository/commits")
            params = {'per_page': per_page}

            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()

            commits = response.json()
            return [{
                'id': c['short_id'],
                'message': c['title'],
                'author': c['author_name'],
                'date': c['created_at']
            } for c in commits]

        except requests.RequestException as e:
            LogUtils.error(f"Erreur lors de la récupération des commits: {e}")
            return []
