import requests
from fastapi import HTTPException
import os
import string
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
        self.base_url = base_url
        self.username = username
        self.password = password
        self.token = token
        if self.token == None:
            self.authenticate()

    def authenticate(self):
        response = self.post("api/auth/login", data={
            "username": self.username,
            "password": self.password
        }, is_json=False)
        if response.status_code == 200:
            self.token = response.json().get("access_token")
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        try:
            url = f"{self.base_url}/{endpoint}"
            headers = self._get_headers()
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Unauthorized")
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None, is_json: bool = True) -> requests.Response:
        try:
            url = f"{self.base_url}/{endpoint}"
            headers = self._get_headers()
            if is_json:
                response = requests.post(url, headers=headers, json=data, params=params)
            else:
                if "Content-Type" in headers:
                    del headers["Content-Type"]
                response = requests.post(url, headers=headers, data=data, params=params)

            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Unauthorized")
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

