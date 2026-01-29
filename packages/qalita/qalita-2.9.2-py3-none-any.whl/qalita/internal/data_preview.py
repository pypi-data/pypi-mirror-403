"""
# QALITA (c) COPYRIGHT 2025 - ALL RIGHTS RESERVED -
Data Preview module for Studio integration.

This module provides data preview functionality for various source types,
used by the gRPC worker to respond to DataPreviewRequest from the platform.
"""

import base64
import json
import mimetypes
import os
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from qalita.internal.utils import logger


@dataclass
class DataPreviewResult:
    """Result of a data preview operation."""
    
    ok: bool
    data_type: str  # table, image, pdf, text, json, error
    error: Optional[str] = None
    
    # For table data
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    total_rows: Optional[int] = None
    
    # For text/json content
    content: Optional[str] = None
    
    # For binary content (image, pdf)
    binary_base64: Optional[str] = None
    mime_type: Optional[str] = None


# Maximum size for binary content (5MB base64 encoded)
MAX_BINARY_SIZE = 5 * 1024 * 1024
# Maximum content size for text/json (1MB)
MAX_TEXT_SIZE = 1 * 1024 * 1024
# Default row limit
DEFAULT_ROW_LIMIT = 1000


def _error_result(message: str) -> DataPreviewResult:
    """Create an error result."""
    return DataPreviewResult(ok=False, data_type="error", error=message)


def _dataframe_to_preview(
    df: pd.DataFrame,
    limit: int = DEFAULT_ROW_LIMIT,
    total_rows: Optional[int] = None,
) -> DataPreviewResult:
    """Convert a pandas DataFrame to a preview result."""
    try:
        # Get headers
        headers = [str(col) for col in df.columns.tolist()]
        
        # Limit rows
        df_limited = df.head(limit)
        
        # Convert all values to strings for transport
        rows = []
        for _, row in df_limited.iterrows():
            row_values = []
            for val in row:
                if pd.isna(val):
                    row_values.append("")
                else:
                    row_values.append(str(val))
            rows.append(row_values)
        
        return DataPreviewResult(
            ok=True,
            data_type="table",
            headers=headers,
            rows=rows,
            total_rows=total_rows if total_rows is not None else len(df),
        )
    except Exception as e:
        logger.error(f"Error converting DataFrame to preview: {e}")
        return _error_result(f"Failed to convert data: {str(e)}")


def preview_csv(
    file_path: str,
    limit: int = DEFAULT_ROW_LIMIT,
    encoding: str = "utf-8",
) -> DataPreviewResult:
    """Preview a CSV file."""
    try:
        if not os.path.exists(file_path):
            return _error_result(f"File not found: {file_path}")
        
        # Count total rows (without loading all data)
        total_rows = sum(1 for _ in open(file_path, encoding=encoding, errors="ignore")) - 1
        total_rows = max(0, total_rows)
        
        # Read only the needed rows
        df = pd.read_csv(
            file_path,
            nrows=limit,
            low_memory=False,
            encoding=encoding,
            on_bad_lines="warn",
        )
        
        return _dataframe_to_preview(df, limit, total_rows)
    except Exception as e:
        logger.error(f"Error previewing CSV file {file_path}: {e}")
        return _error_result(f"Failed to read CSV: {str(e)}")


def preview_excel(
    file_path: str,
    limit: int = DEFAULT_ROW_LIMIT,
    sheet_name: Optional[str] = None,
) -> DataPreviewResult:
    """Preview an Excel file."""
    try:
        if not os.path.exists(file_path):
            return _error_result(f"File not found: {file_path}")
        
        # Read the Excel file
        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name or 0,
            nrows=limit,
            engine="openpyxl",
        )
        
        # Get total rows - need to read without limit for count
        df_full = pd.read_excel(
            file_path,
            sheet_name=sheet_name or 0,
            engine="openpyxl",
            usecols=[0],  # Only read first column for counting
        )
        total_rows = len(df_full)
        
        return _dataframe_to_preview(df, limit, total_rows)
    except Exception as e:
        logger.error(f"Error previewing Excel file {file_path}: {e}")
        return _error_result(f"Failed to read Excel: {str(e)}")


def preview_parquet(
    file_path: str,
    limit: int = DEFAULT_ROW_LIMIT,
) -> DataPreviewResult:
    """Preview a Parquet file."""
    try:
        if not os.path.exists(file_path):
            return _error_result(f"File not found: {file_path}")
        
        # Read parquet with row limit
        df = pd.read_parquet(file_path)
        total_rows = len(df)
        
        return _dataframe_to_preview(df, limit, total_rows)
    except Exception as e:
        logger.error(f"Error previewing Parquet file {file_path}: {e}")
        return _error_result(f"Failed to read Parquet: {str(e)}")


def preview_json(file_path: str) -> DataPreviewResult:
    """Preview a JSON file."""
    try:
        if not os.path.exists(file_path):
            return _error_result(f"File not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        if file_size > MAX_TEXT_SIZE:
            # Read first part and indicate truncation
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read(MAX_TEXT_SIZE)
            content += "\n\n... [truncated - file too large] ..."
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        
        # Validate JSON and pretty print
        try:
            parsed = json.loads(content.split("... [truncated")[0] if "... [truncated" in content else content)
            content = json.dumps(parsed, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            pass  # Keep raw content if not valid JSON
        
        return DataPreviewResult(
            ok=True,
            data_type="json",
            content=content,
        )
    except Exception as e:
        logger.error(f"Error previewing JSON file {file_path}: {e}")
        return _error_result(f"Failed to read JSON: {str(e)}")


def preview_text(file_path: str) -> DataPreviewResult:
    """Preview a text file."""
    try:
        if not os.path.exists(file_path):
            return _error_result(f"File not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        if file_size > MAX_TEXT_SIZE:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(MAX_TEXT_SIZE)
            content += "\n\n... [truncated - file too large] ..."
        else:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        
        return DataPreviewResult(
            ok=True,
            data_type="text",
            content=content,
        )
    except Exception as e:
        logger.error(f"Error previewing text file {file_path}: {e}")
        return _error_result(f"Failed to read text file: {str(e)}")


def preview_image(file_path: str) -> DataPreviewResult:
    """Preview an image file (PNG, JPG, GIF, WebP)."""
    try:
        if not os.path.exists(file_path):
            return _error_result(f"File not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        if file_size > MAX_BINARY_SIZE:
            return _error_result(f"Image too large for preview ({file_size} bytes)")
        
        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            ext = os.path.splitext(file_path)[1].lower()
            mime_map = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }
            mime_type = mime_map.get(ext, "application/octet-stream")
        
        with open(file_path, "rb") as f:
            binary_data = f.read()
        
        binary_base64 = base64.b64encode(binary_data).decode("utf-8")
        
        return DataPreviewResult(
            ok=True,
            data_type="image",
            binary_base64=binary_base64,
            mime_type=mime_type,
        )
    except Exception as e:
        logger.error(f"Error previewing image file {file_path}: {e}")
        return _error_result(f"Failed to read image: {str(e)}")


def preview_pdf(file_path: str) -> DataPreviewResult:
    """Preview a PDF file."""
    try:
        if not os.path.exists(file_path):
            return _error_result(f"File not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        if file_size > MAX_BINARY_SIZE:
            return _error_result(f"PDF too large for preview ({file_size} bytes)")
        
        with open(file_path, "rb") as f:
            binary_data = f.read()
        
        binary_base64 = base64.b64encode(binary_data).decode("utf-8")
        
        return DataPreviewResult(
            ok=True,
            data_type="pdf",
            binary_base64=binary_base64,
            mime_type="application/pdf",
        )
    except Exception as e:
        logger.error(f"Error previewing PDF file {file_path}: {e}")
        return _error_result(f"Failed to read PDF: {str(e)}")


def preview_database(
    config: dict,
    limit: int = DEFAULT_ROW_LIMIT,
    query: Optional[str] = None,
    table: Optional[str] = None,
) -> DataPreviewResult:
    """Preview data from a database source."""
    try:
        from sqlalchemy import create_engine, text
        
        # Build connection string from config
        db_type = config.get("type", "").lower()
        
        connection_string = config.get("connection_string")
        if not connection_string:
            # Build connection string from components
            db_type_map = {
                "postgresql": "postgresql",
                "mysql": "mysql",
                "mssql": "mssql+pymssql",
                "oracle": "oracle+oracledb",
                "sqlite": "sqlite",
            }
            
            dialect = db_type_map.get(db_type)
            if not dialect:
                return _error_result(f"Unsupported database type: {db_type}")
            
            if db_type == "sqlite":
                database_path = config.get("database", ":memory:")
                connection_string = f"sqlite:///{database_path}"
            elif db_type == "oracle":
                connection_string = (
                    f"{dialect}://{config['username']}:{config['password']}"
                    f"@{config['host']}:{config['port']}/?service_name={config['database']}"
                )
            else:
                connection_string = (
                    f"{dialect}://{config['username']}:{config['password']}"
                    f"@{config['host']}:{config['port']}/{config['database']}"
                )
        
        engine = create_engine(connection_string)
        
        # Determine what to query
        if query:
            # Custom query provided
            sql = query
        elif table:
            # Specific table
            schema = config.get("schema")
            qualified_table = f"{schema}.{table}" if schema else table
            sql = f"SELECT * FROM {qualified_table}"
        else:
            return _error_result("No table or query specified for database preview")
        
        # Add LIMIT clause if not present
        sql_lower = sql.strip().lower()
        if "limit" not in sql_lower:
            sql = f"{sql.rstrip(';')} LIMIT {limit}"
        
        # Execute query
        with engine.connect() as conn:
            # Get total count (approximate)
            try:
                if table and not query:
                    schema = config.get("schema")
                    qualified_table = f"{schema}.{table}" if schema else table
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {qualified_table}"))
                    total_rows = count_result.scalar()
                else:
                    total_rows = None
            except Exception:
                total_rows = None
            
            # Get data
            df = pd.read_sql(sql, conn)
        
        return _dataframe_to_preview(df, limit, total_rows)
    except Exception as e:
        logger.error(f"Error previewing database: {e}")
        return _error_result(f"Failed to query database: {str(e)}")


def preview_s3(
    config: dict,
    limit: int = DEFAULT_ROW_LIMIT,
) -> DataPreviewResult:
    """Preview data from S3 source."""
    try:
        # Build path
        path = config.get("path")
        if not path:
            bucket = config.get("bucket")
            key = config.get("key")
            if bucket and key:
                path = f"s3://{bucket}/{key}"
        
        if not path:
            return _error_result("S3 path not configured")
        
        # Build storage options
        storage_options = {}
        for opt_key in ["key", "secret", "token", "client_kwargs"]:
            if opt_key in config:
                storage_options[opt_key] = config[opt_key]
        
        # Determine file type from path
        ext = os.path.splitext(path)[1].lower()
        
        if ext == ".csv":
            df = pd.read_csv(
                path,
                storage_options=storage_options or None,
                nrows=limit,
            )
            return _dataframe_to_preview(df, limit)
        elif ext == ".parquet":
            df = pd.read_parquet(path, storage_options=storage_options or None)
            total_rows = len(df)
            return _dataframe_to_preview(df.head(limit), limit, total_rows)
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(path, nrows=limit, engine="openpyxl")
            return _dataframe_to_preview(df, limit)
        elif ext == ".json":
            df = pd.read_json(path, storage_options=storage_options or None)
            return _dataframe_to_preview(df.head(limit), limit, len(df))
        else:
            return _error_result(f"Unsupported file type in S3: {ext}")
    except Exception as e:
        logger.error(f"Error previewing S3 source: {e}")
        return _error_result(f"Failed to read S3: {str(e)}")


def preview_source(
    source_config: dict,
    limit: int = DEFAULT_ROW_LIMIT,
    query: Optional[str] = None,
) -> DataPreviewResult:
    """
    Preview data from a source configuration.
    
    This is the main entry point for data preview.
    
    Args:
        source_config: Source configuration dict with 'type' and 'config' keys
        limit: Maximum number of rows to return
        query: Optional SQL query for database sources
    
    Returns:
        DataPreviewResult with the preview data
    """
    source_type = source_config.get("type", "").lower()
    config = source_config.get("config", {})
    
    logger.info(f"Previewing source type: {source_type}")
    
    # File-based sources
    if source_type in ("file", "csv"):
        path = config.get("path")
        if not path:
            return _error_result("File path not configured")
        return preview_csv(path, limit)
    
    elif source_type == "excel":
        path = config.get("path")
        if not path:
            return _error_result("Excel path not configured")
        return preview_excel(path, limit, config.get("sheet_name"))
    
    elif source_type == "parquet":
        path = config.get("path")
        if not path:
            return _error_result("Parquet path not configured")
        return preview_parquet(path, limit)
    
    elif source_type == "json":
        path = config.get("path")
        if not path:
            return _error_result("JSON path not configured")
        return preview_json(path)
    
    elif source_type == "text":
        path = config.get("path")
        if not path:
            return _error_result("Text file path not configured")
        return preview_text(path)
    
    elif source_type == "image":
        path = config.get("path")
        if not path:
            return _error_result("Image path not configured")
        return preview_image(path)
    
    elif source_type == "pdf":
        path = config.get("path")
        if not path:
            return _error_result("PDF path not configured")
        return preview_pdf(path)
    
    # Database sources
    elif source_type in ("postgresql", "mysql", "mssql", "oracle", "sqlite"):
        db_config = {**config, "type": source_type}
        table = config.get("table") or config.get("default_table")
        return preview_database(db_config, limit, query, table)
    
    # Cloud storage sources
    elif source_type == "s3":
        return preview_s3(config, limit)
    
    elif source_type in ("gcs", "azure_blob"):
        return _error_result(f"Preview for {source_type} not yet implemented")
    
    # Folder - try to preview first file
    elif source_type == "folder":
        path = config.get("path")
        if not path or not os.path.isdir(path):
            return _error_result("Folder path not configured or not accessible")
        
        # Find first data file
        for ext in ("*.csv", "*.xlsx", "*.parquet", "*.json"):
            import glob
            files = glob.glob(os.path.join(path, ext))
            if files:
                # Preview first file found
                file_ext = os.path.splitext(files[0])[1].lower()
                if file_ext == ".csv":
                    return preview_csv(files[0], limit)
                elif file_ext == ".xlsx":
                    return preview_excel(files[0], limit)
                elif file_ext == ".parquet":
                    return preview_parquet(files[0], limit)
                elif file_ext == ".json":
                    return preview_json(files[0])
        
        return _error_result("No supported data files found in folder")
    
    else:
        return _error_result(f"Unsupported source type: {source_type}")


def detect_preview_type(file_path: str) -> str:
    """
    Detect the type of preview based on file extension.
    
    Returns one of: csv, excel, parquet, json, text, image, pdf, unknown
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    ext_map = {
        ".csv": "csv",
        ".xlsx": "excel",
        ".xls": "excel",
        ".parquet": "parquet",
        ".pq": "parquet",
        ".json": "json",
        ".txt": "text",
        ".log": "text",
        ".md": "text",
        ".yml": "text",
        ".yaml": "text",
        ".xml": "text",
        ".png": "image",
        ".jpg": "image",
        ".jpeg": "image",
        ".gif": "image",
        ".webp": "image",
        ".pdf": "pdf",
    }
    
    return ext_map.get(ext, "unknown")
