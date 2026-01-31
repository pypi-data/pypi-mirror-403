"""
Query Engine - High-level query interface
"""

from typing import List, Dict, Optional, Any
import polars as pl
import json

from yetanotherschema.exceptions import DatabaseError, FieldNotFoundError


class QueryEngine:
    """High-level query interface combining value and context stores"""
    
    def __init__(self, value_store, context_store):
        """
        Initialize query engine.
        
        Args:
            value_store: ValueStore instance
            context_store: ContextStore instance
        """
        self.values = value_store
        self.contexts = context_store
        self.schema = value_store.schema
    
    def query(
        self,
        fields: List[str],
        context_filter: Optional[Dict[str, str]] = None,
        value_filters: Optional[Dict[str, Any]] = None,
        as_of: Optional[str] = None,
        include_metadata: bool = False
    ) -> pl.DataFrame:
        """
        Query values with context and value filters.
        
        Args:
            fields: List of fields to retrieve (contexts + values)
            context_filter: Optional context filter
            value_filters: Optional value filters (dict-based syntax)
            as_of: Optional timestamp for time-travel
            include_metadata: If True, include metadata column
        
        Returns:
            Polars DataFrame with requested fields
        """
        # Separate context fields from value fields
        context_fields, value_fields = self._separate_fields(fields)
        
        # Validate value fields exist in schema
        self._validate_fields(value_fields)
        
        # Get unique contexts matching filter
        context_keys = self.contexts.get_unique_contexts(context_filter)
        
        if not context_keys:
            # No matching contexts, return empty DataFrame
            return self._create_empty_dataframe(fields)
        
        # Get latest values for each field and context
        result_dfs = []
        
        for field in value_fields:
            df = self.values.get_latest_values(field, context_keys, as_of)
            
            if not df.is_empty():
                # Parse context_key into separate columns
                df = self._parse_context_keys(df)
                
                # Convert raw_value to appropriate type
                df = self._convert_raw_values(df, field)
                
                # Add field column
                df = df.with_columns(pl.lit(field).alias('field_name'))
                
                result_dfs.append(df)
        
        if not result_dfs:
            return self._create_empty_dataframe(fields)
        
        # Combine all field DataFrames
        combined_df = self._combine_field_dataframes(result_dfs, context_fields, value_fields)
        
        # Apply value filters
        if value_filters:
            combined_df = self._apply_value_filters(combined_df, value_filters)
        
        # Select requested columns
        select_cols = context_fields + value_fields
        if include_metadata:
            select_cols.append('metadata')
        
        # Ensure all columns exist
        for col in select_cols:
            if col not in combined_df.columns:
                combined_df = combined_df.with_columns(pl.lit(None).alias(col))
        
        result_df = combined_df.select(select_cols)
        
        return result_df
    
    def _separate_fields(self, fields: List[str]) -> tuple:
        """Separate context fields from value fields"""
        context_fields = []
        value_fields = []
        
        # Get all possible context names
        all_contexts = set()
        if 'contexts' in self.schema:
            all_contexts.update(self.schema['contexts'].get('required', []))
            all_contexts.update(self.schema['contexts'].get('optional', []))
        
        for field in fields:
            if field in all_contexts:
                context_fields.append(field)
            else:
                value_fields.append(field)
        
        return context_fields, value_fields
    
    def _validate_fields(self, value_fields: List[str]):
        """Validate that value fields exist in schema"""
        if 'values' not in self.schema:
            return
        
        schema_fields = set(self.schema['values'].keys())
        
        for field in value_fields:
            if field not in schema_fields:
                raise FieldNotFoundError(f"Field '{field}' not found in schema")
    
    def _parse_context_keys(self, df: pl.DataFrame) -> pl.DataFrame:
        """Parse context_key column into separate context columns"""
        if 'context_key' not in df.columns:
            return df
        
        # Extract context keys
        context_keys = df['context_key'].to_list()
        
        # Parse each context key
        context_dicts = []
        for key in context_keys:
            context_dict = {}
            for pair in key.split(','):
                k, v = pair.split('=')
                context_dict[k] = v
            context_dicts.append(context_dict)
        
        # Add context columns
        if context_dicts:
            all_keys = set()
            for d in context_dicts:
                all_keys.update(d.keys())
            
            for key in all_keys:
                values = [d.get(key) for d in context_dicts]
                df = df.with_columns(pl.Series(key, values))
        
        return df
    
    def _convert_raw_values(self, df: pl.DataFrame, field: str) -> pl.DataFrame:
        """Convert raw_value from string to appropriate type"""
        if 'raw_value' not in df.columns:
            return df
        
        # Get field type from schema
        field_type = 'string'  # default
        if 'values' in self.schema and field in self.schema['values']:
            field_type = self.schema['values'][field].get('type', 'string')
        
        # Convert based on type
        if field_type == 'numeric':
            df = df.with_columns(
                pl.col('raw_value').cast(pl.Float64, strict=False).alias(field)
            )
        else:
            df = df.with_columns(
                pl.col('raw_value').alias(field)
            )
        
        return df
    
    def _combine_field_dataframes(
        self,
        dfs: List[pl.DataFrame],
        context_fields: List[str],
        value_fields: List[str]
    ) -> pl.DataFrame:
        """Combine multiple field DataFrames into wide format"""
        if not dfs:
            return pl.DataFrame()
        
        # Extract field name from each DataFrame and prepare for joining
        prepared_dfs = []
        for df in dfs:
            # Get the field name (should be in the DataFrame)
            field_name = df['field_name'][0] if 'field_name' in df.columns and len(df) > 0 else None
            
            if field_name:
                # Select only context columns and the value column
                select_cols = [col for col in context_fields if col in df.columns]
                if field_name in df.columns:
                    select_cols.append(field_name)
                
                # Drop unnecessary columns
                df_clean = df.select(select_cols).unique()
                prepared_dfs.append(df_clean)
        
        if not prepared_dfs:
            return pl.DataFrame()
        
        # Start with first DataFrame
        result = prepared_dfs[0]
        
        # Join remaining DataFrames
        for df in prepared_dfs[1:]:
            # Find common context columns
            common_cols = [col for col in context_fields if col in result.columns and col in df.columns]
            
            if common_cols:
                result = result.join(df, on=common_cols, how='outer', suffix='_dup')
                # Remove duplicate columns
                for col in result.columns:
                    if col.endswith('_dup'):
                        result = result.drop(col)
            else:
                # No common columns, cross join
                result = result.join(df, how='cross')
        
        return result
    
    def _apply_value_filters(
        self,
        df: pl.DataFrame,
        filters: Dict[str, Any]
    ) -> pl.DataFrame:
        """Apply value filters to DataFrame"""
        for field, filter_spec in filters.items():
            if field not in df.columns:
                continue
            
            # Apply filter based on operator
            if isinstance(filter_spec, dict):
                for op, value in filter_spec.items():
                    if op == 'gt':
                        df = df.filter(pl.col(field) > value)
                    elif op == 'gte':
                        df = df.filter(pl.col(field) >= value)
                    elif op == 'lt':
                        df = df.filter(pl.col(field) < value)
                    elif op == 'lte':
                        df = df.filter(pl.col(field) <= value)
                    elif op == 'eq':
                        df = df.filter(pl.col(field) == value)
                    elif op == 'ne':
                        df = df.filter(pl.col(field) != value)
                    elif op == 'contains':
                        df = df.filter(pl.col(field).str.contains(value))
                    elif op == 'in':
                        df = df.filter(pl.col(field).is_in(value))
                    elif op == 'not_in':
                        df = df.filter(~pl.col(field).is_in(value))
        
        return df
    
    def _create_empty_dataframe(self, fields: List[str]) -> pl.DataFrame:
        """Create empty DataFrame with requested columns"""
        schema = {field: pl.Utf8 for field in fields}
        return pl.DataFrame(schema=schema)
