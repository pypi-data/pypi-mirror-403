"""Tests for the TelescopiusClient."""

import httpx
import pytest
from pytest_httpx import HTTPXMock

from telescopius import (
    TelescopiusAuthError,
    TelescopiusBadRequestError,
    TelescopiusClient,
    TelescopiusNetworkError,
    TelescopiusRateLimitError,
)


class TestTelescopiusClient:
    """Tests for TelescopiusClient initialization and configuration."""

    def test_init_requires_api_key(self) -> None:
        """Test that API key is required."""
        with pytest.raises(ValueError, match="API key is required"):
            TelescopiusClient(api_key="")

    def test_init_with_api_key(self) -> None:
        """Test initialization with API key."""
        client = TelescopiusClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.base_url == "https://api.telescopius.com/v2.0"
        client.close()

    def test_init_with_custom_base_url(self) -> None:
        """Test initialization with custom base URL."""
        client = TelescopiusClient(api_key="test-key", base_url="https://custom.api.com")
        assert client.base_url == "https://custom.api.com"
        client.close()

    def test_context_manager(self) -> None:
        """Test that client works as context manager."""
        with TelescopiusClient(api_key="test-key") as client:
            assert client.api_key == "test-key"


class TestGetQuoteOfTheDay:
    """Tests for get_quote_of_the_day method."""

    def test_get_quote_success(self, httpx_mock: HTTPXMock) -> None:
        """Test successful quote retrieval."""
        httpx_mock.add_response(
            url="https://api.telescopius.com/v2.0/quote-of-the-day/",
            json={"text": "Test quote", "author": "Test Author"},
        )

        with TelescopiusClient(api_key="test-key") as client:
            quote = client.get_quote_of_the_day()
            assert quote["text"] == "Test quote"
            assert quote["author"] == "Test Author"


class TestSearchTargets:
    """Tests for search_targets method."""

    def test_search_targets_success(self, httpx_mock: HTTPXMock) -> None:
        """Test successful target search."""
        httpx_mock.add_response(
            json={
                "matched": 1,
                "page_results": [
                    {
                        "object": {
                            "main_id": "NGC 7000",
                            "main_name": "North America Nebula",
                        }
                    }
                ],
            }
        )

        with TelescopiusClient(api_key="test-key") as client:
            results = client.search_targets(
                lat=38.7223,
                lon=-9.1393,
                timezone="Europe/Lisbon",
            )
            assert results["matched"] == 1
            assert len(results["page_results"]) == 1
            assert results["page_results"][0]["object"]["main_id"] == "NGC 7000"

    def test_search_targets_with_filters(self, httpx_mock: HTTPXMock) -> None:
        """Test target search with filters."""
        httpx_mock.add_response(json={"matched": 0, "page_results": []})

        with TelescopiusClient(api_key="test-key") as client:
            results = client.search_targets(
                lat=38.7223,
                lon=-9.1393,
                timezone="Europe/Lisbon",
                types="galaxy,eneb",
                min_alt=30,
                mag_max=10,
            )
            assert results["matched"] == 0


class TestGetTargetHighlights:
    """Tests for get_target_highlights method."""

    def test_get_highlights_success(self, httpx_mock: HTTPXMock) -> None:
        """Test successful highlights retrieval."""
        httpx_mock.add_response(
            json={
                "matched": 2,
                "page_results": [
                    {"object": {"main_id": "M31"}},
                    {"object": {"main_id": "M42"}},
                ],
            }
        )

        with TelescopiusClient(api_key="test-key") as client:
            highlights = client.get_target_highlights(
                lat=40.7128,
                lon=-74.0060,
                timezone="America/New_York",
            )
            assert highlights["matched"] == 2
            assert len(highlights["page_results"]) == 2


class TestGetTargetLists:
    """Tests for get_target_lists method."""

    def test_get_lists_success(self, httpx_mock: HTTPXMock) -> None:
        """Test successful lists retrieval."""
        httpx_mock.add_response(
            json=[
                {"id": "123", "name": "My List"},
                {"id": "456", "name": "Favorites"},
            ]
        )

        with TelescopiusClient(api_key="test-key") as client:
            lists = client.get_target_lists()
            assert len(lists) == 2
            assert lists[0]["id"] == "123"
            assert lists[0]["name"] == "My List"


class TestGetTargetListById:
    """Tests for get_target_list_by_id method."""

    def test_get_list_by_id_success(self, httpx_mock: HTTPXMock) -> None:
        """Test successful list retrieval by ID."""
        httpx_mock.add_response(
            url="https://api.telescopius.com/v2.0/targets/lists/123",
            json={
                "id": "123",
                "name": "My List",
                "targets": [{"main_id": "NGC 7000"}],
            },
        )

        with TelescopiusClient(api_key="test-key") as client:
            target_list = client.get_target_list_by_id("123")
            assert target_list["id"] == "123"
            assert target_list["name"] == "My List"
            assert len(target_list["targets"]) == 1


class TestGetSolarSystemTimes:
    """Tests for get_solar_system_times method."""

    def test_get_times_success(self, httpx_mock: HTTPXMock) -> None:
        """Test successful solar system times retrieval."""
        httpx_mock.add_response(
            json={
                "sun": {"rise": "07:00", "set": "19:00"},
                "moon": {"rise": "14:00", "phase": "Waxing Gibbous"},
            }
        )

        with TelescopiusClient(api_key="test-key") as client:
            times = client.get_solar_system_times(
                lat=35.6762,
                lon=139.6503,
                timezone="Asia/Tokyo",
            )
            assert times["sun"]["rise"] == "07:00"
            assert times["moon"]["phase"] == "Waxing Gibbous"


class TestSearchPictures:
    """Tests for search_pictures method."""

    def test_search_pictures_success(self, httpx_mock: HTTPXMock) -> None:
        """Test successful pictures search."""
        httpx_mock.add_response(
            json={
                "results": [
                    {"title": "M31 Image", "username": "astro_user"},
                ],
                "total": 1,
            }
        )

        with TelescopiusClient(api_key="test-key") as client:
            pictures = client.search_pictures(order="is_featured")
            assert len(pictures["results"]) == 1
            assert pictures["results"][0]["title"] == "M31 Image"


class TestErrorHandling:
    """Tests for error handling."""

    def test_unauthorized_error(self, httpx_mock: HTTPXMock) -> None:
        """Test 401 Unauthorized error."""
        httpx_mock.add_response(
            status_code=401,
            json={"error": "Invalid API key"},
        )

        with TelescopiusClient(api_key="bad-key") as client:
            with pytest.raises(TelescopiusAuthError):
                client.get_quote_of_the_day()

    def test_bad_request_error(self, httpx_mock: HTTPXMock) -> None:
        """Test 400 Bad Request error."""
        httpx_mock.add_response(
            status_code=400,
            json={"error": "Invalid parameters"},
        )

        with TelescopiusClient(api_key="test-key") as client:
            with pytest.raises(TelescopiusBadRequestError):
                client.search_targets()

    def test_rate_limit_error(self, httpx_mock: HTTPXMock) -> None:
        """Test 429 Rate Limit error."""
        httpx_mock.add_response(
            status_code=429,
            json={"error": "Rate limit exceeded"},
        )

        with TelescopiusClient(api_key="test-key") as client:
            with pytest.raises(TelescopiusRateLimitError):
                client.get_quote_of_the_day()

    def test_network_error(self, httpx_mock: HTTPXMock) -> None:
        """Test network error handling."""
        httpx_mock.add_exception(httpx.ConnectError("Connection failed"))

        with TelescopiusClient(api_key="test-key") as client:
            with pytest.raises(TelescopiusNetworkError):
                client.get_quote_of_the_day()
