"""
LCRA Flood Status Data Models

This module contains all Pydantic models and data structures for the LCRA Flood Status API.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

# ===============================================================================
# Pydantic Models for Data Structures
# ===============================================================================


class TimeFrame(str, Enum):
    """Available time frames for historical data"""

    HOURS_6 = "6hours"
    HOURS_12 = "12hours"
    HOURS_24 = "24hours"
    HOURS_48 = "48hours"
    DAYS_7 = "7days"
    DAYS_14 = "14days"


class DataSource(str, Enum):
    """Data source agencies"""

    LCRA = "LCRA"
    USGS = "USGS"
    NWS = "NWS"
    COA = "COA"  # City of Austin


class LakeLevel(BaseModel):
    """Model for current lake level data at dams"""

    dam_lake_name: str = Field(..., description="Name of the dam or lake")
    measurement_time: datetime | None = Field(None, description="Time of measurement")
    head_elevation: float | None = Field(None, description="Head elevation above dam (feet)")
    tail_elevation: float | None = Field(None, description="Tail elevation below dam (feet)")
    gate_operations: str | None = Field(
        None, description="Current gate operations or spillway status"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dam_lake_name": "Lake Travis at Mansfield Dam",
                "measurement_time": "2025-01-15T10:30:00",
                "head_elevation": 681.5,
                "tail_elevation": 515.2,
                "gate_operations": "Closed",
            }
        }
    )


class RiverCondition(BaseModel):
    """Model for river level conditions"""

    location: str = Field(..., description="River gauge location")
    current_stage: float | None = Field(None, description="Current river stage (feet)")
    current_flow: float | None = Field(None, description="Current flow rate (cfs)")
    bankfull_stage: float | None = Field(None, description="Bankfull stage level (feet)")
    flood_stage: float | None = Field(None, description="Flood stage level (feet)")
    action_stage: float | None = Field(None, description="Action stage level (feet)")
    measurement_time: datetime | None = Field(None, description="Time of measurement")
    data_source: DataSource | None = Field(None, description="Source of the data")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "location": "Colorado River at Austin",
                "current_stage": 4.2,
                "current_flow": 1250.0,
                "bankfull_stage": 21.0,
                "flood_stage": 22.0,
                "action_stage": 20.0,
                "measurement_time": "2025-01-15T10:30:00",
                "data_source": "USGS",
            }
        }
    )


class RiverForecast(BaseModel):
    """Model for river forecast data"""

    location: str = Field(..., description="River gauge location")
    forecast_stage: float | None = Field(None, description="Forecasted stage (feet)")
    forecast_flow: float | None = Field(None, description="Forecasted flow (cfs)")
    forecast_time: datetime | None = Field(None, description="Time of forecast")
    valid_time: datetime | None = Field(None, description="Valid time for forecast")
    issued_by: DataSource | None = Field(None, description="Agency that issued forecast")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "location": "Colorado River at Austin",
                "forecast_stage": 4.8,
                "forecast_flow": 1400.0,
                "forecast_time": "2025-01-15T12:00:00",
                "valid_time": "2025-01-16T06:00:00",
                "issued_by": "NWS",
            }
        }
    )


class HistoricalLakeData(BaseModel):
    """Model for historical lake level data"""

    lake_name: str = Field(..., description="Name of the lake")
    timestamp: datetime = Field(..., description="Timestamp of measurement")
    elevation: float | None = Field(None, description="Lake elevation (feet msl)")
    discharge: float | None = Field(None, description="Discharge rate (cfs)")
    storage: float | None = Field(None, description="Storage volume (acre-feet)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "lake_name": "Lake Travis",
                "timestamp": "2025-01-15T10:30:00",
                "elevation": 681.5,
                "discharge": 1200.0,
                "storage": 1142000.0,
            }
        }
    )


class FloodgateOperation(BaseModel):
    """Model for floodgate operations and forecasts"""

    dam_name: str = Field(..., description="Name of the dam")
    last_update: datetime | None = Field(None, description="Last update time")
    inflows: float | None = Field(None, description="Current inflows (cfs)")
    gate_operations: str | None = Field(None, description="Current gate operations")
    lake_level_forecast: str | None = Field(None, description="Lake level forecast description")
    current_elevation: float | None = Field(None, description="Current lake elevation (feet msl)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dam_name": "Mansfield Dam",
                "last_update": "2025-01-15T10:30:00",
                "inflows": 850.0,
                "gate_operations": "All gates closed",
                "lake_level_forecast": "Lake level expected to remain stable",
                "current_elevation": 681.5,
            }
        }
    )


class FloodOperationsReport(BaseModel):
    """Complete flood operations report"""

    report_time: datetime = Field(..., description="Time the report was generated")
    last_update: datetime | None = Field(None, description="Last data update time")
    lake_levels: list[LakeLevel] = Field(default_factory=list, description="Current lake levels")
    river_conditions: list[RiverCondition] = Field(
        default_factory=list, description="Current river conditions"
    )
    river_forecasts: list[RiverForecast] = Field(
        default_factory=list, description="River forecasts"
    )
    floodgate_operations: list[FloodgateOperation] = Field(
        default_factory=list, description="Floodgate operations"
    )
