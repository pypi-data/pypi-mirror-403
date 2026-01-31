from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DriveClockData(BaseModel):
    """Drive time remaining clock data."""

    driveRemainingDurationMs: int = Field(
        default=0, description="Remaining drive time in milliseconds"
    )


class ShiftClockData(BaseModel):
    """Shift time remaining clock data."""

    shiftRemainingDurationMs: int = Field(
        default=0, description="Remaining shift time in milliseconds"
    )


class CycleClockData(BaseModel):
    """Cycle (weekly) time remaining clock data."""

    cycleStartedAtTime: Optional[str] = Field(
        default=None, description="When the current cycle started"
    )
    cycleRemainingDurationMs: int = Field(
        default=0, description="Remaining cycle time in milliseconds"
    )
    cycleTomorrowDurationMs: int = Field(
        default=0, description="Cycle time available tomorrow in milliseconds"
    )


class BreakClockData(BaseModel):
    """Break time clock data."""

    timeUntilBreakDurationMs: int = Field(
        default=0, description="Time until break required in milliseconds"
    )


class HOSClocks(BaseModel):
    """HOS clocks for a driver."""

    drive: Optional[DriveClockData] = None
    shift: Optional[ShiftClockData] = None
    cycle: Optional[CycleClockData] = None
    break_: Optional[BreakClockData] = Field(default=None, alias="break")


class HOSClocksDriver(BaseModel):
    """Driver info in clocks response."""

    id: str
    name: Optional[str] = None


class HOSClocksEntry(BaseModel):
    """Single entry in HOS clocks response."""

    driver: HOSClocksDriver
    clocks: HOSClocks


class HOSClocksResponse(BaseModel):
    """Response from GET /fleet/hos/clocks."""

    data: list[HOSClocksEntry]



class DailyLogDriver(BaseModel):
    """Driver info in daily log entry."""

    id: str
    name: Optional[str] = None
    timezone: Optional[str] = None
    eldSettings: Optional[dict] = None


class DistanceTraveled(BaseModel):
    """Distance traveled data."""

    driveDistanceMeters: float = Field(
        default=0, description="Distance driven in meters"
    )


class DutyStatusDurations(BaseModel):
    """Duty status durations for a log day."""

    activeDurationMs: int = 0
    onDutyDurationMs: int = 0
    driveDurationMs: int = 0
    offDutyDurationMs: int = 0
    sleeperBerthDurationMs: int = 0
    yardMoveDurationMs: int = 0
    personalConveyanceDurationMs: int = 0
    waitingTimeDurationMs: int = 0


class DailyLogEntry(BaseModel):
    """Single entry in HOS daily logs response."""

    driver: DailyLogDriver
    startTime: Optional[str] = None
    endTime: Optional[str] = None
    distanceTraveled: Optional[DistanceTraveled] = None
    dutyStatusDurations: Optional[DutyStatusDurations] = None


class HOSDailyLogsResponse(BaseModel):
    """Response from GET /fleet/hos/daily-logs."""

    data: list[DailyLogEntry]




class HOSLogEntry(BaseModel):
    """Individual duty status log segment."""

    status: str  # onDuty, offDuty, driving, sleeperBerth, etc.
    logStartMs: int  # Start time in milliseconds since epoch
    logEndMs: Optional[int] = None  # End time in milliseconds
    location: Optional[str] = None
    vehicleId: Optional[str] = None
    logType: Optional[str] = None  # original, manual, etc.


class HOSLogsDriverEntry(BaseModel):
    """HOS logs for a single driver."""

    driverId: str
    events: list[HOSLogEntry] = Field(default_factory=list)


class HOSLogsResponse(BaseModel):
    """Response from GET /fleet/hos/logs."""

    data: list[HOSLogsDriverEntry]




class ShiftData(BaseModel):
    """Shift data for Gravitate ELD payload."""

    total_drive_hours: float
    total_on_duty_hours: float
    total_miles: float


class HOSComplianceData(BaseModel):
    """HOS compliance data for Gravitate ELD payload."""

    drive_time_max_shift_hours: float = 11.0
    on_duty_max_shift_hours: float = 14.0
    weekly_on_duty_hours: float
    weekly_on_duty_max_hours: float  # 60 or 70 depending on cycle
    hos_cycle: str  # "7-day" or "8-day"


class GravitateELDRecord(BaseModel):
    """The format to send to Gravitate's ELD upsert endpoint."""

    source_system: str = "samsara"
    source_id: str
    driver_id: str  # Gravitate internal driver ID
    duty_period_start: datetime
    duty_period_end: datetime
    shift_data: ShiftData
    hos_compliance_data: HOSComplianceData