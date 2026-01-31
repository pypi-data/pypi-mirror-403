import enum


class Phase(str, enum.Enum):
    DEV = "dev"
    STAGING = "staging"
    PRODUCTION = "production"


class OperationChoices(enum.Enum):
    CREATE = 0
    DELETE = 1
