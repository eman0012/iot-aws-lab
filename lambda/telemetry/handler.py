import json
import logging
import uuid
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

import sys
sys.path.insert(0, '/opt/python')

from shared.db_service import DatabaseService
from shared.rabbitmq_service import RabbitMQService
from shared.auth import authenticate_user
from shared.response import api_response, error_response

def main(event, context):
    """Main handler for telemetry endpoints"""
    http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')

    if http_method == 'OPTIONS':
        return api_response(200, {})
    elif http_method == 'POST':
        return post_telemetry(event)
    elif http_method == 'GET':
        return get_telemetry(event)
    elif http_method == 'DELETE':
        return delete_telemetry(event)
    else:
        return error_response(405, "Method not allowed")

def post_telemetry(event):
    """POST /api/telemetry - Submit telemetry data"""
    # Note: Telemetry from IoT devices may not have JWT
    # Validate by deviceId instead

    try:
        body = json.loads(event.get('body', '{}'))
        params = event.get('queryStringParameters', {}) or {}

        device_id = params.get('deviceId') or body.get('deviceId')

        if not device_id:
            return error_response(400, "deviceId required")

        db = DatabaseService()

        # Validate device exists and get owner
        device_owner = db.find_user_by_device(device_id)
        if not device_owner:
            return error_response(404, "Device not found")

        # Create telemetry record
        telemetry_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)

        telemetry_data = {
            "id": telemetry_id,
            "device_id": device_id,
            "timestamp": timestamp,
            "temperature": body.get('temperature'),
            "humidity": body.get('humidity'),
            "pressure": body.get('pressure'),
            "light_level": body.get('lightLevel'),
            "motion_detected": body.get('motionDetected'),
            "sound_level": body.get('soundLevel'),
            "air_quality": body.get('airQuality'),
            "battery_level": body.get('batteryLevel'),
            "image_url": body.get('imageUrl')
        }

        # Send to RabbitMQ for async processing (condition evaluation, storage)
        rabbitmq = RabbitMQService()
        rabbitmq.send_message({
            "type": "telemetry",
            "data": telemetry_data,
            "userId": device_owner
        })

        return api_response(202, {
            "message": "Telemetry queued for processing",
            "telemetryId": telemetry_id,
            "timestamp": timestamp.isoformat()
        })

    except Exception as e:
        logger.exception(f"Post telemetry error: {e}")
        return error_response(500, f"Failed to process telemetry: {str(e)}")

def get_telemetry(event):
    """GET /api/telemetry - Get telemetry history"""
    auth = authenticate_user(event)
    if not auth:
        return error_response(401, "Authentication required")

    try:
        params = event.get('queryStringParameters', {}) or {}
        device_id = params.get('deviceId')

        if not device_id:
            return error_response(400, "deviceId required")

        db = DatabaseService()

        # Verify device ownership
        device_owner = db.find_user_by_device(device_id)
        if not device_owner or device_owner != auth['userId']:
            return error_response(403, "Device not found or not owned by user")

        # Pagination
        limit = int(params.get('limit', 100))
        offset = int(params.get('offset', 0))

        telemetry = db.get_device_telemetry(device_id, limit, offset)

        return api_response(200, {
            "telemetry": telemetry,
            "count": len(telemetry),
            "limit": limit,
            "offset": offset
        })

    except Exception as e:
        logger.exception(f"Get telemetry error: {e}")
        return error_response(500, f"Failed to get telemetry: {str(e)}")

def delete_telemetry(event):
    """DELETE /api/telemetry - Delete telemetry record"""
    auth = authenticate_user(event)
    if not auth:
        return error_response(401, "Authentication required")

    try:
        params = event.get('queryStringParameters', {}) or {}
        telemetry_id = params.get('telemetryId')

        if not telemetry_id:
            body = json.loads(event.get('body', '{}'))
            telemetry_id = body.get('telemetryId')

        if not telemetry_id:
            return error_response(400, "telemetryId required")

        # Get device_id from params
        device_id = params.get('deviceId')
        if not device_id:
            body = json.loads(event.get('body', '{}'))
            device_id = body.get('deviceId')

        if not device_id:
            return error_response(400, "deviceId required")

        db = DatabaseService()

        # Verify device ownership
        device_owner = db.find_user_by_device(device_id)
        if not device_owner or device_owner != auth['userId']:
            return error_response(403, "Device not found or not owned by user")

        success = db.delete_telemetry(telemetry_id, device_id)

        if success:
            return api_response(200, {"message": "Telemetry deleted successfully"})
        else:
            return error_response(404, "Telemetry not found")

    except Exception as e:
        logger.exception(f"Delete telemetry error: {e}")
        return error_response(500, f"Failed to delete telemetry: {str(e)}")
