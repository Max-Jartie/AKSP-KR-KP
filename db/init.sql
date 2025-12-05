CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS property_mgmt;
CREATE SCHEMA IF NOT EXISTS leasing;

-- =========================
-- 1. AUTH-SERVICE
-- =========================

CREATE TABLE auth.app_user (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'USER' CHECK (role IN ('USER', 'ADMIN')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =========================
-- 2. PROPERTY-SERVICE
-- =========================

CREATE TABLE property_mgmt.property (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,
    description TEXT,
    property_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_property_user
        FOREIGN KEY (user_id)
        REFERENCES auth.app_user(id)
);

CREATE TABLE property_mgmt.unit (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL,
    unit_number VARCHAR(50) NOT NULL,
    area NUMERIC(10, 2),
    floor INT,
    status VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE'
        CHECK (status IN ('AVAILABLE', 'OCCUPIED', 'MAINTENANCE')),
    monthly_rent NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_unit_property
        FOREIGN KEY (property_id)
        REFERENCES property_mgmt.property(id)
        ON DELETE CASCADE,
    CONSTRAINT uq_unit_property_number
        UNIQUE (property_id, unit_number)
);

CREATE INDEX idx_unit_property_id ON property_mgmt.unit(property_id);
CREATE INDEX idx_property_user_id ON property_mgmt.property(user_id);

-- =========================
-- 3. LEASING-SERVICE
-- =========================

CREATE TABLE leasing.lease (
    id SERIAL PRIMARY KEY,
    unit_id INT NOT NULL,
    user_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    monthly_rent NUMERIC(12, 2) NOT NULL,
    status VARCHAR(20) NOT NULL
        CHECK (status IN ('DRAFT', 'ACTIVE', 'COMPLETED', 'CANCELLED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_lease_unit
        FOREIGN KEY (unit_id)
        REFERENCES property_mgmt.unit(id),
    CONSTRAINT fk_lease_user
        FOREIGN KEY (user_id)
        REFERENCES auth.app_user(id)
);

CREATE TABLE leasing.payment (
    id SERIAL PRIMARY KEY,
    lease_id INT NOT NULL,
    payment_date DATE NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    status VARCHAR(20) NOT NULL
        CHECK (status IN ('PLANNED', 'PAID', 'OVERDUE', 'CANCELLED')),
    method VARCHAR(20), -- cash, card, bank_transfer etc.
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_payment_lease
        FOREIGN KEY (lease_id)
        REFERENCES leasing.lease(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_lease_unit_id ON leasing.lease(unit_id);
CREATE INDEX idx_lease_user_id ON leasing.lease(user_id);
CREATE INDEX idx_payment_lease_id ON leasing.payment(lease_id);
