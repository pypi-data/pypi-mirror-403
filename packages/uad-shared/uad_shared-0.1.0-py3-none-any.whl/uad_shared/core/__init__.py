"""
UAD Shared Core - Database base classes for models.
"""
from .database import Base
from .database_artwork import ArtworkBase

__all__ = ["Base", "ArtworkBase"]
