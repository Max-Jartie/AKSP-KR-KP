# Управление базой данных

## Структура файлов

- `init.sql` - Инициализация схемы базы данных (выполняется автоматически при первом запуске)
- `migration_owner_to_user.sql` - Миграция для переименования колонок owner_id → user_id и tenant_id → user_id

## Выполнение миграций

### Вариант 1: Через скрипт (рекомендуется)

**Windows (PowerShell):**
```powershell
.\scripts\migrate.ps1
```

**Linux/Mac:**
```bash
chmod +x scripts/migrate.sh
./scripts/migrate.sh
```

### Вариант 2: Вручную через Docker

```bash
# Выполнить SQL файл напрямую
docker-compose exec -T db psql -U rental_user -d rental_db < db/migration_owner_to_user.sql

# Или подключиться к БД интерактивно
docker-compose exec db psql -U rental_user -d rental_db
# Затем выполнить команды из migration_owner_to_user.sql
```

### Вариант 3: Пересоздание БД (если данных нет)

⚠️ **ВНИМАНИЕ: Это удалит все данные!**

```bash
# Linux/Mac
chmod +x scripts/init_db.sh
./scripts/init_db.sh

# Windows
docker-compose down -v
docker-compose up -d db
# Подождать 5 секунд
docker-compose exec -T db psql -U rental_user -d rental_db < db/init.sql
```

## Структура базы данных

Система использует PostgreSQL с тремя схемами:
- `auth` - пользователи и аутентификация
- `property_mgmt` - объекты недвижимости и помещения
- `leasing` - договоры аренды и платежи

## Проверка состояния БД

```bash
# Подключиться к БД
docker-compose exec db psql -U rental_user -d rental_db

# Проверить схемы
\dn

# Проверить таблицы в схеме
\dt property_mgmt.*
\dt leasing.*
\dt auth.*

# Проверить структуру таблицы
\d property_mgmt.property
\d leasing.lease
```

## Решение проблем

### Ошибка "column owner_id does not exist"
Выполните миграцию: `.\scripts\migrate.ps1` или `./scripts/migrate.sh`

### Ошибка "column user_id does not exist"
База данных использует старую структуру. Выполните `init.sql` или миграцию.

### База данных не запускается
```bash
docker-compose down -v
docker-compose up -d db
```

