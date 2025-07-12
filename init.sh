#!/bin/sh

echo "Создаем тестовую базу ${DB_TEST}..."

psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE DATABASE ${DB_TEST};"
