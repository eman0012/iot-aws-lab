-- ============================================
-- IoT Smart Home Platform - Database Schema
-- PostgreSQL 15.x - Azure Parity Version
-- ============================================
-- Run this script after Terraform deployment to initialize the database.
--
-- Connection example:
--   psql -h <rds-endpoint> -U admin -d iotlab -f scripts/init_database.sql
--
-- Schema verified against live Azure Cosmos DB on 2024-11-25
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- ============================================
-- USERS TABLE
-- Matches Azure: Users collection
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    -- Note: Azure stores both _id and userId with same value
    -- In PostgreSQL, id serves both purposes
    username VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,              -- Azure: name (not first_name)
    surname VARCHAR(100) NOT NULL,           -- Azure: surname (not last_name)
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    address TEXT,
    emergency_contact VARCHAR(255),          -- Azure: emergencyContact
    password_hash VARCHAR(255) NOT NULL,     -- Azure: password
    type VARCHAR(20) DEFAULT 'user' CHECK (type IN ('user', 'admin')),  -- Azure: type
    uploaded_images JSONB DEFAULT '[]'::jsonb,  -- Azure: uploadedImages array
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_type ON users(type);

-- ============================================
-- DEVICES TABLE
-- Azure: Embedded in Users.Devices[] array
-- PostgreSQL: Normalized to separate table
-- ============================================
CREATE TABLE IF NOT EXISTS devices (
    device_id VARCHAR(255) PRIMARY KEY,      -- Azure: deviceId (user-provided)
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_name VARCHAR(255) NOT NULL,       -- Azure: deviceName
    sensor_type VARCHAR(100) NOT NULL,       -- Azure: sensorType
    location_name VARCHAR(255) NOT NULL,     -- Azure: location.name
    location_longitude VARCHAR(50),          -- Azure: location.longitude
    location_latitude VARCHAR(50),           -- Azure: location.latitude
    registration_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  -- Azure: registrationDate
    status JSONB DEFAULT '[]'::jsonb,        -- Azure: status array [{valueType, value}]
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_devices_user_id ON devices(user_id);
CREATE INDEX IF NOT EXISTS idx_devices_sensor_type ON devices(sensor_type);

-- ============================================
-- TELEMETRY TABLE
-- Azure: Embedded in Devices[].telemetryData[] array
-- PostgreSQL: Normalized to separate table
-- ============================================
CREATE TABLE IF NOT EXISTS telemetry (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),  -- Azure: eventId
    device_id VARCHAR(255) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,  -- Azure: userId
    event_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),    -- Azure: event_date
    -- Azure: values array - flexible structure [{valueType, value, longitude, latitude}]
    values JSONB NOT NULL DEFAULT '[]'::jsonb,
    image_url VARCHAR(500),                  -- Azure: imageUrl (blob filename)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_telemetry_device_id ON telemetry(device_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_user_id ON telemetry(user_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_event_date ON telemetry(event_date DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_device_date ON telemetry(device_id, event_date DESC);

-- ============================================
-- CONDITIONS TABLE
-- Matches Azure: Conditions collection
-- ============================================
CREATE TABLE IF NOT EXISTS conditions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),  -- Azure: _id (ObjectId)
    type VARCHAR(20) DEFAULT 'condition',    -- Azure: type (always "condition")
    user_id VARCHAR(255) DEFAULT '',         -- Azure: userId (empty string for general)
    device_id VARCHAR(255) DEFAULT '',       -- Azure: deviceId (empty string for general/user)
    value_type VARCHAR(100) NOT NULL,        -- Azure: valueType (e.g., "temperature")
    min_value DECIMAL(10, 2),                -- Azure: minValue
    max_value DECIMAL(10, 2),                -- Azure: maxValue
    exact_value DECIMAL(10, 2),              -- Azure: exactValue
    unit VARCHAR(50),                        -- Azure: unit (e.g., "Celsius")
    scope VARCHAR(20) DEFAULT 'general' CHECK (scope IN ('general', 'user', 'device')),
    notification_methods JSONB DEFAULT '["Log"]'::jsonb,  -- Azure: notificationMethods array
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- Azure validation: at least one threshold must be present
    CONSTRAINT chk_threshold CHECK (
        min_value IS NOT NULL OR max_value IS NOT NULL OR exact_value IS NOT NULL
    )
);

CREATE INDEX IF NOT EXISTS idx_conditions_user_id ON conditions(user_id);
CREATE INDEX IF NOT EXISTS idx_conditions_device_id ON conditions(device_id);
CREATE INDEX IF NOT EXISTS idx_conditions_value_type ON conditions(value_type);
CREATE INDEX IF NOT EXISTS idx_conditions_scope ON conditions(scope);

-- ============================================
-- ALERT_LOGS TABLE
-- Matches Azure: AlertLogs collection
-- ============================================
CREATE TABLE IF NOT EXISTS alert_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),  -- Azure: _id (ObjectId)
    device_id VARCHAR(255) NOT NULL,         -- Azure: deviceId
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,  -- Azure: user_id
    message TEXT NOT NULL,                   -- Azure: message
    -- Azure: condition (embedded full condition object)
    condition JSONB NOT NULL,
    -- Azure: telemetry_data (the values that triggered the alert)
    telemetry_data JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),  -- Azure: timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alert_logs_user_id ON alert_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_alert_logs_device_id ON alert_logs(device_id);
CREATE INDEX IF NOT EXISTS idx_alert_logs_timestamp ON alert_logs(timestamp DESC);

-- ============================================
-- LOGS TABLE (optional - for system logging)
-- Matches Azure: Logs collection
-- ============================================
CREATE TABLE IF NOT EXISTS logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    level VARCHAR(20),
    message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at DESC);

-- ============================================
-- IMAGE_ANALYSIS TABLE
-- For Rekognition results (AWS equivalent of Azure Vision)
-- ============================================
CREATE TABLE IF NOT EXISTS image_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID REFERENCES telemetry(event_id) ON DELETE CASCADE,
    device_id VARCHAR(255) NOT NULL,
    image_key VARCHAR(500) NOT NULL,         -- S3 key
    content_type VARCHAR(50),                -- 'fire', 'animal', 'human', 'flood', 'thunder', 'other'
    confidence DECIMAL(5, 4),                -- 0.0000 to 1.0000
    labels JSONB,                            -- Full Rekognition response
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_image_analysis_device_id ON image_analysis(device_id);
CREATE INDEX IF NOT EXISTS idx_image_analysis_event_id ON image_analysis(event_id);
CREATE INDEX IF NOT EXISTS idx_image_analysis_content_type ON image_analysis(content_type);

-- ============================================
-- FUNCTIONS & TRIGGERS
-- ============================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to tables with updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_devices_updated_at ON devices;
CREATE TRIGGER update_devices_updated_at
    BEFORE UPDATE ON devices
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_conditions_updated_at ON conditions;
CREATE TRIGGER update_conditions_updated_at
    BEFORE UPDATE ON conditions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- VIEWS (for API compatibility)
-- ============================================

-- User with devices count (mimics Azure embedded array)
CREATE OR REPLACE VIEW v_user_summary AS
SELECT
    u.id,
    u.username,
    u.name,
    u.surname,
    u.email,
    u.type,
    COUNT(d.device_id) AS device_count,
    u.created_at
FROM users u
LEFT JOIN devices d ON u.id = d.user_id
GROUP BY u.id;

-- Device with latest telemetry
CREATE OR REPLACE VIEW v_device_status AS
SELECT
    d.device_id,
    d.device_name,
    d.sensor_type,
    d.user_id,
    d.location_name,
    t.event_date AS last_telemetry_date,
    t.values AS last_values
FROM devices d
LEFT JOIN LATERAL (
    SELECT event_date, values
    FROM telemetry
    WHERE device_id = d.device_id
    ORDER BY event_date DESC
    LIMIT 1
) t ON true;

-- ============================================
-- VERIFICATION
-- ============================================

-- List all created tables
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Success message
DO $$ BEGIN RAISE NOTICE 'Database schema initialized successfully with Azure parity!'; END $$;
