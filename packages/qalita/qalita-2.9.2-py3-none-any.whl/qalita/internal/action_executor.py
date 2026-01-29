"""
# QALITA (c) COPYRIGHT 2025 - ALL RIGHTS RESERVED -
Action Executor module for Studio Agent integration.

This module provides an abstraction layer that translates LLM agent commands
into concrete operations on data sources (SQL queries, file manipulations, etc.).
"""

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from qalita.internal.utils import logger
from qalita.internal.data_preview import (
    DataPreviewResult,
    _dataframe_to_preview,
    _error_result,
    DEFAULT_ROW_LIMIT,
)


@dataclass
class ActionResult:
    """Result of an action execution."""
    
    ok: bool
    action_type: str
    error: Optional[str] = None
    result_json: Optional[str] = None  # Structured result as JSON string
    data: Optional[DataPreviewResult] = None  # Tabular data if applicable
    execution_time_ms: int = 0


# Supported action types
ACTION_TYPES = {
    "query": "Execute a SQL query on a database source",
    "read_data": "Read data from a file or database source",
    "filter": "Filter data based on conditions",
    "aggregate": "Perform aggregation on data",
    "describe": "Get metadata about a source (schema, columns, row count)",
    "sample": "Get a random sample of data",
    "count": "Count rows in a source or query result",
    "distinct": "Get distinct values from a column",
    "head": "Get first N rows from a source",
    "tail": "Get last N rows from a source",
}


class ActionExecutor:
    """
    Executes actions requested by the LLM agent.
    
    This class provides a unified interface for executing various data operations
    on different source types (databases, files, etc.).
    """
    
    def __init__(self):
        """Initialize the action executor."""
        self._engines: Dict[int, Any] = {}  # Cache for database engines
    
    def execute(
        self,
        action_type: str,
        source_config: dict,
        params: dict,
        timeout_seconds: Optional[int] = None,
    ) -> ActionResult:
        """
        Execute an action on a data source.
        
        Args:
            action_type: Type of action to execute (query, read_data, etc.)
            source_config: Source configuration dict with 'type' and 'config' keys
            params: Action parameters (specific to each action type)
            timeout_seconds: Optional timeout for the action
        
        Returns:
            ActionResult with the execution result
        """
        start_time = time.time()
        
        if action_type not in ACTION_TYPES:
            return ActionResult(
                ok=False,
                action_type=action_type,
                error=f"Unknown action type: {action_type}. Supported: {list(ACTION_TYPES.keys())}",
            )
        
        handlers = {
            "query": self._execute_query,
            "read_data": self._read_data,
            "filter": self._filter_data,
            "aggregate": self._aggregate_data,
            "describe": self._describe_source,
            "sample": self._sample_data,
            "count": self._count_rows,
            "distinct": self._get_distinct,
            "head": self._get_head,
            "tail": self._get_tail,
        }
        
        handler = handlers.get(action_type)
        if not handler:
            return ActionResult(
                ok=False,
                action_type=action_type,
                error=f"Handler not implemented for action: {action_type}",
            )
        
        try:
            result = handler(source_config, params)
            result.execution_time_ms = int((time.time() - start_time) * 1000)
            return result
        except Exception as e:
            logger.error(f"Error executing action {action_type}: {e}")
            return ActionResult(
                ok=False,
                action_type=action_type,
                error=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
    
    def _get_database_engine(self, source_config: dict) -> Any:
        """Get or create a SQLAlchemy engine for a database source."""
        from sqlalchemy import create_engine
        
        config = source_config.get("config", {})
        source_type = source_config.get("type", "").lower()
        
        connection_string = config.get("connection_string")
        if not connection_string:
            db_type_map = {
                "postgresql": "postgresql",
                "mysql": "mysql",
                "mssql": "mssql+pymssql",
                "oracle": "oracle+oracledb",
                "sqlite": "sqlite",
            }
            
            dialect = db_type_map.get(source_type)
            if not dialect:
                raise ValueError(f"Unsupported database type: {source_type}")
            
            if source_type == "sqlite":
                database_path = config.get("database", ":memory:")
                connection_string = f"sqlite:///{database_path}"
            elif source_type == "oracle":
                connection_string = (
                    f"{dialect}://{config['username']}:{config['password']}"
                    f"@{config['host']}:{config['port']}/?service_name={config['database']}"
                )
            else:
                connection_string = (
                    f"{dialect}://{config['username']}:{config['password']}"
                    f"@{config['host']}:{config['port']}/{config['database']}"
                )
        
        return create_engine(connection_string)
    
    def _is_database_source(self, source_config: dict) -> bool:
        """Check if the source is a database."""
        source_type = source_config.get("type", "").lower()
        return source_type in ("postgresql", "mysql", "mssql", "oracle", "sqlite")
    
    def _is_file_source(self, source_config: dict) -> bool:
        """Check if the source is a file."""
        source_type = source_config.get("type", "").lower()
        return source_type in ("file", "csv", "excel", "parquet", "json", "folder")
    
    def _execute_query(self, source_config: dict, params: dict) -> ActionResult:
        """Execute a SQL query on a database source."""
        if not self._is_database_source(source_config):
            return ActionResult(
                ok=False,
                action_type="query",
                error=f"Query action only supported for database sources, not {source_config.get('type')}",
            )
        
        sql = params.get("sql")
        if not sql:
            return ActionResult(
                ok=False,
                action_type="query",
                error="SQL query is required for 'query' action",
            )
        
        limit = params.get("limit", DEFAULT_ROW_LIMIT)
        
        # Add LIMIT if not present (for safety)
        sql_lower = sql.strip().lower()
        if "limit" not in sql_lower and not sql_lower.startswith(("insert", "update", "delete", "create", "drop", "alter")):
            sql = f"{sql.rstrip(';')} LIMIT {limit}"
        
        try:
            engine = self._get_database_engine(source_config)
            with engine.connect() as conn:
                df = pd.read_sql(sql, conn)
            
            preview = _dataframe_to_preview(df, limit)
            return ActionResult(
                ok=True,
                action_type="query",
                data=preview,
                result_json=json.dumps({"rows_returned": len(df), "columns": list(df.columns)}),
            )
        except Exception as e:
            return ActionResult(
                ok=False,
                action_type="query",
                error=f"Query execution failed: {str(e)}",
            )
    
    def _read_data(self, source_config: dict, params: dict) -> ActionResult:
        """Read data from a source."""
        limit = params.get("limit", DEFAULT_ROW_LIMIT)
        columns = params.get("columns")  # Optional list of columns to select
        
        if self._is_database_source(source_config):
            config = source_config.get("config", {})
            table = params.get("table") or config.get("table") or config.get("default_table")
            if not table:
                return ActionResult(
                    ok=False,
                    action_type="read_data",
                    error="Table name is required for database sources",
                )
            
            schema = config.get("schema")
            qualified_table = f"{schema}.{table}" if schema else table
            
            cols = ", ".join(columns) if columns else "*"
            sql = f"SELECT {cols} FROM {qualified_table} LIMIT {limit}"
            
            try:
                engine = self._get_database_engine(source_config)
                with engine.connect() as conn:
                    df = pd.read_sql(sql, conn)
                
                preview = _dataframe_to_preview(df, limit)
                return ActionResult(
                    ok=True,
                    action_type="read_data",
                    data=preview,
                    result_json=json.dumps({"rows_returned": len(df), "columns": list(df.columns)}),
                )
            except Exception as e:
                return ActionResult(
                    ok=False,
                    action_type="read_data",
                    error=f"Failed to read data: {str(e)}",
                )
        
        elif self._is_file_source(source_config):
            return self._read_file_data(source_config, params)
        
        else:
            return ActionResult(
                ok=False,
                action_type="read_data",
                error=f"Unsupported source type: {source_config.get('type')}",
            )
    
    def _read_file_data(self, source_config: dict, params: dict) -> ActionResult:
        """Read data from a file source."""
        import os
        
        config = source_config.get("config", {})
        source_type = source_config.get("type", "").lower()
        path = config.get("path")
        
        if not path:
            return ActionResult(
                ok=False,
                action_type="read_data",
                error="File path not configured",
            )
        
        if not os.path.exists(path):
            return ActionResult(
                ok=False,
                action_type="read_data",
                error=f"File not found: {path}",
            )
        
        limit = params.get("limit", DEFAULT_ROW_LIMIT)
        columns = params.get("columns")
        
        try:
            if source_type in ("csv", "file") and path.endswith(".csv"):
                usecols = columns if columns else None
                df = pd.read_csv(path, nrows=limit, usecols=usecols, low_memory=False)
            elif source_type == "excel" or path.endswith((".xlsx", ".xls")):
                usecols = columns if columns else None
                df = pd.read_excel(path, nrows=limit, usecols=usecols, engine="openpyxl")
            elif source_type == "parquet" or path.endswith(".parquet"):
                df = pd.read_parquet(path, columns=columns)
                df = df.head(limit)
            elif source_type == "json" or path.endswith(".json"):
                df = pd.read_json(path)
                if columns:
                    df = df[columns]
                df = df.head(limit)
            else:
                return ActionResult(
                    ok=False,
                    action_type="read_data",
                    error=f"Unsupported file type: {source_type}",
                )
            
            preview = _dataframe_to_preview(df, limit)
            return ActionResult(
                ok=True,
                action_type="read_data",
                data=preview,
                result_json=json.dumps({"rows_returned": len(df), "columns": list(df.columns)}),
            )
        except Exception as e:
            return ActionResult(
                ok=False,
                action_type="read_data",
                error=f"Failed to read file: {str(e)}",
            )
    
    def _filter_data(self, source_config: dict, params: dict) -> ActionResult:
        """Filter data based on a condition."""
        condition = params.get("condition")
        if not condition:
            return ActionResult(
                ok=False,
                action_type="filter",
                error="Filter condition is required",
            )
        
        limit = params.get("limit", DEFAULT_ROW_LIMIT)
        
        if self._is_database_source(source_config):
            config = source_config.get("config", {})
            table = params.get("table") or config.get("table") or config.get("default_table")
            if not table:
                return ActionResult(
                    ok=False,
                    action_type="filter",
                    error="Table name is required for database sources",
                )
            
            schema = config.get("schema")
            qualified_table = f"{schema}.{table}" if schema else table
            columns = params.get("columns")
            cols = ", ".join(columns) if columns else "*"
            
            sql = f"SELECT {cols} FROM {qualified_table} WHERE {condition} LIMIT {limit}"
            
            try:
                engine = self._get_database_engine(source_config)
                with engine.connect() as conn:
                    df = pd.read_sql(sql, conn)
                
                preview = _dataframe_to_preview(df, limit)
                return ActionResult(
                    ok=True,
                    action_type="filter",
                    data=preview,
                    result_json=json.dumps({"rows_returned": len(df), "condition": condition}),
                )
            except Exception as e:
                return ActionResult(
                    ok=False,
                    action_type="filter",
                    error=f"Filter failed: {str(e)}",
                )
        
        elif self._is_file_source(source_config):
            # First read the data
            read_result = self._read_file_data(source_config, {"limit": 10000})  # Read more for filtering
            if not read_result.ok or not read_result.data:
                return ActionResult(
                    ok=False,
                    action_type="filter",
                    error=read_result.error or "Failed to read data for filtering",
                )
            
            # Reconstruct dataframe and filter
            try:
                df = pd.DataFrame(
                    [row for row in read_result.data.rows],
                    columns=read_result.data.headers
                )
                # Use query for filtering
                df_filtered = df.query(condition)
                df_filtered = df_filtered.head(limit)
                
                preview = _dataframe_to_preview(df_filtered, limit)
                return ActionResult(
                    ok=True,
                    action_type="filter",
                    data=preview,
                    result_json=json.dumps({"rows_returned": len(df_filtered), "condition": condition}),
                )
            except Exception as e:
                return ActionResult(
                    ok=False,
                    action_type="filter",
                    error=f"Filter failed: {str(e)}",
                )
        
        else:
            return ActionResult(
                ok=False,
                action_type="filter",
                error=f"Unsupported source type: {source_config.get('type')}",
            )
    
    def _aggregate_data(self, source_config: dict, params: dict) -> ActionResult:
        """Perform aggregation on data."""
        group_by = params.get("group_by")  # Column(s) to group by
        agg_func = params.get("agg_func", "count")  # Aggregation function
        agg_column = params.get("agg_column")  # Column to aggregate
        
        if not group_by:
            return ActionResult(
                ok=False,
                action_type="aggregate",
                error="group_by column is required for aggregation",
            )
        
        limit = params.get("limit", DEFAULT_ROW_LIMIT)
        
        if self._is_database_source(source_config):
            config = source_config.get("config", {})
            table = params.get("table") or config.get("table") or config.get("default_table")
            if not table:
                return ActionResult(
                    ok=False,
                    action_type="aggregate",
                    error="Table name is required for database sources",
                )
            
            schema = config.get("schema")
            qualified_table = f"{schema}.{table}" if schema else table
            
            # Build SQL aggregation
            group_cols = group_by if isinstance(group_by, list) else [group_by]
            group_str = ", ".join(group_cols)
            
            if agg_func.upper() == "COUNT":
                agg_expr = "COUNT(*) as count"
            elif agg_column:
                agg_expr = f"{agg_func.upper()}({agg_column}) as {agg_func.lower()}_{agg_column}"
            else:
                agg_expr = "COUNT(*) as count"
            
            sql = f"SELECT {group_str}, {agg_expr} FROM {qualified_table} GROUP BY {group_str} LIMIT {limit}"
            
            try:
                engine = self._get_database_engine(source_config)
                with engine.connect() as conn:
                    df = pd.read_sql(sql, conn)
                
                preview = _dataframe_to_preview(df, limit)
                return ActionResult(
                    ok=True,
                    action_type="aggregate",
                    data=preview,
                    result_json=json.dumps({
                        "groups": len(df),
                        "group_by": group_by,
                        "agg_func": agg_func,
                    }),
                )
            except Exception as e:
                return ActionResult(
                    ok=False,
                    action_type="aggregate",
                    error=f"Aggregation failed: {str(e)}",
                )
        
        else:
            return ActionResult(
                ok=False,
                action_type="aggregate",
                error="Aggregation currently only supported for database sources",
            )
    
    def _describe_source(self, source_config: dict, params: dict) -> ActionResult:
        """Get metadata about a source."""
        source_type = source_config.get("type", "").lower()
        config = source_config.get("config", {})
        
        metadata = {
            "source_type": source_type,
            "name": source_config.get("name", "unknown"),
        }
        
        if self._is_database_source(source_config):
            try:
                from sqlalchemy import inspect
                
                engine = self._get_database_engine(source_config)
                inspector = inspect(engine)
                
                # Get schema info
                schema = config.get("schema")
                tables = inspector.get_table_names(schema=schema)
                
                metadata["tables"] = tables
                metadata["schema"] = schema
                
                # Get column info for specified table or first table
                table = params.get("table") or config.get("table") or (tables[0] if tables else None)
                if table:
                    columns = inspector.get_columns(table, schema=schema)
                    metadata["table"] = table
                    metadata["columns"] = [
                        {"name": col["name"], "type": str(col["type"])}
                        for col in columns
                    ]
                    
                    # Get row count
                    with engine.connect() as conn:
                        from sqlalchemy import text
                        qualified_table = f"{schema}.{table}" if schema else table
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {qualified_table}"))
                        metadata["row_count"] = result.scalar()
                
                return ActionResult(
                    ok=True,
                    action_type="describe",
                    result_json=json.dumps(metadata),
                )
            except Exception as e:
                return ActionResult(
                    ok=False,
                    action_type="describe",
                    error=f"Failed to describe database source: {str(e)}",
                )
        
        elif self._is_file_source(source_config):
            import os
            
            path = config.get("path")
            if not path:
                return ActionResult(
                    ok=False,
                    action_type="describe",
                    error="File path not configured",
                )
            
            if not os.path.exists(path):
                return ActionResult(
                    ok=False,
                    action_type="describe",
                    error=f"File not found: {path}",
                )
            
            metadata["path"] = path
            metadata["file_size_bytes"] = os.path.getsize(path)
            
            try:
                # Read a small sample to get column info
                if source_type in ("csv", "file") and path.endswith(".csv"):
                    df = pd.read_csv(path, nrows=5, low_memory=False)
                elif source_type == "excel" or path.endswith((".xlsx", ".xls")):
                    df = pd.read_excel(path, nrows=5, engine="openpyxl")
                elif source_type == "parquet" or path.endswith(".parquet"):
                    df = pd.read_parquet(path)
                    df = df.head(5)
                elif source_type == "json" or path.endswith(".json"):
                    df = pd.read_json(path)
                    df = df.head(5)
                else:
                    df = None
                
                if df is not None:
                    metadata["columns"] = [
                        {"name": col, "type": str(df[col].dtype)}
                        for col in df.columns
                    ]
                    # Try to get total row count
                    if source_type in ("csv", "file") and path.endswith(".csv"):
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            metadata["row_count"] = sum(1 for _ in f) - 1  # Exclude header
                    elif source_type == "parquet" or path.endswith(".parquet"):
                        metadata["row_count"] = len(pd.read_parquet(path))
                
                return ActionResult(
                    ok=True,
                    action_type="describe",
                    result_json=json.dumps(metadata),
                )
            except Exception as e:
                return ActionResult(
                    ok=False,
                    action_type="describe",
                    error=f"Failed to describe file source: {str(e)}",
                )
        
        else:
            return ActionResult(
                ok=False,
                action_type="describe",
                error=f"Describe not supported for source type: {source_type}",
            )
    
    def _sample_data(self, source_config: dict, params: dict) -> ActionResult:
        """Get a random sample of data."""
        n = params.get("n", 10)  # Number of samples
        
        if self._is_database_source(source_config):
            config = source_config.get("config", {})
            table = params.get("table") or config.get("table") or config.get("default_table")
            if not table:
                return ActionResult(
                    ok=False,
                    action_type="sample",
                    error="Table name is required",
                )
            
            schema = config.get("schema")
            qualified_table = f"{schema}.{table}" if schema else table
            source_type = source_config.get("type", "").lower()
            
            # Different databases have different random sampling syntax
            if source_type == "postgresql":
                sql = f"SELECT * FROM {qualified_table} ORDER BY RANDOM() LIMIT {n}"
            elif source_type == "mysql":
                sql = f"SELECT * FROM {qualified_table} ORDER BY RAND() LIMIT {n}"
            else:
                sql = f"SELECT * FROM {qualified_table} LIMIT {n}"  # Fallback
            
            try:
                engine = self._get_database_engine(source_config)
                with engine.connect() as conn:
                    df = pd.read_sql(sql, conn)
                
                preview = _dataframe_to_preview(df, n)
                return ActionResult(
                    ok=True,
                    action_type="sample",
                    data=preview,
                    result_json=json.dumps({"samples": len(df)}),
                )
            except Exception as e:
                return ActionResult(
                    ok=False,
                    action_type="sample",
                    error=f"Sampling failed: {str(e)}",
                )
        
        elif self._is_file_source(source_config):
            # Read all data and sample
            read_result = self._read_file_data(source_config, {"limit": 10000})
            if not read_result.ok or not read_result.data:
                return ActionResult(
                    ok=False,
                    action_type="sample",
                    error=read_result.error or "Failed to read data for sampling",
                )
            
            try:
                df = pd.DataFrame(
                    [row for row in read_result.data.rows],
                    columns=read_result.data.headers
                )
                df_sample = df.sample(n=min(n, len(df)))
                
                preview = _dataframe_to_preview(df_sample, n)
                return ActionResult(
                    ok=True,
                    action_type="sample",
                    data=preview,
                    result_json=json.dumps({"samples": len(df_sample)}),
                )
            except Exception as e:
                return ActionResult(
                    ok=False,
                    action_type="sample",
                    error=f"Sampling failed: {str(e)}",
                )
        
        else:
            return ActionResult(
                ok=False,
                action_type="sample",
                error=f"Sampling not supported for source type: {source_config.get('type')}",
            )
    
    def _count_rows(self, source_config: dict, params: dict) -> ActionResult:
        """Count rows in a source."""
        if self._is_database_source(source_config):
            config = source_config.get("config", {})
            table = params.get("table") or config.get("table") or config.get("default_table")
            condition = params.get("condition")
            
            if not table:
                return ActionResult(
                    ok=False,
                    action_type="count",
                    error="Table name is required",
                )
            
            schema = config.get("schema")
            qualified_table = f"{schema}.{table}" if schema else table
            
            sql = f"SELECT COUNT(*) as count FROM {qualified_table}"
            if condition:
                sql += f" WHERE {condition}"
            
            try:
                engine = self._get_database_engine(source_config)
                with engine.connect() as conn:
                    from sqlalchemy import text
                    result = conn.execute(text(sql))
                    count = result.scalar()
                
                return ActionResult(
                    ok=True,
                    action_type="count",
                    result_json=json.dumps({"count": count, "table": table}),
                )
            except Exception as e:
                return ActionResult(
                    ok=False,
                    action_type="count",
                    error=f"Count failed: {str(e)}",
                )
        
        else:
            # Use describe for file sources
            describe_result = self._describe_source(source_config, params)
            if describe_result.ok and describe_result.result_json:
                metadata = json.loads(describe_result.result_json)
                if "row_count" in metadata:
                    return ActionResult(
                        ok=True,
                        action_type="count",
                        result_json=json.dumps({"count": metadata["row_count"]}),
                    )
            
            return ActionResult(
                ok=False,
                action_type="count",
                error="Could not determine row count",
            )
    
    def _get_distinct(self, source_config: dict, params: dict) -> ActionResult:
        """Get distinct values from a column."""
        column = params.get("column")
        if not column:
            return ActionResult(
                ok=False,
                action_type="distinct",
                error="Column name is required for distinct action",
            )
        
        limit = params.get("limit", 100)
        
        if self._is_database_source(source_config):
            config = source_config.get("config", {})
            table = params.get("table") or config.get("table") or config.get("default_table")
            
            if not table:
                return ActionResult(
                    ok=False,
                    action_type="distinct",
                    error="Table name is required",
                )
            
            schema = config.get("schema")
            qualified_table = f"{schema}.{table}" if schema else table
            
            sql = f"SELECT DISTINCT {column} FROM {qualified_table} LIMIT {limit}"
            
            try:
                engine = self._get_database_engine(source_config)
                with engine.connect() as conn:
                    df = pd.read_sql(sql, conn)
                
                values = df[column].tolist()
                return ActionResult(
                    ok=True,
                    action_type="distinct",
                    result_json=json.dumps({
                        "column": column,
                        "distinct_count": len(values),
                        "values": values[:limit],
                    }),
                )
            except Exception as e:
                return ActionResult(
                    ok=False,
                    action_type="distinct",
                    error=f"Distinct failed: {str(e)}",
                )
        
        else:
            return ActionResult(
                ok=False,
                action_type="distinct",
                error="Distinct currently only supported for database sources",
            )
    
    def _get_head(self, source_config: dict, params: dict) -> ActionResult:
        """Get first N rows from a source."""
        n = params.get("n", 10)
        params["limit"] = n
        return self._read_data(source_config, params)
    
    def _get_tail(self, source_config: dict, params: dict) -> ActionResult:
        """Get last N rows from a source."""
        n = params.get("n", 10)
        
        if self._is_database_source(source_config):
            config = source_config.get("config", {})
            table = params.get("table") or config.get("table") or config.get("default_table")
            
            if not table:
                return ActionResult(
                    ok=False,
                    action_type="tail",
                    error="Table name is required",
                )
            
            schema = config.get("schema")
            qualified_table = f"{schema}.{table}" if schema else table
            
            # This requires knowing the order - use a subquery with DESC ordering
            sql = f"""
                SELECT * FROM (
                    SELECT * FROM {qualified_table} ORDER BY 1 DESC LIMIT {n}
                ) sub ORDER BY 1 ASC
            """
            
            try:
                engine = self._get_database_engine(source_config)
                with engine.connect() as conn:
                    df = pd.read_sql(sql, conn)
                
                preview = _dataframe_to_preview(df, n)
                return ActionResult(
                    ok=True,
                    action_type="tail",
                    data=preview,
                    result_json=json.dumps({"rows_returned": len(df)}),
                )
            except Exception as e:
                return ActionResult(
                    ok=False,
                    action_type="tail",
                    error=f"Tail failed: {str(e)}",
                )
        
        else:
            # For files, read all and take tail
            read_result = self._read_file_data(source_config, {"limit": 10000})
            if not read_result.ok or not read_result.data:
                return ActionResult(
                    ok=False,
                    action_type="tail",
                    error=read_result.error or "Failed to read data",
                )
            
            try:
                df = pd.DataFrame(
                    [row for row in read_result.data.rows],
                    columns=read_result.data.headers
                )
                df_tail = df.tail(n)
                
                preview = _dataframe_to_preview(df_tail, n)
                return ActionResult(
                    ok=True,
                    action_type="tail",
                    data=preview,
                    result_json=json.dumps({"rows_returned": len(df_tail)}),
                )
            except Exception as e:
                return ActionResult(
                    ok=False,
                    action_type="tail",
                    error=f"Tail failed: {str(e)}",
                )


# Singleton instance
_executor: Optional[ActionExecutor] = None


def get_action_executor() -> ActionExecutor:
    """Get the singleton ActionExecutor instance."""
    global _executor
    if _executor is None:
        _executor = ActionExecutor()
    return _executor
