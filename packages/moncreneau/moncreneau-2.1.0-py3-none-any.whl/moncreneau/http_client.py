import requests
from typing import Optional, Dict, Any
from .error import MoncreneauError


class HttpClient:
    """HTTP client for making requests to Moncreneau API"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://mc-prd.duckdns.org/api/v1",
        timeout: int = 30
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'moncreneau-python/1.0.0'
        })
    
    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make a GET request"""
        response = self.session.get(
            f"{self.base_url}{path}",
            params=params,
            timeout=self.timeout
        )
        return self._handle_response(response)
    
    def post(self, path: str, data: Optional[Dict[str, Any]] = None) -> Any:
        """Make a POST request"""
        response = self.session.post(
            f"{self.base_url}{path}",
            json=data,
            timeout=self.timeout
        )
        return self._handle_response(response)
    
    def delete(self, path: str) -> None:
        """Make a DELETE request"""
        response = self.session.delete(
            f"{self.base_url}{path}",
            timeout=self.timeout
        )
        
        if response.status_code not in (200, 204):
            self._handle_response(response)
    
    def _handle_response(self, response: requests.Response) -> Any:
        """Handle API response and errors"""
        if response.status_code >= 400:
            try:
                error_data = response.json().get('error', {})
            except ValueError:
                error_data = {'code': 'UNKNOWN_ERROR', 'message': response.text}
            
            raise MoncreneauError(error_data, response.status_code)
        
        if response.status_code == 204:
            return None
        
        return response.json()
