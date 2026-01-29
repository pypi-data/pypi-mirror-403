"""
SheetSandbox SDK for Python
Turn Google Sheets into your production-ready database for MVPs.

Version: 2.0.0
Author: Aravind Kumar Vemula
License: MIT
"""

from .client import SheetSandbox
from .utils import (
    format_success_response,
    format_error_response,
    validate_table_name,
    validate_id,
    validate_data,
    validate_token,
    check_duplicates,
    build_query_params
)

__version__ = "1.0.0"
__author__ = "Aravind Kumar Vemula"
__license__ = "MIT"

__all__ = [
    "SheetSandbox",
    "format_success_response",
    "format_error_response",
    "validate_table_name",
    "validate_id",
    "validate_data",
    "validate_token",
    "check_duplicates",
    "build_query_params",
]
