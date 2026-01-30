"""Telescopius API Client."""

from __future__ import annotations

import logging
from typing import Any, TypedDict

import httpx

from .exceptions import (
    TelescopiusAuthError,
    TelescopiusBadRequestError,
    TelescopiusError,
    TelescopiusNetworkError,
    TelescopiusNotFoundError,
    TelescopiusRateLimitError,
    TelescopiusServerError,
)

logger = logging.getLogger("telescopius")


class Quote(TypedDict):
    """Quote of the day response."""

    text: str
    author: str


class SearchTargetsParams(TypedDict, total=False):
    """Parameters for searching targets."""

    # Location & Time
    lat: float
    lon: float
    timezone: str
    datetime: str
    time_format: str
    partner_observatory: str
    partner_telescope: str

    # Object Filtering
    types: str
    name: str
    name_exact: bool
    con: str
    cat: str

    # Magnitude
    mag_max: float
    mag_min: float
    mag_unknown: bool

    # Size
    size_max: float
    size_min: float
    size_unknown: bool

    # Surface Brightness
    subr_max: float
    subr_min: float
    subr_unknown: bool

    # Positional
    min_alt: float
    min_alt_minutes: int
    az_quadrants: str
    ra_min: float
    ra_max: float
    dec_min: float
    dec_max: float

    # Observing Session
    hour_min: float | str
    hour_max: float | str

    # Moon Avoidance
    moon_dist_min: float | str
    moon_dist_max: float

    # Center Point Search
    center_ra: float
    center_dec: float
    dist_min: float
    dist_max: float

    # Comet
    comet_orbit: str

    # Computation & Results
    compute_current: int
    ephemeris: str
    ephemeris_hour: float
    order: str
    order_asc: bool
    results_per_page: int
    page: int


class HighlightsParams(TypedDict, total=False):
    """Parameters for getting target highlights."""

    types: str
    lat: float
    lon: float
    timezone: str
    datetime: str
    time_format: str
    partner_observatory: str
    partner_telescope: str
    compute_current: int
    ephemeris: str
    ephemeris_hour: float
    min_alt: float
    min_alt_minutes: int
    moon_dist_min: float | str
    moon_dist_max: float


class TargetListParams(TypedDict, total=False):
    """Parameters for getting a target list by ID."""

    lat: float
    lon: float
    timezone: str
    datetime: str
    partner_observatory: str
    partner_telescope: str


class SolarSystemTimesParams(TypedDict, total=False):
    """Parameters for getting solar system times."""

    lat: float
    lon: float
    timezone: str
    datetime: str
    partner_observatory: str
    partner_telescope: str
    time_format: str


class SearchPicturesParams(TypedDict, total=False):
    """Parameters for searching pictures."""

    results_per_page: int
    order: str
    page: int
    username: str


class TelescopiusClient:
    """Telescopius API Client.

    A Python client for the Telescopius REST API, providing access to astronomical
    target search, observation planning, and astrophotography features.

    Args:
        api_key: Your Telescopius API key (get one at https://api.telescopius.com)
        base_url: Base URL for the API (default: https://api.telescopius.com/v2.0)
        debug: Enable debug logging for HTTP requests/responses
        timeout: Request timeout in seconds (default: 30)

    Example:
        >>> client = TelescopiusClient(api_key="YOUR_API_KEY")
        >>> quote = client.get_quote_of_the_day()
        >>> print(f"{quote['text']} - {quote['author']}")
    """

    DEFAULT_BASE_URL = "https://api.telescopius.com/v2.0"

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        debug: bool = False,
        timeout: float = 30.0,
    ) -> None:
        if not api_key:
            raise ValueError("API key is required")

        self.api_key = api_key
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.debug = debug
        self.timeout = timeout

        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Key {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )

        if self.debug:
            logging.basicConfig(level=logging.DEBUG)
            logger.setLevel(logging.DEBUG)

    def __enter__(self) -> TelescopiusClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def _log_request(self, method: str, url: str, params: dict[str, Any] | None) -> None:
        """Log request details if debug mode is enabled."""
        if self.debug:
            logger.debug("\n[Telescopius Debug] HTTP Request:")
            logger.debug(f"  Method: {method}")
            full_url = f"{self.base_url}{url}"
            if params:
                query_string = "&".join(f"{k}={v}" for k, v in params.items())
                full_url = f"{full_url}?{query_string}"
            logger.debug(f"  URL: {full_url}")

    def _log_response(self, response: httpx.Response) -> None:
        """Log response details if debug mode is enabled."""
        if self.debug:
            logger.debug("\n[Telescopius Debug] HTTP Response:")
            logger.debug(f"  Status: {response.status_code} {response.reason_phrase}")
            logger.debug(f"  Data: {response.text[:500]}...")

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle API error responses by raising appropriate exceptions."""
        status = response.status_code
        try:
            data = response.json()
            message = data.get("error") or data.get("message") or ""
        except Exception:
            message = response.text or ""

        if status == 400:
            raise TelescopiusBadRequestError(message or "Invalid parameters")
        elif status == 401:
            raise TelescopiusAuthError(message or "Invalid API key")
        elif status == 404:
            raise TelescopiusNotFoundError(message or "Resource not found")
        elif status == 429:
            raise TelescopiusRateLimitError(message or "Rate limit exceeded")
        elif status >= 500:
            raise TelescopiusServerError(message or "Internal server error", status)
        else:
            raise TelescopiusError(f"API Error ({status}): {message or 'Unknown error'}", status)

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Parsed JSON response data

        Raises:
            TelescopiusError: For any API errors
            TelescopiusNetworkError: For network connectivity issues
        """
        # Filter out None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        self._log_request(method, endpoint, params)

        try:
            response = self._client.request(method, endpoint, params=params)
            self._log_response(response)

            if response.status_code >= 400:
                self._handle_error(response)

            return response.json()
        except httpx.RequestError as e:
            raise TelescopiusNetworkError(str(e)) from e

    def get_quote_of_the_day(self) -> Quote:
        """Get the astronomy quote of the day.

        Returns:
            Quote dictionary with 'text' and 'author' keys.

        Example:
            >>> quote = client.get_quote_of_the_day()
            >>> print(f"{quote['text']} - {quote['author']}")
        """
        return self._request("GET", "/quote-of-the-day/")

    def search_targets(
        self,
        *,
        lat: float | None = None,
        lon: float | None = None,
        timezone: str | None = None,
        datetime: str | None = None,
        types: str | None = None,
        name: str | None = None,
        name_exact: bool | None = None,
        con: str | None = None,
        cat: str | None = None,
        min_alt: float | None = None,
        min_alt_minutes: int | None = None,
        moon_dist_min: float | str | None = None,
        moon_dist_max: float | None = None,
        mag_max: float | None = None,
        mag_min: float | None = None,
        mag_unknown: bool | None = None,
        size_max: float | None = None,
        size_min: float | None = None,
        size_unknown: bool | None = None,
        subr_max: float | None = None,
        subr_min: float | None = None,
        subr_unknown: bool | None = None,
        az_quadrants: str | None = None,
        ra_min: float | None = None,
        ra_max: float | None = None,
        dec_min: float | None = None,
        dec_max: float | None = None,
        hour_min: float | str | None = None,
        hour_max: float | str | None = None,
        center_ra: float | None = None,
        center_dec: float | None = None,
        dist_min: float | None = None,
        dist_max: float | None = None,
        comet_orbit: str | None = None,
        compute_current: int | None = None,
        ephemeris: str | None = None,
        ephemeris_hour: float | None = None,
        time_format: str | None = None,
        partner_observatory: str | None = None,
        partner_telescope: str | None = None,
        order: str | None = None,
        order_asc: bool | None = None,
        results_per_page: int | None = None,
        page: int | None = None,
    ) -> dict[str, Any]:
        """Search for astronomical targets in the sky.

        Args:
            lat: Latitude in decimal degrees (-90 to 90)
            lon: Longitude in decimal degrees (-180 to 180)
            timezone: IANA timezone identifier (e.g., 'Europe/Lisbon')
            datetime: Date/time string ('YYYY-MM-DD' or 'YYYY-MM-DD HH:mm:ss')
            types: Object types, comma-separated (e.g., 'GXY,ENEB,PNEB')
            name: Object name to search for (fuzzy search)
            name_exact: Whether to match name exactly
            con: Constellation codes, comma-separated (e.g., 'ORI,CYG')
            cat: Catalog codes, comma-separated
            min_alt: Minimum altitude in degrees (0-90)
            min_alt_minutes: Minimum minutes above min_alt (1-1440)
            moon_dist_min: Min Moon distance (degrees or 'narrowband'/'ha_s2'/'o3'/'lrgb')
            moon_dist_max: Max Moon distance in degrees
            mag_max: Maximum magnitude (brighter objects have lower values)
            mag_min: Minimum magnitude
            mag_unknown: Include objects with unknown magnitude
            size_max: Maximum size in arcminutes
            size_min: Minimum size in arcminutes
            size_unknown: Include objects with unknown size
            subr_max: Maximum surface brightness
            subr_min: Minimum surface brightness
            subr_unknown: Include objects with unknown surface brightness
            az_quadrants: Azimuth quadrants, comma-separated ('NE','NW','SW','SE')
            ra_min: Minimum Right Ascension (0-24 hours)
            ra_max: Maximum Right Ascension (0-24 hours)
            dec_min: Minimum Declination (-90 to 90 degrees)
            dec_max: Maximum Declination (-90 to 90 degrees)
            hour_min: Min hour of observing session (0-24 or twilight keywords)
            hour_max: Max hour of observing session (0-24 or twilight keywords)
            center_ra: Center RA for distance search
            center_dec: Center Dec for distance search
            dist_min: Min distance from center point in degrees
            dist_max: Max distance from center point in degrees
            comet_orbit: Comet orbit type ('PERIODIC','NON_PERIODIC','ASTEROIDAL','INTERSTELLAR')
            compute_current: Return observation at datetime (1) or not (0)
            ephemeris: Ephemeris calculation ('daily' or 'yearly')
            ephemeris_hour: Decimal hour for yearly ephemeris
            time_format: Time format ('24hr' or 'ampm')
            partner_observatory: MPC code of partner observatory
            partner_telescope: Partner telescope code
            order: Sort field ('name','con','dec','mag','ra','rise','set','transit',etc.)
            order_asc: Ascending order (True) or descending (False)
            results_per_page: Results per page (1-120)
            page: Page number for pagination

        Returns:
            Dictionary with 'matched' count and 'page_results' array.

        Example:
            >>> results = client.search_targets(
            ...     lat=38.7223,
            ...     lon=-9.1393,
            ...     timezone='Europe/Lisbon',
            ...     types='GXY,ENEB',
            ...     min_alt=30,
            ...     mag_max=10
            ... )
            >>> print(f"Found {results['matched']} objects")
            >>> for item in results['page_results']:
            ...     print(item['object']['main_name'])
        """
        params = {
            "lat": lat,
            "lon": lon,
            "timezone": timezone,
            "datetime": datetime,
            "types": types,
            "name": name,
            "name_exact": name_exact,
            "con": con,
            "cat": cat,
            "min_alt": min_alt,
            "min_alt_minutes": min_alt_minutes,
            "moon_dist_min": moon_dist_min,
            "moon_dist_max": moon_dist_max,
            "mag_max": mag_max,
            "mag_min": mag_min,
            "mag_unknown": mag_unknown,
            "size_max": size_max,
            "size_min": size_min,
            "size_unknown": size_unknown,
            "subr_max": subr_max,
            "subr_min": subr_min,
            "subr_unknown": subr_unknown,
            "az_quadrants": az_quadrants,
            "ra_min": ra_min,
            "ra_max": ra_max,
            "dec_min": dec_min,
            "dec_max": dec_max,
            "hour_min": hour_min,
            "hour_max": hour_max,
            "center_ra": center_ra,
            "center_dec": center_dec,
            "dist_min": dist_min,
            "dist_max": dist_max,
            "comet_orbit": comet_orbit,
            "compute_current": compute_current,
            "ephemeris": ephemeris,
            "ephemeris_hour": ephemeris_hour,
            "time_format": time_format,
            "partner_observatory": partner_observatory,
            "partner_telescope": partner_telescope,
            "order": order,
            "order_asc": order_asc,
            "results_per_page": results_per_page,
            "page": page,
        }
        return self._request("GET", "/targets/search", params)

    def get_target_highlights(
        self,
        *,
        lat: float | None = None,
        lon: float | None = None,
        timezone: str | None = None,
        datetime: str | None = None,
        types: str | None = None,
        min_alt: float | None = None,
        min_alt_minutes: int | None = None,
        moon_dist_min: float | str | None = None,
        moon_dist_max: float | None = None,
        compute_current: int | None = None,
        ephemeris: str | None = None,
        ephemeris_hour: float | None = None,
        time_format: str | None = None,
        partner_observatory: str | None = None,
        partner_telescope: str | None = None,
    ) -> dict[str, Any]:
        """Get popular targets best seen around this time of year.

        Returns targets near opposition with the longest time up in the night sky.

        Args:
            lat: Latitude in decimal degrees (-90 to 90)
            lon: Longitude in decimal degrees (-180 to 180)
            timezone: IANA timezone identifier (e.g., 'Europe/Lisbon')
            datetime: Date/time string ('YYYY-MM-DD' or 'YYYY-MM-DD HH:mm:ss')
            types: Object types, comma-separated (e.g., 'GXY,ENEB')
            min_alt: Minimum altitude in degrees (0-90)
            min_alt_minutes: Minimum minutes above min_alt (1-1440)
            moon_dist_min: Min Moon distance (degrees or 'narrowband'/'ha_s2'/'o3'/'lrgb')
            moon_dist_max: Max Moon distance in degrees
            compute_current: Return observation at datetime (1) or not (0)
            ephemeris: Ephemeris calculation ('daily' or 'yearly')
            ephemeris_hour: Decimal hour for yearly ephemeris
            time_format: Time format ('24hr' or 'ampm')
            partner_observatory: MPC code of partner observatory
            partner_telescope: Partner telescope code

        Returns:
            Dictionary with 'matched' count and 'page_results' array.

        Example:
            >>> highlights = client.get_target_highlights(
            ...     lat=38.7223,
            ...     lon=-9.1393,
            ...     timezone='Europe/Lisbon',
            ...     min_alt=20
            ... )
            >>> for item in highlights['page_results']:
            ...     obj = item['object']
            ...     print(obj.get('main_name') or obj['main_id'])
        """
        params = {
            "lat": lat,
            "lon": lon,
            "timezone": timezone,
            "datetime": datetime,
            "types": types,
            "min_alt": min_alt,
            "min_alt_minutes": min_alt_minutes,
            "moon_dist_min": moon_dist_min,
            "moon_dist_max": moon_dist_max,
            "compute_current": compute_current,
            "ephemeris": ephemeris,
            "ephemeris_hour": ephemeris_hour,
            "time_format": time_format,
            "partner_observatory": partner_observatory,
            "partner_telescope": partner_telescope,
        }
        return self._request("GET", "/targets/highlights", params)

    def get_target_lists(self) -> list[dict[str, Any]]:
        """Get all target lists for the current user.

        Returns:
            List of dictionaries with 'id' and 'name' keys.

        Example:
            >>> lists = client.get_target_lists()
            >>> for lst in lists:
            ...     print(f"{lst['id']}: {lst['name']}")
        """
        return self._request("GET", "/targets/lists")

    def get_target_list_by_id(
        self,
        list_id: str,
        *,
        lat: float | None = None,
        lon: float | None = None,
        timezone: str | None = None,
        datetime: str | None = None,
        partner_observatory: str | None = None,
        partner_telescope: str | None = None,
    ) -> dict[str, Any]:
        """Get a specific target list by ID with all its targets.

        Args:
            list_id: The target list ID
            lat: Latitude in decimal degrees (-90 to 90)
            lon: Longitude in decimal degrees (-180 to 180)
            timezone: IANA timezone identifier (e.g., 'Europe/Lisbon')
            datetime: Date/time string ('YYYY-MM-DD' or 'YYYY-MM-DD HH:mm:ss')
            partner_observatory: MPC code of partner observatory
            partner_telescope: Partner telescope code

        Returns:
            Dictionary with list details and targets.

        Example:
            >>> target_list = client.get_target_list_by_id(
            ...     '12345678',
            ...     lat=38.7223,
            ...     lon=-9.1393,
            ...     timezone='Europe/Lisbon'
            ... )
            >>> print(f"List: {target_list['name']}")
        """
        params = {
            "lat": lat,
            "lon": lon,
            "timezone": timezone,
            "datetime": datetime,
            "partner_observatory": partner_observatory,
            "partner_telescope": partner_telescope,
        }
        return self._request("GET", f"/targets/lists/{list_id}", params)

    def get_solar_system_times(
        self,
        *,
        lat: float | None = None,
        lon: float | None = None,
        timezone: str | None = None,
        datetime: str | None = None,
        time_format: str | None = None,
        partner_observatory: str | None = None,
        partner_telescope: str | None = None,
    ) -> dict[str, Any]:
        """Get rise/transit/set times for Sun, Moon, and planets.

        Args:
            lat: Latitude in decimal degrees (-90 to 90)
            lon: Longitude in decimal degrees (-180 to 180)
            timezone: IANA timezone identifier (e.g., 'Europe/Lisbon')
            datetime: Date/time string ('YYYY-MM-DD' or 'YYYY-MM-DD HH:mm:ss')
            time_format: Time format ('24hr' or 'ampm')
            partner_observatory: MPC code of partner observatory
            partner_telescope: Partner telescope code

        Returns:
            Dictionary with times for sun, moon, and planets.

        Example:
            >>> times = client.get_solar_system_times(
            ...     lat=38.7223,
            ...     lon=-9.1393,
            ...     timezone='Europe/Lisbon'
            ... )
            >>> print(f"Sunrise: {times['sun']['rise']}")
            >>> print(f"Moon phase: {times['moon']['phase']}")
        """
        params = {
            "lat": lat,
            "lon": lon,
            "timezone": timezone,
            "datetime": datetime,
            "time_format": time_format,
            "partner_observatory": partner_observatory,
            "partner_telescope": partner_telescope,
        }
        return self._request("GET", "/solar-system/times", params)

    def search_pictures(
        self,
        *,
        results_per_page: int | None = None,
        order: str | None = None,
        page: int | None = None,
        username: str | None = None,
    ) -> dict[str, Any]:
        """Search for astrophotography pictures.

        Args:
            results_per_page: Number of results per page
            order: Sort order ('is_featured', 'acquisition_timestamp',
                   'created_timestamp', 'final_revision_timestamp', 'popularity')
            page: Page number for pagination
            username: Filter by username

        Returns:
            Dictionary with 'results' array and pagination info.

        Example:
            >>> pictures = client.search_pictures(
            ...     order='is_featured',
            ...     results_per_page=10
            ... )
            >>> for pic in pictures['results']:
            ...     print(f"{pic['title']} by {pic['username']}")
        """
        params = {
            "results_per_page": results_per_page,
            "order": order,
            "page": page,
            "username": username,
        }
        return self._request("GET", "/pictures/search", params)
