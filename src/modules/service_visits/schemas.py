from pydantic import BaseModel, Field
from typing import Literal


class ScheduleVisitRequest(BaseModel):
    invoiceNumber: str | None = None
    phone: str | None = None
    address: str = Field(..., min_length=1, max_length=1000)
    date: str = Field(..., description="YYYY-MM-DD")
    time: str = Field(..., min_length=1, max_length=30)


class ScheduleVisitResponse(BaseModel):
    success: bool
    message: str
    visitNumber: str
    status: Literal["scheduled", "confirmed", "rescheduled", "cancelled", "completed"]
    date: str
    time: str

class ServiceVisitOrderPreviewRequest(BaseModel):
    invoiceNumber: str | None = None
    phone: str | None = None


class ServiceVisitOrderPreviewResponse(BaseModel):
    success: bool
    message: str
    invoiceNumber: str
    orderNo: str
    productName: str
    productDescription: str
