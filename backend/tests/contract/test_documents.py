import requests
import pytest
from openapi_spec_validator import validate
from openapi_spec_validator.readers import read_from_filename

import os

SPEC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../specs/001-build-an-simple/contracts/openapi.yaml'))

@pytest.fixture
def spec():
    spec_dict, _ = read_from_filename(SPEC_PATH)
    return spec_dict

def test_post_documents_contract(spec):
    # This is a placeholder test. It will fail because the endpoint is not implemented yet.
    # The purpose of this test is to validate the contract.
    with pytest.raises(requests.exceptions.ConnectionError):
        response = requests.post("http://localhost:8000/api/v1/documents", json={"title": "test"})
        assert response.status_code == 201
        validate(response.json(), spec['paths']['/documents']['post']['responses']['201']['content']['application/json']['schema'])
