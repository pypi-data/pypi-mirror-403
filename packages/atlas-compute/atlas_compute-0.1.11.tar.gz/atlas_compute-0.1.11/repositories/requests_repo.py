import requests
import os
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

load_dotenv(".env")

logger = logging.getLogger(__name__)

class RequestsRepo:
    """
    Handles HTTP requests with optional authentication.
    """
    def __init__(self, base_url: str, username: Optional[str] = None, password: Optional[str] = None, token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.token = token
        
        if not self.token:
            if self.username and self.password:
                self.authenticate()
            else:
                # We don't raise here because some endpoints might be public, 
                # but ComputeClient will require it.
                pass

    def authenticate(self):
        """Authenticates using username and password to get a token."""
        url = f"{self.base_url}/api/auth/login"
        try:
            # Standard FastAPI OAuth2 login expects form data
            response = requests.post(url, data={
                "username": self.username,
                "password": self.password
            })
            
            if response.status_code == 200:
                self.token = response.json().get("access_token")
                if not self.token:
                    raise ValueError("Login successful but no access_token found in response")
            else:
                raise ConnectionError(f"Authentication failed ({response.status_code}): {response.text}")
        except Exception as e:
            logger.error(f"Authentication request failed: {e}")
            raise ConnectionError(f"Authentication request failed: {str(e)}")
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        endpoint = endpoint.lstrip("/")
        url = f"{self.base_url}/{endpoint}"
        try:
            headers = self._get_headers()
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 401:
                # Potential token expiry - could implement auto-refresh here if needed
                raise ConnectionError("Unauthorized: Token may be expired or invalid")
            
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"GET request failed: {e}")
            raise ConnectionError(f"GET request failed: {str(e)}")

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None, is_json: bool = True) -> requests.Response:
        endpoint = endpoint.lstrip("/")
        url = f"{self.base_url}/{endpoint}"
        try:
            headers = self._get_headers()
            if is_json:
                response = requests.post(url, headers=headers, json=data, params=params)
            else:
                # If not JSON, we let requests handle the Content-Type (e.g. for form data)
                if "Content-Type" in headers:
                    del headers["Content-Type"]
                response = requests.post(url, headers=headers, data=data, params=params)

            if response.status_code == 401:
                raise ConnectionError("Unauthorized: Token may be expired or invalid")
            
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"POST request failed: {e}")
            raise ConnectionError(f"POST request failed: {str(e)}")

