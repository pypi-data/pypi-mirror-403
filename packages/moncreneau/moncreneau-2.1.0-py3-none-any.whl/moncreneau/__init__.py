import hmac
import hashlib
import json
from typing import Any, Optional

from .http_client import HttpClient
from .resources import Appointments, Departments
from .error import MoncreneauError


class Moncreneau:
    """
    Moncreneau API client
    
    Example:
        >>> client = Moncreneau('mk_live_YOUR_API_KEY')
        >>> appointment = client.appointments.create(
        ...     department_id='dept_123',
        ...     date_time='2026-01-20T10:00:00',
        ...     user_name='Jean Dupont',
        ...     user_phone='+224621234567'
        ... )
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://mc-prd.duckdns.org/api/v1",
        timeout: int = 30
    ):
        """
        Initialize Moncreneau client
        
        Args:
            api_key: Your Moncreneau API key (mk_test_... or mk_live_...)
            base_url: API base URL (default: https://mc-prd.duckdns.org/api/v1)
            timeout: Request timeout in seconds (default: 30)
        """
        http = HttpClient(api_key, base_url, timeout)
        
        self.appointments = Appointments(http)
        self.departments = Departments(http)
    
    @staticmethod
    def verify_webhook_signature(
        payload: Any,
        signature: str,
        secret: str
    ) -> bool:
        """
        Verify webhook signature using HMAC-SHA256
        
        Args:
            payload: Webhook payload (dict or JSON string)
            signature: Signature from X-Webhook-Signature header
            secret: Your webhook secret
        
        Returns:
            True if signature is valid, False otherwise
        
        Example:
            >>> is_valid = Moncreneau.verify_webhook_signature(
            ...     request.json,
            ...     request.headers['X-Webhook-Signature'],
            ...     os.getenv('WEBHOOK_SECRET')
            ... )
        """
        # Convert payload to JSON string if it's a dict
        payload_string = json.dumps(payload) if isinstance(payload, dict) else payload
        
        # Compute HMAC-SHA256
        computed = hmac.new(
            secret.encode('utf-8'),
            payload_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Constant-time comparison
        return hmac.compare_digest(computed, signature)


__version__ = '1.0.0'
__all__ = ['Moncreneau', 'MoncreneauError']
