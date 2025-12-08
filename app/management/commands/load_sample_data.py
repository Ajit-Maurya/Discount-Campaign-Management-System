from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from app.models import Campaign, Redemption

User = get_user_model()


class Command(BaseCommand):
    help = "Load sample data for campaigns, users, and redemptions"

    def handle(self, *args, **kwargs):
        now = timezone.now()

        # ---------------- USERS ----------------
        self.stdout.write("Creating sample users...")
        user1, _ = User.objects.get_or_create(
            username="user1", defaults={"password": "pass123"}
        )
        user2, _ = User.objects.get_or_create(
            username="user2", defaults={"password": "pass123"}
        )
        user3, _ = User.objects.get_or_create(
            username="user3", defaults={"password": "pass123"}
        )

        # ---------------- CAMPAIGNS ----------------
        self.stdout.write("Creating sample campaigns...")

        campaign1, _ = Campaign.objects.get_or_create(
            name="Holiday Sale",
            defaults={
                "description": "10% off on all carts above 50",
                "sponsor_type": Campaign.SPONSOR_PLATFORM,
                "scope": Campaign.SCOPE_CART,
                "discount_type": Campaign.TYPE_PERCENTAGE,
                "discount_value": Decimal("10.00"),
                "max_discount_cap": Decimal("50.00"),
                "start_date": now,
                "end_date": now + timezone.timedelta(days=30),
                "total_budget": Decimal("10000.00"),
                "current_spend": Decimal("0.00"),
                "max_transactions_per_user_day": 1,
                "is_active": True,
            },
        )
        campaign1.target_users.set([user1, user2, user3])

        campaign2, _ = Campaign.objects.get_or_create(
            name="Free Delivery Promo",
            defaults={
                "description": "Flat 20 off delivery fee",
                "sponsor_type": Campaign.SPONSOR_VENDOR,
                "vendor_id": 101,
                "scope": Campaign.SCOPE_DELIVERY,
                "discount_type": Campaign.TYPE_FIXED,
                "discount_value": Decimal("20.00"),
                "start_date": now,
                "end_date": now + timezone.timedelta(days=15),
                "total_budget": Decimal("5000.00"),
                "current_spend": Decimal("0.00"),
                "max_transactions_per_user_day": 2,
                "is_active": True,
            },
        )
        campaign2.target_users.set([user2, user3])

        campaign3, _ = Campaign.objects.get_or_create(
            name="Mega Cart Discount",
            defaults={
                "description": "20% off for carts above 500",
                "sponsor_type": Campaign.SPONSOR_PLATFORM,
                "scope": Campaign.SCOPE_CART,
                "discount_type": Campaign.TYPE_PERCENTAGE,
                "discount_value": Decimal("20.00"),
                "max_discount_cap": Decimal("150.00"),
                "start_date": now,
                "end_date": now + timezone.timedelta(days=60),
                "total_budget": Decimal("20000.00"),
                "current_spend": Decimal("0.00"),
                "max_transactions_per_user_day": 1,
                "is_active": True,
            },
        )
        campaign3.target_users.set([user1, user3])

        # ---------------- REDEMPTIONS ----------------
        self.stdout.write("Creating sample redemptions...")

        Redemption.objects.get_or_create(
            campaign=campaign1,
            user=user1,
            order_id="ORD001",
            defaults={"applied_discount": Decimal("10.00")},
        )

        Redemption.objects.get_or_create(
            campaign=campaign1,
            user=user2,
            order_id="ORD002",
            defaults={"applied_discount": Decimal("10.00")},
        )

        Redemption.objects.get_or_create(
            campaign=campaign2,
            user=user3,
            order_id="ORD003",
            defaults={"applied_discount": Decimal("20.00")},
        )

        Redemption.objects.get_or_create(
            campaign=campaign3,
            user=user3,
            order_id="ORD004",
            defaults={"applied_discount": Decimal("100.00")},
        )

        self.stdout.write(self.style.SUCCESS("Sample data loaded successfully!"))
