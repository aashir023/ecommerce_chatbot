from src.db.client import get_supabase_client


def create_complaint(payload: dict) -> dict:
    supabase = get_supabase_client()
    resp = supabase.table("complaints").insert(payload).execute()
    return resp.data[0]


def get_complaint_by_case_id(case_id: str) -> dict | None:
    supabase = get_supabase_client()
    resp = supabase.table("complaints").select("*").eq("case_id", case_id).limit(1).execute()
    if not resp.data:
        return None
    return resp.data[0]


def add_complaint_event(payload: dict) -> dict:
    supabase = get_supabase_client()
    resp = supabase.table("complaint_events").insert(payload).execute()
    return resp.data[0]


def get_complaint_events(complaint_id: str, limit: int = 20) -> list[dict]:
    supabase = get_supabase_client()
    resp = (
        supabase.table("complaint_events")
        .select("*")
        .eq("complaint_id", complaint_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return resp.data or []
