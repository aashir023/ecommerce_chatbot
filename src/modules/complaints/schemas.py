""" 
This module defines the data models for handling customer complaints in the e-commerce chatbot application.
It includes request and response schemas for logging a new complaint and tracking an existing complaint.
"""

from pydantic import BaseModel, Field
from typing import Literal


class LogComplaintRequest(BaseModel):
    invoiceNumber: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)
    description: str = ""


class LogComplaintResponse(BaseModel):
    success: bool
    message: str
    complaintNumber: str
    status: Literal["pending", "in-progress", "resolved", "escalated"]
    date: str


class TrackComplaintRequest(BaseModel):
    type: Literal["invoice", "phone", "complaint"]
    identifier: str = Field(..., min_length=1)


class TrackComplaintResponse(BaseModel):
    success: bool
    message: str
    complaintNumber: str
    status: Literal["pending", "in-progress", "resolved", "escalated"]
    description: str
    date: str

class OrderPreviewRequest(BaseModel):
    invoiceNumber: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)


class OrderPreviewResponse(BaseModel):
    success: bool
    message: str
    invoiceNumber: str
    orderNo: str
    productName: str
    productDescription: str
