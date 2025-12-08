from rest_framework.throttling import UserRateThrottle


class RedeemRateThrottle(UserRateThrottle):
    scope = "redeem"
