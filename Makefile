.PHONY: up up-build down restart ps logs logs-app logs-vllm prune

up:
	docker compose up -d

up-build:
	docker compose up --build -d

down:
	docker compose down

restart:
	docker compose down
	docker compose up -d

ps:
	docker compose ps

logs:
	docker compose logs -f

logs-app:
	docker compose logs -f app

logs-vllm:
	docker compose logs -f vllm

prune:
	docker image prune -f
