"""
LCRA Flood Status Web Scraper

This module contains the LCRAFloodDataScraper class for extracting data from the LCRA API.
"""

import logging
import re
from datetime import datetime

import httpx
from fastapi import HTTPException

from lcra import (
    DataSource,
    FloodgateOperation,
    FloodOperationsReport,
    LakeLevel,
    RiverCondition,
)

logger = logging.getLogger(__name__)


class LCRAFloodDataScraper:
    """
    Web scraper for LCRA flood status data using the API endpoints
    """

    BASE_URL = "https://hydromet.lcra.org"
    TIMEOUT = 30.0

    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = httpx.AsyncClient(timeout=self.TIMEOUT)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()

    async def fetch_api_data(self, endpoint: str) -> dict:
        """Fetch data from LCRA API endpoints"""
        if not self.session:
            raise RuntimeError("Scraper must be used as async context manager")
        url = f"{self.BASE_URL}/api/{endpoint}"
        try:
            logger.debug(f"Fetching data from {url}")
            response = await self.session.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} from {url}: {e}")
            raise HTTPException(
                status_code=503, detail=f"Failed to fetch data from LCRA API: {str(e)}"
            )
        except httpx.RequestError as e:
            logger.error(f"Request error fetching {url}: {e}")
            raise HTTPException(
                status_code=503, detail=f"Failed to fetch data from LCRA API: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error parsing LCRA API data from {url}: {e}")
            raise HTTPException(status_code=500, detail=f"Error parsing LCRA API data: {str(e)}")

    async def scrape_lake_levels(self) -> list[LakeLevel]:
        """Extract current lake levels from API"""
        try:
            data = await self.fetch_api_data("FloodStatus/GetLakeLevelsGateOps")
            lake_levels = []
            for record in data.get("records", []):
                lake_level = LakeLevel(
                    dam_lake_name=f"{record.get('dam', '')}/{record.get('lake', '')}",
                    measurement_time=self.parse_datetime(record.get("lastDataUpdate")),
                    head_elevation=self.parse_float(record.get("head")),
                    tail_elevation=self.parse_float(record.get("tail")),
                    gate_operations=record.get("gateOps"),
                )
                lake_levels.append(lake_level)
            return lake_levels
        except Exception as e:
            logger.error(f"Error fetching lake levels: {e}", exc_info=True)
            return []

    async def scrape_river_conditions(self) -> list[RiverCondition]:
        """Extract current river conditions from API"""
        try:
            data = await self.fetch_api_data("GetForecastReferences")
            river_conditions = []
            for site in data.get("sites", []):
                condition = RiverCondition(
                    location=site.get("location", ""),
                    current_stage=self.parse_float(site.get("stage")),
                    current_flow=self.parse_float(site.get("flow")),
                    bankfull_stage=self.parse_float(site.get("bankfull")),
                    flood_stage=self.parse_float(site.get("floodStage")),
                    action_stage=self.parse_float(site.get("bankfull")),
                    measurement_time=self.parse_datetime(site.get("dateTime")),
                    data_source=DataSource.LCRA,
                )
                river_conditions.append(condition)
            return river_conditions
        except Exception as e:
            logger.error(f"Error fetching river conditions: {e}", exc_info=True)
            return []

    async def scrape_floodgate_operations(self) -> list[FloodgateOperation]:
        """Extract floodgate operations data from API"""
        try:
            data = await self.fetch_api_data("FloodStatus/GetLakeLevelsGateOps")
            operations = []
            for record in data.get("records", []):
                operation = FloodgateOperation(
                    dam_name=record.get("dam", "Unknown Dam"),
                    last_update=self.parse_datetime(record.get("lastUpdate")),
                    inflows=self.parse_float(record.get("inflows")),
                    gate_operations=record.get("gateOps"),
                    lake_level_forecast=record.get("forecast"),
                    current_elevation=self.parse_float(record.get("head")),
                )
                operations.append(operation)
            return operations
        except Exception as e:
            logger.error(f"Error fetching floodgate operations: {e}", exc_info=True)
            return []

    async def get_narrative_summary(self) -> tuple[datetime | None, str | None]:
        """Get narrative summary and last update time"""
        try:
            data = await self.fetch_api_data("FloodStatus/GetNarrativeSummary")
            if data and len(data) > 0:
                record = data[0]
                last_update = self.parse_datetime(record.get("lastUpdate"))
                narrative = record.get("narrive_sum")
                return last_update, narrative
            return None, None
        except Exception as e:
            logger.error(f"Error fetching narrative summary: {e}", exc_info=True)
            return None, None

    @staticmethod
    def parse_datetime(text: str | None) -> datetime | None:
        """Parse various datetime formats found on the site"""
        if not text or (isinstance(text, str) and (text.strip() == "" or text == "/")):
            return None
        try:
            if "T" in text:
                clean_text = (
                    text.split("T")[0]
                    + " "
                    + text.split("T")[1].split("+")[0].split("-")[0].split("Z")[0]
                )
                return datetime.fromisoformat(clean_text.replace("Z", ""))
        except (ValueError, IndexError) as e:
            logger.debug(f"Failed to parse ISO datetime format: {text}, error: {e}")
            pass
        patterns = [
            r"(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}:\d{2}:\d{2})\s*(AM|PM)?",
            r"(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}:\d{2})\s*(AM|PM)?",
            r"(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})",
            r"(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if len(match.groups()) >= 3 and match.group(3):
                        date_str = f"{match.group(1)} {match.group(2)} {match.group(3)}"
                        if "/" in match.group(1):
                            return datetime.strptime(date_str, "%m/%d/%Y %I:%M:%S %p")
                        else:
                            return datetime.strptime(date_str, "%Y-%m-%d %I:%M:%S %p")
                    else:
                        date_str = f"{match.group(1)} {match.group(2)}"
                        if "/" in match.group(1):
                            if ":" in match.group(2) and len(match.group(2).split(":")) == 3:
                                return datetime.strptime(date_str, "%m/%d/%Y %H:%M:%S")
                            else:
                                return datetime.strptime(date_str, "%m/%d/%Y %H:%M")
                        else:
                            if ":" in match.group(2) and len(match.group(2).split(":")) == 3:
                                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                            else:
                                return datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                except ValueError as e:
                    logger.debug(
                        f"Failed to parse datetime with pattern {pattern}: {text}, error: {e}"
                    )
                    continue
        logger.warning(f"Could not parse datetime from text: {text}")
        return None

    @staticmethod
    def parse_float(text: str | None) -> float | None:
        """Parse float values from text, handling various formats"""
        if not text or text in ["/", "N/A", "n/a", "--", None]:
            return None
        if isinstance(text, (int, float)):
            return float(text)
        if isinstance(text, str):
            cleaned = re.sub(r"[^\d.-]", "", text.strip())
            if not cleaned:
                return None
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None

    async def scrape_all_data(self) -> FloodOperationsReport:
        """Scrape all available data from the flood status APIs"""
        last_update, narrative = await self.get_narrative_summary()
        lake_levels = await self.scrape_lake_levels()
        river_conditions = await self.scrape_river_conditions()
        floodgate_operations = await self.scrape_floodgate_operations()
        return FloodOperationsReport(
            report_time=datetime.now(),
            last_update=last_update,
            lake_levels=lake_levels,
            river_conditions=river_conditions,
            river_forecasts=[],
            floodgate_operations=floodgate_operations,
        )
