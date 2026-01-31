from datetime import datetime
from sqlalchemy import ForeignKey, text, Integer, Float, Boolean
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from uad_shared.core.database_artwork import ArtworkBase
from uad_shared.enums.user_enums import SubscriptionTypeChoices


class UserEntity(ArtworkBase):
    __tablename__ = "users"

    id_user: Mapped[int] = mapped_column(primary_key=True)
    is_employee: Mapped[bool]
    is_alert: Mapped[bool]
    id_location: Mapped[int | None]
    id_timezone: Mapped[int | None]
    subscription: Mapped[str | None] = mapped_column(
        PG_ENUM(
            SubscriptionTypeChoices,
            name='subscriptiontypechoices',
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj]
        ),
        nullable=True,
    )
    create_date: Mapped[datetime] = mapped_column(server_default=text("NOW()"))
    update_date: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"), onupdate=func.now()
    )

    followed_artists = relationship(
        "UserFollowedArtistEntity", back_populates="user", cascade="all, delete-orphan"
    )
    followed_venues = relationship(
        "UserFollowedVenueEntity", back_populates="user", cascade="all, delete-orphan"
    )


class UserFollowedArtistEntity(ArtworkBase):
    __tablename__ = "user_followed_artist"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_user: Mapped[int] = mapped_column(ForeignKey("users.id_user", ondelete="CASCADE"))
    id_artist: Mapped[int]
    lot_price_range_from: Mapped[float | None] = mapped_column(Float, nullable=True)
    lot_price_range_to: Mapped[float | None] = mapped_column(Float, nullable=True)
    create_date: Mapped[datetime] = mapped_column(server_default=text("NOW()"))
    update_date: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"), onupdate=func.now()
    )

    user = relationship("UserEntity", back_populates="followed_artists")
    broad_media = relationship(
        "UserArtistBroadMediaEntity",
        back_populates="followed_artist",
        cascade="all, delete-orphan",
    )
    exclude_organizations = relationship(
        "UserArtistExcludeOrganizationEntity",
        back_populates="followed_artist",
        cascade="all, delete-orphan",
    )


class UserArtistBroadMediaEntity(ArtworkBase):
    __tablename__ = "user_artist_broad_media"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_user_followed_artist: Mapped[int] = mapped_column(
        ForeignKey("user_followed_artist.id", ondelete="CASCADE")
    )
    id_broad_media: Mapped[int]
    create_date: Mapped[datetime] = mapped_column(server_default=text("NOW()"))
    update_date: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"), onupdate=func.now()
    )

    followed_artist = relationship(
        "UserFollowedArtistEntity", back_populates="broad_media"
    )


class UserArtistExcludeOrganizationEntity(ArtworkBase):
    __tablename__ = "user_artist_exclude_organization"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_user_followed_artist: Mapped[int] = mapped_column(
        ForeignKey("user_followed_artist.id", ondelete="CASCADE")
    )
    id_organization: Mapped[int]
    create_date: Mapped[datetime] = mapped_column(server_default=text("NOW()"))
    update_date: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"), onupdate=func.now()
    )

    followed_artist = relationship(
        "UserFollowedArtistEntity", back_populates="exclude_organizations"
    )


class UserFollowedVenueEntity(ArtworkBase):
    __tablename__ = "user_followed_venue"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_user: Mapped[int] = mapped_column(ForeignKey("users.id_user", ondelete="CASCADE"))
    id_location: Mapped[int]
    create_date: Mapped[datetime] = mapped_column(server_default=text("NOW()"))
    update_date: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"), onupdate=func.now()
    )

    user = relationship("UserEntity", back_populates="followed_venues")
