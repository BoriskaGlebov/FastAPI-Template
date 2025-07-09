.PHONY: up

up:
	@echo "Подготовка к запуску"
	@if [ -f .env-template ] && [ ! -f .env ]; then \
		echo "Копируем .env-template → .env"; \
		cp .env-template .env; \
	else \
		echo "Либо .env-template отсутствует, либо .env уже существует — пропускаем копирование"; \
	fi
	chmod +x init.sh

	@echo "Запускаем docker compose."
	docker compose up -d --build

down:
	@echo "Сворачиваю проект c удалением всех volumes"
	docker compose down -v

#lint:
#	@echo "🔍 Запуск линтеров через pre-commit..."
#	pre-commit run --all-files
#
#test:
#	@echo "🧪 Запуск тестов..."
#	ENV=local pytest tests
#test-CI:
#	@echo "🧪 Запуск тестов CI..."
#	docker compose exec api pytest tests
#
## Полная проверка: линтеры + тесты
#check: lint test test-CI
#
#push:
#	@echo "📦 Собираем образ из Dockerfile..."
#	docker build -t boristhebladeglebov/girumed-app:latest .
#
#	@echo "🚀 Пушим образ на Docker Hub..."
#	docker push boristhebladeglebov/girumed-app:latest
