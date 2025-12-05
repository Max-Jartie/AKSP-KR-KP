-- Миграция: переименование owner_id -> user_id и tenant_id -> user_id
-- Выполните этот скрипт для обновления существующей базы данных

-- 1. Переименование owner_id в user_id в таблице property
ALTER TABLE property_mgmt.property 
    RENAME COLUMN owner_id TO user_id;

-- 2. Переименование constraint
ALTER TABLE property_mgmt.property 
    DROP CONSTRAINT IF EXISTS fk_property_owner;

ALTER TABLE property_mgmt.property 
    ADD CONSTRAINT fk_property_user 
    FOREIGN KEY (user_id) 
    REFERENCES auth.app_user(id);

-- 3. Переименование индекса
DROP INDEX IF EXISTS property_mgmt.idx_property_owner_id;
CREATE INDEX IF NOT EXISTS idx_property_user_id ON property_mgmt.property(user_id);

-- 4. Переименование tenant_id в user_id в таблице lease
ALTER TABLE leasing.lease 
    RENAME COLUMN tenant_id TO user_id;

-- 5. Переименование constraint для lease
ALTER TABLE leasing.lease 
    DROP CONSTRAINT IF EXISTS fk_lease_tenant;

ALTER TABLE leasing.lease 
    ADD CONSTRAINT fk_lease_user 
    FOREIGN KEY (user_id) 
    REFERENCES auth.app_user(id);

-- 6. Переименование индекса для lease
DROP INDEX IF EXISTS leasing.idx_lease_tenant_id;
CREATE INDEX IF NOT EXISTS idx_lease_user_id ON leasing.lease(user_id);

