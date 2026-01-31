"""
Context Store - Middle Sphere: Manages context relationships
"""

from typing import Dict, List, Optional
from datetime import datetime
import polars as pl

from yetanotherschema.exceptions import DatabaseError, ValidationError


class ContextStore:
    """Manages context relationships in the Middle Sphere"""
    
    def __init__(self, db_manager):
        """
        Initialize context store.
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager
        self.schema = db_manager.get_schema()
    
    def add_relationship(
        self,
        contexts: Dict[str, str],
        field: str,
        value_id: int
    ):
        """
        Add context → value relationship.
        
        Args:
            contexts: Context dict (e.g., {'subject_id': 'S001', 'visit': 'V1'})
            field: Field name
            value_id: Value ID from value_store
        """
        # Validate required contexts
        self._validate_contexts(contexts)
        
        # Create context key
        context_key = self._create_context_key(contexts)
        
        try:
            # Get next relationship_id
            result = self.db.execute("SELECT nextval('seq_relationship_id')").fetchone()
            relationship_id = result[0]
            
            # Insert relationship
            self.db.execute(
                """
                INSERT INTO context_relationships 
                (relationship_id, context_key, field_name, value_id)
                VALUES (?, ?, ?, ?)
                """,
                [relationship_id, context_key, field, value_id]
            )
            
        except Exception as e:
            raise DatabaseError(f"Failed to add relationship: {e}")
    
    def _validate_contexts(self, contexts: Dict[str, str]):
        """Validate that required contexts are provided"""
        required_contexts = self.schema['contexts'].get('required', [])
        
        for req_context in required_contexts:
            if req_context not in contexts:
                raise ValidationError(f"Required context '{req_context}' missing")
    
    def _create_context_key(self, contexts: Dict[str, str]) -> str:
        """
        Create context key from context dict.
        Format: "key1=value1,key2=value2" (sorted by key)
        """
        sorted_items = sorted(contexts.items())
        return ','.join([f"{k}={v}" for k, v in sorted_items])
    
    def _parse_context_key(self, context_key: str) -> Dict[str, str]:
        """Parse context key back to dict"""
        contexts = {}
        for pair in context_key.split(','):
            k, v = pair.split('=')
            contexts[k] = v
        return contexts
    
    def get_value_ids(
        self,
        fields: List[str],
        context_filter: Optional[Dict[str, str]] = None,
        as_of: Optional[str] = None
    ) -> pl.DataFrame:
        """
        Get value IDs matching context filter.
        
        Args:
            fields: List of field names
            context_filter: Optional context filter (e.g., {'subject_id': 'S001'})
            as_of: Optional timestamp for time-travel
        
        Returns:
            Polars DataFrame with columns:
                - context_key
                - field_name
                - value_id
                - created_timestamp
        """
        try:
            # Build query
            query = """
                SELECT DISTINCT context_key, field_name, value_id, created_timestamp
                FROM context_relationships
                WHERE field_name IN ({})
            """.format(','.join(['?'] * len(fields)))
            
            params = fields.copy()
            
            # Add context filter
            if context_filter:
                for key, value in context_filter.items():
                    query += f" AND context_key LIKE ?"
                    params.append(f"%{key}={value}%")
            
            # Add time-travel filter
            if as_of:
                as_of_dt = datetime.fromisoformat(as_of)
                query += " AND created_timestamp <= ?"
                params.append(as_of_dt)
            
            # Execute query
            result = self.db.execute(query, params)
            df = pl.from_arrow(result.fetch_arrow_table())
            
            return df
            
        except Exception as e:
            raise DatabaseError(f"Failed to get value IDs: {e}")
    
    def get_unique_contexts(
        self,
        context_filter: Optional[Dict[str, str]] = None
    ) -> List[str]:
        """
        Get unique context keys.
        
        Args:
            context_filter: Optional context filter
        
        Returns:
            List of unique context keys
        """
        try:
            query = "SELECT DISTINCT context_key FROM context_relationships WHERE 1=1"
            params = []
            
            if context_filter:
                for key, value in context_filter.items():
                    query += f" AND context_key LIKE ?"
                    params.append(f"%{key}={value}%")
            
            result = self.db.execute(query, params if params else None)
            context_keys = [row[0] for row in result.fetchall()]
            
            return context_keys
            
        except Exception as e:
            raise DatabaseError(f"Failed to get unique contexts: {e}")
