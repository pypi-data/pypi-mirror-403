from pydantic import BaseModel, Field
from typing import Optional


class DocumentUpload(BaseModel):
    """Schema for uploading a document to an employee via SOAP API."""
    employee_id: int = Field(..., description="Employee ID", alias="employeeId", example=276967)
    document_name: str = Field(..., description="Document name (with extension)", alias="documentName", example="contract.pdf")
    document_type_guid: str = Field(..., description="Document type GUID", alias="documentTypeGuid", example="00000000-0000-0000-0000-000000000000")

    class Config:
        populate_by_name = True

