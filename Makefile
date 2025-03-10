docker:
	docker compose up --build

migrations:
	alembic upgrade head

migration-create:
	alembic revision --autogenerate -m "initial"

test:
	poetry run pytest \
		--strict-markers \
		--tb=short \
		-rsxX \
		-l \
		tests
