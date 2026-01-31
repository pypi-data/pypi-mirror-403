# UAD Shared Package

Shared Python package containing models, enums, and core database utilities for use across UAD and RS projects.

## Purpose

This package provides a single source of truth for:
- **Models**: SQLAlchemy ORM models for UAD entities (users, events, artwork, etc.)
- **Enums**: Common enumerations used across projects (subscription types, entity types, etc.)
- **Core Database**: Base classes for SQLAlchemy declarative models

## Installation

### For UAD Project

The package is installed as an editable dependency:

```bash
pip install -e ./shared/uad_shared
```

Or via requirements.txt:

```txt
-e ./shared/uad_shared
```

### For RS Project

Install from the UAD repository:

```bash
pip install -e ../user-action-data/shared/uad_shared
```

Or via requirements.txt:

```txt
-e ../user-action-data/shared/uad_shared
```

## Usage

### Importing Models

```python
from uad_shared.models.user_models import UserEntity
from uad_shared.models.event_models import UADEventEntity, EventTypeEntity
from uad_shared.models.artwork_models import ArtworkEntity, ArtistEntity
from uad_shared.models.user_preference_models import UserEntity as UserPreferenceEntity
```

### Importing Enums

```python
from uad_shared.enums.user_enums import SubscriptionTypeChoices
from uad_shared.enums.event_enums import EntityTypeChoices, AppChoices, EventCategoryChoices
from uad_shared.enums.common_enums import Phase, OperationChoices
```

### Importing Database Base Classes

```python
from uad_shared.core.database import Base
from uad_shared.core.database_artwork import ArtworkBase
```

**Note**: The shared package only provides Base classes. Each project (UAD, RS) creates its own database engine and session using these Base classes.

## Package Structure

```
uad_shared/
├── uad_shared/
│   ├── __init__.py
│   ├── models/          # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user_models.py
│   │   ├── event_models.py
│   │   ├── artwork_models.py
│   │   └── user_preference_models.py
│   ├── enums/           # Enumeration classes
│   │   ├── __init__.py
│   │   ├── common_enums.py
│   │   ├── event_enums.py
│   │   └── user_enums.py
│   └── core/            # Database base classes
│       ├── __init__.py
│       ├── database.py      # Base for main database
│       └── database_artwork.py  # ArtworkBase for artwork database
├── setup.py
├── pyproject.toml
└── README.md
```

## Models

### User Models (`user_models.py`)
- `UserEntity`: Main user entity for UAD events

### Event Models (`event_models.py`)
- `EventTypeEntity`: Event type definitions
- `UADEventEntity`: User action data events
- `UserArtworkFeatureScore`: User artwork feature scores for recommendations

### Artwork Models (`artwork_models.py`)
- `ArtistEntity`: Artist information
- `EventEntity`: Auction events
- `ArtworkEntity`: Artwork details
- `ArtworkArtistEntity`: Artwork-artist relationships
- `ArtworkOrganizationEntity`: Artwork-organization relationships
- `ArtworkColorEntity`: Artwork color analysis

### User Preference Models (`user_preference_models.py`)
- `UserEntity`: User entity for preferences (different from main UserEntity)
- `UserFollowedArtistEntity`: User followed artists
- `UserArtistBroadMediaEntity`: User artist broad media preferences
- `UserArtistExcludeOrganizationEntity`: User artist excluded organizations
- `UserFollowedVenueEntity`: User followed venues

## Enums

### Common Enums (`common_enums.py`)
- `Phase`: Environment phase (DEV, STAGING, PRODUCTION)
- `OperationChoices`: CRUD operation types (CREATE, DELETE)

### Event Enums (`event_enums.py`)
- `EventCategoryChoices`: Event categories (INTERACTION, PAGE_VISIT)
- `EntityTypeChoices`: Entity types (ARTICLE, EVENT, ARTWORK, etc.)
- `AppChoices`: Application identifiers (MA, GLR, PSS)

### User Enums (`user_enums.py`)
- `SubscriptionTypeChoices`: User subscription types (FREE, PREMIUM, VIP, etc.)

## Database Base Classes

### Base (`core/database.py`)
Base class for models in the main UAD database. Used by:
- `UserEntity`
- `UADEventEntity`
- `EventTypeEntity`
- `UserArtworkFeatureScore`

### ArtworkBase (`core/database_artwork.py`)
Base class for models in the artwork/entity database. Used by:
- `ArtworkEntity`
- `ArtistEntity`
- `EventEntity`
- All artwork-related models
- User preference models

## Versioning

The package version is defined in:
- `setup.py`: `version="0.1.0"`
- `pyproject.toml`: `version = "0.1.0"`
- `uad_shared/__init__.py`: `__version__ = "0.1.0"`

**Versioning Strategy:**
- Update version when making breaking changes
- Tag releases in Git for production use
- Follow semantic versioning (MAJOR.MINOR.PATCH)

## Development

### Making Changes

1. Edit files in `shared/uad_shared/uad_shared/`
2. Both UAD and RS projects will pick up changes automatically (editable install)
3. Test changes in both projects before committing

### Adding New Models

1. Create model file in `uad_shared/models/`
2. Import appropriate Base class (`Base` or `ArtworkBase`)
3. Add import to `uad_shared/models/__init__.py` for re-export
4. Update this README if needed

### Adding New Enums

1. Create enum file in `uad_shared/enums/` or add to existing file
2. Add import to `uad_shared/enums/__init__.py` for re-export
3. Update this README if needed

## Dependencies

The package requires:
- `sqlalchemy>=2.0.0`: ORM framework
- `psycopg2-binary>=2.9.0`: PostgreSQL adapter

These are specified in `setup.py` and `pyproject.toml`.

## Notes

- **Single Source of Truth**: Files are moved (not copied) from UAD project, ensuring only one location for models/enums
- **No Engine/Session**: The shared package provides Base classes only. Each project creates its own database connections
- **Compatibility**: Both UAD and RS projects use the same package, ensuring model/enum compatibility
- **Editable Install**: Both projects use editable installs (`-e`) for development convenience

## Troubleshooting

### Import Errors

If you see import errors:
1. Ensure the package is installed: `pip install -e ./shared/uad_shared`
2. Verify Python path includes the package
3. Check that imports use `uad_shared.*` not `app.*`

### Database Connection Issues

The shared package does not handle database connections. Each project must:
- Create its own engine using project-specific settings
- Create its own session factory
- Use the Base classes from the shared package

### Version Conflicts

If you encounter version conflicts:
1. Check that both projects use the same version
2. Update version in `setup.py` and `pyproject.toml`
3. Reinstall the package in both projects
