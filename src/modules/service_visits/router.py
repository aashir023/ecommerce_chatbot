from fastapi import APIRouter, HTTPException

from src.modules.service_visits.schemas import (
    ScheduleVisitRequest,
    ScheduleVisitResponse,
)
from src.modules.service_visits.service import schedule_visit_from_form

router = APIRouter(prefix="/service-visits", tags=["Service Visits"])


@router.post("/schedule", response_model=ScheduleVisitResponse)
def schedule_visit(request: ScheduleVisitRequest):
    try:
        result = schedule_visit_from_form(
            invoice_number=request.invoiceNumber,
            phone=request.phone,
            address=request.address,
            date=request.date,
            time=request.time,
        )
        return ScheduleVisitResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to schedule visit: {str(exc)}")
