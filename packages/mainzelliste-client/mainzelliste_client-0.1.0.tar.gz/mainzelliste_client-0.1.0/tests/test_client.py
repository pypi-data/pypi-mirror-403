import pytest
import requests

from mainzelliste_client import MainzellisteClient

URL = "http://localhost:8081"
API_KEY = "e8KcR1vcOLOTY0lRC7RjnMbdr4ARYIGurhEUZSpbvqU="


@pytest.fixture
def client():
    """Create a test client instance."""
    return MainzellisteClient(
        base_url=URL,
        api_key=API_KEY
    )


class TestMainzellisteClient:
    """Test cases for MainzellisteClient."""

    def test_init(self, client):
        """Test client initialization."""
        assert client.base_url == URL
        assert client.api_key == API_KEY
        assert client.api_version == "2.0"
        assert "mainzellisteApiKey" in client.session.headers
        assert client.session.headers["mainzellisteApiKey"] == client.api_key
        assert client.session.headers["Content-Type"] == "application/json"

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is removed from base_url."""
        client = MainzellisteClient(
            base_url="http://localhost:8081/",
            api_key="test-key"
        )
        assert client.base_url == "http://localhost:8081"

    def test_create_session(self, client):
        """Test creating a session."""
        result = client.create_session()

        assert "sessionId" in result

    def test_create_token(self, client):
        """Test creating a token."""
        session_result = client.create_session()
        session_id = session_result["sessionId"]

        result = client.create_token(
            session_id=session_id,
            token_type="addPatient",
            idtypes=["pid"],
            fields={"patientID": "5Yp0E"},
            ids={}
        )

        assert "tokenId" in result
        assert isinstance(result["tokenId"], str)

    def test_create_token_with_defaults(self, client):
        """Test creating a token with default parameters."""
        session_result = client.create_session()
        session_id = session_result["sessionId"]

        result = client.create_token(
            session_id=session_id,
            token_type="addPatient"
        )

        assert "tokenId" in result
        assert isinstance(result["tokenId"], str)

    def test_add_patient(self, client):
        """Test adding a patient."""
        session_result = client.create_session()
        session_id = session_result["sessionId"]

        token_result = client.create_token(
            session_id=session_id,
            token_type="addPatient",
            idtypes=["pid"],
            fields={"patientID": "TestPatient123"},
            ids={}
        )
        token_id = token_result["tokenId"]

        result = client.add_patient(token_id=token_id, sureness=True)

        assert "idString" in result[0]
        assert isinstance(result[0]["idString"], str)

    def test_add_patient_default_sureness(self, client):
        """Test adding a patient with default sureness."""
        session_result = client.create_session()
        session_id = session_result["sessionId"]

        token_result = client.create_token(
            session_id=session_id,
            token_type="addPatient",
            idtypes=["pid"],
            fields={"patientID": "TestPatient456"},
            ids={}
        )
        token_id = token_result["tokenId"]

        result = client.add_patient(token_id=token_id)

        assert "idString" in result[0]
        assert isinstance(result[0]["idString"], str)

    def test_generate_patient_id(self, client):
        """Test the complete generate_patient_id workflow."""
        original_patient_id = "5Yp0E"

        result = client.generate_patient_id(original_patient_id)

        assert isinstance(result, str)
        assert len(result) > 0
        assert result != original_patient_id
        assert result == 'PQRYHQG0'

    def test_http_error_handling(self, client):
        """Test that HTTP errors are raised."""
        with pytest.raises(requests.HTTPError):
            client.add_patient(token_id="invalid-token-id")

    def test_context_manager(self):
        """Test using client as context manager."""
        with MainzellisteClient(
                base_url="http://localhost:8081",
                api_key=API_KEY
        ) as client:
            assert isinstance(client, MainzellisteClient)
            assert client.session is not None

    def test_close(self, client):
        """Test closing the client."""
        client.close()
        assert client.session is not None
