# Stage 1: build React frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/japan-electronics-helper-main
COPY japan-electronics-helper-main/package*.json ./
RUN npm ci
COPY japan-electronics-helper-main/ ./
RUN npm run build

# Stage 2: backend runtime
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN --mount=type=cache,id=pip-cache,target=/root/.cache/pip \
    pip install -r requirements.txt

COPY . .
COPY --from=frontend-builder /app/japan-electronics-helper-main/dist ./japan-electronics-helper-main/dist

EXPOSE 7860
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "7860", "--log-level", "info", "--access-log"]