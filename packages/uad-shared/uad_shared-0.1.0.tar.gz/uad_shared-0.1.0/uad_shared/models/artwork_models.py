from datetime import datetime
from sqlalchemy import ForeignKey, text, ARRAY, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from uad_shared.core.database_artwork import ArtworkBase


class ArtistEntity(ArtworkBase):
    __tablename__ = "artist"

    id_artist: Mapped[int] = mapped_column(primary_key=True)
    display_name: Mapped[str]
    id_nationality: Mapped[list[int] | None] = mapped_column(ARRAY(Integer))
    id_category: Mapped[list[int] | None] = mapped_column(ARRAY(Integer))
    birth: Mapped[int | None]
    death: Mapped[int | None]
    active_in: Mapped[list[int] | None] = mapped_column(ARRAY(Integer))
    create_date: Mapped[datetime] = mapped_column(server_default=text("NOW()"))
    update_date: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"), onupdate=func.now()
    )

    artwork_artists = relationship("ArtworkArtistEntity", back_populates="artist")


class EventEntity(ArtworkBase):
    __tablename__ = "event"

    id_event: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    start_date: Mapped[datetime]
    end_date: Mapped[datetime | None] = mapped_column(nullable=True)
    location: Mapped[list[int]] = mapped_column(ARRAY(Integer))
    create_date: Mapped[datetime] = mapped_column(server_default=text("NOW()"))
    update_date: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"), onupdate=func.now()
    )

    artworks = relationship("ArtworkEntity", back_populates="event")


class ArtworkEntity(ArtworkBase):
    __tablename__ = "artwork"

    id_artwork: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    dimensions_h_in: Mapped[float | None]
    dimensions_w_in: Mapped[float | None]
    dimensions_d_in: Mapped[float | None]
    dimensions_h_cm: Mapped[float | None]
    dimensions_w_cm: Mapped[float | None]
    dimensions_d_cm: Mapped[float | None]
    dimensions_descr: Mapped[str | None]
    is_signed: Mapped[bool]
    medium_text: Mapped[str | None]
    broad_media: Mapped[int | None]
    artwork_orientation: Mapped[int | None]
    repeate_sale_group_id: Mapped[int | None]
    from_year: Mapped[int | None]
    to_year: Mapped[int | None]
    has_image: Mapped[bool]
    lot_status: Mapped[int]
    min_est_usd: Mapped[float | None]
    max_est_usd: Mapped[float | None]
    min_est_eur: Mapped[float | None]
    max_est_eur: Mapped[float | None]
    min_est_gbp: Mapped[float | None]
    max_est_gbp: Mapped[float | None]
    usd_price: Mapped[float | None]
    real_eur: Mapped[float | None]
    real_gbp: Mapped[float | None]
    min_estimated_price: Mapped[float | None]
    max_estimated_price: Mapped[float | None]
    realized_price: Mapped[float | None]
    currency: Mapped[int]
    is_lot: Mapped[bool]
    price_sort: Mapped[float | None]
    price_sort_eur: Mapped[float | None]
    price_sort_gbp: Mapped[float | None]
    performance_sort: Mapped[float | None]
    artwork_performance: Mapped[float | None]
    estimate_sort: Mapped[float | None]
    first_publish_date: Mapped[datetime]
    last_modified_date: Mapped[datetime]
    id_event: Mapped[int | None] = mapped_column(ForeignKey("event.id_event"), nullable=True)
    create_date: Mapped[datetime] = mapped_column(server_default=text("NOW()"))
    update_date: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"), onupdate=func.now()
    )

    event = relationship("EventEntity", back_populates="artworks")
    artwork_artists = relationship("ArtworkArtistEntity", back_populates="artwork")
    organizations = relationship("ArtworkOrganizationEntity", back_populates="artwork")
    colors = relationship("ArtworkColorEntity", back_populates="artwork")


class ArtworkArtistEntity(ArtworkBase):
    __tablename__ = "artwork_artist"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_artwork: Mapped[int] = mapped_column(ForeignKey("artwork.id_artwork"))
    id_artist: Mapped[int] = mapped_column(ForeignKey("artist.id_artist"))
    artwork_artist_type: Mapped[int]
    create_date: Mapped[datetime] = mapped_column(server_default=text("NOW()"))
    update_date: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"), onupdate=func.now()
    )

    artwork = relationship("ArtworkEntity", back_populates="artwork_artists")
    artist = relationship("ArtistEntity", back_populates="artwork_artists")


class ArtworkOrganizationEntity(ArtworkBase):
    __tablename__ = "artwork_organization"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_organization: Mapped[int]
    importance: Mapped[int]
    id_artwork: Mapped[int] = mapped_column(ForeignKey("artwork.id_artwork"))
    create_date: Mapped[datetime] = mapped_column(server_default=text("NOW()"))
    update_date: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"), onupdate=func.now()
    )

    artwork = relationship("ArtworkEntity", back_populates="organizations")


class ArtworkColorEntity(ArtworkBase):
    __tablename__ = "artwork_color"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_artwork: Mapped[int] = mapped_column(ForeignKey("artwork.id_artwork"))
    l: Mapped[float]
    a: Mapped[float]
    b: Mapped[float]
    percentage: Mapped[float]
    create_date: Mapped[datetime] = mapped_column(server_default=text("NOW()"))
    update_date: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"), onupdate=func.now()
    )

    artwork = relationship("ArtworkEntity", back_populates="colors")
