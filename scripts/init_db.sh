#!/bin/bash
# Скрипт для пересоздания базы данных (если данных нет)

echo "⚠️  ВНИМАНИЕ: Это удалит все данные в базе!"
read -p "Продолжить? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Отменено"
    exit 0
fi

echo "Остановка контейнеров..."
docker-compose down -v

echo "Запуск контейнеров с новой БД..."
docker-compose up -d db

echo "Ожидание готовности БД..."
sleep 5

echo "Выполнение init.sql..."
docker-compose exec -T db psql -U rental_user -d rental_db < db/init.sql

if [ $? -eq 0 ]; then
    echo "✅ База данных успешно инициализирована!"
else
    echo "❌ Ошибка при инициализации базы данных"
    exit 1
fi

