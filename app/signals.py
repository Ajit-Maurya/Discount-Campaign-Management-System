# campaign/signals.py

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Campaign
from .services.cache_service import invalidate_campaign_cache


@receiver(post_save, sender=Campaign)
@receiver(post_delete, sender=Campaign)
def clear_cache_on_change(sender, **kwargs) -> None:  # noqa: ANN001, ANN003, ARG001
    invalidate_campaign_cache()
