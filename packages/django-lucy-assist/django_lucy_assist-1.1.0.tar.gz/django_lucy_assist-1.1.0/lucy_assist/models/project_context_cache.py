"""
Cache du contexte projet pour optimiser les tokens Claude.
"""
import hashlib
import json
from datetime import timedelta
from typing import Optional, Dict, Any

from django.db import models
from django.core.cache import cache
from django.utils import timezone

from lucy_assist.models.base import LucyAssistBaseModel


class ProjectContextCache(LucyAssistBaseModel):
    """
    Cache du contexte projet analysé.

    Stocke les informations sur la structure du projet pour éviter
    de re-analyser GitLab à chaque requête Claude.
    """
    cache_key = models.CharField(
        max_length=255,
        unique=True,
        db_index=True
    )  # Clé unique pour identifier le type de contexte
    contenu = models.JSONField(default=dict)  # Contenu mis en cache (JSON)
    content_hash = models.CharField(max_length=64, blank=True)  # Hash du contenu source pour détecter les changements
    expire_at = models.DateTimeField()
    tokens_economises = models.BigIntegerField(default=0)  # Nombre de tokens économisés grâce au cache
    hit_count = models.IntegerField(default=0)  # Nombre d'utilisations

    class Meta:
        verbose_name = "Cache contexte projet"
        verbose_name_plural = "Caches contexte projet"

    def __str__(self):
        return f"Cache: {self.cache_key}"

    @property
    def is_expired(self) -> bool:
        """Vérifie si le cache est expiré."""
        return timezone.now() > self.expire_at

    @property
    def is_valid(self) -> bool:
        """Vérifie si le cache est valide (non expiré)."""
        return not self.is_expired

    def increment_hit(self, tokens_saved: int = 0):
        """Incrémente le compteur d'utilisation."""
        self.hit_count += 1
        self.tokens_economises += tokens_saved
        self.save(update_fields=['hit_count', 'tokens_economises'])

    @classmethod
    def get_or_create_cache(
            cls,
            cache_key: str,
            ttl_hours: int = 24
    ) -> 'ProjectContextCache':
        """
        Récupère ou crée un cache.

        Args:
            cache_key: Clé unique du cache
            ttl_hours: Durée de vie en heures

        Returns:
            Instance de ProjectContextCache
        """
        expire_at = timezone.now() + timedelta(hours=ttl_hours)

        cache_obj, created = cls.objects.get_or_create(
            cache_key=cache_key,
            defaults={
                'expire_at': expire_at,
                'contenu': {}
            }
        )

        # Renouveler si expiré
        if cache_obj.is_expired:
            cache_obj.expire_at = expire_at
            cache_obj.contenu = {}
            cache_obj.content_hash = ''
            cache_obj.save()

        return cache_obj

    @classmethod
    def get_cached_content(
            cls,
            cache_key: str,
            content_hash: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Récupère le contenu mis en cache si valide.

        Args:
            cache_key: Clé du cache
            content_hash: Hash pour vérifier si le contenu a changé

        Returns:
            Contenu caché ou None si invalide/expiré
        """
        # D'abord vérifier le cache Django (plus rapide)
        django_cache_key = f"lucy_assist_context_{cache_key}"
        cached = cache.get(django_cache_key)
        if cached:
            return cached

        try:
            cache_obj = cls.objects.get(cache_key=cache_key)

            # Vérifier l'expiration
            if cache_obj.is_expired:
                return None

            # Vérifier le hash si fourni
            if content_hash and cache_obj.content_hash != content_hash:
                return None

            # Mettre en cache Django pour accès rapide
            cache.set(django_cache_key, cache_obj.contenu, timeout=3600)

            return cache_obj.contenu

        except cls.DoesNotExist:
            return None

    @classmethod
    def set_cached_content(
            cls,
            cache_key: str,
            contenu: Dict,
            content_hash: str = '',
            ttl_hours: int = 24
    ) -> 'ProjectContextCache':
        """
        Stocke le contenu en cache.

        Args:
            cache_key: Clé du cache
            contenu: Contenu à cacher
            content_hash: Hash du contenu source
            ttl_hours: Durée de vie en heures

        Returns:
            Instance de ProjectContextCache
        """
        expire_at = timezone.now() + timedelta(hours=ttl_hours)

        cache_obj, _ = cls.objects.update_or_create(
            cache_key=cache_key,
            defaults={
                'contenu': contenu,
                'content_hash': content_hash,
                'expire_at': expire_at
            }
        )

        # Mettre aussi en cache Django
        django_cache_key = f"lucy_assist_context_{cache_key}"
        cache.set(django_cache_key, contenu, timeout=ttl_hours * 3600)

        return cache_obj

    @staticmethod
    def compute_hash(content: Any) -> str:
        """Calcule le hash d'un contenu."""
        if isinstance(content, dict) or isinstance(content, list):
            content = json.dumps(content, sort_keys=True)
        return hashlib.sha256(str(content).encode()).hexdigest()[:16]

    @classmethod
    def invalidate_cache(cls, cache_key: str):
        """Invalide un cache spécifique."""
        # Supprimer du cache Django
        django_cache_key = f"lucy_assist_context_{cache_key}"
        cache.delete(django_cache_key)

        # Supprimer de la BDD
        cls.objects.filter(cache_key=cache_key).delete()

    @classmethod
    def invalidate_all(cls):
        """Invalide tous les caches Lucy Assist."""
        # Supprimer tous les caches (la suppression du cache Django pattern n'est pas disponible)
        cls.objects.all().delete()

    @classmethod
    def get_stats(cls) -> Dict:
        """Retourne les statistiques des caches."""
        from django.db.models import Sum, Count

        stats = cls.objects.aggregate(
            total_caches=Count('id'),
            total_hits=Sum('hit_count'),
            total_tokens_saved=Sum('tokens_economises')
        )

        active_caches = cls.objects.filter(
            expire_at__gt=timezone.now()
        ).count()

        return {
            'total_caches': stats['total_caches'] or 0,
            'active_caches': active_caches,
            'total_hits': stats['total_hits'] or 0,
            'total_tokens_saved': stats['total_tokens_saved'] or 0
        }
