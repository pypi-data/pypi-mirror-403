"""
Définition des tools pour l'API Claude.

Ces tools permettent à Lucy Assist d'exécuter des actions CRUD
directement dans l'application.
"""

# Tools disponibles pour Claude
LUCY_ASSIST_TOOLS = [
    {
        "name": "create_object",
        "description": """Crée un nouvel objet dans la base de données.
        Utilise ce tool quand l'utilisateur demande de créer un objet métier (client, facture, etc.).
        IMPORTANT: Utilise ce tool en priorité quand l'utilisateur demande une création.
        Ne demande pas de confirmation, exécute directement l'action.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Nom de l'application Django (ex: client, facture)"
                },
                "model_name": {
                    "type": "string",
                    "description": "Nom du modèle Django (ex: Client, Facture)"
                },
                "data": {
                    "type": "object",
                    "description": "Données pour créer l'objet. Les clés sont les noms des champs du modèle.",
                    "additionalProperties": True
                }
            },
            "required": ["app_name", "model_name", "data"]
        }
    },
    {
        "name": "update_object",
        "description": """Met à jour un objet existant dans la base de données.
        Utilise ce tool quand l'utilisateur demande de modifier un objet existant.
        IMPORTANT: Exécute directement l'action sans demander de confirmation.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Nom de l'application Django"
                },
                "model_name": {
                    "type": "string",
                    "description": "Nom du modèle Django"
                },
                "object_id": {
                    "type": "integer",
                    "description": "ID de l'objet à modifier"
                },
                "data": {
                    "type": "object",
                    "description": "Données à mettre à jour",
                    "additionalProperties": True
                }
            },
            "required": ["app_name", "model_name", "object_id", "data"]
        }
    },
    {
        "name": "get_deletion_impact",
        "description": """Analyse l'impact d'une suppression AVANT de supprimer.
        OBLIGATOIRE: Utilise TOUJOURS ce tool AVANT delete_object pour montrer à l'utilisateur
        toutes les conséquences de la suppression (objets supprimés en cascade, champs mis à NULL, etc.)
        Affiche le résultat à l'utilisateur et demande sa confirmation explicite avant de supprimer.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Nom de l'application Django"
                },
                "model_name": {
                    "type": "string",
                    "description": "Nom du modèle Django"
                },
                "object_id": {
                    "type": "integer",
                    "description": "ID de l'objet à analyser"
                }
            },
            "required": ["app_name", "model_name", "object_id"]
        }
    },
    {
        "name": "delete_object",
        "description": """Supprime un objet de la base de données.
        IMPORTANT: Tu DOIS d'abord utiliser get_deletion_impact pour analyser les conséquences,
        puis afficher le résultat à l'utilisateur, et obtenir sa CONFIRMATION EXPLICITE avant d'exécuter ce tool.
        Ne JAMAIS supprimer sans avoir montré l'impact et obtenu confirmation.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Nom de l'application Django"
                },
                "model_name": {
                    "type": "string",
                    "description": "Nom du modèle Django"
                },
                "object_id": {
                    "type": "integer",
                    "description": "ID de l'objet à supprimer"
                },
                "confirmed": {
                    "type": "boolean",
                    "description": "OBLIGATOIRE: true si l'utilisateur a explicitement confirmé la suppression après avoir vu l'impact"
                }
            },
            "required": ["app_name", "model_name", "object_id", "confirmed"]
        }
    },
    {
        "name": "search_objects",
        "description": """Recherche des objets dans la base de données.
        Utilise ce tool pour trouver des clients, réservations, ou tout autre objet métier.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Terme de recherche"
                },
                "model_name": {
                    "type": "string",
                    "description": "Nom du modèle à rechercher (optionnel, cherche dans tous si non spécifié)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Nombre maximum de résultats (défaut: 10)",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_object_details",
        "description": """Récupère les détails d'un objet spécifique.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Nom de l'application Django"
                },
                "model_name": {
                    "type": "string",
                    "description": "Nom du modèle Django"
                },
                "object_id": {
                    "type": "integer",
                    "description": "ID de l'objet"
                }
            },
            "required": ["app_name", "model_name", "object_id"]
        }
    },
    {
        "name": "get_form_fields",
        "description": """Récupère les champs requis et optionnels d'un formulaire.
        Utilise ce tool uniquement si tu as besoin de connaître les champs avant de créer un objet,
        ou si l'utilisateur demande explicitement quels champs sont disponibles.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Nom de l'application Django"
                },
                "model_name": {
                    "type": "string",
                    "description": "Nom du modèle Django"
                }
            },
            "required": ["app_name", "model_name"]
        }
    },
    {
        "name": "navigate_to_page",
        "description": """Génère une URL pour naviguer vers une page spécifique.
        Utilise ce tool uniquement si l'utilisateur demande explicitement d'aller quelque part
        ou si tu as besoin de lui montrer où aller.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "page_type": {
                    "type": "string",
                    "enum": ["list", "create", "detail", "edit"],
                    "description": "Type de page"
                },
                "app_name": {
                    "type": "string",
                    "description": "Nom de l'application"
                },
                "model_name": {
                    "type": "string",
                    "description": "Nom du modèle"
                },
                "object_id": {
                    "type": "integer",
                    "description": "ID de l'objet (pour detail/edit)"
                }
            },
            "required": ["page_type", "app_name", "model_name"]
        }
    },
    {
        "name": "analyze_bug",
        "description": """Analyse un bug potentiel en se connectant à GitLab pour examiner le code source.
        Utilise ce tool quand l'utilisateur signale un problème technique, une erreur, ou un comportement inattendu.
        Ce tool analyse le code via GitLab et si un bug est détecté, envoie automatiquement une notification
        à l'équipe Revolucy pour correction.
        IMPORTANT: Utilise ce tool dès qu'un utilisateur signale un message d'erreur ou un dysfonctionnement.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_description": {
                    "type": "string",
                    "description": "Description du problème par l'utilisateur (obligatoire)"
                },
                "error_message": {
                    "type": "string",
                    "description": "Message d'erreur exact (si disponible)"
                },
                "page_url": {
                    "type": "string",
                    "description": "URL de la page où le problème se produit"
                },
                "model_name": {
                    "type": "string",
                    "description": "Nom du modèle Django concerné (si identifiable, ex: Client, Reservation)"
                },
                "action_type": {
                    "type": "string",
                    "enum": ["create", "update", "delete", "list", "search", "other"],
                    "description": "Type d'action qui a causé le problème"
                }
            },
            "required": ["user_description"]
        }
    }
]

def get_app_for_model(model_name: str) -> str:
    """
    Retourne le nom de l'app Django pour un modèle donné.

    Utilise la configuration stockée en base de données.
    """
    from lucy_assist.models import ConfigurationLucyAssist
    return ConfigurationLucyAssist.get_app_for_model_static(model_name)
