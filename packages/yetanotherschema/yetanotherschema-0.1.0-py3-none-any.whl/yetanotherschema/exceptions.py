"""
YetAnotherSchema Exceptions
"""


class YetAnotherSchemaError(Exception):
    """Base exception for YetAnotherSchema"""
    pass


class SpaceExistsError(YetAnotherSchemaError):
    """Space already exists"""
    pass


class SpaceNotFoundError(YetAnotherSchemaError):
    """Space not found"""
    pass


class SchemaValidationError(YetAnotherSchemaError):
    """Schema validation failed"""
    pass


class ValidationError(YetAnotherSchemaError):
    """Validation error (missing required fields, contexts, etc.)"""
    pass


class FieldNotFoundError(YetAnotherSchemaError):
    """Field not found in space"""
    pass


class DatabaseError(YetAnotherSchemaError):
    """Database operation failed"""
    pass
