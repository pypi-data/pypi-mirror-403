from django.db import models
from django.core.cache import cache

from lucy_assist.models.base import LucyAssistBaseModel
from lucy_assist.conf import lucy_assist_settings


class ConfigurationLucyAssist(LucyAssistBaseModel):
    """
    Configuration singleton pour Lucy Assist.
    Gère les tokens disponibles et les paramètres globaux.
    """
    tokens_disponibles = models.BigIntegerField(default=0)
    prix_par_million_tokens = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=lucy_assist_settings.PRIX_PAR_MILLION_TOKENS
    )
    questions_frequentes = models.JSONField(default=list, blank=True)
    actif = models.BooleanField(default=True)
    avatar = models.ImageField(null=True, blank=True)

    # Instructions complémentaires pour le prompt
    prompt_complementaire = models.TextField(blank=True,default='')

    # Mapping des modèles vers leurs applications Django
    model_app_mapping = models.JSONField(blank=True, default=dict)

    # Mapping des vues CRUD découvertes automatiquement
    # Structure: {
    #   "model_name": {
    #     "list": {"url_name": "app:model-list", "url": "/app/model/"},
    #     "create": {"url_name": "app:model-formulaire", "url": "/app/model/formulaire/"},
    #     "detail": {"url_name": "app:model-detail", "url": "/app/model/detail/<pk>/"},
    #     "delete": {"url_name": "app:model-suppression", "url": "/app/model/suppression/<pk>/"}
    #   }
    # }
    crud_views_mapping = models.JSONField(blank=True, default=dict)

    class Meta:
        verbose_name = "Configuration Lucy Assist"
        verbose_name_plural = "Configuration Lucy Assist"

    def __str__(self):
        return f"Configuration Lucy Assist - {self.tokens_disponibles:,} tokens"

    @classmethod
    def get_config(cls):
        """
        Retourne la configuration singleton.
        Utilise le cache pour optimiser les performances.
        """
        cache_key = 'lucy_assist_config'
        config = cache.get(cache_key)

        if config is None:
            config, _ = cls.objects.get_or_create(pk=1)
            cache.set(cache_key, config, timeout=300)  # Cache 5 minutes

        return config

    def save(self, *args, **kwargs):
        # Forcer l'ID à 1 pour le singleton
        self.pk = 1

        # Auto-découverte des vues CRUD si le mapping est vide
        if not self.crud_views_mapping:
            self.crud_views_mapping = self._discover_crud_views()

        super().save(*args, **kwargs)
        # Invalider le cache
        cache.delete('lucy_assist_config')

    def refresh_crud_views_mapping(self):
        """
        Force la redécouverte des vues CRUD.
        Utile après l'ajout de nouvelles vues dans le projet.
        """
        self.crud_views_mapping = self._discover_crud_views()
        self.save(update_fields=['crud_views_mapping'])
        cache.delete('lucy_assist_config')
        return self.crud_views_mapping

    def _discover_crud_views(self) -> dict:
        """
        Découvre automatiquement les vues CRUD du projet
        en parcourant les URL patterns.
        """
        from lucy_assist.services.view_discovery_service import ViewDiscoveryService
        service = ViewDiscoveryService()
        return service.discover_crud_views()

    def get_crud_view_for_model(self, model_name: str, action: str) -> dict:
        """
        Retourne les infos de la vue CRUD pour un modèle et une action donnés.

        Args:
            model_name: Nom du modèle (ex: 'Client', 'Reservation')
            action: Type d'action ('list', 'create', 'detail', 'update', 'delete')

        Returns:
            Dict avec 'url_name', 'url', 'method' ou None si non trouvé
        """
        if not self.crud_views_mapping:
            self.crud_views_mapping = self._discover_crud_views()
            self.save(update_fields=['crud_views_mapping'])

        model_lower = model_name.lower()
        model_views = self.crud_views_mapping.get(model_lower, {})
        return model_views.get(action)

    @property
    def tokens_restants_en_euros(self):
        """Retourne la valeur en euros des tokens restants."""
        return (self.tokens_disponibles / 1_000_000) * float(self.prix_par_million_tokens)

    @property
    def conversations_estimees(self):
        """Estime le nombre de conversations possibles avec les tokens restants."""
        return int(self.tokens_disponibles / lucy_assist_settings.TOKENS_MOYENS_PAR_CONVERSATION)

    def ajouter_tokens(self, montant_euros):
        """
        Ajoute des tokens en fonction d'un montant en euros.
        Retourne le nombre de tokens ajoutés.
        """
        tokens_a_ajouter = int((montant_euros / float(self.prix_par_million_tokens)) * 1_000_000)
        self.tokens_disponibles += tokens_a_ajouter
        self.save(update_fields=['tokens_disponibles'])
        return tokens_a_ajouter

    def a_suffisamment_tokens(self, tokens_requis=2000):
        """Vérifie si suffisamment de tokens sont disponibles."""
        return self.tokens_disponibles >= tokens_requis

    def get_questions_frequentes(self):
        """
        Retourne les questions fréquentes configurées.
        Si aucune n'est configurée, retourne les questions par défaut.
        """
        if self.questions_frequentes:
            return self.questions_frequentes

        # Questions par défaut si aucune n'est configurée
        return lucy_assist_settings.QUESTIONS_FREQUENTES_DEFAULT

    def get_app_for_model(self, model_name: str) -> str:
        """
        Retourne le nom de l'application Django pour un modèle donné.

        Args:
            model_name: Nom du modèle (insensible à la casse)

        Returns:
            Nom de l'application Django, ou le nom du modèle en minuscules si non trouvé
        """
        # Si le mapping est vide, le construire dynamiquement depuis les modèles Django
        if not self.model_app_mapping:
            self.model_app_mapping = self._build_model_app_mapping()
            self.save(update_fields=['model_app_mapping'])
            # Invalider le cache pour que les prochains appels utilisent la nouvelle valeur
            cache.delete('lucy_assist_config')

        model_lower = model_name.lower()
        return self.model_app_mapping.get(model_lower, model_lower)

    def _build_model_app_mapping(self) -> dict:
        """
        Construit dynamiquement le mapping modèle -> application
        en parcourant tous les modèles Django enregistrés.

        Returns:
            Dict avec les noms de modèles en minuscules comme clés
            et les noms d'applications comme valeurs.
        """
        from django.apps import apps

        mapping = {}
        apps_prefix = lucy_assist_settings.PROJECT_APPS_PREFIX

        for app_config in apps.get_app_configs():
            app_label = app_config.label

            # Filtrer les apps si un préfixe est configuré
            if apps_prefix and not app_config.name.startswith(apps_prefix):
                continue

            # Utiliser le label de l'app
            app_name = app_label

            for model in app_config.get_models():
                model_name_lower = model.__name__.lower()
                # Ne pas écraser si déjà présent (priorité au premier trouvé)
                if model_name_lower not in mapping:
                    mapping[model_name_lower] = app_name

        return mapping

    def update_model_mapping(self, model_name: str, app_name: str) -> None:
        """
        Met à jour le mapping pour un modèle spécifique.
        Utilisé quand le chatbot découvre un nouveau mapping.

        Args:
            model_name: Nom du modèle
            app_name: Nom de l'application Django
        """
        if not self.model_app_mapping:
            self.model_app_mapping = {}

        model_lower = model_name.lower()
        self.model_app_mapping[model_lower] = app_name
        self.save(update_fields=['model_app_mapping'])
        cache.delete('lucy_assist_config')

    @classmethod
    def get_app_for_model_static(cls, model_name: str) -> str:
        """
        Version statique pour récupérer l'app d'un modèle.
        Utilise la config en cache.
        """
        config = cls.get_config()
        return config.get_app_for_model(model_name)


def get_default_model_app_mapping() -> dict:
    """
    Fonction utilisée par la migration pour la valeur par défaut.
    Retourne un dict vide car le mapping est maintenant construit
    dynamiquement lors du premier accès.
    """
    return {}
