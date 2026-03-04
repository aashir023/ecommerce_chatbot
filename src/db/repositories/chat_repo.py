from src.db.client import get_supabase_client


def save_chat_message(external_user_id: str, role: str, content: str) -> None:
    supabase = get_supabase_client()
    payload = {
        "external_user_id": external_user_id,
        "role": role,
        "content": content
    }
    supabase.table("chat_messages").insert(payload).execute()

def get_chat_messages(external_user_id: str, limit: int = 200) -> list[dict]:
    supabase = get_supabase_client()
    resp = (
        supabase.table("chat_messages")
        .select("role,content,created_at")
        .eq("external_user_id", external_user_id)
        .order("created_at", desc=False)
        .limit(limit)
        .execute()
    )
    return resp.data or []
