import random
import string
from datetime import datetime


def generate_case_id(prefix: str = "JE") -> str:
    date_part = datetime.utcnow().strftime("%Y%m%d")
    token = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"{prefix}-{date_part}-{token}"
