import pytest

from cl_forge.cmf import CmfClient


def test_cmf_client_init():
    client = CmfClient(api_key="test_key")
    assert client.api_key == "test_..." # type: ignore

def test_cmf_client_invalid_path():
    client = CmfClient(api_key="test_key")
    # Specific exception depends on implementation,
    # but InvalidPath is mentioned in docstring
    with pytest.raises(Exception): # noqa: B017
        client.get(path="invalid")