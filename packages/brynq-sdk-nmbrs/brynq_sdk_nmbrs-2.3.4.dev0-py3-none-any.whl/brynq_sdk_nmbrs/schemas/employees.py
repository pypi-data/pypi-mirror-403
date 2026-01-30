import math
from typing import Annotated, Optional

import pandas as pd
import pandera as pa
import pandera.extensions as extensions
from pandera.typing import DateTime, Series, String
from pydantic import BaseModel, Field, StringConstraints

from brynq_sdk_functions import BrynQPanderaDataFrameModel


# ---------------------------
# Get Schemas
# ---------------------------
class EmployeeGet(BrynQPanderaDataFrameModel):
    employee_id: Series[String] = pa.Field(coerce=True, description="Employee ID", alias="employeeId")
    personal_info_id: Series[String] = pa.Field(coerce=True, description="Personal Info ID", alias="personalInfoId")
    created_at: Series[DateTime] = pa.Field(coerce=True, description="Employee Created At", alias="createdAt", nullable=True)
    employee_number: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Employee Number", alias="basicInfo.employeeNumber")
    first_name: Series[String] = pa.Field(coerce=True, nullable=True, description="First Name", alias="basicInfo.firstName")
    first_name_in_full: Series[String] = pa.Field(coerce=True, nullable=True, description="First Name In Full", alias="basicInfo.firstNameInFull")
    prefix: Series[String] = pa.Field(coerce=True, nullable=True, description="Prefix", alias="basicInfo.prefix")
    initials: Series[String] = pa.Field(coerce=True, nullable=True, description="Initials", alias="basicInfo.initials")
    last_name: Series[String] = pa.Field(coerce=True, description="Last Name", alias="basicInfo.lastName")
    employee_type: Series[String] = pa.Field(coerce=True, description="Employee Type", alias="basicInfo.employeeType")
    birth_date: Series[DateTime] = pa.Field(coerce=True, description="Birth Date", alias="birthInfo.birthDate")
    birth_country_code_iso: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, description="Birth Country Code ISO", alias="birthInfo.birthCountry")
    birth_country: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, description="Birth Country Code ISO", alias="birthInfo.birthCountry.codeISO")
    birth_country_description: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, description="Birth Country Code ISO", alias="birthInfo.birthCountry.description")
    nationality_code_iso: Series[String] = pa.Field(coerce=True, nullable=True, description="Nationality Code ISO", alias="birthInfo.nationality.codeISO")
    gender: Series[String] = pa.Field(coerce=True, nullable=True, description="Gender", alias="birthInfo.gender")
    private_email: Series[String] = pa.Field(coerce=True, nullable=True, description="Private Email", alias="contactInfo.privateEmail")
    business_email: Series[String] = pa.Field(coerce=True, nullable=True, description="Business Email", alias="contactInfo.businessEmail")
    business_phone: Series[String] = pa.Field(coerce=True, nullable=True, description="Business Phone", alias="contactInfo.businessPhone")
    business_mobile_phone: Series[String] = pa.Field(coerce=True, nullable=True, description="Business Mobile Phone", alias="contactInfo.businessMobilePhone")
    private_phone: Series[String] = pa.Field(coerce=True, nullable=True, description="Private Phone", alias="contactInfo.privatePhone")
    private_mobile_phone: Series[String] = pa.Field(coerce=True, nullable=True, description="Private Mobile Phone", alias="contactInfo.privateMobilePhone")
    other_phone: Series[String] = pa.Field(coerce=True, nullable=True, description="Other Phone", alias="contactInfo.otherPhone")
    partner_prefix: Series[String] = pa.Field(coerce=True, nullable=True, description="Partner Prefix", alias="partnerInfo.partnerPrefix")
    partner_name: Series[String] = pa.Field(coerce=True, nullable=True, description="Partner Name", alias="partnerInfo.partnerName")
    period_year: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Year", alias="period.year")
    period_period: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Period", alias="period.period")
    company_id: Series[String] = pa.Field(coerce=True, description="Company ID", alias="companyId")

    class _Annotation:
        primary_key = "employee_id"

# ---------------------------
# Upload Schemas
# ---------------------------
class BasicInfo(BaseModel):
    employee_number: Optional[int] = Field(None, ge=1, example=98072, description="Employee Number", alias="employeeNumber")
    first_name: Optional[str] = Field(None, max_length=50, example="John", description="First Name", alias="firstName")
    first_name_in_full: Optional[str] = Field(None, max_length=100, example="John in Full", description="First Name In Full", alias="firstNameInFull")
    prefix: Optional[str] = Field(None, max_length=50, example="van der", description="Prefix", alias="prefix")
    initials: Optional[str] = Field(None, max_length=50, example="J.D.", description="Initials", alias="initials")
    last_name: str = Field(..., max_length=100, example="Doe", description="Last Name", alias="lastName")
    employee_type: Annotated[
        str,
        StringConstraints(
            pattern=r'^(applicant|newHire|payroll|formerPayroll|external|formerExternal|rejectedApplicant)$',
            strip_whitespace=True
        )
    ] = Field(..., example="payroll", description="Employee Type", alias="employeeType")

class BasicInfoUpdate(BaseModel):
    employee_number: Optional[int] = Field(None, ge=1, example=98072, description="Employee Number", alias="employeeNumber")
    first_name: Optional[str] = Field(None, max_length=50, example="John", description="First Name", alias="firstName")
    first_name_in_full: Optional[str] = Field(None, max_length=100, example="John in Full", description="First Name In Full", alias="firstNameInFull")
    prefix: Optional[str] = Field(None, max_length=50, example="van der", description="Prefix", alias="prefix")
    initials: Optional[str] = Field(None, max_length=50, example="J.D.", description="Initials", alias="initials")
    last_name: str = Field(..., max_length=100, example="Doe", description="Last Name", alias="lastName")

class BirthInfo(BaseModel):
    birth_date: Optional[str] = Field(None, example="1980-02-27", description="Birth Date", alias="birthDate")
    birth_country_code_iso: Optional[Annotated[
        str,
        StringConstraints(
            pattern=r'^[A-Za-z]+$',
            strip_whitespace=True,
            min_length=2,
            max_length=3
        )
    ]] = Field(None, example="NL", description="Birth Country Code ISO", alias="birthCountryCodeISO")
    nationality_code_iso: Optional[Annotated[
        str,
        StringConstraints(
            pattern=r'^[A-Za-z]+$',
            strip_whitespace=True,
            min_length=2,
            max_length=3
        )
    ]] = Field(None, example="PT", description="Nationality Code ISO", alias="nationalityCodeISO")
    deceased_on: Optional[str] = Field(None, example="1980-02-27", description="Deceased On", alias="deceasedOn")
    gender: Optional[Annotated[
        str,
        StringConstraints(
            pattern=r'^(|unspecified|male|female|unknown)$',
            strip_whitespace=True
        )
    ]] = Field(None, example="male", description="Gender", alias="gender")

class ContactInfo(BaseModel):
    private_email: Optional[str] = Field(None, max_length=100, example="doe@private.com", description="Private Email", alias="privateEmail")
    business_email: Optional[str] = Field(None, max_length=100, example="doe@business.com", description="Business Email", alias="businessEmail")
    business_phone: Optional[str] = Field(None, max_length=50, example="+351222222", description="Business Phone", alias="businessPhone")
    business_mobile_phone: Optional[str] = Field(None, max_length=50, example="+351222222", description="Business Mobile Phone", alias="businessMobilePhone")
    private_phone: Optional[str] = Field(None, max_length=50, example="+351222222", description="Private Phone", alias="privatePhone")
    private_mobile_phone: Optional[str] = Field(None, max_length=50, example="+351222222", description="Private Mobile Phone", alias="privateMobilePhone")
    other_phone: Optional[str] = Field(None, max_length=50, example="+351222222", description="Other Phone", alias="otherPhone")

class PartnerInfo(BaseModel):
    partner_prefix: Optional[str] = Field(None, max_length=50, example="Mstr", description="Partner Prefix", alias="partnerPrefix")
    partner_name: Optional[str] = Field(None, max_length=100, example="Jane Doe", description="Partner Name", alias="partnerName")
    ascription_code: Optional[int] = Field(None, ge=0, example=0, description="Ascription Code", alias="ascriptionCode")

class Period(BaseModel):
    period_year: int = Field(..., ge=1900, le=2100, example=2021, description="Year", alias="year")
    period_period: int = Field(..., ge=1, le=53, example=4, description="Period", alias="period")

class AdditionalEmployeeInfo(BaseModel):
    in_service_date: Optional[str] = Field(None, example="2019-08-24", description="In Service Date", alias="inServiceDate")
    default_employee_template: Optional[str] = Field(None, description="Default employee template unique identifier to be only used for employee's of type Payroll", alias="defaultEmployeeTemplate")

class CreateEmployeePersonalInfo(BaseModel):
    basic_info: BasicInfo  = Field(..., alias="basicInfo")
    birth_info: BirthInfo = Field(..., alias="birthInfo")
    contact_info: ContactInfo = Field(..., alias="contactInfo")
    partner_info: PartnerInfo = Field(..., alias="partnerInfo")
    period: Period = Field(..., alias="period")
    created_at: Optional[str] = Field(None, example="2021-07-01T10:15:08Z", description="Created At", alias="createdAt")

class EmployeeCreate(BaseModel):
    personal_info: CreateEmployeePersonalInfo = Field(..., alias="personalInfo")
    additional_employee_info: AdditionalEmployeeInfo = Field(..., alias="additionalEmployeeInfo")

class EmployeeUpdate(BaseModel):
    basic_info: Optional[BasicInfoUpdate] = Field(None, alias="basicInfo")
    birth_info: Optional[BirthInfo] = Field(None, alias="birthInfo")
    contact_info: Optional[ContactInfo] = Field(None, alias="contactInfo")
    partner_info: Optional[PartnerInfo] = Field(None, alias="partnerInfo")
    period: Period = Field(..., alias="period")

class EmployeeDelete(BaseModel):
    employee_id: str = Field(..., example="3054d4cf-b449-489d-8d2e-5dd30e5ab994", description="Employee ID", alias="employeeId")

class BsnGet(BrynQPanderaDataFrameModel):
    employee_id: Series[String] = pa.Field(coerce=True, description="Employee ID", alias="employeeId")
    social_security_number: Series[String] = pa.Field(coerce=True, description="Social Security Number", alias="BSN")
    company_id: Series[String] = pa.Field(coerce=True, description="Company ID", alias="companyId")
    created_at: Series[DateTime] = pa.Field(coerce=True, description="Created At", alias="createdAt")

    class _Annotation:
        primary_key = "employee_id"

class DefaultEmployeeTemplates(BrynQPanderaDataFrameModel):
    default_employee_template: Series[String] = pa.Field(coerce=True, description="UID of the default employee tempalte", alias="defaultEmployeeTemplateId")
    description: Series[String] = pa.Field(coerce=True, description="The description of the default employee template ")
