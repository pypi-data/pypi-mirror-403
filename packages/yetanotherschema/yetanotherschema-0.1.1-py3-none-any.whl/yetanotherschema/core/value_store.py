"""
Value Store - Inner Sphere: Manages atomic values
"""

import json
from typing import Any, Dict, Optional, List
from datetime import datetime
import polars as pl

from yetanotherschema.exceptions import DatabaseError, ValidationError


class ValueStore:
    """Manages atomic values in the Inner Sphere"""
    
    def __init__(self, db_manager):
        """
        Initialize value store.
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager
        self.schema = db_manager.get_schema()
    
    def add_value(
        self,
        field: str,
        raw_value: Any,
        metadata: Dict[str, Any],
        user_id: str,
        reported_timestamp: Optional[str] = None
    ) -> int:
        """
        Add a value to the database.
        
        Args:
            field: Field name (e.g., 'height', 'weight')
            raw_value: The actual measurement/value
            metadata: Metadata dict (merged with schema metadata)
            user_id: User who created this value
            reported_timestamp: Optional user-reported timestamp (ISO format)
        
        Returns:
            value_id: Unique ID of created value
        """
        # Merge schema metadata with user metadata (schema first, user overrides)
        final_metadata = self._merge_metadata(field, metadata)
        
        # Convert raw_value to string for storage
        raw_value_str = str(raw_value)
        
        # Convert reported_timestamp to proper format
        reported_ts = None
        if reported_timestamp:
            try:
                reported_ts = datetime.fromisoformat(reported_timestamp)
            except ValueError:
                raise ValidationError(f"Invalid timestamp format: {reported_timestamp}")
        
        # Insert value
        try:
            # Get next value_id
            result = self.db.execute("SELECT nextval('seq_value_id')").fetchone()
            value_id = result[0]
            
            # Insert value
            self.db.execute(
                """
                INSERT INTO values 
                (value_id, field_name, raw_value, metadata, reported_timestamp, user_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    value_id,
                    field,
                    raw_value_str,
                    json.dumps(final_metadata),
                    reported_ts,
                    user_id
                ]
            )
            
            return value_id
            
        except Exception as e:
            raise DatabaseError(f"Failed to add value: {e}")
    
    def _merge_metadata(self, field: str, user_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge schema metadata with user metadata.
        User metadata wins on conflicts.
        
        Args:
            field: Field name
            user_metadata: User-provided metadata
        
        Returns:
            Merged metadata dict
        """
        # Start with schema metadata
        final_metadata = {}
        
        if 'values' in self.schema and field in self.schema['values']:
            final_metadata = dict(self.schema['values'][field])
        
        # Merge user metadata (user wins on conflicts)
        if user_metadata:
            final_metadata.update(user_metadata)
        
        return final_metadata
    
    def get_values(
        self,
        field: Optional[str] = None,
        value_ids: Optional[List[int]] = None,
        as_of: Optional[str] = None
    ) -> pl.DataFrame:
        """
        Get values as Polars DataFrame.
        
        Args:
            field: Optional field name filter
            value_ids: Optional list of value IDs to retrieve
            as_of: Optional timestamp for time-travel (ISO format)
        
        Returns:
            Polars DataFrame with columns:
                - value_id
                - field_name
                - raw_value
                - metadata (JSON string)
                - reported_timestamp
                - created_timestamp
                - user_id
        """
        try:
            # Build query
            query = "SELECT * FROM values WHERE 1=1"
            params = []
            
            if field:
                query += " AND field_name = ?"
                params.append(field)
            
            if value_ids:
                placeholders = ','.join(['?'] * len(value_ids))
                query += f" AND value_id IN ({placeholders})"
                params.extend(value_ids)
            
            if as_of:
                as_of_dt = datetime.fromisoformat(as_of)
                query += " AND created_timestamp <= ?"
                params.append(as_of_dt)
            
            # Execute query
            result = self.db.execute(query, params if params else None)
            
            # Convert to Polars DataFrame
            df = pl.from_arrow(result.fetch_arrow_table())
            
            return df
            
        except Exception as e:
            raise DatabaseError(f"Failed to get values: {e}")
    
    def get_latest_values(
        self,
        field: str,
        context_keys: List[str],
        as_of: Optional[str] = None
    ) -> pl.DataFrame:
        """
        Get latest values for each context.
        
        Args:
            field: Field name
            context_keys: List of context keys
            as_of: Optional timestamp for time-travel
        
        Returns:
            Polars DataFrame with latest values
        """
        try:
            # Build query to get latest value_id for each context
            query = """
                SELECT 
                    cr.context_key,
                    v.value_id,
                    v.field_name,
                    v.raw_value,
                    v.metadata,
                    v.reported_timestamp,
                    v.created_timestamp,
                    v.user_id
                FROM context_relationships cr
                JOIN values v ON cr.value_id = v.value_id
                WHERE cr.field_name = ?
                AND cr.context_key IN ({})
            """.format(','.join(['?'] * len(context_keys)))
            
            params = [field] + context_keys
            
            if as_of:
                as_of_dt = datetime.fromisoformat(as_of)
                query += " AND v.created_timestamp <= ?"
                params.append(as_of_dt)
            
            # Execute query
            result = self.db.execute(query, params)
            df = pl.from_arrow(result.fetch_arrow_table())
            
            # Get latest value for each context
            if not df.is_empty():
                df = df.sort('created_timestamp', descending=True)
                df = df.unique(subset=['context_key'], keep='first')
            
            return df
            
        except Exception as e:
            raise DatabaseError(f"Failed to get latest values: {e}")
