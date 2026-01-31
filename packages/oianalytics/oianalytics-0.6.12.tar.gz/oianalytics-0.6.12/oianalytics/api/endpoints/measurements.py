from typing import Optional
import requests

from .. import _credentials


__all__ = ["get_measurements"]


def get_measurements(
    name: Optional[str] = None,
    unit_id: Optional[str] = None,
    unit_family_id: Optional[str] = None,
    page: int = 0,
    page_size: int = 20,
    api_credentials: Optional[_credentials.OIAnalyticsAPICredentials] = None,
) -> dict:
    """
    List measurements by page.

    Parameters
    ----------
    name : str, optional
        The text the measurement name should contain. The search is performed in case insensitive manner.
    unit_id : str, optional
        Search by storage unit ID.
    unit_family_id : str, optional
        Search by unit family ID.
    page : int, default 0
        The page to retrieve, defaults to 0 (the first page).
    page_size : int, default 20
        The size of one page.
    api_credentials : OIAnalyticsAPICredentials, optional
        The credentials to use to query the API. If None, previously set default credentials are used.

    Returns
    -------
    dict
        A dictionary containing the paginated measurements response with keys:
        - content: List of measurements
        - size: Size of the page
        - number: Page number
        - totalElements: Total number of measurements
        - totalPages: Total number of pages
    """
    # Get credentials from environment if not provided
    if api_credentials is None:
        api_credentials = _credentials.get_default_oianalytics_credentials()

    # Query endpoint
    url = f"{api_credentials.base_url}/api/oianalytics/measurements"
    response = requests.get(
        url=url,
        params={
            "page": page,
            "size": page_size,
            "name": name,
            "unitId": unit_id,
            "unitFamilyId": unit_family_id,
        },
        **api_credentials.auth_kwargs,
    )

    # Output
    response.raise_for_status()
    return response.json()
