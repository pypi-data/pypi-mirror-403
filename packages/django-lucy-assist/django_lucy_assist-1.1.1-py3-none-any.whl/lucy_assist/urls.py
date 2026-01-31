"""
URLs pour Lucy Assist.

Ce module définit toutes les routes de l'application Lucy Assist,
incluant les API REST et les vues de documentation.
"""
from django.urls import path

from lucy_assist import views

app_name = "lucy_assist"

urlpatterns = [
    # API - Conversations
    path("api/conversations", views.ConversationListCreateView.as_view(), name="api-conversations"),
    path("api/conversations/<int:pk>", views.ConversationDetailView.as_view(), name="api-conversation-detail"),

    # API - Messages
    path("api/conversations/<int:conversation_id>/messages", views.MessageCreateView.as_view(), name="api-messages"),
    path("api/conversations/<int:conversation_id>/chat", views.ChatCompletionView.as_view(), name="api-chat"),

    # API - Tokens
    path("api/tokens/status", views.TokenStatusView.as_view(), name="api-token-status"),
    path("api/tokens/buy", views.AcheterTokensView.as_view(), name="api-token-buy"),

    # API - Utilitaires
    path("api/suggestions", views.SuggestionsView.as_view(), name="api-suggestions"),
    path("api/context", views.PageContextView.as_view(), name="api-context"),

    # API - Cache (admin only)
    path("api/cache/stats", views.CacheStatsView.as_view(), name="api-cache-stats"),
    path("api/cache/invalidate", views.CacheInvalidateView.as_view(), name="api-cache-invalidate"),

    # API - Feedback
    path("api/feedback", views.FeedbackCreateView.as_view(), name="api-feedback"),
]
