# Django Lucy Assist

Assistant IA intelligent basé sur Claude d'Anthropic, intégrable dans n'importe quelle application Django.

## Installation

```bash
pip install django-lucy-assist
```

## Configuration

### 1. Ajouter l'application à INSTALLED_APPS

```python
INSTALLED_APPS = [
    ...
    'lucy_assist',
]
```

### 2. Configurer les variables d'environnement

Ajouter dans votre fichier `.env` :

```bash
# ======================================== LUCY ASSIST ========================================
CLAUDE_LUCY_ASSIST_API_KEY=sk-ant-...
GITLAB_TOKEN=glpat-...
GITLAB_PROJECT_ID=123

# SIREN client pour l'API Lucy CRM  (Si non présent via le module de retour)
SIREN_CLIENT=123456789
```

Puis dans votre `settings.py` :

```python
import os

#############################################################################################################
# Lucy Assist
CLAUDE_LUCY_ASSIST_API_KEY = env('CLAUDE_LUCY_ASSIST_API_KEY', default=None)
GITLAB_URL = env('GITLAB_URL', default=None)
GITLAB_TOKEN = env('GITLAB_TOKEN', default=None)
GITLAB_PROJECT_ID = env('GITLAB_PROJECT_ID', default=None)
LUCY_ASSIST = {'PROJECT_APPS_PREFIX': 'apps.'}
```

### 3. Ajouter les URLs

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    ...
    path('lucy-assist/', include('lucy_assist.urls')),
]
```

### 4. Ajouter le context processor

```python
# settings.py
TEMPLATES = [
    {
        ...
        'OPTIONS': {
            'context_processors': [
                ...
                'lucy_assist.context_processors.lucy_assist_context',
            ],
        },
    },
]
```

### 5. Inclure le template dans votre base.html

```html
<!-- templates/base.html -->
{% include 'lucy_assist/chatbot_sidebar.html' %}
```

### 6. Exécuter les migrations

```bash
python manage.py migrate lucy_assist
```

## Utilisation

Une fois installé et configuré, Lucy Assist apparaîtra automatiquement sur toutes les pages de votre application avec un bouton flottant en bas à droite.

### Fonctionnalités

- **Chat IA contextuel** : Lucy comprend le contexte de la page actuelle
- **Actions CRUD** : Lucy peut créer, modifier, rechercher et supprimer des objets
- **Analyse de bugs** : Connexion à GitLab pour analyser les problèmes signalés
- **Historique des conversations** : Sauvegarde automatique des conversations
- **Gestion des tokens** : Suivi de la consommation des tokens Claude

## Configuration avancée

### Modèle de base personnalisé

Si vous utilisez un modèle de base personnalisé avec des champs d'audit (created_date, updated_date, etc.), vous pouvez le configurer :

```python
LUCY_ASSIST = {
    'BASE_MODEL': 'mon_app.models.MonModeleBase',
}
```

### Personnalisation des questions fréquentes

```python
LUCY_ASSIST = {
    'QUESTIONS_FREQUENTES_DEFAULT': [
        "Comment créer un nouveau membre ?",
        "Comment effectuer un paiement ?",
        "Comment exporter des données ?",
    ],
}
```

## API

Lucy Assist expose plusieurs endpoints API :

- `GET /lucy-assist/api/conversations/` - Liste des conversations
- `POST /lucy-assist/api/conversations/` - Créer une conversation
- `GET /lucy-assist/api/conversations/<id>/` - Détail d'une conversation
- `POST /lucy-assist/api/conversations/<id>/messages/` - Ajouter un message
- `POST /lucy-assist/api/convers2ations/<id>/completion/` - Générer une réponse (streaming)
- `GET /lucy-assist/api/tokens/status/` - Statut des tokens

## Licence

[Revolucy](https://www.revolucy.fr)

## Déploiement Pypi

1. `docker-compose exec django pip install build twine`
2. `python -m build`
3. `python -m twine upload dist/*`
4. Indiquer le token présent dans 1Password
