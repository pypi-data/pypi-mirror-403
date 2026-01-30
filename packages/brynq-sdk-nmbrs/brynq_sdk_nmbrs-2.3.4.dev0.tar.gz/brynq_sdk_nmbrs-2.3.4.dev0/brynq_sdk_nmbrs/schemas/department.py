from datetime import datetime
from typing import Optional

import pandas as pd
import pandera as pa
import pandera.extensions as extensions
from pandera.typing import DateTime, Float, Series, String
from pydantic import BaseModel, Field

from brynq_sdk_functions import BrynQPanderaDataFrameModel


# ---------------------------
# Get Schemas
# ---------------------------
class EmployeeDepartmentGet(BrynQPanderaDataFrameModel):
    employee_id: Series[String] = pa.Field(coerce=True, description="Employee ID", alias="employeeId")
    department_id: Series[String] = pa.Field(coerce=True, description="Department ID", alias="departmentId")
    code: Series[String] = pa.Field(coerce=True, description="Department Code", alias="code")
    description: Series[String] = pa.Field(coerce=True, description="Department Description", alias="description")
    created_at: Series[DateTime] = pa.Field(coerce=True, description="Created At", alias="createdAt")
    period_year: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Year", alias="period.year")
    period_period: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Period", alias="period.period")

    class _Annotation:
        primary_key = "department_id"
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
class Period(BaseModel):
    period_year: int = Field(..., ge=1900, le=2100, example=2021, description="Year", alias="year")
    period_period: int = Field(..., ge=1, le=53, example=4, description="Period", alias="period")

class DepartmentGet(BrynQPanderaDataFrameModel):
    department_id: Series[String] = pa.Field(coerce=True, description="Department ID", alias="departmentId")
    code: Series[String] = pa.Field(coerce=True, description="Department Code", alias="code")
    description: Series[String] = pa.Field(coerce=True, description="Department Description", alias="description")
    created_at: Series[DateTime] = pa.Field(coerce=True, description="Created At", alias="createdAt")
    managers: Series[String] = pa.Field(coerce=True, description="List of managers", alias="managers")

class DepartmentCreate(BaseModel):
    code: int = Field(..., ge=1, example=2, description="Department Code", alias="code")
    description: str = Field(..., min_length=1, max_length=200, example="Sales", description="Department Description", alias="description")

class EmployeeDepartmentUpdate(BaseModel):
    department_id: str = Field(..., example="3214", description="Department ID", alias="departmentId")
    period_details: Period = Field(..., example=Period(year=2021, period=4), description="Period details", alias="periodDetails")

    class Config:
        primary_key = "departmentId"


# ---------------------------
# SOAP Schemas (DebtorService)
# ---------------------------
class DepartmentMasterCreate(BaseModel):
    """Schema for creating a master department via SOAP API."""
    debtor_id: int = Field(..., description="Debtor ID", alias="debtorId", example=34548)
    code: int = Field(..., ge=1, description="Department Code", alias="code", example=101)
    description: str = Field(..., min_length=1, max_length=200, description="Department Description", alias="description", example="Engineering")

    class Config:
        populate_by_name = True


class DepartmentMasterUpdate(BaseModel):
    """Schema for updating a master department via SOAP API."""
    debtor_id: int = Field(..., description="Debtor ID", alias="debtorId", example=34548)
    department_id: int = Field(..., description="Department ID", alias="departmentId", example=12345)
    code: int = Field(..., ge=1, description="Department Code", alias="code", example=101)
    description: str = Field(..., min_length=1, max_length=200, description="Department Description", alias="description", example="Engineering Updated")

    class Config:
        populate_by_name = True


class DepartmentMasterDelete(BaseModel):
    """Schema for deleting a master department via SOAP API."""
    debtor_id: int = Field(..., description="Debtor ID", alias="debtorId", example=34548)
    department_id: int = Field(..., description="Department ID to delete", alias="departmentId", example=12345)

    class Config:
        populate_by_name = True