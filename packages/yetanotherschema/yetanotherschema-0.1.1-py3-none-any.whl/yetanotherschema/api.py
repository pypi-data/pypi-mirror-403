"""
YetAnotherSchema Main API

Functions:
    - create(space_name, schema_path, storage_path)
    - write(space_name, field, value, contexts)
    - write_batch(space_name, records)
    - read(space_name, fields, contexts, filters, as_of, include_metadata)
    - schema(space_name, detail)
    - list_spaces(storage_path)
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import polars as pl
import json
from datetime import datetime

from yetanotherschema.core import DatabaseManager, ValueStore, ContextStore, QueryEngine
from yetanotherschema.exceptions import (
    SpaceNotFoundError,
    ValidationError
)


# Global cache for database connections
_db_cache: Dict[str, tuple] = {}


def _get_db_components(space_name: str, storage_path: Optional[str] = None):
    """Get or create database components for a space"""
    # Determine database path
    if storage_path:
        db_path = storage_path
    else:
        db_path = f"./{space_name}.db"
    
    # Check cache
    if db_path in _db_cache:
        return _db_cache[db_path]
    
    # Check if database exists
    if not Path(db_path).exists():
        raise SpaceNotFoundError(f"Space '{space_name}' not found at {db_path}")
    
    # Create components
    db_manager = DatabaseManager(db_path)
    value_store = ValueStore(db_manager)
    context_store = ContextStore(db_manager)
    query_engine = QueryEngine(value_store, context_store)
    
    # Cache components
    _db_cache[db_path] = (db_manager, value_store, context_store, query_engine)
    
    return _db_cache[db_path]


def create(
    space_name: str,
    schema_path: str,
    storage_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new space.
    
    Args:
        space_name: Name of the space (e.g., 'clinical_study_001')
        schema_path: Path to schema.toml
        storage_path: Optional custom storage path (default: ./{space_name}.db)
    
    Returns:
        Dict with creation info:
            - space_name: str
            - storage_path: str
            - created_at: str (ISO timestamp)
            - schema_version: str
    
    Raises:
        SpaceExistsError: If space already exists
        SchemaValidationError: If schema.toml is invalid
    """
    # Determine database path
    if storage_path:
        db_path = storage_path
    else:
        db_path = f"./{space_name}.db"
    
    # Create database
    db_manager = DatabaseManager(db_path, schema_path, create_new=True)
    
    # Get schema info
    schema = db_manager.get_schema()
    schema_version = schema.get('metadata', {}).get('version', '0.1.0')
    created_at = datetime.now().isoformat()
    
    # Close connection
    db_manager.close()
    
    return {
        'space_name': space_name,
        'storage_path': db_path,
        'created_at': created_at,
        'schema_version': schema_version
    }


def write(
    space_name: str,
    field: str,
    value: Dict[str, Any],
    contexts: Dict[str, str]
) -> int:
    """
    Write a value to the space.
    
    Args:
        space_name: Name of the space
        field: Field name (e.g., 'height', 'weight')
        value: Value dict with:
            - raw_value: Any (required) - the actual measurement
            - metadata: Dict[str, Any] (optional) - informational only, no validation
            - reported_timestamp: str (optional) - ISO format, user-reported time
            - user_id: str (required) - who created this value
        contexts: Context mappings (at least 1 required per schema)
            e.g., {'subject_id': 'S001', 'visit': 'V1'}
    
    Returns:
        value_id: int - Unique ID of created value
    
    Raises:
        SpaceNotFoundError: If space doesn't exist
        ValidationError: If required contexts missing (per schema)
        ValidationError: If required value fields missing (raw_value, user_id)
    """
    # Validate value dict
    if 'raw_value' not in value:
        raise ValidationError("Value dict must contain 'raw_value'")
    
    if 'user_id' not in value:
        raise ValidationError("Value dict must contain 'user_id'")
    
    # Get database components
    db_manager, value_store, context_store, _ = _get_db_components(space_name)
    
    # Add value
    value_id = value_store.add_value(
        field=field,
        raw_value=value['raw_value'],
        metadata=value.get('metadata', {}),
        user_id=value['user_id'],
        reported_timestamp=value.get('reported_timestamp')
    )
    
    # Add context relationship
    context_store.add_relationship(
        contexts=contexts,
        field=field,
        value_id=value_id
    )
    
    return value_id


def write_batch(
    space_name: str,
    records: List[Dict[str, Any]]
) -> List[int]:
    """
    Write multiple values in batch (faster).
    
    Args:
        space_name: Name of the space
        records: List of dicts, each with:
            - field: str
            - value: Dict (same structure as write())
            - contexts: Dict
    
    Returns:
        List[int]: List of value_ids
    """
    value_ids = []
    
    for record in records:
        value_id = write(
            space_name=space_name,
            field=record['field'],
            value=record['value'],
            contexts=record['contexts']
        )
        value_ids.append(value_id)
    
    return value_ids


def read(
    space_name: str,
    fields: List[str],
    contexts: Optional[Dict[str, str]] = None,
    filters: Optional[Dict[str, Any]] = None,
    as_of: Optional[str] = None,
    include_metadata: bool = False
) -> pl.DataFrame:
    """
    Read values from the space as a Polars DataFrame.
    
    Args:
        space_name: Name of the space
        fields: List of fields to include
            - Context fields (e.g., 'subject_id', 'visit')
            - Value fields (e.g., 'height', 'weight')
        contexts: Optional context filter
            e.g., {'subject_id': 'S001'} - returns all visits for S001
            e.g., {'subject_id': 'S001', 'visit': 'V1'} - specific visit
        filters: Optional value filters (dict-based syntax)
            e.g., {'height': {'gt': 160, 'lt': 200}}
            e.g., {'weight': {'gte': 50, 'lte': 100}}
            Supported operators: gt, gte, lt, lte, eq, ne, contains, in, not_in
        as_of: Optional timestamp for time-travel (ISO format)
            Uses created_timestamp for filtering
            e.g., '2026-01-15T23:59:59' - data as it existed on Jan 15
        include_metadata: If True, include metadata column in result
    
    Returns:
        Polars DataFrame with requested fields
        - Context columns (from fields list)
        - Value columns (from fields list)
        - metadata column (if include_metadata=True)
    
    Raises:
        SpaceNotFoundError: If space doesn't exist
        FieldNotFoundError: If field in fields list doesn't exist
    
    Notes:
        - Returns latest value by default (based on created_timestamp)
        - Pivoted to wide format (one row per unique context combination)
        - Metadata not validated - can contain any fields
    """
    # Get database components
    _, _, _, query_engine = _get_db_components(space_name)
    
    # Query values
    df = query_engine.query(
        fields=fields,
        context_filter=contexts,
        value_filters=filters,
        as_of=as_of,
        include_metadata=include_metadata
    )
    
    return df


def schema(
    space_name: str,
    detail: str = 'summary'
) -> Dict[str, Any]:
    """
    Display the schema of a space.
    
    Args:
        space_name: Name of the space
        detail: Level of detail
            - 'summary': High-level overview (default)
            - 'full': Complete schema with all metadata
            - 'contexts': Only context definitions
            - 'hierarchies': Only hierarchy definitions
            - 'values': Only value field definitions
            - 'stats': Statistics about the space
    
    Returns:
        Dict with schema information (structure depends on detail level)
    
    Raises:
        SpaceNotFoundError: If space doesn't exist
    """
    # Get database components
    db_manager, value_store, context_store, _ = _get_db_components(space_name)
    
    schema_data = db_manager.get_schema()
    
    if detail == 'summary':
        return {
            'space_name': space_name,
            'schema_version': schema_data.get('metadata', {}).get('version', '0.1.0'),
            'created_at': schema_data.get('created_at', 'unknown'),
            'contexts': schema_data.get('contexts', {}),
            'hierarchies': schema_data.get('hierarchies', {}),
            'value_fields': list(schema_data.get('values', {}).keys())
        }
    
    elif detail == 'full':
        return schema_data
    
    elif detail == 'contexts':
        return schema_data.get('contexts', {})
    
    elif detail == 'hierarchies':
        return schema_data.get('hierarchies', {})
    
    elif detail == 'values':
        return schema_data.get('values', {})
    
    elif detail == 'stats':
        # Get statistics
        result = db_manager.execute("SELECT COUNT(*) FROM values").fetchone()
        total_values = result[0] if result else 0
        
        result = db_manager.execute("SELECT COUNT(DISTINCT context_key) FROM context_relationships").fetchone()
        unique_contexts = result[0] if result else 0
        
        return {
            'space_name': space_name,
            'total_values': total_values,
            'unique_contexts': unique_contexts,
            'value_fields': len(schema_data.get('values', {}))
        }
    
    else:
        raise ValidationError(f"Invalid detail level: {detail}")


def list_spaces(
    storage_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List all available spaces.
    
    Args:
        storage_path: Optional path to search for spaces (default: current directory)
    
    Returns:
        List of dicts, each with:
            - space_name: str
            - storage_path: str
            - created_at: str
            - schema_version: str
            - total_values: int
    """
    # Determine search path
    search_path = Path(storage_path) if storage_path else Path('.')
    
    # Find all .db files
    db_files = list(search_path.glob('*.db'))
    
    spaces = []
    
    for db_file in db_files:
        try:
            # Try to open database
            db_manager = DatabaseManager(str(db_file))
            schema_data = db_manager.get_schema()
            
            # Get statistics
            result = db_manager.execute("SELECT COUNT(*) FROM values").fetchone()
            total_values = result[0] if result else 0
            
            space_name = db_file.stem
            
            spaces.append({
                'space_name': space_name,
                'storage_path': str(db_file),
                'created_at': schema_data.get('created_at', 'unknown'),
                'schema_version': schema_data.get('metadata', {}).get('version', '0.1.0'),
                'total_values': total_values
            })
            
            db_manager.close()
            
        except Exception:
            # Skip invalid databases
            continue
    
    return spaces
