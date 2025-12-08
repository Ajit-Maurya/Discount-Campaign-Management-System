from django.core.exceptions import ValidationError
from django.http import HttpRequest
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Campaign
from .serializers import (
    AvailableDiscountRequestSerializer,
    CampaignSerializer,
    DiscountResponseSerializer,
    RedeemRequestSerializer,
)
from .services.campaign_service import CampaignService
from .throttles import RedeemRateThrottle


class CampaignViewSet(viewsets.ModelViewSet):
    """
    Management of Campaigns.

    Standard CRUD is protected by IsAdminUser.
    Public actions 'available' and 'redeem' are accessible to authenticated users.
    """

    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
    permission_classes = [permissions.IsAdminUser]  # noqa: RUF012

    def get_permissions(self):  # noqa: ANN201
        if self.action in ["available", "redeem"]:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    # ------------- AVAILABLE DISCOUNTS -----------------------------

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="cart_total",
                description="Total value of the cart",
                required=True,
                type=str,  # Decimal is represented as string
            ),
            OpenApiParameter(
                name="delivery_fee",
                description="Delivery fee",
                required=False,
                type=str,
            ),
        ],
        responses=OpenApiResponse(
            response=DiscountResponseSerializer(many=True),
            description="List of discounts that can be applied",
        ),
        summary="Fetch applicable discounts",
        description="Calculates potential discounts based on the provided cart context. Does not reserve funds.",
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="available",
    )
    def available(self, request: HttpRequest) -> Response:
        # Validate query params
        input_serializer = AvailableDiscountRequestSerializer(data=request.query_params)
        input_serializer.is_valid(raise_exception=True)
        params = input_serializer.validated_data

        # Business logic
        results = CampaignService.get_available_discounts(
            user=request.user,
            cart_total=params["cart_total"],
            delivery_fee=params.get("delivery_fee", 0),
        )

        return Response(DiscountResponseSerializer(results, many=True).data)

    # ------------- REDEEM DISCOUNT -----------------------------

    @extend_schema(
        request=RedeemRequestSerializer,
        responses={
            200: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "discount_applied": {"type": "string"},  # Decimal
                    },
                },
                description="Discount successfully redeemed",
            ),
            400: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {"error": {"type": "string"}},
                },
                description="Invalid redemption attempt",
            ),
        },
        summary="Redeem a discount",
        description="Atomic operation. Locks the campaign, checks limits, applies discount, and logs redemption.",
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="redeem",
        throttle_classes=[RedeemRateThrottle],
    )
    def redeem(self, request: HttpRequest) -> Response:
        input_serializer = RedeemRequestSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        data = input_serializer.validated_data

        try:
            amount = CampaignService.redeem_campaign(
                campaign_id=data["campaign_id"],
                user=request.user,
                order_id=data["order_id"],
                cart_total=data["cart_total"],
                delivery_fee=data.get("delivery_fee", 0),
            )
            return Response(
                {"status": "success", "discount_applied": str(amount)},
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
