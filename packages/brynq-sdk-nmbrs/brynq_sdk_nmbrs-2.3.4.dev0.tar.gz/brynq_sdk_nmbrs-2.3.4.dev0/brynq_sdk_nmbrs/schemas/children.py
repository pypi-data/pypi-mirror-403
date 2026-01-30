import pandas as pd
import pandera as pa
from pandera import Bool
from pandera.typing import Series, String, DateTime
from brynq_sdk_functions import BrynQPanderaDataFrameModel
from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

# ---------------------------
# Get Schemas
# ---------------------------
class ChildrenGet(BrynQPanderaDataFrameModel):
    employee_id: Series[String] = pa.Field(coerce=True, description="Employee ID", alias="employeeId")
    child_id: Series[String] = pa.Field(coerce=True, description="Child ID", alias="childId")
    name: Series[String] = pa.Field(coerce=True, description="Last Name", alias="name")
    first_name: Series[String] = pa.Field(coerce=True, description="First Name", alias="firstName")
    initials: Series[String] = pa.Field(coerce=True, nullable=True, description="Initials", alias="initials")
    gender: Series[String] = pa.Field(coerce=True, description="Gender", alias="gender")
    birthday: Series[DateTime] = pa.Field(coerce=True, description="Birthday", alias="birthday")

    class _Annotation:
        primary_key = "child_id"
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
class ChildCreate(BaseModel):
    """Schema for creating a child via SOAP API."""
    name: str = Field(..., min_length=1, max_length=100, example="Doe", description="Last Name", alias="name")
    first_name: str = Field(..., min_length=1, max_length=100, example="John", description="First Name", alias="firstName")
    initials: Optional[str] = Field(None, max_length=20, example="J.D.", description="Initials", alias="initials")
    gender: Literal["male", "female", "unknown", "undefined"] = Field(..., example="male", description="Gender", alias="gender")
    birthday: datetime = Field(..., example="2020-01-01T00:00:00", description="Birthday", alias="birthday")

    class Config:
        populate_by_name = True


class ChildDelete(BaseModel):
    """Schema for deleting a child via SOAP API."""
    employee_id: int = Field(..., example=12345, description="Employee ID", alias="employeeId")
    child_id: int = Field(..., example=67890, description="Child ID to delete", alias="childId")

    class Config:
        populate_by_name = True


class ChildUpdate(BaseModel):
    """Schema for updating a child via SOAP API."""
    id: int = Field(..., example=67890, description="Child ID to update", alias="id")
    name: str = Field(..., min_length=1, max_length=100, example="Doe", description="Last Name", alias="name")
    first_name: str = Field(..., min_length=1, max_length=100, example="John", description="First Name", alias="firstName")
    initials: Optional[str] = Field(None, max_length=20, example="J.D.", description="Initials", alias="initials")
    gender: Literal["male", "female", "unknown", "undefined"] = Field(..., example="male", description="Gender", alias="gender")
    birthday: datetime = Field(..., example="2020-01-01T00:00:00", description="Birthday", alias="birthday")

    class Config:
        populate_by_name = True

