from typing import Optional

import pandas as pd
import pandera as pa
from pandera import Bool
from pandera.typing import DateTime, Float, Series, String
from pydantic import BaseModel, Field, model_serializer

from brynq_sdk_functions import BrynQPanderaDataFrameModel


# ---------------------------
# Get Schemas
# ---------------------------
class EmployeeWageTaxSettingsGet(BrynQPanderaDataFrameModel):
    employee_id: Series[String] = pa.Field(coerce=True, description="Employee unique identifier", alias="employeeId")
    wage_tax_settings_id: Series[String] = pa.Field(coerce=True, description="Wage Tax Settings ID", alias="wageTaxSettingsId")
    wage_tax: Series[Bool] = pa.Field(coerce=True, nullable=True, description="Wage Tax", alias="wageTax")
    wage_tax_rebate: Series[Bool] = pa.Field(coerce=True, nullable=True, description="Loonheffingskorting", alias="wageTaxRebate")
    single_elderly_discount: Series[Bool] = pa.Field(coerce=True, nullable=True, description="Single Elderly Discount", alias="singleElderlyDiscount")
    color_table: Series[String] = pa.Field(coerce=True, nullable=True, description="List of available color table values for wage tax settings", alias="colorTable")
    period_table: Series[String] = pa.Field(coerce=True, nullable=True, description="List of available period table values for wage tax settings", alias="periodTable")
    income_type: Series[String] = pa.Field(coerce=True, nullable=True, description="Income Type", alias="incomeType")
    special_annual_salary_rate: Series[Float] = pa.Field(coerce=True, nullable=True, description="Loonheffing BT", alias="specialAnnualSalaryRate")
    special_table: Series[String] = pa.Field(coerce=True, nullable=True, description="Special Table", alias="specialTable")
    different_special_rate: Series[String] = pa.Field(coerce=True, nullable=True, description="Afwijkend Bijzonder tarief %", alias="differentSpecialRate")
    calc_30_percent_ruling: Series[String] = pa.Field(coerce=True, nullable=True, description="List of available 30 Percent Ruling Calculation types", alias="Calc30PercentRuling.Cal30PercentRuling")
    calc_30_percent_ruling_end_period: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="30 Percent Ruling End Period", alias="Calc30PercentRuling.endPeriod")
    calc_30_percent_ruling_end_year: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="30 Percent Ruling End Year", alias="Calc30PercentRuling.endYear")
    period_year: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Period Year", alias="period.year")
    period_period: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Period Period", alias="period.period")
    created_at: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Created At", alias="createdAt")

    class _Annotation:
        primary_key = "wage_tax_settings_id"
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

class Calc30PercentRuling(BaseModel):
    cal_30_percent_ruling: Optional[str] = Field(None, example="None", description="List of available 30 Percent Ruling Calculation types", alias="Cal30PercentRuling")
    end_period: Optional[int] = Field(None, example=8, description="30 Percent Ruling End Period", alias="endPeriod")
    end_year: Optional[int] = Field(None, example=2025, description="30 Percent Ruling End Year", alias="endYear")

class EmployeeWageTaxSettingsCreate(BaseModel):
    wage_tax: bool = Field(..., example=True, description="Wage Tax", alias="wageTax")
    wage_tax_rebate: bool = Field(..., example=True, description="Loonheffingskorting", alias="wageTaxRebate")
    single_elderly_discount: bool = Field(..., example=True, description="Single Elderly Discount", alias="singleElderlyDiscount")
    color_table: str = Field(..., example="White", description="List of available color table values for wage tax settings", alias="colorTable")
    period_table: str = Field(..., example="Month", description="List of available period table values for wage tax settings", alias="periodTable")
    income_type: str = Field(..., description="Income Type", alias="incomeType")
    special_annual_salary_rate: Optional[float] = Field(None, ge=0, example=32000.0, description="Loonheffing BT", alias="specialAnnualSalaryRate")
    special_table: str = Field(..., description="Special Table", alias="specialTable")
    different_special_rate: Optional[float] = Field(None, example=0.0, description="Afwijkend Bijzonder tarief %", alias="differentSpecialRate")
    calc_30_percent_ruling: Optional[Calc30PercentRuling] = Field(None, description="Calc 30 percent ruling", alias="Calc30PercentRuling")
    period: Period = Field(..., description="Period", alias="period")

    @model_serializer(mode='wrap')
    def serialize_model(self, serializer, info):
        data = serializer(self)
        # Exclude Calc30PercentRuling if it exists but all its nested fields are None
        if 'Calc30PercentRuling' in data and data['Calc30PercentRuling'] is not None:
            if isinstance(data['Calc30PercentRuling'], dict) and all(v is None for v in data['Calc30PercentRuling'].values()):
                data.pop('Calc30PercentRuling')
        return data
