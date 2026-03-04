from src.db.client import get_supabase_client


def create_service_visit(payload: dict) -> dict:
    supabase = get_supabase_client()
    resp = supabase.table("service_visits").insert(payload).execute()
    return resp.data[0]


def add_service_visit_event(payload: dict) -> dict:
    supabase = get_supabase_client()
    resp = supabase.table("service_visit_events").insert(payload).execute()
    return resp.data[0]


def get_service_visit_by_visit_no(visit_no: str) -> dict | None:
    supabase = get_supabase_client()
    resp = (
        supabase.table("service_visits")
        .select("*")
        .eq("visit_no", visit_no)
        .limit(1)
        .execute()
    )
    if not resp.data:
        return None
    return resp.data[0]


def find_conflicting_visit(
    invoice_no: str,
    scheduled_date: str,
    scheduled_time: str,
) -> dict | None:
    """
    Returns an existing active visit if same invoice/date/time is already booked.
    Active statuses are treated as blocking.
    """
    supabase = get_supabase_client()
    resp = (
        supabase.table("service_visits")
        .select("*")
        .eq("invoice_no", invoice_no)
        .eq("scheduled_date", scheduled_date)
        .eq("scheduled_time", scheduled_time)
        .in_("status", ["scheduled", "confirmed", "rescheduled"])
        .limit(1)
        .execute()
    )
    if not resp.data:
        return None
    return resp.data[0]
