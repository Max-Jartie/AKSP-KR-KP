# PowerShell скрипт для выполнения SQL миграций в Docker контейнере

Write-Host "Выполнение миграции базы данных..." -ForegroundColor Cyan

Get-Content db/migration_owner_to_user.sql | docker-compose exec -T db psql -U rental_user -d rental_db

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Миграция успешно выполнена!" -ForegroundColor Green
} else {
    Write-Host "❌ Ошибка при выполнении миграции" -ForegroundColor Red
    exit 1
}

