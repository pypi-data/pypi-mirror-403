from django.contrib import admin

from lucy_assist.models import Conversation, Message, ConfigurationLucyAssist


class BlockMessage(admin.StackedInline):
    model = Message
    extra = 1


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'utilisateur', 'titre', 'created_date', 'is_active')
    list_filter = ('is_active', 'created_date')
    search_fields = ('utilisateur__email', 'titre')
    ordering = ('-created_date',)
    inlines = [BlockMessage]


@admin.register(ConfigurationLucyAssist)
class ConfigurationLucyAssistAdmin(admin.ModelAdmin):
    list_display = ('id', 'tokens_disponibles', 'prix_par_million_tokens', 'nb_vues_crud', 'updated_date')
    readonly_fields = ('crud_views_mapping_display', 'model_app_mapping_display')
    fieldsets = (
        ('Configuration Tokens', {
            'fields': ('tokens_disponibles', 'prix_par_million_tokens', 'actif')
        }),
        ('Personnalisation', {
            'fields': ('avatar', 'questions_frequentes', 'prompt_complementaire')
        }),
        ('Mapping Automatique (lecture seule)', {
            'fields': ('crud_views_mapping_display', 'model_app_mapping_display'),
            'classes': ('collapse',)
        }),
    )
    actions = ['refresh_crud_views']

    def nb_vues_crud(self, obj):
        """Affiche le nombre de modèles avec des vues CRUD découvertes."""
        if obj.crud_views_mapping:
            return len(obj.crud_views_mapping)
        return 0
    nb_vues_crud.short_description = "Modèles CRUD"

    def crud_views_mapping_display(self, obj):
        """Affiche le mapping des vues CRUD de manière lisible."""
        import json
        if obj.crud_views_mapping:
            return json.dumps(obj.crud_views_mapping, indent=2, ensure_ascii=False)
        return "Aucune vue découverte. Utilisez l'action 'Rafraîchir les vues CRUD'."
    crud_views_mapping_display.short_description = "Vues CRUD découvertes"

    def model_app_mapping_display(self, obj):
        """Affiche le mapping modèle -> app de manière lisible."""
        import json
        if obj.model_app_mapping:
            return json.dumps(obj.model_app_mapping, indent=2, ensure_ascii=False)
        return "Aucun mapping. Sera construit automatiquement."
    model_app_mapping_display.short_description = "Mapping Modèle -> App"

    @admin.action(description="Rafraîchir les vues CRUD découvertes")
    def refresh_crud_views(self, request, queryset):
        """Action admin pour rafraîchir le mapping des vues CRUD."""
        for config in queryset:
            mapping = config.refresh_crud_views_mapping()
            nb_models = len(mapping)
            nb_views = sum(len(actions) for actions in mapping.values())
            self.message_user(
                request,
                f"Mapping rafraîchi: {nb_models} modèles, {nb_views} vues découvertes."
            )
