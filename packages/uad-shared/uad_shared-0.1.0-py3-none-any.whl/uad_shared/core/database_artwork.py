"""
Shared artwork database Base for UAD models.
Simplified version without engine/session (consumers create their own connections).
"""
from sqlalchemy.ext.declarative import declarative_base

ArtworkBase = declarative_base()
