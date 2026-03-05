from fastapi import APIRouter, HTTPException

from src.modules.complaints.schemas import (
    LogComplaintRequest,
    LogComplaintResponse,
    TrackComplaintRequest,
    TrackComplaintResponse,
    OrderPreviewRequest,
    OrderPreviewResponse,
)
from src.modules.complaints.service import (
    log_complaint_from_form,
    track_complaint_from_form,
    preview_order_from_form,
)

router = APIRouter(prefix="/complaints", tags=["Complaints"])

@router.post("/order-preview", response_model=OrderPreviewResponse)
def preview_order(request: OrderPreviewRequest):
    try:
        result = preview_order_from_form(
            invoice_number=request.invoiceNumber.strip(),
            phone=request.phone.strip(),
        )
        return OrderPreviewResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to preview order: {str(exc)}")


@router.post("/log", response_model=LogComplaintResponse)
def log_complaint(request: LogComplaintRequest):
    try:
        result = log_complaint_from_form(
            invoice_number=request.invoiceNumber.strip(),
            phone=request.phone.strip(),
            description=request.description.strip(),
        )
        return LogComplaintResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to log complaint: {str(exc)}")


@router.post("/track", response_model=TrackComplaintResponse)
def track_complaint(request: TrackComplaintRequest):
    try:
        result = track_complaint_from_form(
            track_type=request.type,
            identifier=request.identifier.strip(),
        )
        return TrackComplaintResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to track complaint: {str(exc)}")
