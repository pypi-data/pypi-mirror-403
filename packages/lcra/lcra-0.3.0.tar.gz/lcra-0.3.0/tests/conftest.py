"""Pytest configuration and fixtures"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from scraper import LCRAFloodDataScraper


@pytest.fixture
def mock_httpx_response():
    """Create a mock httpx response"""
    response = MagicMock()
    response.json.return_value = {}
    response.raise_for_status = MagicMock()
    return response


@pytest.fixture
def mock_scraper_session(mock_httpx_response):
    """Create a mock scraper with mocked session"""
    scraper = LCRAFloodDataScraper()
    scraper.session = AsyncMock()
    scraper.session.get = AsyncMock(return_value=mock_httpx_response)
    return scraper


@pytest.fixture
def sample_lake_levels_data():
    """Sample lake levels API response"""
    return {
        "records": [
            {
                "dam": "Mansfield",
                "lake": "Travis",
                "lastDataUpdate": "2025-01-15T10:30:00",
                "head": 675.17,
                "tail": 492.2,
                "gateOps": "No floodgate operations to pass floodwaters are expected at Mansfield Dam at this time.",
            },
            {
                "dam": "Buchanan",
                "lake": "Buchanan",
                "lastDataUpdate": "2025-01-15T10:30:00",
                "head": 1019.86,
                "tail": 887.65,
                "gateOps": "No floodgate operations to pass floodwaters are expected at Buchanan Dam at this time.",
            },
        ]
    }


@pytest.fixture
def sample_river_conditions_data():
    """Sample river conditions API response"""
    return {
        "sites": [
            {
                "location": "Colorado River at Austin",
                "stage": 4.2,
                "flow": 1250.0,
                "bankfull": 21.0,
                "floodStage": 22.0,
                "dateTime": "2025-01-15T10:30:00",
            }
        ]
    }


@pytest.fixture
def sample_floodgate_operations_data():
    """Sample floodgate operations API response"""
    return {
        "records": [
            {
                "dam": "Mansfield",
                "lastUpdate": "2025-01-15T10:30:00",
                "inflows": 850.0,
                "gateOps": "All gates closed",
                "forecast": "Lake level expected to remain stable",
                "head": 675.17,
            }
        ]
    }


@pytest.fixture
def sample_narrative_summary_data():
    """Sample narrative summary API response"""
    return [
        {
            "lastUpdate": "2025-01-15T10:30:00",
            "narrive_sum": "Current conditions are normal. No flood operations expected.",
        }
    ]
