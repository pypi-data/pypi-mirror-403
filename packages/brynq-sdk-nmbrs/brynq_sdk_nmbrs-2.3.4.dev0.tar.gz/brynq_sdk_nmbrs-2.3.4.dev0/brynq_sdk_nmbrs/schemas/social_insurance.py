import pandas as pd
import pandera as pa
from pandera import Bool
from pandera.typing import Series, String, DateTime
from brynq_sdk_functions import BrynQPanderaDataFrameModel
from typing import Optional
from pydantic import BaseModel, Field

# ---------------------------
# Get Schemas
# ---------------------------
class SocialInsuranceGet(BrynQPanderaDataFrameModel):
    employee_id: Series[String] = pa.Field(coerce=True, description="Employee ID", alias="employee_id")
    id: Series[String] = pa.Field(coerce=True, description="SVW Settings ID", alias="Id")
    creation_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Creation Date", alias="CreationDate")
    start_period: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Start Period", alias="StartPeriod")
    start_year: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Start Year", alias="StartYear")
    influence_obliged_insurance: Series[Bool] = pa.Field(coerce=True, nullable=True, description="Whether employee influences obligatory insurance status", alias="InfluenceObligedInsurance")
    wage_cost_benefit: Series[Bool] = pa.Field(coerce=True, nullable=True, description="Eligible for wage cost subsidy (LKV - Loonkostenvoordeel)", alias="WageCostBenefit")
    cao: Series[String] = pa.Field(coerce=True, nullable=True, description="Collectieve Arbeidsovereenkomst (Collective Labor Agreement)", alias="CAO")
    wao_wia: Series[Bool] = pa.Field(coerce=True, nullable=True, description="Disability Insurance (WAO/WIA - Wet Arbeidsongeschiktheid)", alias="Wao_Wia")
    ww: Series[Bool] = pa.Field(coerce=True, nullable=True, description="Unemployment Insurance (WW - Werkloosheidswet)", alias="Ww")
    zw: Series[Bool] = pa.Field(coerce=True, nullable=True, description="Sickness Benefits (ZW - Ziektewet)", alias="Zw")
    income_related_contribution_zvw: Series[Bool] = pa.Field(coerce=True, nullable=True, description="Income Related Health Insurance Contribution (ZVW - Zorgverzekeringswet)", alias="IncomeRelatedContributionZvw")
    code_zvw: Series[String] = pa.Field(coerce=True, nullable=True, description="Health Insurance Code (ZVW)", alias="CodeZvw")
    risk_group: Series[String] = pa.Field(coerce=True, nullable=True, description="Risk Group for premium calculation", alias="RiskGroup")
    sector: Series[String] = pa.Field(coerce=True, nullable=True, description="Industry Sector code", alias="Sector")
    employment_type: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Employment Type", alias="EmploymentType")
    phase_classification: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Phase Classification", alias="PhaseClassification")
    employment_sequence_tax_id: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Employment Sequence Tax ID", alias="EmploymentSequenceTaxId")

    class _Annotation:
        primary_key = "id"
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
class SocialInsuranceUpdate(BaseModel):
    employee_id: int = Field(None, example="1234567890", description="Employee ID", alias="EmployeeId")
    influence_obliged_insurance: Optional[bool] = Field(None, example="1234567890", description="Influence Obliged Insurance", alias="InfluenceObligedInsurance")
    wage_cost_benefit: bool = Field(..., example="1234567890", description="Wage Cost Benefit", alias="WageCostBenefit")
    code_cao: int = Field(..., example="1234567890", description="Code Cao", alias="CodeCao")
    wao_wia: bool = Field(..., example="1234567890", description="Wao Wia", alias="Wao_Wia")
    ww: bool = Field(..., example="1234567890", description="Ww", alias="Ww")
    zw: bool = Field(..., example="1234567890", description="Zw", alias="Zw")
    income_related_contribution_zvw: bool = Field(None, example="1234567890", description="Income Related Contribution Zvw", alias="IncomeRelatedContributionZvw")
    code_zvw: Optional[int] = Field(None, example="1234567890", description="Code Zvw", alias="CodeZvw")
    risk_group: int = Field(None, example="1234567890", description="Risk Group", alias="RiskGroup")
    sector: int = Field(None, example="1234567890", description="Sector", alias="Sector")
    employment_type: int = Field(None, example="1234567890", description="Employment Type", alias="EmploymentType")
    phase_classification: int = Field(None, example="1234567890", description="Phase Classification", alias="PhaseClassification")
    employment_sequence_tax_id: int = Field(None, example="1234567890", description="Employment Sequence Tax Id", alias="EmploymentSequenceTaxId")

    def to_soap_settings(self, soap_client):
        """Convert to SOAP SVWSettings object"""
        SVWSettingsType = soap_client.get_type(
            '{https://api.nmbrs.nl/soap/v3/EmployeeService}SVWSettings'
        )

        # Get payload with alias renaming, excluding employee_id field
        payload = self.model_dump(exclude_none=True, by_alias=True, exclude={'employee_id'})

        return SVWSettingsType(**payload)

    class Config:
        populate_by_name = True
