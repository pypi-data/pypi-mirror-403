"""Tests for data models"""

from datetime import datetime

from lcra import (
    DataSource,
    FloodgateOperation,
    FloodOperationsReport,
    LakeLevel,
    RiverCondition,
    TimeFrame,
)


class TestLakeLevel:
    """Test cases for LakeLevel model"""

    def test_lake_level_creation(self):
        """Test creating a LakeLevel instance"""
        level = LakeLevel(
            dam_lake_name="Mansfield/Travis",
            measurement_time=datetime.now(),
            head_elevation=675.17,
            tail_elevation=492.2,
            gate_operations="All gates closed",
        )
        assert level.dam_lake_name == "Mansfield/Travis"
        assert level.head_elevation == 675.17
        assert level.tail_elevation == 492.2

    def test_lake_level_optional_fields(self):
        """Test LakeLevel with optional fields"""
        level = LakeLevel(dam_lake_name="Test/Test")
        assert level.measurement_time is None
        assert level.head_elevation is None
        assert level.tail_elevation is None


class TestRiverCondition:
    """Test cases for RiverCondition model"""

    def test_river_condition_creation(self):
        """Test creating a RiverCondition instance"""
        condition = RiverCondition(
            location="Colorado River at Austin",
            current_stage=4.2,
            current_flow=1250.0,
            bankfull_stage=21.0,
            flood_stage=22.0,
            action_stage=20.0,
            measurement_time=datetime.now(),
            data_source=DataSource.LCRA,
        )
        assert condition.location == "Colorado River at Austin"
        assert condition.current_stage == 4.2
        assert condition.data_source == DataSource.LCRA

    def test_river_condition_optional_fields(self):
        """Test RiverCondition with optional fields"""
        condition = RiverCondition(location="Test Location")
        assert condition.current_stage is None
        assert condition.data_source is None


class TestFloodgateOperation:
    """Test cases for FloodgateOperation model"""

    def test_floodgate_operation_creation(self):
        """Test creating a FloodgateOperation instance"""
        operation = FloodgateOperation(
            dam_name="Mansfield Dam",
            last_update=datetime.now(),
            inflows=850.0,
            gate_operations="All gates closed",
            lake_level_forecast="Lake level expected to remain stable",
            current_elevation=675.17,
        )
        assert operation.dam_name == "Mansfield Dam"
        assert operation.inflows == 850.0


class TestFloodOperationsReport:
    """Test cases for FloodOperationsReport model"""

    def test_flood_operations_report_creation(self):
        """Test creating a FloodOperationsReport instance"""
        report = FloodOperationsReport(
            report_time=datetime.now(),
            last_update=datetime.now(),
            lake_levels=[],
            river_conditions=[],
            river_forecasts=[],
            floodgate_operations=[],
        )
        assert report.report_time is not None
        assert isinstance(report.lake_levels, list)
        assert isinstance(report.river_conditions, list)

    def test_flood_operations_report_with_data(self):
        """Test FloodOperationsReport with actual data"""
        lake_level = LakeLevel(dam_lake_name="Test/Test")
        report = FloodOperationsReport(
            report_time=datetime.now(),
            lake_levels=[lake_level],
        )
        assert len(report.lake_levels) == 1


class TestEnums:
    """Test cases for enum types"""

    def test_data_source_enum(self):
        """Test DataSource enum"""
        assert DataSource.LCRA == "LCRA"
        assert DataSource.USGS == "USGS"
        assert DataSource.NWS == "NWS"
        assert DataSource.COA == "COA"

    def test_time_frame_enum(self):
        """Test TimeFrame enum"""
        assert TimeFrame.HOURS_6 == "6hours"
        assert TimeFrame.DAYS_7 == "7days"
