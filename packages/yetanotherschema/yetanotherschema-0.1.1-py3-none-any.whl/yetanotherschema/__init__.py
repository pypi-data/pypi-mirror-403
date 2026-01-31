"""
YetAnotherSchema - Semantic Database for Auditable Data

Philosophy: "Values are free ions, not tables. Everything else is a view."

Main API:
    - create(space_name, schema_path) - Create a space
    - write(space_name, field, value, contexts) - Write a value
    - write_batch(space_name, records) - Write multiple values
    - read(space_name, fields, contexts, filters, as_of) - Read values
    - schema(space_name, detail) - View schema
    - list_spaces() - List all spaces
"""

__version__ = "0.1.0"
__author__ = "Krishnamoorthy Sankaran"

from yetanotherschema.api import (
    create,
    write,
    write_batch,
    read,
    schema,
    list_spaces
)

__all__ = [
    'create',
    'write',
    'write_batch',
    'read',
    'schema',
    'list_spaces'
]
