from fastapi import APIRouter, HTTPException

from src.modules.service_visits.schemas import (
    ScheduleVisitRequest,
    ScheduleVisitResponse,
    ServiceVisitOrderPreviewRequest,
    ServiceVisitOrderPreviewResponse,
)
from src.modules.service_visits.service import (
    schedule_visit_from_form,
    preview_order_for_visit,
)

router = APIRouter(prefix="/service-visits", tags=["Service Visits"])

@router.post("/order-preview", response_model=ServiceVisitOrderPreviewResponse)
def preview_order(request: ServiceVisitOrderPreviewRequest):
    try:
        result = preview_order_for_visit(
            invoice_number=(request.invoiceNumber or "").strip(),
            phone=(request.phone or "").strip(),
        )
        return ServiceVisitOrderPreviewResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to preview order: {str(exc)}")

@router.post("/schedule", response_model=ScheduleVisitResponse)
def schedule_visit(request: ScheduleVisitRequest):
    try:
        result = schedule_visit_from_form(
            invoice_number=(request.invoiceNumber or "").strip(),
            phone=(request.phone or "").strip(),
            address=(request.address or "").strip(),
            date=(request.date or "").strip(),
            time=(request.time or "").strip(),
        )
        return ScheduleVisitResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to schedule visit: {str(exc)}")
