from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
import pandera as pa
import pandera.extensions as extensions
from pandera import Bool, Int
from pandera.typing import DateTime, Float, Series, String
from pydantic import BaseModel, Field

from brynq_sdk_functions import BrynQPanderaDataFrameModel


# ---------------------------
# Get Schemas
# ---------------------------
class ScheduleGet(BrynQPanderaDataFrameModel):
    schedule_id: Series[String] = pa.Field(coerce=True, description="Schedule ID", alias="scheduleId")
    start_date_schedule: Series[datetime] = pa.Field(coerce=True, description="Start Date", alias="startDate")
    parttime_percentage: Series[Float] = pa.Field(coerce=True, description="Part-Time Percentage", alias="parttimePercentage")
    hours_per_week: Series[Float] = pa.Field(coerce=True, nullable=True, description="Hours per week", alias="hoursPerWeek")
    days_per_week: Series[Float] = pa.Field(coerce=True, nullable=True, description="Days per week", alias="daysPerWeek")

    week1_hours_monday: Series[Float] = pa.Field(coerce=True, description="Week 1 Hours Monday", alias="week1.hoursMonday")
    week1_hours_tuesday: Series[Float] = pa.Field(coerce=True, description="Week 1 Hours Tuesday", alias="week1.hoursTuesday")
    week1_hours_wednesday: Series[Float] = pa.Field(coerce=True, description="Week 1 Hours Wednesday", alias="week1.hoursWednesday")
    week1_hours_thursday: Series[Float] = pa.Field(coerce=True, description="Week 1 Hours Thursday", alias="week1.hoursThursday")
    week1_hours_friday: Series[Float] = pa.Field(coerce=True, description="Week 1 Hours Friday", alias="week1.hoursFriday")
    week1_hours_saturday: Series[Float] = pa.Field(coerce=True, description="Week 1 Hours Saturday", alias="week1.hoursSaturday")
    week1_hours_sunday: Series[Float] = pa.Field(coerce=True, description="Week 1 Hours Sunday", alias="week1.hoursSunday")
    week2_hours_monday: Series[Float] = pa.Field(coerce=True, description="Week 2 Hours Monday", alias="week2.hoursMonday")
    week2_hours_tuesday: Series[Float] = pa.Field(coerce=True, description="Week 2 Hours Tuesday", alias="week2.hoursTuesday")
    week2_hours_wednesday: Series[Float] = pa.Field(coerce=True, description="Week 2 Hours Wednesday", alias="week2.hoursWednesday")
    week2_hours_thursday: Series[Float] = pa.Field(coerce=True, description="Week 2 Hours Thursday", alias="week2.hoursThursday")
    week2_hours_friday: Series[Float] = pa.Field(coerce=True, description="Week 2 Hours Friday", alias="week2.hoursFriday")
    week2_hours_saturday: Series[Float] = pa.Field(coerce=True, description="Week 2 Hours Saturday", alias="week2.hoursSaturday")
    week2_hours_sunday: Series[Float] = pa.Field(coerce=True, description="Week 2 Hours Sunday", alias="week2.hoursSunday")
    created_at: Series[datetime] = pa.Field(coerce=True, description="Created At", alias="createdAt")
    employee_id: Series[String] = pa.Field(coerce=True, description="Employee ID", alias="employeeId")

    class _Annotation:
        primary_key = "schedule_id"
        foreign_keys = {
            "employee_id": {
                "parent_schema": "EmployeeSchema",
                "parent_column": "employee_id",
                "cardinality": "N:1"
            }
        }

# ---------------------------
# Upload Schemas
# ---------------------------
class ScheduleHoursWeek1(BaseModel):
    """Schedule hours for each day of the week"""
    week1_hours_monday: Optional[float] = Field(None, description="Monday hours", alias="hoursMonday")
    week1_hours_tuesday: Optional[float] = Field(None, description="Tuesday hours", alias="hoursTuesday")
    week1_hours_wednesday: Optional[float] = Field(None, description="Wednesday hours", alias="hoursWednesday")
    week1_hours_thursday: Optional[float] = Field(None, description="Thursday hours", alias="hoursThursday")
    week1_hours_friday: Optional[float] = Field(None, description="Friday hours", alias="hoursFriday")
    week1_hours_saturday: Optional[float] = Field(None, description="Saturday hours", alias="hoursSaturday")
    week1_hours_sunday: Optional[float] = Field(None, description="Sunday hours", alias="hoursSunday")

class ScheduleHoursWeek2(BaseModel):
    """Schedule hours for each day of the week"""
    week2_hours_monday: Optional[float] = Field(None, description="Monday hours", alias="hoursMonday")
    week2_hours_tuesday: Optional[float] = Field(None, description="Tuesday hours", alias="hoursTuesday")
    week2_hours_wednesday: Optional[float] = Field(None, description="Wednesday hours", alias="hoursWednesday")
    week2_hours_thursday: Optional[float] = Field(None, description="Thursday hours", alias="hoursThursday")
    week2_hours_friday: Optional[float] = Field(None, description="Friday hours", alias="hoursFriday")
    week2_hours_saturday: Optional[float] = Field(None, description="Saturday hours", alias="hoursSaturday")
    week2_hours_sunday: Optional[float] = Field(None, description="Sunday hours", alias="hoursSunday")

class ScheduleCreate(BaseModel):
    """
    Pydantic model for creating a new schedule
    """
    start_date_schedule: datetime = Field(..., description="Start date of the schedule", example="2021-01-01T09:29:18Z", alias="startDate")
    hours_per_week: Optional[float] = Field(None, description="Hours per week", example=40, alias="hoursPerWeek")
    # split per week schema so we can better sync with get fields.
    week1: Optional[ScheduleHoursWeek1] = Field(None, description="Week 1 schedule hours", alias="week1")
    week2: Optional[ScheduleHoursWeek2] = Field(None, description="Week 2 schedule hours", alias="week2")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "start_date": "2021-01-01T09:29:18Z",
                "hours_per_week": 40,
                "week1": {
                    "hours_monday": 8,
                    "hours_tuesday": 8,
                    "hours_wednesday": 8,
                    "hours_thursday": 8,
                    "hours_friday": 2.5,
                    "hours_saturday": 0,
                    "hours_sunday": 0
                },
                "week2": {
                    "hours_monday": 8,
                    "hours_tuesday": 8,
                    "hours_wednesday": 8,
                    "hours_thursday": 8,
                    "hours_friday": 2.5,
                    "hours_saturday": 0,
                    "hours_sunday": 0
                }
            }
        }


class ScheduleUpdate(BaseModel):
    """
    Pydantic model for updating a schedule via SOAP API
    """
    employee_id: int = Field(..., example=12345, description="Employee ID", alias="employeeId")
    start_date: datetime = Field(..., example="2025-01-01T00:00:00", description="Start date of the schedule", alias="startDate")
    parttime_percentage: float = Field(..., ge=0, le=100, example=100.0, description="Part-time percentage", alias="parttimePercentage")
    company_rooster_nr: Optional[int] = Field(0, example=0, description="Company Rooster Number (schedule template)", alias="companyRoosterNr")
    hours_monday: Optional[float] = Field(0, ge=0, le=24, example=8.0, description="Hours Monday", alias="hoursMonday")
    hours_tuesday: Optional[float] = Field(0, ge=0, le=24, example=8.0, description="Hours Tuesday", alias="hoursTuesday")
    hours_wednesday: Optional[float] = Field(0, ge=0, le=24, example=8.0, description="Hours Wednesday", alias="hoursWednesday")
    hours_thursday: Optional[float] = Field(0, ge=0, le=24, example=8.0, description="Hours Thursday", alias="hoursThursday")
    hours_friday: Optional[float] = Field(0, ge=0, le=24, example=8.0, description="Hours Friday", alias="hoursFriday")
    hours_saturday: Optional[float] = Field(0, ge=0, le=24, example=0.0, description="Hours Saturday", alias="hoursSaturday")
    hours_sunday: Optional[float] = Field(0, ge=0, le=24, example=0.0, description="Hours Sunday", alias="hoursSunday")
    hours_monday2: Optional[float] = Field(0, ge=0, le=24, example=8.0, description="Hours Monday Week 2", alias="hoursMonday2")
    hours_tuesday2: Optional[float] = Field(0, ge=0, le=24, example=8.0, description="Hours Tuesday Week 2", alias="hoursTuesday2")
    hours_wednesday2: Optional[float] = Field(0, ge=0, le=24, example=8.0, description="Hours Wednesday Week 2", alias="hoursWednesday2")
    hours_thursday2: Optional[float] = Field(0, ge=0, le=24, example=8.0, description="Hours Thursday Week 2", alias="hoursThursday2")
    hours_friday2: Optional[float] = Field(0, ge=0, le=24, example=8.0, description="Hours Friday Week 2", alias="hoursFriday2")
    hours_saturday2: Optional[float] = Field(0, ge=0, le=24, example=0.0, description="Hours Saturday Week 2", alias="hoursSaturday2")
    hours_sunday2: Optional[float] = Field(0, ge=0, le=24, example=0.0, description="Hours Sunday Week 2", alias="hoursSunday2")

    def to_soap_schedule(self, soap_client):
        """Convert to SOAP Schedule object"""
        ScheduleType = soap_client.get_type('ns0:Schedule')
        return ScheduleType(
            StartDate=self.start_date,
            ParttimePercentage=self.parttime_percentage,
            HoursMonday=self.hours_monday or 0,
            HoursTuesday=self.hours_tuesday or 0,
            HoursWednesday=self.hours_wednesday or 0,
            HoursThursday=self.hours_thursday or 0,
            HoursFriday=self.hours_friday or 0,
            HoursSaturday=self.hours_saturday or 0,
            HoursSunday=self.hours_sunday or 0,
            HoursMonday2=self.hours_monday2 or 0,
            HoursTuesday2=self.hours_tuesday2 or 0,
            HoursWednesday2=self.hours_wednesday2 or 0,
            HoursThursday2=self.hours_thursday2 or 0,
            HoursFriday2=self.hours_friday2 or 0,
            HoursSaturday2=self.hours_saturday2 or 0,
            HoursSunday2=self.hours_sunday2 or 0
        )

    class Config:
        populate_by_name = True
