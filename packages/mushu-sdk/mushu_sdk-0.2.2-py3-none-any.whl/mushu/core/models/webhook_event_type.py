from enum import Enum


class WebhookEventType(str, Enum):
    CREDITS_LOW = "credits.low"
    CREDITS_PURCHASED = "credits.purchased"
    NOTIFICATION_BOUNCED = "notification.bounced"
    NOTIFICATION_DELIVERED = "notification.delivered"
    NOTIFICATION_FAILED = "notification.failed"
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    QUOTA_EXCEEDED = "quota.exceeded"
    QUOTA_WARNING = "quota.warning"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    SUBSCRIPTION_CREATED = "subscription.created"
    USER_CONSENT_REVOKED = "user.consent_revoked"
    USER_CREATED = "user.created"
    USER_DELETED = "user.deleted"

    def __str__(self) -> str:
        return str(self.value)
