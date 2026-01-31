"""
Utilitaires pour le formatage des messages Lucy Assist.
Sans impact sur la base de données.
"""
import re
from typing import List, Dict


class MessageUtils:
    """Utilitaires de formatage et transformation des messages."""

    @staticmethod
    def tronquer_texte(texte: str, max_length: int = 50, suffix: str = "...") -> str:
        """
        Tronque un texte à une longueur maximale.

        Args:
            texte: Texte à tronquer
            max_length: Longueur maximale
            suffix: Suffixe à ajouter si tronqué

        Returns:
            Texte tronqué
        """
        if not texte:
            return ""
        if len(texte) <= max_length:
            return texte
        return texte[:max_length - len(suffix)] + suffix

    @staticmethod
    def formater_messages_pour_claude(messages: List) -> List[Dict]:
        """
        Formate les messages pour l'API Claude.

        Args:
            messages: Liste de messages (objets Message)

        Returns:
            Liste de dicts formatés pour Claude
        """
        from lucy_assist.constantes import LucyAssistConstantes

        formatted = []
        for msg in messages:
            role = "user" if msg.repondant == LucyAssistConstantes.Repondant.UTILISATEUR else "assistant"
            formatted.append({
                "role": role,
                "content": msg.contenu
            })
        return formatted

    @staticmethod
    def extraire_json_de_reponse(texte: str) -> dict:
        """
        Extrait un objet JSON d'une réponse texte.

        Args:
            texte: Texte contenant potentiellement du JSON

        Returns:
            Dict extrait ou dict vide
        """
        import json

        try:
            # Chercher un bloc JSON dans le texte
            json_match = re.search(r'\{[^{}]*\}', texte, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass

        return {}

    @staticmethod
    def nettoyer_message(message: str) -> str:
        """
        Nettoie un message utilisateur.

        Args:
            message: Message brut

        Returns:
            Message nettoyé
        """
        if not message:
            return ""

        # Supprimer les espaces multiples
        message = re.sub(r'\s+', ' ', message)

        # Trim
        message = message.strip()

        return message

    @staticmethod
    def markdown_to_html_basic(texte: str) -> str:
        """
        Conversion basique de Markdown vers HTML.

        Args:
            texte: Texte en markdown

        Returns:
            Texte en HTML
        """
        if not texte:
            return ""

        # Échapper le HTML
        texte = texte.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        # Gras
        texte = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', texte)

        # Italique
        texte = re.sub(r'\*(.*?)\*', r'<em>\1</em>', texte)

        # Code inline
        texte = re.sub(r'`(.*?)`', r'<code>\1</code>', texte)

        # Liens
        texte = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', texte)

        # Sauts de ligne
        texte = texte.replace('\n', '<br>')

        return texte

    @staticmethod
    def remove_emojis(texte: str) -> str:
        """
        Supprime les emojis et caractères 4-bytes incompatibles avec MySQL utf8.

        Args:
            texte: Texte contenant potentiellement des emojis

        Returns:
            Texte sans emojis
        """
        if not texte:
            return ""

        # Pattern pour les emojis et caractères 4-bytes (U+10000 et au-delà)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002500-\U00002BEF"  # chinese char
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001f926-\U0001f937"
            "\U00010000-\U0010ffff"
            "\u2640-\u2642"
            "\u2600-\u2B55"
            "\u200d"
            "\u23cf"
            "\u23e9"
            "\u231a"
            "\ufe0f"  # dingbats
            "\u3030"
            "]+",
            re.UNICODE
        )
        return emoji_pattern.sub('', texte)
