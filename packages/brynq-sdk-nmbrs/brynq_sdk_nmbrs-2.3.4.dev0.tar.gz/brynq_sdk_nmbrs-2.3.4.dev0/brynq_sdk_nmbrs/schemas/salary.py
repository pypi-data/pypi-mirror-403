import math
from datetime import datetime
from typing import Annotated, Optional

import pandas as pd
import pandera as pa
import pandera.extensions as extensions
from pandera import Bool
from pandera.typing import DateTime, Float, Series, String
from pydantic import BaseModel, Field, StringConstraints, model_serializer

from brynq_sdk_functions import BrynQPanderaDataFrameModel


# ---------------------------
# Get Schemas
# ---------------------------
class SalaryGet(BrynQPanderaDataFrameModel):
    employee_id: Series[String] = pa.Field(coerce=True, description="Employee ID", alias="employeeId")
    salary_id: Series[String] = pa.Field(coerce=True, description="Salary ID", alias="salaryId")
    start_date_salary: Series[DateTime] = pa.Field(coerce=True, description="Start Date", alias="startDate")
    salary_type: Series[String] = pa.Field(
        coerce=True,
        isin=[
            "grossFulltimeSalary",
            "grossParttimeSalary",
            "grossHourlyWage",
            "netParttimeSalaryInclWageComp",
            "netParttimeSalaryExclWageComp",
            "netHourlyWageExclWageComp",
            "netHourlyWageInclWageComp",
            "employerCosts"
        ],
        description="Salary Type",
        alias="type"
    )
    salary_amount: Series[Float] = pa.Field(coerce=True, nullable=True, description="Value", alias="value")
    created_at: Series[DateTime] = pa.Field(coerce=True, description="Created At", alias="createdAt")

    class _Annotation:
        primary_key = "salary_id"
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
class SalaryTableUpdate(BaseModel):
    salary_table_id: Optional[str] = Field(None, example="e17a06f1-ae4c-4098-92a6-87976ea7dc9a", description="Salary Table ID", alias="salaryTableId")
    scale_id: Optional[str] = Field(None, example="d5f761c0-20e7-490b-b756-644739fa6120", description="Scale ID", alias="scaleId")
    step_id: Optional[str] = Field(None, example="c9c6feef-cd69-4773-8602-f70fa3b561e4", description="Step ID", alias="stepId")

class SalaryCreate(BaseModel):
    start_date_salary: datetime = Field(..., example="2021-08-01T00:00:00Z", description="Start Date", alias="startDate")
    salary_type: Optional[Annotated[
        str,
        StringConstraints(
            pattern=r'^(grossFulltimeSalary|grossParttimeSalary|grossHourlyWage|netParttimeSalaryInclWageComp|netParttimeSalaryExclWageComp|netHourlyWageExclWageComp|netHourlyWageInclWageComp|employerCosts)$',
            strip_whitespace=True
        )
    ]] = Field(None, example="grossFulltimeSalary", description="Salary Type", alias="type")
    salary_amount: Optional[float] = Field(None, ge=0, example=3480.95, description="Value", alias="value")
    salary_table_update: Optional[SalaryTableUpdate] = Field(default=None, description="Salary Table Update", alias="salaryTable")

    @model_serializer(mode='wrap')
    def serialize_model(self, serializer, info):
        data = serializer(self)
        # Exclude salaryTable if it exists but all its nested fields are None
        if 'salaryTable' in data and data['salaryTable'] is not None:
            if isinstance(data['salaryTable'], dict) and all(v is None for v in data['salaryTable'].values()):
                data.pop('salaryTable')
        return data

    class Config:
        populate_by_name = True


class SalaryUpdate(BaseModel):
    """Schema for updating salary via SOAP API (Salary_UpdateCurrent)."""
    employee_id: int = Field(..., example=12345, description="Employee ID", alias="employeeId")
    salary_value: float = Field(..., ge=0, example=5000.00, description="Salary value (gross amount)", alias="salaryValue")
    salary_type: str = Field(
        "Bruto_Salaris_Fulltime",
        example="Bruto_Salaris_Fulltime",
        description="Salary type enum: Bruto_Salaris_Fulltime, Bruto_Salaris_Parttime, Bruto_Uurloon, etc.",
        alias="salaryType"
    )

    class Config:
        populate_by_name = True

class SalaryTableGet(BrynQPanderaDataFrameModel):
    code: Series[String] = pa.Field(coerce=True, description="Salary Code", alias="Code")
    description: Series[String] = pa.Field(coerce=True, description="Salary Description", alias="Description")
    guid_salary_table: Series[String] = pa.Field(coerce=True, description="GUID Salary table", alias="GuidSalaryTable")
    company_id: Series[String] = pa.Field(coerce=True, description="Company ID", alias="companyId")

class SalaryScalesGet(BrynQPanderaDataFrameModel):
    scale: Series[String] = pa.Field(coerce=True, description="Salary Scale", alias="Scale")
    description: Series[String] = pa.Field(coerce=True, description="Salary Scale Description", alias="SchaalDescription")
    scale_value: Series[String] = pa.Field(coerce=True, description="Salary Scale Value", alias="ScaleValue")
    scale_percentage_max: Series[String] = pa.Field(coerce=True, description="Salary Scale Max Percentage", alias="ScalePercentageMax")
    scale_percentage_min: Series[String] = pa.Field(coerce=True, description="Salary Scale Min Percentage", alias="ScalePercentageMin")
    guid_salary_table_scale: Series[String] = pa.Field(coerce=True, description="GUID Salary table scale", alias="GuidSalaryTableScale")
    company_id: Series[String] = pa.Field(coerce=True, description="Company ID", alias="companyId")

class SalaryStepsGet(BrynQPanderaDataFrameModel):
    step: Series[String] = pa.Field(coerce=True, description="Salary Step", alias="Step")
    step_description: Series[String] = pa.Field(coerce=True, description="Salary Step Description", alias="StepDescription")
    step_value: Series[String] = pa.Field(coerce=True, description="Salary Step Value", alias="StepValue")
    guid_salary_table_step: Series[String] = pa.Field(coerce=True, description="GUID Salary Step table", alias="GuidSalaryTableStep")
    company_id: Series[String] = pa.Field(coerce=True, description="Company ID", alias="companyId")
