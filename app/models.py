from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

# Create your models here.
from django.db import models


class Campaign(models.Model):
    # Scope Strategy
    SCOPE_CART = "CART"
    SCOPE_DELIVERY = "DELIVERY"
    SCOPE_CHOICES = [  # noqa: RUF012
        (SCOPE_CART, "Cart"),
        (SCOPE_DELIVERY, "Delivery"),
    ]

    # Sponsorship Strategy
    SPONSOR_PLATFORM = "PLATFORM"
    SPONSOR_VENDOR = "VENDOR"
    SPONSOR_CHOICES = [  # noqa: RUF012
        (SPONSOR_PLATFORM, "Platform"),
        (SPONSOR_VENDOR, "Vendor"),
    ]

    # Discount Types
    TYPE_PERCENTAGE = "PERCENTAGE"
    TYPE_FIXED = "FIXED"
    TYPE_CHOICES = [  # noqa: RUF012
        (TYPE_PERCENTAGE, "Percentage"),
        (TYPE_FIXED, "Fixed Amount"),
    ]

    name = models.CharField(max_length=255, help_text="Internal campaign name")
    description = models.TextField(blank=True)

    sponsor_type = models.CharField(
        max_length=20,
        choices=SPONSOR_CHOICES,
        default=SPONSOR_PLATFORM,
    )
    vendor_id = models.IntegerField(null=True, blank=True)

    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default=SCOPE_CART)

    discount_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    max_discount_cap = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    total_budget = models.DecimalField(max_digits=12, decimal_places=2)
    current_spend = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    max_transactions_per_user_day = models.IntegerField(default=1)

    target_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="targeted_campaigns",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [  # noqa: RUF012
            models.Index(fields=["start_date", "end_date", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_scope_display()})"

    def clean(self) -> None:
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("Start date cannot be after end date.")

        if self.sponsor_type == self.SPONSOR_VENDOR and not self.vendor_id:
            raise ValidationError(
                "Vendor ID is required for vendor-sponsored campaigns.",
            )

        if self.discount_type == self.TYPE_PERCENTAGE and self.discount_value > 100:  # noqa: PLR2004
            raise ValidationError("Percentage discount cannot exceed 100%.")

        if self.current_spend > self.total_budget:
            raise ValidationError("Current spend cannot exceed total budget.")


class Redemption(models.Model):
    """
    Stores each successful discount redemption.

    Ensures tracking per user, per campaign, per order.
    """

    campaign = models.ForeignKey(
        "Campaign",
        on_delete=models.CASCADE,
        related_name="redemptions",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="campaign_redemptions",
    )

    order_id = models.CharField(
        max_length=255,
        help_text="Order identifier used to ensure idempotency",
    )

    applied_discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    redeemed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [  # noqa: RUF012
            models.Index(fields=["user", "campaign", "redeemed_at"]),
            models.Index(fields=["campaign", "redeemed_at"]),
            models.Index(fields=["order_id"]),
        ]
        unique_together = [  # noqa: RUF012
            ("campaign", "order_id"),  # Prevent redeeming same order twice
        ]

    def __str__(self) -> str:
        return f"{self.user} redeemed {self.applied_discount} on {self.campaign}"
