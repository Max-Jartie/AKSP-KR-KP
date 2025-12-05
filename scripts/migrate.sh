#!/bin/bash
# Скрипт для выполнения SQL миграций в Docker контейнере

echo "Выполнение миграции базы данных..."

docker-compose exec -T db psql -U rental_user -d rental_db < db/migration_owner_to_user.sql

if [ $? -eq 0 ]; then
    echo "✅ Миграция успешно выполнена!"
else
    echo "❌ Ошибка при выполнении миграции"
    exit 1
fi

