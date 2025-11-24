import psycopg2
from psycopg2.extras import RealDictCursor
import json
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from .config import get_config

class DatabaseService:
    """PostgreSQL database service for all CRUD operations"""

    def __init__(self):
        self.config = get_config()
        self.connection_params = {
            'host': self.config['DB_HOST'],
            'port': self.config['DB_PORT'],
            'database': self.config['DB_NAME'],
            'user': self.config['DB_USERNAME'],
            'password': self.config['DB_PASSWORD'],
            'sslmode': 'require'
        }

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = psycopg2.connect(**self.connection_params)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @contextmanager
    def get_cursor(self):
        """Context manager for database cursors with RealDictCursor"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            try:
                yield cursor
            finally:
                cursor.close()

    # ==================== USER OPERATIONS ====================

    def find_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Find user by ID"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE id = %s",
                (user_id,)
            )
            user = cursor.fetchone()
            return dict(user) if user else None

    def find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find user by email"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE email = %s",
                (email,)
            )
            user = cursor.fetchone()
            return dict(user) if user else None

    def find_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Find user by username"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE username = %s",
                (username,)
            )
            user = cursor.fetchone()
            return dict(user) if user else None

    def find_user_by_email_or_username(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Find user by email or username"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE email = %s OR username = %s",
                (identifier, identifier)
            )
            user = cursor.fetchone()
            return dict(user) if user else None

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (
                    id, username, email, password_hash, first_name, last_name,
                    user_type, notification_methods, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                )
                RETURNING *
                """,
                (
                    user_data['id'],
                    user_data['username'],
                    user_data['email'],
                    user_data['password_hash'],
                    user_data.get('first_name'),
                    user_data.get('last_name'),
                    user_data.get('user_type', 'Standard'),
                    json.dumps(user_data.get('notification_methods', ['email']))
                )
            )
            return dict(cursor.fetchone())

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user profile"""
        # Build dynamic UPDATE query
        set_clauses = []
        values = []

        field_mapping = {
            'firstName': 'first_name',
            'lastName': 'last_name',
            'userType': 'user_type',
            'notificationMethods': 'notification_methods'
        }

        for key, value in updates.items():
            db_field = field_mapping.get(key, key)
            if db_field in ['first_name', 'last_name', 'user_type', 'username', 'email']:
                set_clauses.append(f"{db_field} = %s")
                values.append(value)
            elif db_field == 'notification_methods':
                set_clauses.append(f"{db_field} = %s")
                values.append(json.dumps(value))

        if not set_clauses:
            return self.find_user_by_id(user_id)

        set_clauses.append("updated_at = NOW()")
        values.append(user_id)

        with self.get_cursor() as cursor:
            query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = %s RETURNING *"
            cursor.execute(query, values)
            result = cursor.fetchone()
            return dict(result) if result else None

    def update_password(self, user_id: str, password_hash: str) -> bool:
        """Update user password"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "UPDATE users SET password_hash = %s, updated_at = NOW() WHERE id = %s",
                (password_hash, user_id)
            )
            return cursor.rowcount > 0

    def delete_user(self, user_id: str) -> bool:
        """Delete user and cascade to related records"""
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            return cursor.rowcount > 0

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users (admin only)"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    # ==================== DEVICE OPERATIONS ====================

    def find_device_by_id(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Find device by ID"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM devices WHERE id = %s",
                (device_id,)
            )
            device = cursor.fetchone()
            return dict(device) if device else None

    def find_user_by_device(self, device_id: str) -> Optional[str]:
        """Find user ID that owns a device"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT user_id FROM devices WHERE id = %s",
                (device_id,)
            )
            result = cursor.fetchone()
            return result['user_id'] if result else None

    def get_user_devices(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all devices for a user"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM devices WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def create_device(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new device"""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO devices (
                    id, user_id, device_name, device_type, location,
                    status, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, NOW(), NOW()
                )
                RETURNING *
                """,
                (
                    device_data['id'],
                    device_data['user_id'],
                    device_data['device_name'],
                    device_data.get('device_type'),
                    device_data.get('location'),
                    device_data.get('status', 'active')
                )
            )
            return dict(cursor.fetchone())

    def update_device(self, device_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update device"""
        set_clauses = []
        values = []

        field_mapping = {
            'deviceName': 'device_name',
            'deviceType': 'device_type'
        }

        for key, value in updates.items():
            db_field = field_mapping.get(key, key)
            if db_field in ['device_name', 'device_type', 'location', 'status']:
                set_clauses.append(f"{db_field} = %s")
                values.append(value)

        if not set_clauses:
            return self.find_device_by_id(device_id)

        set_clauses.append("updated_at = NOW()")
        values.append(device_id)

        with self.get_cursor() as cursor:
            query = f"UPDATE devices SET {', '.join(set_clauses)} WHERE id = %s RETURNING *"
            cursor.execute(query, values)
            result = cursor.fetchone()
            return dict(result) if result else None

    def delete_device(self, device_id: str) -> bool:
        """Delete device and cascade to related records"""
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM devices WHERE id = %s", (device_id,))
            return cursor.rowcount > 0

    def transfer_device(self, device_id: str, new_user_id: str) -> Optional[Dict[str, Any]]:
        """Transfer device to another user"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "UPDATE devices SET user_id = %s, updated_at = NOW() WHERE id = %s RETURNING *",
                (new_user_id, device_id)
            )
            result = cursor.fetchone()
            return dict(result) if result else None

    # ==================== TELEMETRY OPERATIONS ====================

    def insert_telemetry(self, telemetry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert telemetry record"""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO telemetry (
                    id, device_id, timestamp, temperature, humidity,
                    pressure, light_level, motion_detected, sound_level,
                    air_quality, battery_level, image_url, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                )
                RETURNING *
                """,
                (
                    telemetry_data['id'],
                    telemetry_data['device_id'],
                    telemetry_data['timestamp'],
                    telemetry_data.get('temperature'),
                    telemetry_data.get('humidity'),
                    telemetry_data.get('pressure'),
                    telemetry_data.get('light_level'),
                    telemetry_data.get('motion_detected'),
                    telemetry_data.get('sound_level'),
                    telemetry_data.get('air_quality'),
                    telemetry_data.get('battery_level'),
                    telemetry_data.get('image_url')
                )
            )
            return dict(cursor.fetchone())

    def get_device_telemetry(
        self,
        device_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get telemetry for a device with pagination"""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM telemetry
                WHERE device_id = %s
                ORDER BY timestamp DESC
                LIMIT %s OFFSET %s
                """,
                (device_id, limit, offset)
            )
            return [dict(row) for row in cursor.fetchall()]

    def delete_telemetry(self, telemetry_id: str, device_id: str) -> bool:
        """Delete telemetry record"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM telemetry WHERE id = %s AND device_id = %s",
                (telemetry_id, device_id)
            )
            return cursor.rowcount > 0

    # ==================== CONDITION OPERATIONS ====================

    def create_condition(self, condition_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new condition"""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO conditions (
                    id, user_id, device_id, condition_name, parameter,
                    operator, threshold, notification_methods, is_active,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                )
                RETURNING *
                """,
                (
                    condition_data['id'],
                    condition_data['user_id'],
                    condition_data.get('device_id'),
                    condition_data['condition_name'],
                    condition_data['parameter'],
                    condition_data['operator'],
                    condition_data['threshold'],
                    json.dumps(condition_data.get('notification_methods', ['email'])),
                    condition_data.get('is_active', True)
                )
            )
            return dict(cursor.fetchone())

    def get_user_conditions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all conditions for a user"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM conditions WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_condition_by_id(self, condition_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get condition by ID for a user"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM conditions WHERE id = %s AND user_id = %s",
                (condition_id, user_id)
            )
            result = cursor.fetchone()
            return dict(result) if result else None

    def update_condition(self, condition_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update condition"""
        set_clauses = []
        values = []

        field_mapping = {
            'conditionName': 'condition_name',
            'deviceId': 'device_id',
            'isActive': 'is_active',
            'notificationMethods': 'notification_methods'
        }

        for key, value in updates.items():
            db_field = field_mapping.get(key, key)
            if db_field in ['condition_name', 'device_id', 'parameter', 'operator', 'threshold', 'is_active']:
                set_clauses.append(f"{db_field} = %s")
                values.append(value)
            elif db_field == 'notification_methods':
                set_clauses.append(f"{db_field} = %s")
                values.append(json.dumps(value))

        if not set_clauses:
            return self.get_condition_by_id(condition_id, user_id)

        set_clauses.append("updated_at = NOW()")
        values.extend([condition_id, user_id])

        with self.get_cursor() as cursor:
            query = f"UPDATE conditions SET {', '.join(set_clauses)} WHERE id = %s AND user_id = %s RETURNING *"
            cursor.execute(query, values)
            result = cursor.fetchone()
            return dict(result) if result else None

    def delete_condition(self, condition_id: str, user_id: str) -> bool:
        """Delete condition"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM conditions WHERE id = %s AND user_id = %s",
                (condition_id, user_id)
            )
            return cursor.rowcount > 0

    def get_active_conditions_for_device(self, device_id: str) -> List[Dict[str, Any]]:
        """Get all active conditions for a device"""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM conditions
                WHERE (device_id = %s OR device_id IS NULL)
                AND is_active = TRUE
                """,
                (device_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    # ==================== ALERT LOG OPERATIONS ====================

    def create_alert_log(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new alert log"""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO alert_logs (
                    id, condition_id, device_id, user_id, triggered_at,
                    parameter, threshold, actual_value, severity, message,
                    is_resolved, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                )
                RETURNING *
                """,
                (
                    alert_data['id'],
                    alert_data['condition_id'],
                    alert_data['device_id'],
                    alert_data['user_id'],
                    alert_data['triggered_at'],
                    alert_data['parameter'],
                    alert_data['threshold'],
                    alert_data['actual_value'],
                    alert_data.get('severity', 'warning'),
                    alert_data.get('message'),
                    alert_data.get('is_resolved', False)
                )
            )
            return dict(cursor.fetchone())

    def get_user_alert_logs(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get alert logs for a user with pagination"""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM alert_logs
                WHERE user_id = %s
                ORDER BY triggered_at DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, limit, offset)
            )
            return [dict(row) for row in cursor.fetchall()]

    def delete_alert_log(self, alert_id: str, user_id: str) -> bool:
        """Delete alert log"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM alert_logs WHERE id = %s AND user_id = %s",
                (alert_id, user_id)
            )
            return cursor.rowcount > 0

    def resolve_alert_log(self, alert_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Mark alert log as resolved"""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE alert_logs
                SET is_resolved = TRUE, resolved_at = NOW()
                WHERE id = %s AND user_id = %s
                RETURNING *
                """,
                (alert_id, user_id)
            )
            result = cursor.fetchone()
            return dict(result) if result else None
