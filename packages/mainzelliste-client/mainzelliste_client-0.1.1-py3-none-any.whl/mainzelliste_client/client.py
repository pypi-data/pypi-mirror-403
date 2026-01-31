"""
Python client for Mainzelliste web service.
"""
from typing import Any, Dict, List, Optional

import requests


class MainzellisteClient:
    """Client for interacting with Mainzelliste API."""

    def __init__(self, base_url: str, api_key: str, api_version: str = "2.0"):
        """
        Initialize the Mainzelliste client.
        
        Args:
            base_url: Base URL of the Mainzelliste service (e.g., "http://localhost:8081")
            api_key: API key for authentication
            api_version: API version to use (default: "2.0")
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.api_version = api_version
        self.session = requests.Session()
        self.session.headers.update({
            "mainzellisteApiKey": self.api_key,
            "Content-Type": "application/json"
        })

    def generate_patient_id(self, patient_id: str) -> str:
        """
        Generate a new patient ID using the Mainzelliste API.

        Args:
             patient_id: Original Patient ID
        Returns:
            New Patient ID
        """
        # Create a session
        session_response = self.create_session()
        session_id = session_response["sessionId"]

        # Create token
        token_response = self.create_token(session_id, "addPatient", fields={"patientID": patient_id})
        token_id = token_response["tokenId"]

        # Get new patient ID
        patient_response = self.add_patient(token_id)
        new_patient_id = patient_response[0]["idString"]

        return new_patient_id

    def create_session(self) -> Dict[str, Any]:
        """
        Create a new session.
        
        Returns:
            Response data containing session information
        
        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.base_url}/sessions"
        response = self.session.post(url)
        response.raise_for_status()

        return response.json()

    def create_token(
            self,
            session_id: str,
            token_type: str,
            idtypes: Optional[List[str]] = None,
            fields: Optional[Dict[str, str]] = None,
            ids: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a token for a session.
        
        Args:
            session_id: The session ID
            token_type: Type of token (e.g., "addPatient")
            idtypes: List of ID types to generate (default: ["pid"])
            fields: Patient fields (e.g., {"patientID": "5Yp0E"})
            ids: Patient IDs (default: {})
        
        Returns:
            Response data containing token information
        
        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.base_url}/sessions/{session_id}/tokens"

        payload = {
            "type": token_type,
            "data": {
                "idtypes": idtypes or ["pid"],
                "fields": fields or {},
                "ids": ids or {}
            }
        }

        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def add_patient(
            self,
            token_id: str,
            sureness: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Add a patient using a token.
        
        Args:
            token_id: The token ID for adding the patient
            sureness: Whether the data is certain (default: True)
        
        Returns:
            Response data containing patient information
        
        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.base_url}/patients"

        params = {
            "tokenId": token_id,
            "mainzellisteApiVersion": self.api_version
        }

        payload = {
            "type": "addPatient",
            "data": {"sureness": sureness}
        }

        patient_headers = {**self.session.headers, "Content-Type": "application/x-www-form-urlencoded"}
        response = self.session.post(url, json=payload, params=params, headers=patient_headers)
        response.raise_for_status()
        return response.json()

    def close(self):
        """Close the underlying session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
