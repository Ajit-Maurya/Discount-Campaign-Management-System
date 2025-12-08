from datetime import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from app.models import Campaign, Redemption
from app.services.cache_service import get_cached_active_campaigns


class CampaignService:
    @staticmethod
    def get_available_discounts(  # noqa: ANN205
        user,  # noqa: ANN001
        cart_total: Decimal,
        delivery_fee: Decimal = Decimal("0.00"),
    ):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # --- 1. Load active campaigns from Redis ---
        active_campaigns = get_cached_active_campaigns()

        # --- 2. Filter in Python ---
        candidates = [
            c
            for c in active_campaigns
            if datetime.fromisoformat(c["start_date"])
            <= now
            <= datetime.fromisoformat(c["end_date"])
            and c["current_spend"] < c["total_budget"]
            and c["is_active"] is True
        ]

        applicable_campaigns = []

        for c in candidates:
            # --- 3. Targeting ---
            if c["target_users"] and user.pk not in c["target_users"]:
                continue

            # --- 4. Real-time daily limits (DB read) ---
            daily_usage = Redemption.objects.filter(
                campaign_id=c["id"],
                user=user,
                redeemed_at__gte=today_start,
            ).count()

            if daily_usage >= c["max_transactions_per_user_day"]:
                continue

            # --- 5. Calculate discount ---
            discount = CampaignService._calculate_discount_struct(
                c,
                cart_total,
                delivery_fee,
            )

            if discount > 0:
                applicable_campaigns.append(
                    {
                        "id": c["id"],
                        "name": c["name"],
                        "scope": c["scope"],
                        "sponsor": c["sponsor_type"],
                        "amount": discount,
                    },
                )

        return applicable_campaigns

    @staticmethod
    def _calculate_discount_struct(campaign_dict, cart_total, delivery_fee):  # noqa: ANN001, ANN205
        base_value = (
            cart_total
            if campaign_dict["scope"] == Campaign.SCOPE_CART
            else delivery_fee
        )

        if base_value <= 0:
            return Decimal("0.00")

        if campaign_dict["discount_type"] == Campaign.TYPE_FIXED:
            discount = Decimal(campaign_dict["discount_value"])
        else:
            discount = base_value * (
                Decimal(campaign_dict["discount_value"]) / Decimal("100.0")
            )
            if campaign_dict.get("max_discount_cap"):
                discount = min(discount, Decimal(campaign_dict["max_discount_cap"]))

        return min(discount, base_value)

    # ---------------- REDEEM — FIXED FOR CONCURRENCY ---------------- #

    @staticmethod
    def redeem_campaign(campaign_id, user, order_id, cart_total, delivery_fee):  # noqa: ANN001, ANN205
        """
        Concurrency-safe redeem logic.
        Uses SELECT ... FOR UPDATE and real commits.
        """  # noqa: D205
        # Ensure real DB commits (important for race tests)
        with transaction.atomic():
            now = timezone.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

            # Lock campaign row
            campaign = Campaign.objects.select_for_update().get(pk=campaign_id)

            # 1. Active?
            if not campaign.is_active:
                raise ValidationError("Campaign is not active.")

            # Date validity
            if not (campaign.start_date <= now <= campaign.end_date):
                raise ValidationError("Campaign is outside its active period.")

            # 2. Targeting
            if (
                campaign.target_users.exists()
                and not campaign.target_users.filter(pk=user.pk).exists()
            ):
                raise ValidationError("User is not eligible.")

            # 3. Daily limit
            usage = Redemption.objects.filter(
                campaign=campaign,
                user=user,
                redeemed_at__gte=today_start,
            ).count()
            if usage >= campaign.max_transactions_per_user_day:
                raise ValidationError("Daily redemption limit reached.")

            # 4. Calculate discount
            discount_to_apply = CampaignService._calculate_discount(
                campaign,
                cart_total,
                delivery_fee,
            )
            if discount_to_apply == 0:
                raise ValidationError("No discount applicable.")

            # 5. Budget check
            if campaign.current_spend + discount_to_apply > campaign.total_budget:
                raise ValidationError("Campaign budget exhausted.")

            # 6. Apply the redemption
            campaign.current_spend += discount_to_apply
            campaign.save(update_fields=["current_spend"])

            Redemption.objects.create(
                campaign=campaign,
                user=user,
                order_id=order_id,
                applied_discount=discount_to_apply,
            )

            # Important: ensures visibility in concurrent tests
            transaction.on_commit(lambda: None)

            return discount_to_apply

    # ORM version of calculator
    @staticmethod
    def _calculate_discount(campaign, cart_total, delivery_fee):  # noqa: ANN001, ANN205
        base_value = (
            cart_total if campaign.scope == Campaign.SCOPE_CART else delivery_fee
        )

        if base_value <= 0:
            return Decimal("0.00")

        if campaign.discount_type == Campaign.TYPE_FIXED:
            discount = campaign.discount_value
        else:
            discount = base_value * (campaign.discount_value / Decimal("100.0"))
            if campaign.max_discount_cap:
                discount = min(discount, campaign.max_discount_cap)

        return min(discount, base_value)
