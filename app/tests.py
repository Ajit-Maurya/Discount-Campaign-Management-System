import threading
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.utils import timezone

from app.models import Campaign, Redemption
from app.services.campaign_service import CampaignService

User = get_user_model()


class ConcurrentBudgetTest(TransactionTestCase):
    """Tests that SELECT FOR UPDATE budget locking works under concurrency."""

    reset_sequences = True

    def test_race_condition_on_budget(self) -> None:
        """Budget = $20, each redemption = $10 → Only 2 redemptions must succeed."""
        user = User.objects.create_user(username="tester", password="pass")  # noqa: S106

        campaign = Campaign.objects.create(
            name="Flash Sale",
            description="Test concurrency",
            sponsor_type=Campaign.SPONSOR_PLATFORM,
            scope=Campaign.SCOPE_CART,
            discount_type=Campaign.TYPE_FIXED,
            discount_value=Decimal("10.00"),
            total_budget=Decimal("20.00"),
            current_spend=Decimal("0.00"),
            max_discount_cap=None,
            max_transactions_per_user_day=100,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=1),
            is_active=True,
        )

        results = []
        lock = threading.Lock()

        def attempt_redemption(i: int) -> None:
            try:
                CampaignService.redeem_campaign(
                    campaign_id=campaign.id,
                    user=user,
                    order_id=f"order_{i}",
                    cart_total=Decimal("100.00"),
                    delivery_fee=Decimal("0.00"),
                )
                with lock:
                    results.append(True)
            except Exception:  # noqa: BLE001
                with lock:
                    results.append(False)

        threads = [
            threading.Thread(target=attempt_redemption, args=(i,)) for i in range(5)
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        successes = results.count(True)
        campaign.refresh_from_db()

        # Validate exactly 2 success
        self.assertEqual(  # noqa: PT009
            successes,
            2,
            f"Expected exactly 2 redemptions but got {successes}",
        )

        # Budget should be exactly $20
        self.assertEqual(campaign.current_spend, Decimal("20.00"))  # noqa: PT009

        # Sanity check: DB must contain exactly 2 redemption rows
        redemption_count = Redemption.objects.filter(campaign=campaign).count()
        self.assertEqual(redemption_count, 2)  # noqa: PT009
