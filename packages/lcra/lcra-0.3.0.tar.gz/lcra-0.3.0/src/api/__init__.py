"""
LCRA Flood Status API Routes

This module defines the FastAPI app and all route handlers for the LCRA Flood Status API.
"""

from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from lcra import (
    FloodgateOperation,
    FloodOperationsReport,
    LakeLevel,
    RiverCondition,
)
from scraper import LCRAFloodDataScraper

app = FastAPI(
    title="LCRA Flood Status Data Extractor API",
    description="API for extracting flood and water level data from LCRA hydromet website",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/", response_class=JSONResponse)
async def root():
    """API root endpoint with basic information"""
    return {
        "message": "LCRA Flood Status Data Extractor API",
        "version": "1.0.0",
        "endpoints": {
            "complete_report": "/flood-report",
            "lake_levels": "/lake-levels",
            "river_conditions": "/river-conditions",
            "floodgate_operations": "/floodgate-operations",
            "docs": "/docs",
        },
    }


@app.get("/flood-report", response_model=FloodOperationsReport)
async def get_complete_flood_report():
    """Get complete flood operations report with all available data"""
    async with LCRAFloodDataScraper() as scraper:
        return await scraper.scrape_all_data()


@app.get("/lake-levels", response_model=list[LakeLevel])
async def get_lake_levels():
    """Get current lake levels at dams"""
    async with LCRAFloodDataScraper() as scraper:
        return await scraper.scrape_lake_levels()


@app.get("/river-conditions", response_model=list[RiverCondition])
async def get_river_conditions():
    """Get current river conditions"""
    async with LCRAFloodDataScraper() as scraper:
        return await scraper.scrape_river_conditions()


@app.get("/floodgate-operations", response_model=list[FloodgateOperation])
async def get_floodgate_operations():
    """Get floodgate operations data"""
    async with LCRAFloodDataScraper() as scraper:
        return await scraper.scrape_floodgate_operations()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        async with LCRAFloodDataScraper() as scraper:
            await scraper.fetch_api_data("FloodStatus/GetNarrativeSummary")
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "lcra_accessible": True,
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "lcra_accessible": False,
            "error": str(e),
        }
