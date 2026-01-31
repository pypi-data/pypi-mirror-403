from sqlalchemy import Column, Integer, Enum
from uad_shared.core.database import Base
from uad_shared.enums.user_enums import SubscriptionTypeChoices


class UserEntity(Base):
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True)
    subscription_type: SubscriptionTypeChoices = Column(
        Enum(SubscriptionTypeChoices), nullable=False
    )
