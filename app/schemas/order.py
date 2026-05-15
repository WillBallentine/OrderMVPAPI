from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional
import re


class OrderBase(BaseModel):
    patient_first_name: str
    patient_last_name: str
    patient_dob: str

    @field_validator("patient_first_name", "patient_last_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        if len(v) > 100:
            raise ValueError("Name cannot exceed 100 characters")
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", v):
            raise ValueError("Name contains invalid characters")
        return v

    @field_validator("patient_dob")
    @classmethod
    def validate_dob(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Date of birth cannot be empty")
        if len(v) > 50:
            raise ValueError("Date of birth value is too long")
        return v


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    patient_first_name: Optional[str] = None
    patient_last_name: Optional[str] = None
    patient_dob: Optional[str] = None

    @field_validator("patient_first_name", "patient_last_name", mode="before")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        if len(v) > 100:
            raise ValueError("Name cannot exceed 100 characters")
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", v):
            raise ValueError("Name contains invalid characters")
        return v


class OrderResponse(OrderBase):
    id: int
    patient_first_name: str
    patient_last_name: str
    patient_dob: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
