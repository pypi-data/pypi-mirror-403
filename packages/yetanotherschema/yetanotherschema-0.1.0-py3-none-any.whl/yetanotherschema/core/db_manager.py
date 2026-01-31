"""
Database Manager - Manages DuckDB connection and schema
"""

import duckdb
from pathlib import Path
from typing import Dict, Any, Optional
import toml
from datetime import datetime

from yetanotherschema.exceptions import (
    SpaceExistsError,
    SchemaValidationError,
    DatabaseError
)


class DatabaseManager:
    """Manages DuckDB connection and schema initialization"""
    
    def __init__(self, db_path: str, schema_path: Optional[str] = None, create_new: bool = False):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to DuckDB database file
            schema_path: Path to schema.toml (required for new databases)
            create_new: If True, create new database (error if exists)
        """
        self.db_path = Path(db_path)
        self.conn = None
        self.schema = None
        
        # Check if database exists
        db_exists = self.db_path.exists()
        
        if create_new and db_exists:
            raise SpaceExistsError(f"Database already exists: {db_path}")
        
        # Connect to database
        try:
            self.conn = duckdb.connect(str(self.db_path))
        except Exception as e:
            raise DatabaseError(f"Failed to connect to database: {e}")
        
        # Load or create schema
        if create_new:
            if not schema_path:
                raise SchemaValidationError("schema_path required for new database")
            self.schema = self._load_schema(schema_path)
            self._initialize_tables()
            self._store_schema()
        else:
            self.schema = self._load_stored_schema()
    
    def _load_schema(self, schema_path: str) -> Dict[str, Any]:
        """Load and validate schema from TOML file"""
        try:
            schema = toml.load(schema_path)
        except Exception as e:
            raise SchemaValidationError(f"Failed to load schema: {e}")
        
        # Validate required sections
        required_sections = ['metadata', 'contexts', 'values']
        for section in required_sections:
            if section not in schema:
                raise SchemaValidationError(f"Missing required section: {section}")
        
        # Validate contexts
        if 'required' not in schema['contexts']:
            raise SchemaValidationError("Schema must define at least one required context")
        
        if not schema['contexts']['required']:
            raise SchemaValidationError("At least one required context must be specified")
        
        return schema
    
    def _initialize_tables(self):
        """Create database tables"""
        try:
            # Table 1: values (Inner Sphere)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS values (
                    value_id INTEGER PRIMARY KEY,
                    field_name VARCHAR NOT NULL,
                    raw_value VARCHAR NOT NULL,
                    metadata JSON,
                    reported_timestamp TIMESTAMP,
                    created_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    user_id VARCHAR NOT NULL
                )
            """)
            
            # Indexes for values table
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_values_field ON values(field_name)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_values_created ON values(created_timestamp)")
            
            # Table 2: context_relationships (Middle Sphere)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS context_relationships (
                    relationship_id INTEGER PRIMARY KEY,
                    context_key VARCHAR NOT NULL,
                    field_name VARCHAR NOT NULL,
                    value_id INTEGER NOT NULL,
                    created_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (value_id) REFERENCES values(value_id)
                )
            """)
            
            # Indexes for context_relationships table
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_rel_context ON context_relationships(context_key)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_rel_field ON context_relationships(field_name)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_rel_value ON context_relationships(value_id)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_rel_composite ON context_relationships(context_key, field_name)")
            
            # Table 3: schema_metadata (Configuration)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_metadata (
                    key VARCHAR PRIMARY KEY,
                    value JSON NOT NULL,
                    updated_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sequences for auto-increment IDs
            self.conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_value_id START 1")
            self.conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_relationship_id START 1")
            
        except Exception as e:
            raise DatabaseError(f"Failed to initialize tables: {e}")
    
    def _store_schema(self):
        """Store schema in schema_metadata table"""
        try:
            import json
            
            # Store each section of schema
            for key in ['metadata', 'contexts', 'hierarchies', 'values']:
                if key in self.schema:
                    self.conn.execute(
                        "INSERT OR REPLACE INTO schema_metadata (key, value) VALUES (?, ?)",
                        [key, json.dumps(self.schema[key])]
                    )
            
            # Store creation timestamp
            self.conn.execute(
                "INSERT OR REPLACE INTO schema_metadata (key, value) VALUES (?, ?)",
                ['created_at', json.dumps(datetime.now().isoformat())]
            )
            
        except Exception as e:
            raise DatabaseError(f"Failed to store schema: {e}")
    
    def _load_stored_schema(self) -> Dict[str, Any]:
        """Load schema from schema_metadata table"""
        try:
            import json
            
            result = self.conn.execute(
                "SELECT key, value FROM schema_metadata"
            ).fetchall()
            
            schema = {}
            for key, value in result:
                schema[key] = json.loads(value)
            
            return schema
            
        except Exception as e:
            raise DatabaseError(f"Failed to load stored schema: {e}")
    
    def get_schema(self) -> Dict[str, Any]:
        """Get current schema"""
        return self.schema
    
    def execute(self, query: str, params: Optional[list] = None):
        """Execute SQL query"""
        try:
            if params:
                return self.conn.execute(query, params)
            else:
                return self.conn.execute(query)
        except Exception as e:
            raise DatabaseError(f"Query execution failed: {e}")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
