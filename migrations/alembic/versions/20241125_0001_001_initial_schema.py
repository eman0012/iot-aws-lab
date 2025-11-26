"""Initial schema - Azure parity

Revision ID: 001
Revises:
Create Date: 2024-11-25

This migration creates the initial database schema matching
the Azure Cosmos DB structure for feature parity.

Tables:
- users: User accounts with authentication
- devices: IoT devices registered to users
- telemetry: Sensor readings from devices
- conditions: Alert rules/thresholds
- alert_logs: Triggered alert history
- logs: System logging
- image_analysis: Rekognition results
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # ==================== USERS TABLE ====================
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('username', sa.String(100), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('surname', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('emergency_contact', sa.String(255), nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('type', sa.String(20), server_default='user', nullable=False),
        sa.Column('uploaded_images', postgresql.JSONB, server_default='[]'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.CheckConstraint("type IN ('user', 'admin')", name='chk_users_type')
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_type', 'users', ['type'])

    # ==================== DEVICES TABLE ====================
    op.create_table(
        'devices',
        sa.Column('device_id', sa.String(255), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('device_name', sa.String(255), nullable=False),
        sa.Column('sensor_type', sa.String(100), nullable=False),
        sa.Column('location_name', sa.String(255), nullable=False),
        sa.Column('location_longitude', sa.String(50), nullable=True),
        sa.Column('location_latitude', sa.String(50), nullable=True),
        sa.Column('registration_date', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('status', postgresql.JSONB, server_default='[]'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('idx_devices_user_id', 'devices', ['user_id'])
    op.create_index('idx_devices_sensor_type', 'devices', ['sensor_type'])

    # ==================== TELEMETRY TABLE ====================
    op.create_table(
        'telemetry',
        sa.Column('event_id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('device_id', sa.String(255),
                  sa.ForeignKey('devices.device_id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_date', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('values', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('idx_telemetry_device_id', 'telemetry', ['device_id'])
    op.create_index('idx_telemetry_user_id', 'telemetry', ['user_id'])
    op.create_index('idx_telemetry_event_date', 'telemetry', ['event_date'],
                    postgresql_using='btree', postgresql_ops={'event_date': 'DESC'})
    op.create_index('idx_telemetry_device_date', 'telemetry', ['device_id', 'event_date'])

    # ==================== CONDITIONS TABLE ====================
    op.create_table(
        'conditions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('type', sa.String(20), server_default='condition'),
        sa.Column('user_id', sa.String(255), server_default=''),
        sa.Column('device_id', sa.String(255), server_default=''),
        sa.Column('value_type', sa.String(100), nullable=False),
        sa.Column('min_value', sa.Numeric(10, 2), nullable=True),
        sa.Column('max_value', sa.Numeric(10, 2), nullable=True),
        sa.Column('exact_value', sa.Numeric(10, 2), nullable=True),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('scope', sa.String(20), server_default='general'),
        sa.Column('notification_methods', postgresql.JSONB, server_default='["Log"]'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.CheckConstraint("scope IN ('general', 'user', 'device')", name='chk_conditions_scope')
    )
    op.create_index('idx_conditions_user_id', 'conditions', ['user_id'])
    op.create_index('idx_conditions_device_id', 'conditions', ['device_id'])
    op.create_index('idx_conditions_value_type', 'conditions', ['value_type'])
    op.create_index('idx_conditions_scope', 'conditions', ['scope'])

    # ==================== ALERT_LOGS TABLE ====================
    op.create_table(
        'alert_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('device_id', sa.String(255), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('condition', postgresql.JSONB, nullable=False),
        sa.Column('telemetry_data', postgresql.JSONB, nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('idx_alert_logs_user_id', 'alert_logs', ['user_id'])
    op.create_index('idx_alert_logs_device_id', 'alert_logs', ['device_id'])
    op.create_index('idx_alert_logs_timestamp', 'alert_logs', ['timestamp'],
                    postgresql_using='btree', postgresql_ops={'timestamp': 'DESC'})

    # ==================== LOGS TABLE ====================
    op.create_table(
        'logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('level', sa.String(20), nullable=True),
        sa.Column('message', sa.Text, nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('idx_logs_level', 'logs', ['level'])
    op.create_index('idx_logs_created_at', 'logs', ['created_at'],
                    postgresql_using='btree', postgresql_ops={'created_at': 'DESC'})

    # ==================== IMAGE_ANALYSIS TABLE ====================
    op.create_table(
        'image_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('event_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('telemetry.event_id', ondelete='CASCADE'), nullable=True),
        sa.Column('device_id', sa.String(255), nullable=False),
        sa.Column('image_key', sa.String(500), nullable=False),
        sa.Column('content_type', sa.String(50), nullable=True),
        sa.Column('confidence', sa.Numeric(5, 4), nullable=True),
        sa.Column('labels', postgresql.JSONB, nullable=True),
        sa.Column('processed_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('idx_image_analysis_device_id', 'image_analysis', ['device_id'])
    op.create_index('idx_image_analysis_event_id', 'image_analysis', ['event_id'])
    op.create_index('idx_image_analysis_content_type', 'image_analysis', ['content_type'])

    # ==================== TRIGGERS ====================
    # Create update_updated_at function
    op.execute('''
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    ''')

    # Apply triggers
    op.execute('''
        CREATE TRIGGER update_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
    ''')

    op.execute('''
        CREATE TRIGGER update_devices_updated_at
            BEFORE UPDATE ON devices
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
    ''')

    op.execute('''
        CREATE TRIGGER update_conditions_updated_at
            BEFORE UPDATE ON conditions
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
    ''')


def downgrade() -> None:
    # Drop triggers first
    op.execute('DROP TRIGGER IF EXISTS update_conditions_updated_at ON conditions')
    op.execute('DROP TRIGGER IF EXISTS update_devices_updated_at ON devices')
    op.execute('DROP TRIGGER IF EXISTS update_users_updated_at ON users')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('image_analysis')
    op.drop_table('logs')
    op.drop_table('alert_logs')
    op.drop_table('conditions')
    op.drop_table('telemetry')
    op.drop_table('devices')
    op.drop_table('users')
