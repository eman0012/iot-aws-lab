import psycopg2
from psycopg2.extras import RealDictCursor
import json
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from .config import get_config


class DatabaseService:
    """
    PostgreSQL database service for all CRUD operations.
    Schema matches Azure Cosmos DB structure for feature parity.
    """

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
    # Azure: Users collection with fields: _id, userId, username, name, surname,
    #        email, phone, address, emergencyContact, password, type, Devices[], uploadedImages[]

    def find_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Find user by ID (Azure: _id or userId)"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            return self._format_user(user) if user else None

    def find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find user by email"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            return self._format_user(user) if user else None

    def find_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Find user by username"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            return self._format_user(user) if user else None

    def find_user_by_email_or_username(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Find user by email or username (Azure: login supports both)"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE email = %s OR username = %s",
                (identifier, identifier)
            )
            user = cursor.fetchone()
            return self._format_user(user) if user else None

    def find_user_by_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Find user that owns a device (Azure: {"Devices.deviceId": device_id})"""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT u.* FROM users u
                JOIN devices d ON u.id = d.user_id
                WHERE d.device_id = %s
                """,
                (device_id,)
            )
            user = cursor.fetchone()
            return self._format_user(user) if user else None

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user.
        Azure fields: username, name, surname, email, password, phone, address,
                      emergencyContact, type, Devices[], uploadedImages[]
        """
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (
                    id, username, name, surname, email, password_hash,
                    phone, address, emergency_contact, type, uploaded_images,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                )
                RETURNING *
                """,
                (
                    user_data['id'],
                    user_data['username'],
                    user_data['name'],
                    user_data['surname'],
                    user_data['email'],
                    user_data['password_hash'],
                    user_data.get('phone'),
                    user_data.get('address'),
                    user_data.get('emergencyContact'),
                    user_data.get('type', 'user'),
                    json.dumps(user_data.get('uploadedImages', []))
                )
            )
            return self._format_user(cursor.fetchone())

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user profile (Azure: $set operator)"""
        set_clauses = []
        values = []

        # Map Azure camelCase to PostgreSQL snake_case
        field_mapping = {
            'name': 'name',
            'surname': 'surname',
            'username': 'username',
            'email': 'email',
            'phone': 'phone',
            'address': 'address',
            'emergencyContact': 'emergency_contact',
            'type': 'type',
            'uploadedImages': 'uploaded_images'
        }

        for key, value in updates.items():
            db_field = field_mapping.get(key)
            if db_field:
                if db_field == 'uploaded_images':
                    set_clauses.append(f"{db_field} = %s")
                    values.append(json.dumps(value))
                else:
                    set_clauses.append(f"{db_field} = %s")
                    values.append(value)

        if not set_clauses:
            return self.find_user_by_id(user_id)

        set_clauses.append("updated_at = NOW()")
        values.append(user_id)

        with self.get_cursor() as cursor:
            query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = %s RETURNING *"
            cursor.execute(query, values)
            result = cursor.fetchone()
            return self._format_user(result) if result else None

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
            return [self._format_user(row) for row in cursor.fetchall()]

    def _format_user(self, user: Dict) -> Dict[str, Any]:
        """Format user dict to match Azure API response format"""
        if not user:
            return None
        result = dict(user)
        # Add Azure compatibility fields
        result['_id'] = str(result['id'])
        result['userId'] = str(result['id'])
        # Map snake_case back to camelCase for API response
        if 'emergency_contact' in result:
            result['emergencyContact'] = result.pop('emergency_contact')
        if 'uploaded_images' in result:
            result['uploadedImages'] = result.pop('uploaded_images')
        if 'password_hash' in result:
            result['password'] = result.pop('password_hash')
        return result

    # ==================== DEVICE OPERATIONS ====================
    # Azure: Embedded in Users.Devices[] array with fields:
    #        deviceId, deviceName, sensorType, location{name, longitude, latitude},
    #        registrationDate, telemetryData[], status[]

    def find_device_by_id(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Find device by ID"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM devices WHERE device_id = %s", (device_id,))
            device = cursor.fetchone()
            return self._format_device(device) if device else None

    def get_user_devices(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all devices for a user (Azure: user.Devices array)"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM devices WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,)
            )
            return [self._format_device(row) for row in cursor.fetchall()]

    def create_device(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new device.
        Azure: $push to Users.Devices array
        """
        location = device_data.get('location', {})
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO devices (
                    device_id, user_id, device_name, sensor_type,
                    location_name, location_longitude, location_latitude,
                    status, registration_date, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW()
                )
                RETURNING *
                """,
                (
                    device_data['deviceId'],
                    device_data['user_id'],
                    device_data['deviceName'],
                    device_data['sensorType'],
                    location.get('name'),
                    location.get('longitude', ''),
                    location.get('latitude', ''),
                    json.dumps(device_data.get('status', []))
                )
            )
            return self._format_device(cursor.fetchone())

    def update_device(self, device_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update device (Azure: $set on Devices.$)"""
        set_clauses = []
        values = []

        field_mapping = {
            'deviceName': 'device_name',
            'sensorType': 'sensor_type',
            'status': 'status'
        }

        for key, value in updates.items():
            if key == 'location':
                # Handle nested location object
                if 'name' in value:
                    set_clauses.append("location_name = %s")
                    values.append(value['name'])
                if 'longitude' in value:
                    set_clauses.append("location_longitude = %s")
                    values.append(value['longitude'])
                if 'latitude' in value:
                    set_clauses.append("location_latitude = %s")
                    values.append(value['latitude'])
            elif key in field_mapping:
                db_field = field_mapping[key]
                if db_field == 'status':
                    set_clauses.append(f"{db_field} = %s")
                    values.append(json.dumps(value))
                else:
                    set_clauses.append(f"{db_field} = %s")
                    values.append(value)

        if not set_clauses:
            return self.find_device_by_id(device_id)

        set_clauses.append("updated_at = NOW()")
        values.append(device_id)

        with self.get_cursor() as cursor:
            query = f"UPDATE devices SET {', '.join(set_clauses)} WHERE device_id = %s RETURNING *"
            cursor.execute(query, values)
            result = cursor.fetchone()
            return self._format_device(result) if result else None

    def delete_device(self, device_id: str) -> bool:
        """Delete device (Azure: $pull from Users.Devices)"""
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM devices WHERE device_id = %s", (device_id,))
            return cursor.rowcount > 0

    def transfer_device(self, device_id: str, new_user_id: str) -> Optional[Dict[str, Any]]:
        """Transfer device to another user (Azure: admin function)"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "UPDATE devices SET user_id = %s, updated_at = NOW() WHERE device_id = %s RETURNING *",
                (new_user_id, device_id)
            )
            result = cursor.fetchone()
            return self._format_device(result) if result else None

    def _format_device(self, device: Dict) -> Dict[str, Any]:
        """Format device dict to match Azure API response format"""
        if not device:
            return None
        result = {
            'deviceId': device['device_id'],
            'deviceName': device['device_name'],
            'sensorType': device['sensor_type'],
            'location': {
                'name': device['location_name'],
                'longitude': device.get('location_longitude', ''),
                'latitude': device.get('location_latitude', '')
            },
            'registrationDate': device['registration_date'].isoformat() if device.get('registration_date') else None,
            'status': device.get('status', []),
            'user_id': str(device['user_id'])
        }
        return result

    # ==================== TELEMETRY OPERATIONS ====================
    # Azure: Embedded in Devices[].telemetryData[] with fields:
    #        deviceId, userId, eventId, event_date, values[], imageUrl

    def insert_telemetry(self, telemetry_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert telemetry record.
        Azure: $push to Devices.$.telemetryData
        """
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO telemetry (
                    event_id, device_id, user_id, event_date, values, image_url, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, NOW()
                )
                RETURNING *
                """,
                (
                    telemetry_data['eventId'],
                    telemetry_data['deviceId'],
                    telemetry_data['userId'],
                    telemetry_data['event_date'],
                    json.dumps(telemetry_data.get('values', [])),
                    telemetry_data.get('imageUrl')
                )
            )
            return self._format_telemetry(cursor.fetchone())

    def get_device_telemetry(
        self,
        device_id: str,
        event_id: str = None,
        sensor_type: str = None,
        event_date: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get telemetry for a device with optional filters.
        Azure: filters on eventId, sensorType (valueType), eventDate
        """
        query = "SELECT * FROM telemetry WHERE device_id = %s"
        params = [device_id]

        if event_id:
            query += " AND event_id = %s"
            params.append(event_id)
        if event_date:
            query += " AND DATE(event_date) = %s"
            params.append(event_date)

        query += " ORDER BY event_date DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            results = [self._format_telemetry(row) for row in cursor.fetchall()]

            # Filter by sensor_type (valueType) in Python since it's in JSONB
            if sensor_type:
                results = [
                    r for r in results
                    if any(v.get('valueType') == sensor_type for v in r.get('values', []))
                ]

            return results

    def delete_telemetry(self, event_id: str) -> bool:
        """Delete telemetry record (Azure: $pull from Devices.$.telemetryData)"""
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM telemetry WHERE event_id = %s", (event_id,))
            return cursor.rowcount > 0

    def _format_telemetry(self, telemetry: Dict) -> Dict[str, Any]:
        """Format telemetry dict to match Azure API response format"""
        if not telemetry:
            return None
        return {
            'eventId': str(telemetry['event_id']),
            'deviceId': telemetry['device_id'],
            'userId': str(telemetry['user_id']),
            'event_date': telemetry['event_date'].isoformat() if telemetry.get('event_date') else None,
            'values': telemetry.get('values', []),
            'imageUrl': telemetry.get('image_url')
        }

    # ==================== CONDITION OPERATIONS ====================
    # Azure: Conditions collection with fields:
    #        type, userId, deviceId, valueType, minValue, maxValue, exactValue,
    #        unit, scope, notificationMethods[]

    def create_condition(self, condition_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new condition (Azure: insert to Conditions collection)"""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO conditions (
                    id, type, user_id, device_id, value_type,
                    min_value, max_value, exact_value, unit, scope,
                    notification_methods, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                )
                RETURNING *
                """,
                (
                    condition_data.get('id'),
                    'condition',
                    condition_data.get('userId', ''),
                    condition_data.get('deviceId', ''),
                    condition_data['valueType'],
                    condition_data.get('minValue'),
                    condition_data.get('maxValue'),
                    condition_data.get('exactValue'),
                    condition_data.get('unit'),
                    condition_data.get('scope', 'general'),
                    json.dumps(condition_data.get('notificationMethods', ['Log']))
                )
            )
            return self._format_condition(cursor.fetchone())

    def get_conditions(self, device_id: str = None) -> List[Dict[str, Any]]:
        """
        Get conditions with optional device filter.
        Azure: query by type="condition" and optionally deviceId
        """
        with self.get_cursor() as cursor:
            if device_id:
                cursor.execute(
                    "SELECT * FROM conditions WHERE type = 'condition' AND device_id = %s",
                    (device_id,)
                )
            else:
                cursor.execute("SELECT * FROM conditions WHERE type = 'condition'")
            return [self._format_condition(row) for row in cursor.fetchall()]

    def get_condition_by_id(self, condition_id: str) -> Optional[Dict[str, Any]]:
        """Get condition by ID"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM conditions WHERE id = %s AND type = 'condition'",
                (condition_id,)
            )
            result = cursor.fetchone()
            return self._format_condition(result) if result else None

    def get_conditions_by_value_type(self, value_type: str) -> List[Dict[str, Any]]:
        """Get conditions for a specific value type (used by consumer for evaluation)"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM conditions WHERE value_type = %s AND type = 'condition'",
                (value_type,)
            )
            return [self._format_condition(row) for row in cursor.fetchall()]

    def update_condition(self, condition_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update condition (Azure: $set)"""
        set_clauses = []
        values = []

        field_mapping = {
            'valueType': 'value_type',
            'minValue': 'min_value',
            'maxValue': 'max_value',
            'exactValue': 'exact_value',
            'unit': 'unit',
            'scope': 'scope',
            'notificationMethods': 'notification_methods'
        }

        for key, value in updates.items():
            if key in ['conditionId', 'type', '_id']:
                continue
            db_field = field_mapping.get(key, key)
            if db_field == 'notification_methods':
                set_clauses.append(f"{db_field} = %s")
                values.append(json.dumps(value))
            elif db_field in ['value_type', 'min_value', 'max_value', 'exact_value', 'unit', 'scope']:
                set_clauses.append(f"{db_field} = %s")
                values.append(value)

        if not set_clauses:
            return self.get_condition_by_id(condition_id)

        set_clauses.append("updated_at = NOW()")
        values.append(condition_id)

        with self.get_cursor() as cursor:
            query = f"UPDATE conditions SET {', '.join(set_clauses)} WHERE id = %s RETURNING *"
            cursor.execute(query, values)
            result = cursor.fetchone()
            return self._format_condition(result) if result else None

    def delete_condition(self, condition_id: str) -> bool:
        """Delete condition"""
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM conditions WHERE id = %s", (condition_id,))
            return cursor.rowcount > 0

    def _format_condition(self, condition: Dict) -> Dict[str, Any]:
        """Format condition dict to match Azure API response format"""
        if not condition:
            return None
        return {
            '_id': str(condition['id']),
            'type': condition['type'],
            'userId': condition.get('user_id', ''),
            'deviceId': condition.get('device_id', ''),
            'valueType': condition['value_type'],
            'minValue': float(condition['min_value']) if condition.get('min_value') is not None else None,
            'maxValue': float(condition['max_value']) if condition.get('max_value') is not None else None,
            'exactValue': float(condition['exact_value']) if condition.get('exact_value') is not None else None,
            'unit': condition.get('unit'),
            'scope': condition.get('scope', 'general'),
            'notificationMethods': condition.get('notification_methods', ['Log'])
        }

    # ==================== ALERT LOG OPERATIONS ====================
    # Azure: AlertLogs collection with fields:
    #        deviceId, user_id, message, condition (embedded), telemetry_data[], timestamp

    def create_alert_log(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new alert log (Azure: insert to AlertLogs collection)"""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO alert_logs (
                    id, device_id, user_id, message, condition, telemetry_data, timestamp, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, NOW()
                )
                RETURNING *
                """,
                (
                    alert_data.get('id'),
                    alert_data['deviceId'],
                    alert_data['user_id'],
                    alert_data['message'],
                    json.dumps(alert_data['condition']),
                    json.dumps(alert_data['telemetry_data']),
                    alert_data['timestamp']
                )
            )
            return self._format_alert_log(cursor.fetchone())

    def get_alert_logs(self, user_id: str, device_id: str = None) -> List[Dict[str, Any]]:
        """Get alert logs for a user with optional device filter"""
        with self.get_cursor() as cursor:
            if device_id:
                cursor.execute(
                    "SELECT * FROM alert_logs WHERE user_id = %s AND device_id = %s ORDER BY timestamp DESC",
                    (user_id, device_id)
                )
            else:
                cursor.execute(
                    "SELECT * FROM alert_logs WHERE user_id = %s ORDER BY timestamp DESC",
                    (user_id,)
                )
            return [self._format_alert_log(row) for row in cursor.fetchall()]

    def delete_alert_log(self, alert_id: str, user_id: str) -> bool:
        """Delete alert log"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM alert_logs WHERE id = %s AND user_id = %s",
                (alert_id, user_id)
            )
            return cursor.rowcount > 0

    def _format_alert_log(self, alert: Dict) -> Dict[str, Any]:
        """Format alert log dict to match Azure API response format"""
        if not alert:
            return None
        return {
            '_id': str(alert['id']),
            'deviceId': alert['device_id'],
            'user_id': str(alert['user_id']),
            'message': alert['message'],
            'condition': alert.get('condition', {}),
            'telemetry_data': alert.get('telemetry_data', []),
            'timestamp': alert['timestamp'].isoformat() if alert.get('timestamp') else None
        }
