from typing import List, Optional

import pandas as pd
import pandera as pa
from pandera import Bool
from pandera.typing import DateTime, Float, Series, String
from pydantic import BaseModel, Field

from brynq_sdk_functions import BrynQPanderaDataFrameModel


# ---------------------------
# Get Schemas
# ---------------------------
class EmployeeCostcenterGet(BrynQPanderaDataFrameModel):
    employee_id: Series[String] = pa.Field(coerce=True, description="Employee ID", alias="employeeId")
    employee_cost_center_id: Series[String] = pa.Field(coerce=True, description="Employee Cost Center ID", alias="employeeCostCenterId")
    cost_center_id: Series[String] = pa.Field(coerce=True, description="Cost Center ID", alias="costCenters.costCenterId")
    cost_centers_code: Series[String] = pa.Field(coerce=True, description="Cost Centers Code", alias="costCenters.code")
    cost_centers_description: Series[String] = pa.Field(coerce=True, description="Cost Centers Description", alias="costCenters.description")
    cost_unit_id: Series[String] = pa.Field(coerce=True, nullable=True, description="Cost Unit ID", alias="costUnits.costUnitId")
    cost_units_code: Series[String] = pa.Field(coerce=True, nullable=True, description="Cost Unit Code", alias="costUnits.code")
    cost_units_description: Series[String] = pa.Field(coerce=True, nullable=True, description="Cost Unit Description", alias="costUnits.description")
    percentage: Series[Float] = pa.Field(coerce=True, description="Percentage", alias="percentage")
    default: Series[Bool] = pa.Field(coerce=True, description="Default", alias="default")
    period_year: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Year", alias="period.year")
    period_period: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Period", alias="period.period")
    created_at: Series[DateTime] = pa.Field(coerce=True, description="Created At", alias="createdAt")

    class _Annotation:
        primary_key = "cost_center_id"
        foreign_keys = {
            "employee_id": {
                "parent_schema": "EmployeeSchema",
                "parent_column": "employee_id",
                "cardinality": "N:1"
            }
        }

class CostcenterGet(BrynQPanderaDataFrameModel):
    cost_center_id: Series[String] = pa.Field(coerce=True, description="Cost Center ID", alias="costCenterId")
    code: Series[String] = pa.Field(coerce=True, description="Code", alias="code")
    description: Series[String] = pa.Field(coerce=True, description="Description", alias="description")

    class _Annotation:
        primary_key = "cost_center_id"

# ---------------------------
# API Response Models (Pydantic)
# ---------------------------
class CostCenter(BaseModel):
    cost_center_id: str = Field(..., description="Cost Center ID", alias="costCenterId")
    code: str = Field(..., description="Cost Center Code", alias="code")
    description: str = Field(..., description="Cost Center Description", alias="description")


class CostUnit(BaseModel):
    cost_unit_id: Optional[str] = Field(None, description="Cost Unit ID", alias="costUnitId")
    code: Optional[str] = Field(None, description="Cost Unit Code", alias="code")
    description: Optional[str] = Field(None, description="Cost Unit Description", alias="description")


class Period(BaseModel):
    period_year: int = Field(..., ge=1900, le=2100, example=2021, description="Year", alias="year")
    period_period: int = Field(..., ge=1, le=53, example=4, description="Period", alias="period")


class EmployeeCostCenterItem(BaseModel):
    employee_cost_center_id: str = Field(..., description="Employee Cost Center ID", alias="employeeCostCenterId")
    cost_centers: CostCenter = Field(..., description="Cost Center", alias="costCenters")
    cost_units: Optional[CostUnit] = Field(None, description="Cost Unit", alias="costUnits")
    percentage: float = Field(..., description="Percentage", alias="percentage")
    default: bool = Field(..., description="Default", alias="default")
    period: Period = Field(..., description="Period", alias="period")
    created_at: str = Field(..., description="Created At", alias="createdAt")


class EmployeeCostCentersList(BaseModel):
    employee_id: str = Field(..., description="Employee ID", alias="employeeId")
    employee_cost_centers: List[EmployeeCostCenterItem] = Field(..., description="Employee Cost Centers", alias="employeeCostCenters")


class EmployeeCostCentersResponse(BaseModel):
    data: List[EmployeeCostCentersList] = Field(..., description="List of employee cost centers")


class CostCentersResponse(BaseModel):
    data: List[CostCenter] = Field(..., description="List of cost centers")


# ---------------------------
# Upload Schemas
# ---------------------------
class CostcenterTable(BaseModel):
    cost_center_id: str = Field(..., example="a405f980-1c4c-42c1-8ddb-2d90c58da0b1", description="Cost Center ID", alias="costCenterId")
    cost_unit_id: Optional[str] = Field(None, example="b505f980-1c4c-42c1-8ddb-2d90c58da0b2", description="Cost Unit ID", alias="costUnitId")
    percentage: Optional[float] = Field(100, example=100, description="Percentage", alias="percentage")
    default: Optional[bool] = Field(True, example=True, description="Default", alias="default")




class EmployeeCostcenterUpdate(BaseModel):
    employee_id: str = Field(..., example="c605f980-1c4c-42c1-8ddb-2d90c58da0b3", description="Employee Cost Center ID", alias="employeeId")
    employee_cost_centers: List[CostcenterTable] = Field(..., description="Employee Cost Centers", alias="employeeCostCenters")
    period_details: Period = Field(..., example=Period(year=2021, period=4), description="Period details", alias="period")

    class Config:
        primary_key = "employee_id"


class EmployeeCostcenterDelete(BaseModel):
    cost_center_id: str = Field(..., example="c605f980-1c4c-42c1-8ddb-2d90c58da0b3", description="Employee Cost Center ID", alias="employeeCostCenterId")

# CostCenter CRUD schemas - These are hypothetical since the API doesn't have create/update/delete endpoints
# but we add them for consistency with other schema files
class CostcenterCreate(BaseModel):
    code: str = Field(..., example="CC001", description="Code", alias="code")
    description: str = Field(..., example="Sales Department", description="Description", alias="description")

class CostcenterUpdate(BaseModel):
    cost_center_id: str = Field(..., example="a405f980-1c4c-42c1-8ddb-2d90c58da0b1", description="Cost Center ID", alias="costCenterId")
    code: str = Field(..., example="CC001", description="Code", alias="code")
    description: str = Field(..., example="Sales Department", description="Description", alias="description")

    class Config:
        primary_key = "costCenterId"

class CostcenterDelete(BaseModel):
    cost_center_id: str = Field(..., example="a405f980-1c4c-42c1-8ddb-2d90c58da0b1", description="Cost Center ID", alias="costCenterId")
