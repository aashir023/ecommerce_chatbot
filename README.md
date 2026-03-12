# Japan Electronics Chatbot (Local Inference)

This project runs the Japan Electronics customer support chatbot with:
- FastAPI backend
- Vite/React frontend
- Pinecone for retrieval
- Supabase for complaints/service visits
- vLLM for local chat inference via OpenAI-compatible API

## Chatbot Functionality (What It Does)
The chatbot is a customer support assistant for Japan Electronics. It can:
- Answer product questions (price, specs, availability, comparisons) using the product catalogue stored in Pinecone.
- Answer store and policy questions (locations, delivery, FAQs, contact) using the site-content index.
- Detect and open complaint, tracking, and technician-visit flows inside the chat widget.
- Keep short conversational context across turns to handle follow‑ups.

## Quick Start (Docker Compose)
1. Ensure GPU + NVIDIA Container Toolkit is installed.
2. Make sure the vLLM model is cached in `~/.cache/huggingface`.
3. Configure `.env` (see below).
4. Run:
   ```bash
   docker compose up --build
   ```

## Health & Chat Test
```bash
curl -s http://localhost:7860/health
curl -s http://localhost:7860/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_user","message":"hi"}'
```

## Environment Variables (.env)
Required:
- `OPENAI_API_KEY` (used for embeddings)
- `PINECONE_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

Local vLLM:
- `VLLM_BASE_URL=http://vllm:8000/v1`
- `VLLM_API_KEY=local-key`

## Model Options (Llama or Qwen)
You can run either Llama 3.1 8B AWQ or Qwen2.5 7B AWQ.

### Option A: Llama 3.1 8B AWQ
vLLM model repo:
```
hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4
```
Served model name:
```
llama-3.1-8b-awq
```
Update these in:
- `docker-compose.yml` (vLLM command)
- `src/core/config.py` (`CHAT_MODEL`)

### Option B: Qwen2.5 7B AWQ
vLLM model repo:
```
Qwen/Qwen2.5-7B-Instruct-AWQ
```
Served model name:
```
qwen2.5-7b-awq
```
Update these in:
- `docker-compose.yml` (vLLM command)
- `src/core/config.py` (`CHAT_MODEL`)

## Build Notes
- BuildKit pip cache is enabled in Dockerfile.
- Use `DOCKER_BUILDKIT=1` if not already set in your shell.

## Operations (Makefile)
```bash
make up
make up-build
make down
make restart
make logs
make logs-app
make logs-vllm
make prune
```

## Logs
- App logs are in container stdout.
- vLLM logs are in `docker compose logs -f vllm`.

## Architecture
- Backend: `src/main.py`
- Chat pipeline: `src/modules/chat/service.py`
- RAG: `src/modules/rag/service.py`
- Vector store: Pinecone via `src/modules/rag/vector_store.py`

## Notes
- vLLM startup time depends on model load and compilation.
- Prefix caching is enabled in vLLM for faster repeated prompts.
