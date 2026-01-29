"""
SheetSandbox SDK Client
A Python client for interacting with the SheetSandbox API
"""

import requests
from typing import Any, Dict, List, Optional, Union

from .utils import (
    format_success_response,
    format_error_response,
    validate_table_name,
    validate_id,
    validate_data,
    validate_token,
    check_duplicates,
    build_url
)


class SheetSandbox:
    """
    SheetSandbox SDK Client
    
    A Python client for interacting with the SheetSandbox API
    
    Example:
        >>> client = SheetSandbox('your-api-token')
        >>> records = client.get('Users')
    """
    
    def __init__(self, token: str, base_url: str = "https://api.sheetsandbox.com/api", 
                 timeout: int = 30):
        """
        Create a SheetSandbox client instance
        
        Args:
            token: Your SheetSandbox API token
            base_url: Base API URL (default: https://api.sheetsandbox.com/api)
            timeout: Request timeout in seconds (default: 30)
            
        Raises:
            ValueError: If token is invalid
        """
        validate_token(token)
        
        self.token = token
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.user_plan = None  # Will be set after token verification
        
        # Create session with default headers
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        })
    
    def _make_request(self, method: str, endpoint: str, 
                     data: Optional[Any] = None) -> Dict[str, Any]:
        """
        Make HTTP request to API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request data (optional)
            
        Returns:
            Response dictionary
            
        Raises:
            requests.RequestException: If request fails
        """
        url = build_url(self.base_url, endpoint)
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, timeout=self.timeout)
            elif method.upper() == 'PATCH':
                response = self.session.patch(url, json=data, timeout=self.timeout)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            # Extract error message from response if available
            try:
                error_data = e.response.json()
                error_msg = error_data.get('error') or error_data.get('result') or str(e)
            except:
                error_msg = str(e)
            
            raise requests.RequestException(error_msg) from e
        
        except requests.exceptions.Timeout:
            raise requests.RequestException("Request timeout. Please check your connection.")
        
        except requests.exceptions.ConnectionError:
            raise requests.RequestException("No response from server. Please check your connection.")
    
    def verify_token(self) -> Dict[str, Any]:
        """
        Verify the API token and get user plan
        
        Returns:
            Verification result with plan info
            
        Example:
            >>> result = client.verify_token()
            >>> print(result['data']['plan'])  # 'free' or 'pro'
        """
        try:
            response = self._make_request('GET', '/verifyToken')
            
            # Store user plan from response
            self.user_plan = response.get('plan', 'free')
            
            return format_success_response({
                'verified': True,
                'message': response.get('sheetsandboxTokenStatus'),
                'code': response.get('code'),
                'plan': self.user_plan
            })
            
        except Exception as e:
            return format_error_response(e)
    
    def get(self, table_name: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get records from a table (FREE & PRO)
        Pro users can use advanced query options
        
        Args:
            table_name: Name of the table/sheet
            options: Query options (PRO only)
                - where: Filter conditions (dict)
                - sort: Sort field (use '-' prefix for descending)
                - limit: Limit number of results (int)
        
        Returns:
            Response with records
            
        Examples:
            >>> # Free plan - simple get
            >>> result = client.get('Users')
            
            >>> # Pro plan - advanced query
            >>> result = client.get('Users', {
            ...     'where': {'status': 'active', 'city': 'New York'},
            ...     'sort': '-created_at',
            ...     'limit': 50
            ... })
        """
        try:
            validate_table_name(table_name)
            options = options or {}
            
            # Get all records
            response = self._make_request('GET', f'/{table_name}')
            data = response.get('data', response)
            
            return format_success_response({'data': data})
            
        except Exception as e:
            return format_error_response(e)
    
    def get_by_id(self, table_name: str, record_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get a specific record by ID (FREE & PRO)
        
        Args:
            table_name: Name of the table/sheet
            record_id: Record ID (1-based index)
            
        Returns:
            Response with the record
            
        Example:
            >>> result = client.get_by_id('Users', 1)
        """
        try:
            validate_table_name(table_name)
            validate_id(record_id)
            
            response = self._make_request('GET', f'/{table_name}/{record_id}')
            return format_success_response(response)
            
        except Exception as e:
            return format_error_response(e)
    
    def post(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a single record (FREE & PRO)
        
        Args:
            table_name: Name of the table/sheet
            data: Record data (must be a dictionary)
            
        Returns:
            Response with creation result
            
        Example:
            >>> result = client.post('Users', {
            ...     'name': 'John Doe',
            ...     'email': 'john@example.com'
            ... })
        """
        try:
            validate_table_name(table_name)
            
            # Ensure data is a single dictionary for free plan
            if isinstance(data, list):
                return {
                    'success': False,
                    'error': 'Use post_many() for batch inserts. post() only accepts single records.',
                    'status': 'error'
                }
            
            validate_data(data)
            
            response = self._make_request('POST', f'/{table_name}', data)
            return format_success_response(response)
            
        except Exception as e:
            return format_error_response(e)
    
    def set_token(self, new_token: str) -> None:
        """
        Update the API token
        
        Args:
            new_token: New API token
            
        Raises:
            ValueError: If token is invalid
        """
        validate_token(new_token)
        self.token = new_token
        self.user_plan = None  # Reset plan, will be fetched on next verify_token
        self.session.headers.update({'Authorization': f'Bearer {new_token}'})
    
    def set_base_url(self, new_base_url: str) -> None:
        """
        Update the base URL
        
        Args:
            new_base_url: New base URL
            
        Raises:
            ValueError: If base URL is invalid
        """
        if not new_base_url or not isinstance(new_base_url, str):
            raise ValueError('Base URL must be a non-empty string')
        
        self.base_url = new_base_url.rstrip('/')
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration
        
        Returns:
            Current configuration dictionary
        """
        return {
            'baseURL': self.base_url,
            'timeout': self.timeout,
            'hasToken': bool(self.token),
            'plan': self.user_plan
        }
