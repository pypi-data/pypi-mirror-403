from datetime import datetime
from unittest.mock import patch

import pytest

from cl_forge.cmf import Eur, Ipc, Uf, Usd, Utm

# Mock data based on real API responses
MOCK_RESPONSES = {
    "/dolar": {
        "Dolares": [{"Valor": "872,22", "Fecha": "2026-01-23"}]
    },
    "/dolar/2025": {
        "Dolares": [
            {"Valor": "996,46", "Fecha": "2025-01-02"},
            {"Valor": "999,84", "Fecha": "2025-01-03"}
        ]
    },
    "/euro": {
        "Euros": [{"Valor": "910,15", "Fecha": "2026-01-23"}]
    },
    "/euro/2025": {
        "Euros": [
            {"Valor": "1035,50", "Fecha": "2025-01-02"},
            {"Valor": "1040,12", "Fecha": "2025-01-03"}
        ]
    },
    "/uf": {
        "UFs": [{"Valor": "38.500,12", "Fecha": "2026-01-23"}]
    },
    "/uf/2025": {
        "UFs": [
            {"Valor": "37.100,00", "Fecha": "2025-01-01"},
            {"Valor": "37.105,00", "Fecha": "2025-01-02"}
        ]
    },
    "/utm": {
        "UTMs": [{"Valor": "67.123,00", "Fecha": "2026-01-01"}]
    },
    "/utm/2025": {
        "UTMs": [
            {"Valor": "66.500,00", "Fecha": "2025-01-01"},
            {"Valor": "66.600,00", "Fecha": "2025-02-01"}
        ]
    },
    "/ipc": {
        "IPCs": [{"Valor": "0,5", "Fecha": "2025-12-01"}]
    },
    "/ipc/2025": {
        "IPCs": [
            {"Valor": "0,1", "Fecha": "2025-01-01"},
            {"Valor": "0,2", "Fecha": "2025-02-01"}
        ]
    }
}

def mock_get(path, format='json'):  # noqa: A002
    if path in MOCK_RESPONSES:
        return MOCK_RESPONSES[path]
    raise ValueError(f"Path {path} not mocked")

@pytest.fixture
def mock_cmf_client():
    with patch("cl_forge.core.endpoints.CmfClient") as mock:
        client_instance = mock.return_value
        client_instance.get.side_effect = mock_get
        yield client_instance

def test_usd_endpoints(mock_cmf_client):
    usd = Usd(api_key="test")
    
    # Test current
    current = usd.current()
    assert current.value == 872.22
    assert current.date == datetime(2026, 1, 23)
    
    # Test year
    year_data = usd.year(2025)
    assert len(year_data) == 2
    assert year_data[0].value == 996.46
    assert year_data[0].date == datetime(2025, 1, 2)

def test_eur_endpoints(mock_cmf_client):
    eur = Eur(api_key="test")
    
    current = eur.current()
    assert current.value == 910.15
    assert current.date == datetime(2026, 1, 23)
    
    year_data = eur.year(2025)
    assert len(year_data) == 2
    assert year_data[0].value == 1035.50

def test_uf_endpoints(mock_cmf_client):
    uf = Uf(api_key="test")
    
    current = uf.current()
    assert current.value == 38500.12
    assert current.date == datetime(2026, 1, 23)
    
    year_data = uf.year(2025)
    assert len(year_data) == 2
    assert year_data[0].value == 37100.0

def test_utm_endpoints(mock_cmf_client):
    utm = Utm(api_key="test")
    current = utm.current()
    assert current.value == 67123.0
    
    year_data = utm.year(2025)
    assert len(year_data) == 2
    assert year_data[0].value == 66500.0

def test_ipc_endpoints(mock_cmf_client):
    ipc = Ipc(api_key="test")
    
    current = ipc.current()
    # IpcRecord divides by 100: 0,5 -> 0.005
    assert current.value == 0.005
    
    year_data = ipc.year(2025)
    assert len(year_data) == 2
    assert year_data[0].value == 0.001


def test_endpoint_init():
    api_key = "test_key"

    ipc = Ipc(api_key)
    assert ipc._client.api_key == "test_..."
    assert ipc._path == "/ipc" # type: ignore
    assert ipc._root_key == "IPCs" # type: ignore

    usd = Usd(api_key)
    assert usd._path == "/dolar" # type: ignore
    assert usd._root_key == "Dolares" # type: ignore

    eur = Eur(api_key)
    assert eur._path == "/euro" # type: ignore
    assert eur._root_key == "Euros" # type: ignore

    uf = Uf(api_key)
    assert uf._path == "/uf" # type: ignore
    assert uf._root_key == "UFs" # type: ignore

    utm = Utm(api_key)
    assert utm._path == "/utm" # type: ignore
    assert utm._root_key == "UTMs" # type: ignore