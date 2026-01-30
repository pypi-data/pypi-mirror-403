import pandas as pd
import pandera as pa
from pandera import Bool
from pandera.typing import Series, String, Float, DateTime
import pandera.extensions as extensions
from brynq_sdk_functions import BrynQPanderaDataFrameModel
from typing import Optional, Annotated
from pydantic import BaseModel, Field, StringConstraints

# ---------------------------
# Get Schemas
# ---------------------------
class DebtorsGet(BrynQPanderaDataFrameModel):
    debtor_id: Series[String] = pa.Field(coerce=True, description="Debtor ID", alias="debtorId")
    number: Series[String] = pa.Field(coerce=True, description="Debtor number", alias="number")
    name: Series[Bool] = pa.Field(coerce=True, description="Debtor name", alias="name")


# ---------------------------
# SOAP Schemas
# ---------------------------
class DebtorCreate(BaseModel):
    """Schema for creating a debtor via SOAP API."""
    number: int = Field(..., ge=1, description="Debtor number", alias="number", example=1001)
    name: str = Field(..., min_length=1, max_length=200, description="Debtor name", alias="name", example="New Debtor Company")

    class Config:
        populate_by_name = True


class DebtorUpdate(BaseModel):
    """Schema for updating a debtor via SOAP API."""
    debtor_id: int = Field(..., description="Debtor ID", alias="debtorId", example=34548)
    number: int = Field(..., ge=1, description="Debtor number", alias="number", example=1001)
    name: str = Field(..., min_length=1, max_length=200, description="Debtor name", alias="name", example="Updated Debtor Company")

    class Config:
        populate_by_name = True