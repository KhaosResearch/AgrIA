import pytest
import requests

from unittest.mock import MagicMock

import server.services.sigpac_tools_v2.find as sigpac_find
import server.services.sigpac_tools_v2.locate as sigpac_locate
import server.services.sigpac_tools_v2.utils as sigpac_utils
import server.services.sigpac_tools_v2.search as sigpac_search
import server.utils.parcel_finder_utils as parcel_finder_utils
from server.services.sigpac_tools_v2.find import find_from_cadastral_registry
from server.services.sigpac_tools_v2.locate import generate_cadastral_ref_from_coords
from server.services.sigpac_tools_v2.utils import read_cadastral_registry
from server.services.sigpac_tools_v2.search import search
from server.utils.parcel_finder_utils import build_cadastral_reference

# --- CONSTANTS FOR MOCK RETURNS ---

MOCK_CADASTRAL_REF = "14048A001001990000RM"

MOCK_COMMUNITY = 14

MOCK_REG = {
    "province": 14,
    "municipality": 48,
    "section": "A",
    "polygon": 1,
    "parcel": 199,
    "id_inm": 0,
    "control": "RM"
}

MOCK_FULL_JSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-4.591153071665946, 37.26475453427461],
                        [-4.59113675377588, 37.2646813912686],
                        [-4.591153071665946, 37.26475453427461],
                    ]
                ]
            },
            "properties": {
                "provincia": 14,
                "municipio": 48,
                "agregado": 0,
                "zona": 0,
                "poligono": 1,
                "parcela": 199,
                "recinto": 1,
                "superficie": 7.4659,
                "pendiente_media": 12.4,
                "coef_regadio": 0,
                "admisibilidad": None,
                "incidencias": None,
                "uso_sigpac": "OV",
                "region": 13,
                "altitud": 378
            }
        }
    ],
    "crs": {
        "type": "EPSG",
        "properties": {
            "code": "4258"
        }
    }
}

MOCK_GEOMETRY = {
    "type": "Polygon",
    "coordinates": [
        [
            [-4.591437662441293, 37.265637136158325],
            [4.591275211928052, 37.265473570013704],
            [-4.591437662441293, 37.265637136158325],
        ]
    ],
    "CRS": "epsg:4258"
}

MOCK_METADATA = {
    "arboles": None,
    "convergencia": None,
    "id": None,
    "isRecin": None,
    "parcelaInfo": {
        "provincia": 14,
        "municipio": 48,
        "agregado": 0,
        "poligono": 1,
        "parcela": 199,
        "referencia_cat": MOCK_CADASTRAL_REF,
        "dn_surface": 7.4659
    },
    "query": [
        {
            "admisibilidad": None,
            "altitud": 378,
            "coef_regadio": 0,
            "incidencias": None,
            "pendiente_media": 12.4,
            "recinto": 1,
            "region": 13,
            "uso_sigpac": "OV",
            "dn_surface": 7.4659,
            "inctexto": None,
            "superficie_admisible": 7.4659
        }
    ],
    "usos": [
        {
            "uso_sigpac": "OV",
            "dn_superficie": 7.4659,
            "superficie_admisible": 7.4659
        }
    ],
    "vigencia": None,
    "vuelo": None
}

MOCK_RESPONSE_JSON = [
    {
        "provincia": 14,
        "municipio": 48,
        "agregado": 0,
        "zona": 0,
        "poligono": 1,
        "parcela": 199,
        "recinto": 1,
        "superficie": 7.4659,
        "pendiente_media": 12.4,
        "coef_regadio": 0,
        "admisibilidad": None,
        "incidencias": None,
        "uso_sigpac": "OV",
        "region": 13,
        "altitud": 378,
        "srid": 4258,
        "wkt": "POLYGON((-4.591153071665946 37.26475453427461,-4.59113675377588 37.2646813912686,-4.591153071665946 37.26475453427461))"
    }
]

@pytest.fixture
def mock_sigpact_tools_v2_dependencies(monkeypatch):
    # --- ARRANGE ---
    # Prepare mockups (find.py)
    mock_read_cadastral_registry  = MagicMock(return_value=MOCK_REG)
    monkeypatch.setattr(sigpac_find, "read_cadastral_registry", mock_read_cadastral_registry)
    mock_get_geometry=MagicMock(return_value=MOCK_GEOMETRY)
    monkeypatch.setattr(sigpac_utils, "get_geometry", mock_get_geometry)
    mock_get_metadata=MagicMock(return_value=MOCK_METADATA)
    monkeypatch.setattr(sigpac_utils, "get_metadata", mock_get_metadata)

    mock_search  = MagicMock(return_value=(MOCK_GEOMETRY, MOCK_METADATA))
    monkeypatch.setattr(sigpac_find, "search", mock_search)
    mock_find_community  = MagicMock(return_value=MOCK_COMMUNITY)
    monkeypatch.setattr(sigpac_utils, "find_community", mock_find_community)
    mock_get_parcel_metadata_and_geometry  = MagicMock(return_value=(MOCK_GEOMETRY, MOCK_METADATA))
    monkeypatch.setattr(sigpac_utils, "get_parcel_metadata_and_geometry", mock_get_parcel_metadata_and_geometry)
    
    # Prepare mockups (locate.py)
    mock_build_cadastral_reference  = MagicMock(return_value=MOCK_CADASTRAL_REF)
    monkeypatch.setattr(sigpac_locate, "build_cadastral_reference", mock_build_cadastral_reference)
    
    # Prepare mockups (external dependecies)
    mock_response_json = MagicMock(return_value=MOCK_RESPONSE_JSON)
    mock_response = MagicMock(status_code=200, json=mock_response_json)
    mock_requests_get = MagicMock(return_value=mock_response)
    monkeypatch.setattr(requests, "get", mock_requests_get)
    
    yield {
        "mock_read_cadastral_registry": mock_read_cadastral_registry,
        "mock_get_geometry": mock_get_geometry,
        "mock_get_metadata": mock_get_metadata,
        "mock_search": mock_search,
        "mock_find_community": mock_find_community,
        "mock_get_parcel_metadata_and_geometry": mock_get_parcel_metadata_and_geometry,
        "mock_build_cadastral_reference": mock_build_cadastral_reference,
        "mock_response_json": mock_response_json, 
        "mock_requests_get": mock_requests_get 
    }