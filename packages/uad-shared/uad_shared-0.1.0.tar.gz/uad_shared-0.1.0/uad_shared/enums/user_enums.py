from __future__ import annotations
import enum

def normalize_subscription_value(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip().lower()


class SubscriptionTypeChoices(str, enum.Enum):
    FREE = "Free"
    PREMIUM = "Premium"
    PERSONAL_ALERTS = "Personal Alerts"
    VIP = "VIP"
    ESSENTIALS = "Essentials"
    PERSONAL_ALERTS_STARTER = "Personal Alerts (Starter)"
    OPEN = "Open"
    BASIC = "Basic"
    TERMINATED = "Terminated"
    C100 = "C100"
    C200 = "C200"
    C300 = "C300"
    CU = "CU"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            normalized = normalize_subscription_value(value)
            for member in cls:
                if member.value.lower() == normalized or member.name.lower() == normalized:
                    return member
        return None

    @classmethod
    def from_string(
        cls,
        value: str | None,
        default: "SubscriptionTypeChoices" | None = None,
    ) -> "SubscriptionTypeChoices" | None:
        if value is None:
            return default
        if isinstance(value, cls):
            return value
        matched = cls._missing_(value)
        if matched is not None:
            return matched
        return default
