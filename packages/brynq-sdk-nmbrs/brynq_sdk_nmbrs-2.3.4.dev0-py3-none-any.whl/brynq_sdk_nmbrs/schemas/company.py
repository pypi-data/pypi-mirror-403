from pydantic import BaseModel, Field
from typing import Optional


class CompanyCreate(BaseModel):
    """Schema for creating a company via SOAP API."""
    debtor_id: int = Field(..., description="Debtor ID", alias="debtorId", example=34548)
    company_name: str = Field(..., min_length=1, max_length=200, description="Company name", alias="companyName", example="New Company BV")
    period_type: int = Field(1, ge=1, le=4, description="Period type (1=Monthly, 2=4-Weekly, 3=Weekly, 4=Quarterly)", alias="periodType", example=1)
    default_company_id: int = Field(0, description="Default company ID to copy settings from (0 for none)", alias="defaultCompanyId", example=0)
    labour_agreement_settings_group_guid: Optional[str] = Field(None, description="Labour agreement settings group GUID", alias="labourAgreementSettingsGroupGuid", example="00000000-0000-0000-0000-000000000000")
    pay_in_advance: bool = Field(False, description="Pay in advance", alias="payInAdvance", example=False)

    class Config:
        populate_by_name = True

