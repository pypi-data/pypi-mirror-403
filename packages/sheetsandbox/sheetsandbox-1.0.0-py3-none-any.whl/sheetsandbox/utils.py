"""
Utility functions for SheetSandbox SDK
"""

from typing import Any, Dict, List, Optional, Union


def format_success_response(data: Any) -> Dict[str, Any]:
    """
    Format successful API response
    
    Args:
        data: Response data from API
        
    Returns:
        Formatted response dictionary
    """
    if isinstance(data, dict):
        return {
            "success": True,
            "data": data.get("data", data),
            "status": data.get("status", "success"),
            **({k: v for k, v in data.items() if k == "share_feedback"})
        }
    return {
        "success": True,
        "data": data,
        "status": "success"
    }


def format_error_response(error: Exception, status_code: Optional[int] = None, 
                         details: Optional[Any] = None) -> Dict[str, Any]:
    """
    Format error response
    
    Args:
        error: Error exception
        status_code: HTTP status code (optional)
        details: Additional error details (optional)
        
    Returns:
        Formatted error response dictionary
    """
    response = {
        "success": False,
        "error": str(error) or "An unknown error occurred",
        "status": "error"
    }
    
    if status_code:
        response["statusCode"] = status_code
    
    if details:
        response["details"] = details
    
    return response


def validate_table_name(table_name: str) -> None:
    """
    Validate table name
    
    Args:
        table_name: Name of the table/sheet
        
    Raises:
        ValueError: If table name is invalid
    """
    if not table_name or not isinstance(table_name, str):
        raise ValueError("Table name must be a non-empty string")
    
    if not table_name.strip():
        raise ValueError("Table name cannot be empty or whitespace")


def validate_id(record_id: Union[int, str]) -> None:
    """
    Validate ID parameter
    
    Args:
        record_id: Record ID
        
    Raises:
        ValueError: If ID is invalid
    """
    try:
        num_id = int(record_id)
        if num_id <= 0:
            raise ValueError("ID must be a positive number")
    except (ValueError, TypeError):
        raise ValueError("ID must be a positive number")


def validate_data(data: Union[Dict, List[Dict]]) -> None:
    """
    Validate data object for create/update operations
    
    Args:
        data: Data to validate
        
    Raises:
        ValueError: If data is invalid
    """
    if data is None:
        raise ValueError("Data cannot be None")
    
    if isinstance(data, list):
        if len(data) == 0:
            raise ValueError("Data array cannot be empty")
        
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                raise ValueError(f"Item at index {index} must be a dictionary")
            if len(item) == 0:
                raise ValueError(f"Item at index {index} cannot be an empty dictionary")
    
    elif isinstance(data, dict):
        if len(data) == 0:
            raise ValueError("Data dictionary cannot be empty")
    
    else:
        raise ValueError("Data must be a dictionary or list of dictionaries")


def validate_token(token: str) -> None:
    """
    Validate token
    
    Args:
        token: API token
        
    Raises:
        ValueError: If token is invalid
    """
    if not token or not isinstance(token, str):
        raise ValueError("Token must be a non-empty string")
    
    if not token.strip():
        raise ValueError("Token cannot be empty or whitespace")


def build_url(base_url: str, path: str) -> str:
    """
    Build full URL from base URL and path
    
    Args:
        base_url: Base API URL
        path: API path
        
    Returns:
        Full URL
    """
    base = base_url.rstrip('/')
    endpoint = path if path.startswith('/') else f'/{path}'
    return f"{base}{endpoint}"


def check_duplicates(existing_records: List[Dict], new_data: Union[Dict, List[Dict]], 
                    unique_fields: List[str]) -> Dict[str, Any]:
    """
    Check for duplicate records based on unique fields
    
    Args:
        existing_records: Existing records in the sheet
        new_data: New data to check
        unique_fields: Fields that should be unique
        
    Returns:
        Dictionary with hasDuplicates boolean and duplicates list
    """
    duplicates = []
    new_data_array = new_data if isinstance(new_data, list) else [new_data]
    
    for index, new_record in enumerate(new_data_array):
        record_prefix = f"Record {index + 1}" if isinstance(new_data, list) else "Record"
        
        # Check individual field uniqueness
        for field in unique_fields:
            if field in new_record:
                value = new_record[field]
                existing = next((r for r in existing_records if r.get(field) == value), None)
                
                if existing:
                    duplicates.append({
                        "record": record_prefix,
                        "field": field,
                        "value": value,
                        "message": f"{record_prefix}: Duplicate value '{value}' found for field '{field}'"
                    })
        
        # Check composite uniqueness
        if len(unique_fields) > 1:
            composite_key = "|".join(str(new_record.get(f, "")) for f in unique_fields)
            existing_composite = next(
                (r for r in existing_records 
                 if "|".join(str(r.get(f, "")) for f in unique_fields) == composite_key),
                None
            )
            
            if existing_composite:
                duplicates.append({
                    "record": record_prefix,
                    "fields": unique_fields,
                    "message": f"{record_prefix}: Duplicate composite key found for fields: {', '.join(unique_fields)}"
                })
    
    return {
        "hasDuplicates": len(duplicates) > 0,
        "duplicates": duplicates
    }


def build_query_params(options: Dict[str, Any]) -> str:
    """
    Build query parameters for advanced queries
    
    Args:
        options: Query options dictionary
        
    Returns:
        Query string
    """
    import json
    from urllib.parse import urlencode
    
    params = {}
    
    if "where" in options:
        params["where"] = json.dumps(options["where"])
    
    if "sort" in options:
        params["sort"] = options["sort"]
    
    if "limit" in options:
        params["limit"] = str(options["limit"])
    
    query_string = urlencode(params)
    return f"?{query_string}" if query_string else ""
