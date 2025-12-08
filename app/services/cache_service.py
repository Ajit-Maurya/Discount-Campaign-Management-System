from django.core.cache import cache

from app.models import Campaign

CACHE_KEY = "active_campaigns"
TTL = 300


def get_cached_active_campaigns():  # noqa: ANN201
    campaigns = cache.get(CACHE_KEY)
    if campaigns is not None:
        return campaigns

    campaigns = []
    for c in Campaign.objects.filter(is_active=True):
        campaigns.append(
            {
                "id": c.id,
                "name": c.name,
                "discount_type": c.discount_type,
                "discount_value": float(c.discount_value),
                "max_discount_cap": float(c.max_discount_cap)
                if c.max_discount_cap
                else None,
                "scope": c.scope,
                "sponsor_type": c.sponsor_type,
                "vendor_id": c.vendor_id,
                "start_date": c.start_date,
                "end_date": c.end_date,
                "total_budget": float(c.total_budget),
                "current_spend": float(c.current_spend),
                "max_transactions_per_user_day": c.max_transactions_per_user_day,
                "is_active": c.is_active,
                "target_users": list(c.target_users.values_list("id", flat=True)),
            },
        )

    cache.set(CACHE_KEY, campaigns, TTL)
    return campaigns


def invalidate_campaign_cache() -> None:
    cache.delete(CACHE_KEY)
