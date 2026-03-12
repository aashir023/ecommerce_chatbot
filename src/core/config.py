import os
from dotenv import load_dotenv

load_dotenv()

# ── VLLM settings ─────────────────────────────────────────────────────────────
VLLM_BASE_URL: str = os.getenv("VLLM_BASE_URL", "http://vllm:8000/v1")
VLLM_API_KEY: str = os.getenv("VLLM_API_KEY", "local-key")

# ── API Keys ──────────────────────────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")

# ── OpenAI settings ───────────────────────────────────────────────────────────
EMBEDDING_MODEL: str = "text-embedding-3-small"   # cheap + accurate
# CHAT_MODEL: str = "gpt-oss-20b"                   # fast + cheap for customer service
# EMBEDDING_DIMENSION: int = 1536                    # text-embedding-3-small output dim

CHAT_MODEL = "llama-3.1-8b-awq"
EMBEDDING_DIMENSION: int = 1536


# ── Pinecone settings ─────────────────────────────────────────────────────────
PINECONE_INDEX_NAME: str = "ecommerce-chatbot"
PINECONE_CLOUD: str = "aws"
PINECONE_REGION: str = "us-east-1"

# ── RAG settings ──────────────────────────────────────────────────────────────
TOP_K_RESULTS: int = 5          # how many products to retrieve per query
INGEST_BATCH_SIZE: int = 100    # vectors per Pinecone upsert call

# ── Validation ────────────────────────────────────────────────────────────────
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in your .env file")
if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY is not set in your .env file")

#--─ Supabase settings ─────────────────────────────────────────────────────────────
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is not set in your .env file")
if not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("SUPABASE_SERVICE_ROLE_KEY is not set in your .env file")
