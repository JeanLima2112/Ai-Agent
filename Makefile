start-dev:
	uvicorn app.main:app --reload

start:
	uvicorn app.main:app

psql-up:
	docker compose up -d

psql-down:
	docker compose down