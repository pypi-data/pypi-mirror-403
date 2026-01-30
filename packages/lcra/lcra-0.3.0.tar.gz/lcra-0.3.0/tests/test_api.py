"""Tests for API routes"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from api import app


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def mock_scraper_data():
    """Mock scraper data"""
    from lcra import FloodgateOperation, FloodOperationsReport, LakeLevel, RiverCondition

    return {
        "lake_levels": [
            LakeLevel(
                dam_lake_name="Mansfield/Travis",
                measurement_time=datetime.now(),
                head_elevation=675.17,
                tail_elevation=492.2,
            )
        ],
        "river_conditions": [
            RiverCondition(
                location="Colorado River at Austin",
                current_stage=4.2,
                current_flow=1250.0,
            )
        ],
        "floodgate_operations": [
            FloodgateOperation(
                dam_name="Mansfield Dam",
                last_update=datetime.now(),
                inflows=850.0,
            )
        ],
        "flood_report": FloodOperationsReport(
            report_time=datetime.now(),
            lake_levels=[],
            river_conditions=[],
            river_forecasts=[],
            floodgate_operations=[],
        ),
    }


class TestRootEndpoint:
    """Test cases for root endpoint"""

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data


class TestHealthEndpoint:
    """Test cases for health endpoint"""

    @patch("api.LCRAFloodDataScraper")
    def test_health_check_healthy(self, mock_scraper_class, client):
        """Test health check when LCRA is accessible"""
        mock_scraper = AsyncMock()
        mock_scraper.__aenter__ = AsyncMock(return_value=mock_scraper)
        mock_scraper.__aexit__ = AsyncMock(return_value=None)
        mock_scraper.fetch_api_data = AsyncMock()
        mock_scraper_class.return_value = mock_scraper

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["lcra_accessible"] is True

    @patch("api.LCRAFloodDataScraper")
    def test_health_check_unhealthy(self, mock_scraper_class, client):
        """Test health check when LCRA is not accessible"""
        mock_scraper = AsyncMock()
        mock_scraper.__aenter__ = AsyncMock(return_value=mock_scraper)
        mock_scraper.__aexit__ = AsyncMock(return_value=None)
        mock_scraper.fetch_api_data = AsyncMock(side_effect=Exception("Connection error"))
        mock_scraper_class.return_value = mock_scraper

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["lcra_accessible"] is False


class TestFloodReportEndpoint:
    """Test cases for flood report endpoint"""

    @patch("api.LCRAFloodDataScraper")
    def test_get_flood_report(self, mock_scraper_class, client, mock_scraper_data):
        """Test getting flood report"""
        mock_scraper = AsyncMock()
        mock_scraper.__aenter__ = AsyncMock(return_value=mock_scraper)
        mock_scraper.__aexit__ = AsyncMock(return_value=None)
        mock_scraper.scrape_all_data = AsyncMock(return_value=mock_scraper_data["flood_report"])
        mock_scraper_class.return_value = mock_scraper

        response = client.get("/flood-report")
        assert response.status_code == 200
        data = response.json()
        assert "report_time" in data
        assert "lake_levels" in data


class TestLakeLevelsEndpoint:
    """Test cases for lake levels endpoint"""

    @patch("api.LCRAFloodDataScraper")
    def test_get_lake_levels(self, mock_scraper_class, client, mock_scraper_data):
        """Test getting lake levels"""
        mock_scraper = AsyncMock()
        mock_scraper.__aenter__ = AsyncMock(return_value=mock_scraper)
        mock_scraper.__aexit__ = AsyncMock(return_value=None)
        mock_scraper.scrape_lake_levels = AsyncMock(return_value=mock_scraper_data["lake_levels"])
        mock_scraper_class.return_value = mock_scraper

        response = client.get("/lake-levels")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "dam_lake_name" in data[0]


class TestRiverConditionsEndpoint:
    """Test cases for river conditions endpoint"""

    @patch("api.LCRAFloodDataScraper")
    def test_get_river_conditions(self, mock_scraper_class, client, mock_scraper_data):
        """Test getting river conditions"""
        mock_scraper = AsyncMock()
        mock_scraper.__aenter__ = AsyncMock(return_value=mock_scraper)
        mock_scraper.__aexit__ = AsyncMock(return_value=None)
        mock_scraper.scrape_river_conditions = AsyncMock(
            return_value=mock_scraper_data["river_conditions"]
        )
        mock_scraper_class.return_value = mock_scraper

        response = client.get("/river-conditions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "location" in data[0]


class TestFloodgateOperationsEndpoint:
    """Test cases for floodgate operations endpoint"""

    @patch("api.LCRAFloodDataScraper")
    def test_get_floodgate_operations(self, mock_scraper_class, client, mock_scraper_data):
        """Test getting floodgate operations"""
        mock_scraper = AsyncMock()
        mock_scraper.__aenter__ = AsyncMock(return_value=mock_scraper)
        mock_scraper.__aexit__ = AsyncMock(return_value=None)
        mock_scraper.scrape_floodgate_operations = AsyncMock(
            return_value=mock_scraper_data["floodgate_operations"]
        )
        mock_scraper_class.return_value = mock_scraper

        response = client.get("/floodgate-operations")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "dam_name" in data[0]
