from src.db.client import get_supabase_client


def insert_request_log(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: str | None = None,
) -> None:
    supabase = get_supabase_client()
    payload = {
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 1),
        "user_id": user_id,
    }
    supabase.table("request_logs").insert(payload).execute()
