import math
from datetime import datetime
from typing import Annotated, Optional, Union

import pandas as pd
import pandera as pa
import pandera.extensions as extensions
from pandera import Bool
from pandera.typing import DateTime, Float, Series, String
from pydantic import BaseModel, Field, StringConstraints

from brynq_sdk_functions import BrynQPanderaDataFrameModel


# ---------------------------
# REST API Get Schema (Wage Tax Settings History)
# ---------------------------
class WageTaxSettingsGet(BrynQPanderaDataFrameModel):
    """Schema for REST API: GET /companies/{companyId}/employees/wagetaxsettings"""
    employee_id: Series[String] = pa.Field(coerce=True, description="Employee ID", alias="employeeId")
    wage_tax_setting_id: Series[String] = pa.Field(coerce=True, description="Wage Tax Setting ID", alias="wageTaxSettingId")
    start_date: Series[DateTime] = pa.Field(coerce=True, description="Start Date", alias="startDate")
    created_at: Series[DateTime] = pa.Field(coerce=True, description="Created At", alias="createdAt")
    payroll_tax_reduction: Series[Bool] = pa.Field(coerce=True, nullable=True, description="Payroll Tax Reduction", alias="payrollTaxReduction")
    type_of_income: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Type of Income", alias="typeOfIncome")
    color_table: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Color Table", alias="colorTable")
    period_table: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Period Table", alias="periodTable")
    special_table: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Special Table", alias="specialTable")
    payroll_tax: Series[Bool] = pa.Field(coerce=True, nullable=True, description="Payroll Tax", alias="payrollTax")
    benefit_scheme: Series[Bool] = pa.Field(coerce=True, nullable=True, description="Benefit Scheme", alias="benefitScheme")
    auto_small_jobs: Series[Bool] = pa.Field(coerce=True, nullable=True, description="Auto Small Jobs Regulation", alias="autoSmallJobs")
    yearly_salary: Series[pd.Float64Dtype] = pa.Field(coerce=True, nullable=True, description="Yearly Salary", alias="yearlySalary")
    deviation_special_rate: Series[pd.Float64Dtype] = pa.Field(coerce=True, nullable=True, description="Deviation Special Rate Payroll Tax Deduction", alias="deviationSpecialRatePayrollTaxDeduction")
    code_tax_reduction: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Code Tax Reduction", alias="codeTaxReduction")
    holiday_vouchers: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Holiday Vouchers", alias="holidayVouchers")
    code_30_percent_rule: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Code Calculate 30 Percent Rule", alias="codeCalculate30PercentRule")

    class _Annotation:
        primary_key = "wage_tax_setting_id"
        foreign_keys = {
            "employee_id": {
                "parent_schema": "EmployeeSchema",
                "parent_column": "employee_id",
                "cardinality": "N:1"
            }
        }


class WageTaxSettingsCreate(BaseModel):
    """Schema for REST API: POST /employees/{employeeId}/wagetaxsetting"""
    start_date: datetime = Field(..., example="2024-01-01T00:00:00Z", description="Start Date", alias="startDate")
    payroll_tax_reduction: Optional[bool] = Field(None, example=True, description="Payroll Tax Reduction", alias="payrollTaxReduction")
    type_of_income: Optional[int] = Field(None, example=15, description="Type of Income", alias="typeOfIncome")
    color_table: Optional[int] = Field(None, example=1, description="Color Table", alias="colorTable")
    period_table: Optional[int] = Field(None, example=2, description="Period Table", alias="periodTable")
    special_table: Optional[int] = Field(None, example=0, description="Special Table", alias="specialTable")
    payroll_tax: Optional[bool] = Field(None, example=True, description="Payroll Tax", alias="payrollTax")
    benefit_scheme: Optional[bool] = Field(None, example=True, description="Benefit Scheme", alias="benefitScheme")
    auto_small_jobs: Optional[bool] = Field(None, example=False, description="Auto Small Jobs Regulation", alias="autoSmallJobs")
    yearly_salary: Optional[float] = Field(None, example=45000.00, description="Yearly Salary", alias="yearlySalary")
    deviation_special_rate: Optional[float] = Field(None, example=0.0, description="Deviation Special Rate Payroll Tax Deduction", alias="deviationSpecialRatePayrollTaxDeduction")
    code_tax_reduction: Optional[int] = Field(None, example=0, description="Code Tax Reduction", alias="codeTaxReduction")
    holiday_vouchers: Optional[int] = Field(None, example=0, description="Holiday Vouchers", alias="holidayVouchers")
    code_30_percent_rule: Optional[int] = Field(None, example=0, description="Code Calculate 30 Percent Rule", alias="codeCalculate30PercentRule")

    class Config:
        populate_by_name = True


# ---------------------------
# SOAP API Get Schema (Company Wage Tax List)
# ---------------------------
class CompanyWageTaxGet(BrynQPanderaDataFrameModel):
    wagetax_id: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Loonaangifte ID", alias="LoonaangifteID")
    serial_number: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Serial Number", alias="SerialNumber")
    payment_reference: Series[String] = pa.Field(coerce=True, description="Payment Reference", alias="PaymentReference")
    total_general: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Total General", alias="TotalGeneral")
    period: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Period", alias="Period")
    year: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Year", alias="Year")
    status: Series[String] = pa.Field(coerce=True, description="Status", alias="Status")
    sent_at: Series[DateTime] = pa.Field(coerce=True, description="Sent At", alias="SentAt")
    period_start: Series[String] = pa.Field(coerce=True, description="Tijdvak Start", alias="TijdvakStart")
    period_end: Series[String] = pa.Field(coerce=True, description="Tijdvak End", alias="TijdvakEnd")
    correction_period_start: Series[DateTime] = pa.Field(nullable=True, coerce=True, description="Correction Tijdvak Start", alias="CorrectionTijdvakStart")
    correction_period_end: Series[DateTime] = pa.Field(nullable=True, coerce=True, description="Correction Tijdvak End", alias="CorrectionTijdvakEnd")

# <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
#    <soap:Body>
#       <WageTax_GetListResponse xmlns="https://api.nmbrs.nl/soap/v3/EmployeeService">
#          <WageTax_GetListResult>
#             <WageTaxSettings>
#                <Id>2998190</Id>
#                <JaarloonBT>12144.00</JaarloonBT>
#                <AfwBijzTariefLH>0</AfwBijzTariefLH>
#                <AutoKleineBanenRegeling>true</AutoKleineBanenRegeling>
#                <Loonheffingkorting>true</Loonheffingkorting>
#                <Voordeelreg>true</Voordeelreg>
#                <Loonheffing>true</Loonheffing>
#                <CodeAfdrachtvermindering>0</CodeAfdrachtvermindering>
#                <KleurTabel>1</KleurTabel>
#                <SoortInkomen>15</SoortInkomen>
#                <SpecialeTabel>0</SpecialeTabel>
#                <TijdvakTabel>2</TijdvakTabel>
#                <VakantieBonnen>0</VakantieBonnen>
#                <CodeCalc30PercRule>0</CodeCalc30PercRule>
#             </WageTaxSettings>
#          </WageTax_GetListResult>
#       </WageTax_GetListResponse>
#    </soap:Body>
# </soap:Envelope>

class WageTaxGet(BrynQPanderaDataFrameModel):
    wage_tax_id: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Wage Tax ID", alias="Id")
    employee_id: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Employee ID", alias="EmployeeId")
    yearly_salary: Series[pd.Float64Dtype] = pa.Field(coerce=True, description="Yearly Salary", alias="JaarloonBT")
    deviation_special_rate_payroll_tax_deduction: Series[str] = pa.Field(coerce=True, description="Afw Bijz Tarief LH", alias="AfwBijzTariefLH")
    auto_small_jobs: Series[Bool] = pa.Field(coerce=True, description="Auto Kleine Banen Regeling", alias="AutoKleineBanenRegeling")
    payroll_tax_deduction: Series[Bool] = pa.Field(coerce=True, description="Loonheffingkorting", alias="Loonheffingkorting")
    benefit_scheme: Series[Bool] = pa.Field(coerce=True, description="Voordeelreg", alias="Voordeelreg")
    payroll_tax: Series[Bool] = pa.Field(coerce=True, description="Loonheffing", alias="Loonheffing")
    code_tax_reduction: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Code Afdrachtvermindering", alias="CodeAfdrachtvermindering")
    color_table: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Kleur Tabel", alias="KleurTabel")
    type_of_income: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Soort Inkomen", alias="SoortInkomen")
    special_table: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Speciale Tabel", alias="SpecialeTabel")
    period_table: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Tijdvak Tabel", alias="TijdvakTabel")
    holiday_vouchers: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Vakantie Bonnen", alias="VakantieBonnen")
    code_calculate_30_percent_rule: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Code Calc 30% Rule", alias="CodeCalc30PercRule")

class WageTaxUpdate(BaseModel):
    employee_id: Optional[int] = Field(None, example="1234567890", description="Employee ID", alias="EmployeeId")
    wage_tax_id: Optional[int] = Field(None, example="1234567890", description="Wage Tax Settings ID", alias="Id")
    yearly_salary: Optional[float] = Field(None, example="1234567890", description="Yearly Salary", alias="JaarloonBT")
    deviation_special_rate_payroll_tax_deduction: Optional[float] = Field(None, example="1234567890", description="Afw Bijz Tarief LH", alias="AfwBijzTariefLH")
    auto_small_jobs: Optional[bool] = Field(None, example="1234567890", description="Auto Kleine Banen Regeling", alias="AutoKleineBanenRegeling")
    payroll_tax_deduction: Optional[bool] = Field(None, example="1234567890", description="Loonheffingkorting", alias="Loonheffingkorting")
    benefit_scheme: Optional[bool] = Field(None, example="1234567890", description="Voordeelreg", alias="Voordeelreg")
    payroll_tax: Optional[bool] = Field(None, example="1234567890", description="Loonheffing", alias="Loonheffing")
    code_tax_reduction: Optional[int] = Field(None, example="1234567890", description="Code Afdrachtvermindering", alias="CodeAfdrachtvermindering")
    color_table: Optional[int] = Field(None, example="1234567890", description="Kleur Tabel", alias="KleurTabel")
    type_of_income: Optional[int] = Field(None, example="1234567890", description="Soort Inkomen", alias="SoortInkomen")
    special_table: Optional[int] = Field(None, example="1234567890", description="Speciale Tabel", alias="SpecialeTabel")
    period_table: Optional[int] = Field(None, example="1234567890", description="Tijdvak Tabel", alias="TijdvakTabel")
    holiday_vouchers: Optional[int] = Field(None, example="1234567890", description="Vakantie Bonnen", alias="VakantieBonnen")
    code_calculate_30_percent_rule: Optional[int] = Field(None, example="1234567890", description="Code Calc 30% Rule", alias="CodeCalc30PercRule")

    def to_soap_settings(self, soap_client):
        """Convert to SOAP WageTaxSettings object"""
        WageTaxSettingsType = soap_client.get_type(
            '{https://api.nmbrs.nl/soap/v3/EmployeeService}WageTaxSettings'
        )

        # Get payload with alias renaming, excluding employee_id field
        payload = self.model_dump(exclude_none=True, by_alias=True, exclude={'employee_id'})

        return WageTaxSettingsType(**payload)

    class Config:
        populate_by_name = True
