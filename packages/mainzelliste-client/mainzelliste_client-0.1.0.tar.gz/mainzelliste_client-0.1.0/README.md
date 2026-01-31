# mainzelliste-client

Python client for the mainzelliste, a pseudonymization service



## Installation
pip install mainzelliste-client

## Usage

### Basic Example

```python
from mainzelliste_client import MainzellisteClient

with MainzellisteClient(base_url='http://localhost:8081', api_key='e8KcR1vcOLOTY0lRC7RjnMbdr4ARYIGurhEUZSpbvqU=') as client:
    new_patient_id = client.generate_patient_id('5Yp0E')

print(new_patient_id)  # PQRYHQG0
```

## Setup a test Mainzelliste instance

1. Go in the `tests/docker/` directory
```bash
cd tests/docker/
```
2. Run the docker compose
```bash
docker-compose up -d
```
3. Mainzelliste should be at http://localhost:8081/

## API Reference

### MainzellisteClient

#### `__init__(base_url, api_key, api_version="2.0")`

Initialize the Mainzelliste client.

**Parameters:**

- `base_url` (str): Base URL of the Mainzelliste service

- `api_key` (str): API key for authentication

- `api_version` (str, optional): API version to use (default: "2.0")

#### `generate_patient_id(patient_id)`

Generate a new pseudonymized patient ID using the Mainzelliste API. This is the main method for users to pseudonymize patient identifiers.

This method handles the complete workflow: creating a session, generating a token, and adding the patient to get a new pseudonymized ID.

**Parameters:**

- `patient_id` (str): Original patient ID to be pseudonymized

**Returns:** String containing the new pseudonymized patient ID.

**Example:**

```python
with MainzellisteClient(base_url='http://localhost:8081', api_key='your-api-key') as client:
    new_id = client.generate_patient_id('patient-123')
    print(f"Pseudonymized ID: {new_id}")
```

#### `create_session()`

Create a new session.

**Returns:** Dictionary containing session information with a `uri` field.

#### `create_token(session_id, token_type, idtypes=None, fields=None, ids=None)`

Create a token for a session.

**Parameters:**

- `session_id` (str): The session ID

- `token_type` (str): Type of token (e.g., "addPatient")

- `idtypes` (list, optional): List of ID types to generate (default: ["pid"])

- `fields` (dict, optional): Patient fields (default: {})

- `ids` (dict, optional): Patient IDs (default: {})

**Returns:** Dictionary containing token information with a `tokenId` field.

#### `add_patient(token_id, sureness=True)`

Add a patient using a token.

**Parameters:**

- `token_id` (str): The token ID for adding the patient

- `sureness` (bool, optional): Whether the data is certain (default: True)

**Returns:** Dictionary containing patient information.

#### `close()`

Close the underlying session.

## License

See LICENSE file for details.
