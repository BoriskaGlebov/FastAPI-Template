.PHONY: up down lint lint-mypy test test-CI push check

up:
	@echo "Подготовка к запуску"
	@if [ -f .env-template ] && [ ! -f .env ]; then \
		echo "Копируем .env-template → .env"; \
		cp .env-template .env; \
	else \
		echo "Либо .env-template отсутствует, либо .env уже существует — пропускаем копирование"; \
	fi
	chmod +x init.sh

	@echo "Запускаем docker compose"
	docker compose up -d --build

	@echo "Ожидание готовности базы данных..."
	@until pg_isready -h localhost -p 5432; do \
		echo "Ждём..."; \
		sleep 1; \
	done

	@echo "Применение миграций"
	ENV=local alembic upgrade head
	sleep 5
	@echo "Применение миграций к тестовой БД"
	ENV=local alembic -x db=test upgrade head

down:
	@echo "Сворачиваю проект c удалением всех volumes"
	docker compose down -v

lint:
	@echo "Запуск линтеров через pre-commit..."
	pre-commit run --all-files

test:
	@echo "Запуск тестов локально"
	ENV=local pytest --reruns 2 tests

lint-mypy:
	@mkdir -p reports
	@mypy --config-file=pyproject.toml --linecount-report reports .

	@if [ ! -f reports/linecount.txt ]; then \
		echo "MyPy total report not found"; \
		exit 1; \
	fi

	@total_line=$$(awk '{total+=$$2} END {print total}' reports/linecount.txt); \
	typed_line=$$(awk '{typed+=$$1} END {print typed}' reports/linecount.txt); \
	percent=$$(echo "scale=2; 100 * $$typed_line / $$total_line" | bc); \
	echo "MyPy type покрытие кода: $$percent%"; \
	required=90.00; \
	if (( $$(echo "$$percent < $$required" | bc -l) )); then \
		echo "Type покрытие ($$percent%) ниже цели ($$required%)"; \
		exit 1; \
	else \
		echo "Type  покрытие кода соответствует цели ($$percent%)"; \
	fi

test-CI:
	@echo "Запуск тестов в контейнере"
	docker compose exec api pytest tests

push:
	@echo "Собираем образ из Dockerfile"
	docker build -t boristhebladeglebov/girumed-app:latest .

	@echo "Пушим образ на Docker Hub"
	docker push boristhebladeglebov/girumed-app:latest

check: lint test test-CI push
