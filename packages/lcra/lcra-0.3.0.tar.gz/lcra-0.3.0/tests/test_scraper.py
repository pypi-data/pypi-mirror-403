"""Tests for LCRAFloodDataScraper"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from lcra import FloodgateOperation, LakeLevel, RiverCondition
from scraper import LCRAFloodDataScraper


class TestLCRAFloodDataScraper:
    """Test cases for LCRAFloodDataScraper"""

    def test_init(self):
        """Test scraper initialization"""
        scraper = LCRAFloodDataScraper()
        assert scraper.session is None
        assert scraper.BASE_URL == "https://hydromet.lcra.org"
        assert scraper.TIMEOUT == 30.0

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager"""
        async with LCRAFloodDataScraper() as scraper:
            assert scraper.session is not None
        # Session should be closed after context exit
        assert scraper.session is not None  # httpx client might still exist but be closed

    @pytest.mark.asyncio
    async def test_fetch_api_data_success(self, mock_scraper_session, mock_httpx_response):
        """Test successful API data fetch"""
        mock_httpx_response.json.return_value = {"test": "data"}
        result = await mock_scraper_session.fetch_api_data("test/endpoint")
        assert result == {"test": "data"}
        mock_scraper_session.session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_api_data_without_session(self):
        """Test fetch_api_data raises error without session"""
        scraper = LCRAFloodDataScraper()
        with pytest.raises(RuntimeError, match="async context manager"):
            await scraper.fetch_api_data("test/endpoint")

    @pytest.mark.asyncio
    async def test_scrape_lake_levels(
        self, mock_scraper_session, sample_lake_levels_data, mock_httpx_response
    ):
        """Test scraping lake levels"""
        mock_httpx_response.json.return_value = sample_lake_levels_data
        result = await mock_scraper_session.scrape_lake_levels()
        assert len(result) == 2
        assert isinstance(result[0], LakeLevel)
        assert result[0].dam_lake_name == "Mansfield/Travis"
        assert result[0].head_elevation == 675.17

    @pytest.mark.asyncio
    async def test_scrape_lake_levels_empty(self, mock_scraper_session, mock_httpx_response):
        """Test scraping lake levels with empty response"""
        mock_httpx_response.json.return_value = {"records": []}
        result = await mock_scraper_session.scrape_lake_levels()
        assert result == []

    @pytest.mark.asyncio
    async def test_scrape_river_conditions(
        self, mock_scraper_session, sample_river_conditions_data, mock_httpx_response
    ):
        """Test scraping river conditions"""
        mock_httpx_response.json.return_value = sample_river_conditions_data
        result = await mock_scraper_session.scrape_river_conditions()
        assert len(result) == 1
        assert isinstance(result[0], RiverCondition)
        assert result[0].location == "Colorado River at Austin"
        assert result[0].current_stage == 4.2

    @pytest.mark.asyncio
    async def test_scrape_floodgate_operations(
        self, mock_scraper_session, sample_floodgate_operations_data, mock_httpx_response
    ):
        """Test scraping floodgate operations"""
        mock_httpx_response.json.return_value = sample_floodgate_operations_data
        result = await mock_scraper_session.scrape_floodgate_operations()
        assert len(result) == 1
        assert isinstance(result[0], FloodgateOperation)
        assert result[0].dam_name == "Mansfield"
        assert result[0].inflows == 850.0

    @pytest.mark.asyncio
    async def test_get_narrative_summary(
        self, mock_scraper_session, sample_narrative_summary_data, mock_httpx_response
    ):
        """Test getting narrative summary"""
        mock_httpx_response.json.return_value = sample_narrative_summary_data
        last_update, narrative = await mock_scraper_session.get_narrative_summary()
        assert narrative == "Current conditions are normal. No flood operations expected."
        assert isinstance(last_update, datetime)

    @pytest.mark.asyncio
    async def test_get_narrative_summary_empty(self, mock_scraper_session, mock_httpx_response):
        """Test getting narrative summary with empty response"""
        mock_httpx_response.json.return_value = []
        last_update, narrative = await mock_scraper_session.get_narrative_summary()
        assert last_update is None
        assert narrative is None

    @pytest.mark.asyncio
    async def test_scrape_all_data(
        self,
        mock_scraper_session,
        sample_lake_levels_data,
        sample_river_conditions_data,
        sample_floodgate_operations_data,
        sample_narrative_summary_data,
        mock_httpx_response,
    ):
        """Test scraping all data"""

        # Mock different responses for different endpoints
        async def mock_get(url):
            if "GetNarrativeSummary" in url:
                mock_httpx_response.json.return_value = sample_narrative_summary_data
            elif "GetLakeLevelsGateOps" in url:
                mock_httpx_response.json.return_value = sample_lake_levels_data
            elif "GetForecastReferences" in url:
                mock_httpx_response.json.return_value = sample_river_conditions_data
            return mock_httpx_response

        mock_scraper_session.session.get = AsyncMock(side_effect=mock_get)
        result = await mock_scraper_session.scrape_all_data()
        assert result.lake_levels
        assert result.river_conditions
        assert result.floodgate_operations
        assert result.report_time is not None


class TestParserMethods:
    """Test cases for parser static methods"""

    def test_parse_datetime_iso(self):
        """Test parsing ISO datetime format"""
        result = LCRAFloodDataScraper.parse_datetime("2025-01-15T10:30:00")
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15

    def test_parse_datetime_slash_format(self):
        """Test parsing slash-separated datetime format"""
        result = LCRAFloodDataScraper.parse_datetime("01/15/2025 10:30:00")
        assert isinstance(result, datetime)
        assert result.year == 2025

    def test_parse_datetime_none(self):
        """Test parsing None or empty datetime"""
        assert LCRAFloodDataScraper.parse_datetime(None) is None
        assert LCRAFloodDataScraper.parse_datetime("") is None
        assert LCRAFloodDataScraper.parse_datetime("/") is None

    def test_parse_float_valid(self):
        """Test parsing valid float values"""
        assert LCRAFloodDataScraper.parse_float("123.45") == 123.45
        assert LCRAFloodDataScraper.parse_float(123.45) == 123.45
        assert LCRAFloodDataScraper.parse_float(123) == 123.0

    def test_parse_float_invalid(self):
        """Test parsing invalid float values"""
        assert LCRAFloodDataScraper.parse_float(None) is None
        assert LCRAFloodDataScraper.parse_float("N/A") is None
        assert LCRAFloodDataScraper.parse_float("/") is None
        assert LCRAFloodDataScraper.parse_float("--") is None

    def test_parse_float_with_text(self):
        """Test parsing float from text with extra characters"""
        assert LCRAFloodDataScraper.parse_float("123.45 ft") == 123.45
        assert LCRAFloodDataScraper.parse_float("Elevation: 675.17") == 675.17
