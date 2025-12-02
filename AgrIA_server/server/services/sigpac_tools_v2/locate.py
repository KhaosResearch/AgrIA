import requests
import structlog

from ._globals import BASE_URL, QUERY_URL
from .utils import get_parcel_metadata_and_geometry

from ...utils.parcel_finder_utils import build_cadastral_reference

logger = structlog.get_logger()


def get_cadastral_data_from_coords(lat: float, lon: float, crs: str = "4258", use_cadastral_ref: bool = True):
    """Gets the cadastral reference of the given coordinates and reference in the given parcel.
    WARNING: The result is synthetic and does not necessarily match a real SIGPAC cadastral reference.
    However, it works for the system's scope.

    Parameters
    ----------
    lat : float
        Latitude of the location
    lon : float
        Longitude of the location
    crs : str
        Coordinates reference system
    use_cadastral_ref : bool
        Whether to generate and use the cadastral reference or get the data directly from coords.
    Returns
    -------
    str
        Cadastral code of the found reference

    Raises
    ------
        ValueError: If JSON is invalid
    """
    # Search enclosure by coords
    logger.info(f"Retrieving info from parcel at coordinates: {lat}, {lon}")
    base_endpoint = f"{BASE_URL}/{QUERY_URL}/recinfobypoint/{crs}/{lon}/{lat}.json"
    logger.debug(f"SIGPAC request URL: {base_endpoint}")
    # TODO: Review if the conditional statement is ultimately redundant (if so, also build_cadastral_reference()'s logic)
    if use_cadastral_ref:
        try:
            response = requests.get(base_endpoint)
            response = response.json()[0]

            # Get cadastral data from responses
            provi = str(response["provincia"]).zfill(2) + "-"
            munic = str(response["municipio"]).zfill(3) + "-"
            polig = str(response["poligono"]).zfill(3)
            parcel = str(response["parcela"]).zfill(5)

        except Exception as e:
            logger.exception(f"Failed to parse SIGPAC JSON response:")
            raise ValueError("Invalid JSON returned by SIGPAC", e)

        # Build cadastral reference
        cadastral_ref = build_cadastral_reference(provi, munic, polig, parcel)
        logger.info(
            f'Associated synthetic cadastral reference: {cadastral_ref}')

        # geometry, _ = search(read_cadastral_registry(cadastral_ref))

        return cadastral_ref
    else:
        geojson_endpoint = base_endpoint.replace('.json', '.geojson')
        geometry, metadata = get_parcel_metadata_and_geometry(geojson_endpoint)
        return geometry, metadata
