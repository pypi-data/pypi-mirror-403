import enum


class EventCategoryChoices(enum.Enum):
    INTERACTION = "interaction"
    PAGE_VISIT = "page_visit"


class EntityTypeChoices(enum.Enum):
    ARTICLE = 1
    EVENT = 2
    ARTWORK = 3
    ORGANIZATION = 4
    PERSON = 5
    ASSET = 6
    LOT = 7
    OFFERSHEET = 8


class AppChoices(str, enum.Enum):
    MA = "MA"
    GLR = "GLR"
    PSS = "PSS"
