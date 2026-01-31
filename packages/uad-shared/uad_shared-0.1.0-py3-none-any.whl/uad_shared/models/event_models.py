from sqlalchemy import Column, Integer, String, TIMESTAMP, Enum, Boolean, Text, ForeignKey, Index, BigInteger, DECIMAL
from sqlalchemy.dialects.postgresql import INET, ENUM as PG_ENUM, TIMESTAMP as PG_TIMESTAMP
from sqlalchemy.sql import func
from uad_shared.core.database import Base
from uad_shared.enums.user_enums import SubscriptionTypeChoices
from uad_shared.enums.event_enums import EventCategoryChoices, EntityTypeChoices, AppChoices


class EventTypeEntity(Base):
    __tablename__ = "event_types"

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String(50), unique=True, nullable=False)
    description: str = Column(Text, nullable=True)
    is_active: bool = Column(Boolean, default=True, nullable=False)
    category: EventCategoryChoices = Column(Enum(EventCategoryChoices), nullable=False)


class UADEventEntity(Base):
    __tablename__ = "uad_event"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    app: AppChoices = Column(
        Enum(AppChoices), primary_key=True
    )  # Example: MA, GLR, PSS (values expected to be integers or ENUM/lookup)
    user_id: int = Column(Integer, nullable=False)
    event_type: int = Column(Integer, ForeignKey("event_types.id"), nullable=False)
    user_agent: str | None = Column(String(1500), nullable=True)
    browser: str | None = Column(String(50), nullable=True)  # From user-agent
    device_type: str | None = Column(String(50), nullable=True)  # From user-agent
    os: str | None = Column(String(50), nullable=True)  # From user-agent
    ip: str | None = Column(INET, nullable=True)
    location_id: int | None = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    api_timestamp = Column(
        TIMESTAMP, server_default=func.now(), nullable=False
    )  # Custom API-provided timestamp
    entity_id: int | None = Column(Integer, nullable=True)
    entity_type: EntityTypeChoices | None = Column(
        Enum(EntityTypeChoices), nullable=True
    )
    subscription_type = Column(
        PG_ENUM(
            SubscriptionTypeChoices,
            name="subscriptiontypechoices",
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=True,
    )
    source: str | None = Column(String(100), nullable=True)


class UserArtworkFeatureScore(Base):
    __tablename__ = "user_artwork_feature_scores"
    
    user_id: int = Column(Integer, primary_key=True, nullable=False)
    feature_type: str = Column(String(50), primary_key=True, nullable=False)
    feature_value: str = Column(String(100), primary_key=True, nullable=False)
    raw_score: float = Column(DECIMAL(10, 4), nullable=False)
    last_interaction_g: int = Column(BigInteger, nullable=False)
    last_updated = Column(
        PG_TIMESTAMP(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    
    __table_args__ = (
        Index('idx_uafs_user', 'user_id'),
    )
