from decimal import Decimal

from rest_framework import serializers

from app.models import Campaign


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = "__all__"
        read_only_fields = ("current_spend", "created_at")


class AvailableDiscountRequestSerializer(serializers.Serializer):
    cart_total = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    delivery_fee = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        required=False,
        default=Decimal("0.0"),
    )


class DiscountResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    scope = serializers.CharField()
    sponsor = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class RedeemRequestSerializer(serializers.Serializer):
    campaign_id = serializers.IntegerField()
    order_id = serializers.CharField()
    cart_total = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    delivery_fee = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        required=False,
        default=Decimal("0.0"),
    )
