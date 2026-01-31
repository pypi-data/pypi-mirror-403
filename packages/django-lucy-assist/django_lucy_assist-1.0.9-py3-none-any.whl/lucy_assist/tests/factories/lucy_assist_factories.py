"""
Factories pour les tests Lucy Assist.
Utilise factory_boy avec faker pour générer des données réalistes.
"""
import factory
from factory.django import DjangoModelFactory
from faker import Faker

from lucy_assist.models import Conversation, Message, ConfigurationLucyAssist
from lucy_assist.constantes import LucyAssistConstantes

fake = Faker('fr_FR')


class ConfigurationLucyAssistFactory(DjangoModelFactory):
    """Factory pour créer une configuration Lucy Assist."""

    class Meta:
        model = ConfigurationLucyAssist
        django_get_or_create = ('id',)

    id = 1  # Singleton
    tokens_disponibles = factory.LazyFunction(lambda: fake.random_int(min=100000, max=10000000))
    prix_par_million_tokens = 10.0
    questions_frequentes = factory.LazyFunction(lambda: [
        "Comment créer un nouveau membre ?",
        "Comment effectuer un paiement ?",
        "Comment exporter des données ?",
    ])
    actif = True


class ConversationFactory(DjangoModelFactory):
    """Factory pour créer des conversations."""

    class Meta:
        model = Conversation

    utilisateur = factory.SubFactory('apps.utilisateur.tests.factories.UtilisateurFactory')
    titre = factory.LazyFunction(lambda: fake.sentence(nb_words=5))
    page_contexte = factory.LazyFunction(lambda: f"/{fake.word()}/{fake.word()}/list")
    is_active = True


class MessageUtilisateurFactory(DjangoModelFactory):
    """Factory pour créer des messages utilisateur."""

    class Meta:
        model = Message

    conversation = factory.SubFactory(ConversationFactory)
    repondant = LucyAssistConstantes.Repondant.UTILISATEUR
    contenu = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    tokens_utilises = 0
    type_action = None
    metadata = factory.LazyFunction(dict)


class MessageChatbotFactory(DjangoModelFactory):
    """Factory pour créer des messages chatbot."""

    class Meta:
        model = Message

    conversation = factory.SubFactory(ConversationFactory)
    repondant = LucyAssistConstantes.Repondant.CHATBOT
    contenu = factory.LazyFunction(lambda: fake.text(max_nb_chars=500))
    tokens_utilises = factory.LazyFunction(lambda: fake.random_int(min=100, max=2000))
    type_action = factory.LazyFunction(
        lambda: fake.random_element([
            LucyAssistConstantes.TypeAction.AIDE_NAVIGATION,
            LucyAssistConstantes.TypeAction.RECHERCHE,
            LucyAssistConstantes.TypeAction.EXPLICATION,
        ])
    )
    metadata = factory.LazyFunction(dict)


class ConversationAvecMessagesFactory(ConversationFactory):
    """Factory pour créer une conversation avec plusieurs messages."""

    @factory.post_generation
    def messages(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            # Si des messages sont passés, les utiliser
            for message in extracted:
                message.conversation = self
                message.save()
        else:
            # Créer une conversation type avec échanges
            MessageUtilisateurFactory(
                conversation=self,
                contenu="Comment créer un nouveau membre ?"
            )
            MessageChatbotFactory(
                conversation=self,
                contenu="Pour créer un nouveau membre, suivez ces étapes..."
            )
            MessageUtilisateurFactory(
                conversation=self,
                contenu="Merci, et comment lui ajouter une adhésion ?"
            )
            MessageChatbotFactory(
                conversation=self,
                contenu="Pour ajouter une adhésion, rendez-vous sur..."
            )
