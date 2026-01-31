"""
Utilitaires pour la gestion des tokens Lucy Assist.
Sans impact sur la base de données.
"""


class TokenUtils:
    """Utilitaires de calcul et formatage des tokens."""

    PRIX_PAR_MILLION = 10.0
    TOKENS_PAR_CONVERSATION = 2000

    @staticmethod
    def calculer_tokens_pour_montant(montant_euros: float, prix_par_million: float = None) -> int:
        """
        Calcule le nombre de tokens pour un montant en euros.

        Args:
            montant_euros: Montant en euros
            prix_par_million: Prix par million de tokens (défaut: 50€)

        Returns:
            Nombre de tokens
        """
        prix = prix_par_million or TokenUtils.PRIX_PAR_MILLION
        return int((montant_euros / prix) * 1_000_000)

    @staticmethod
    def calculer_montant_pour_tokens(tokens: int, prix_par_million: float = None) -> float:
        """
        Calcule le montant en euros pour un nombre de tokens.

        Args:
            tokens: Nombre de tokens
            prix_par_million: Prix par million de tokens (défaut: 50€)

        Returns:
            Montant en euros
        """
        prix = prix_par_million or TokenUtils.PRIX_PAR_MILLION
        return (tokens / 1_000_000) * prix

    @staticmethod
    def estimer_conversations(tokens: int, tokens_par_conversation: int = None) -> int:
        """
        Estime le nombre de conversations possibles.

        Args:
            tokens: Nombre de tokens disponibles
            tokens_par_conversation: Tokens moyens par conversation (défaut: 2000)

        Returns:
            Nombre de conversations estimées
        """
        tpc = tokens_par_conversation or TokenUtils.TOKENS_PAR_CONVERSATION
        return int(tokens / tpc) if tpc > 0 else 0

    @staticmethod
    def formater_tokens(tokens: int) -> str:
        """
        Formate un nombre de tokens pour l'affichage.

        Args:
            tokens: Nombre de tokens

        Returns:
            String formatée (ex: "1.5M", "500K", "1234")
        """
        if tokens >= 1_000_000:
            return f"{tokens / 1_000_000:.1f}M"
        elif tokens >= 1_000:
            return f"{tokens / 1_000:.0f}K"
        return str(tokens)

    @staticmethod
    def tokens_suffisants(tokens_disponibles: int, tokens_requis: int = 2000) -> bool:
        """
        Vérifie si suffisamment de tokens sont disponibles.

        Args:
            tokens_disponibles: Tokens actuellement disponibles
            tokens_requis: Tokens minimum requis

        Returns:
            True si suffisant
        """
        return tokens_disponibles >= tokens_requis
