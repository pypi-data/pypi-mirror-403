"""
Tests pour Lucy Assist.
"""
from django.test import TestCase
from django.urls import reverse

from lucy_assist.models import Conversation, Message, ConfigurationLucyAssist
from lucy_assist.tests.factories import (
    ConfigurationLucyAssistFactory,
    ConversationFactory,
    MessageUtilisateurFactory,
    MessageChatbotFactory,
)
from apps.utilisateur.tests.factories import UtilisateurAdminUnafFactory


class TestConfigurationLucyAssist(TestCase):
    """Tests pour le modèle ConfigurationLucyAssist."""

    def setUp(self):
        self.user = UtilisateurAdminUnafFactory()
        self.client.force_login(self.user)

    # -----------------------------------------------------------------
    # CONFIGURATION SINGLETON
    # -----------------------------------------------------------------
    def test_configuration_singleton_ok(self):
        """Vérifie que la configuration est un singleton."""
        config1 = ConfigurationLucyAssist.get_config()
        config2 = ConfigurationLucyAssist.get_config()

        self.assertEqual(config1.pk, config2.pk)
        self.assertEqual(config1.pk, 1)

    def test_ajouter_tokens_ok(self):
        """Vérifie l'ajout de tokens."""
        config = ConfigurationLucyAssist.get_config()
        initial_tokens = config.tokens_disponibles

        tokens_ajoutes = config.ajouter_tokens(10)  # 10€

        self.assertEqual(tokens_ajoutes, 1_000_000)
        self.assertEqual(config.tokens_disponibles, initial_tokens + 1_000_000)

    def test_get_questions_frequentes_default_ok(self):
        """Vérifie les questions fréquentes par défaut."""
        config = ConfigurationLucyAssist.get_config()
        config.questions_frequentes = []
        config.save()

        questions = config.get_questions_frequentes()

        self.assertIsInstance(questions, list)
        self.assertGreater(len(questions), 0)


class TestConversation(TestCase):
    """Tests pour le modèle Conversation."""

    def setUp(self):
        self.user = UtilisateurAdminUnafFactory()
        self.client.force_login(self.user)
        ConfigurationLucyAssistFactory()

    # -----------------------------------------------------------------
    # CRÉATION
    # -----------------------------------------------------------------
    def test_create_conversation_ok(self):
        """Vérifie la création d'une conversation."""
        conversation = ConversationFactory(utilisateur=self.user)

        self.assertIsNotNone(conversation.pk)
        self.assertEqual(conversation.utilisateur, self.user)
        self.assertTrue(conversation.is_active)

    def test_generer_titre_ok(self):
        """Vérifie la génération automatique du titre."""
        conversation = ConversationFactory(utilisateur=self.user, titre=None)
        MessageUtilisateurFactory(
            conversation=conversation,
            contenu="Comment créer un membre ?"
        )

        conversation.generer_titre()

        self.assertIsNotNone(conversation.titre)
        self.assertIn("Comment créer", conversation.titre)


class TestMessage(TestCase):
    """Tests pour le modèle Message."""

    def setUp(self):
        self.user = UtilisateurAdminUnafFactory()
        self.client.force_login(self.user)
        ConfigurationLucyAssistFactory()

    # -----------------------------------------------------------------
    # CRÉATION
    # -----------------------------------------------------------------
    def test_create_message_utilisateur_ok(self):
        """Vérifie la création d'un message utilisateur."""
        conversation = ConversationFactory(utilisateur=self.user)
        message = MessageUtilisateurFactory(conversation=conversation)

        self.assertIsNotNone(message.pk)
        self.assertTrue(message.est_utilisateur)
        self.assertFalse(message.est_chatbot)

    def test_create_message_chatbot_ok(self):
        """Vérifie la création d'un message chatbot."""
        conversation = ConversationFactory(utilisateur=self.user)
        message = MessageChatbotFactory(conversation=conversation)

        self.assertIsNotNone(message.pk)
        self.assertTrue(message.est_chatbot)
        self.assertFalse(message.est_utilisateur)
        self.assertGreater(message.tokens_utilises, 0)


class TestAPIViews(TestCase):
    """Tests pour les vues API Lucy Assist."""

    def setUp(self):
        self.user = UtilisateurAdminUnafFactory()
        self.client.force_login(self.user)
        self.config = ConfigurationLucyAssistFactory(tokens_disponibles=1_000_000)

    # -----------------------------------------------------------------
    # LISTE CONVERSATIONS
    # -----------------------------------------------------------------
    def test_conversation_list_ok(self):
        """Vérifie que la liste des conversations est accessible."""
        ConversationFactory(utilisateur=self.user)
        ConversationFactory(utilisateur=self.user)

        url = reverse("lucy_assist:api-conversations")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('conversations', data)
        self.assertEqual(len(data['conversations']), 2)

    # -----------------------------------------------------------------
    # CRÉATION CONVERSATION
    # -----------------------------------------------------------------
    def test_conversation_create_ok(self):
        """Vérifie la création d'une conversation via API."""
        initial_count = Conversation.objects.count()

        url = reverse("lucy_assist:api-conversations")
        response = self.client.post(
            url,
            data={'page_contexte': '/membre/list'},
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Conversation.objects.count(), initial_count + 1)

    # -----------------------------------------------------------------
    # STATUT TOKENS
    # -----------------------------------------------------------------
    def test_token_status_ok(self):
        """Vérifie le statut des tokens."""
        url = reverse("lucy_assist:api-token-status")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('tokens_disponibles', data)
        self.assertEqual(data['tokens_disponibles'], 1_000_000)

    # -----------------------------------------------------------------
    # SUGGESTIONS
    # -----------------------------------------------------------------
    def test_suggestions_ok(self):
        """Vérifie les suggestions de questions."""
        url = reverse("lucy_assist:api-suggestions")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('suggestions', data)
        self.assertIsInstance(data['suggestions'], list)
