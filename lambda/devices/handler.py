import json
import logging
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

import sys
sys.path.insert(0, '/opt/python')

from shared.db_service import DatabaseService
from shared.auth import authenticate_user
from shared.response import api_response, error_response

def main(event, context):
    """Main handler for device endpoints"""
    http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')

    if http_method == 'OPTIONS':
        return api_response(200, {})
    elif http_method == 'POST':
        return register_device(event)
    elif http_method == 'GET':
        return get_devices(event)
    elif http_method in ['PUT', 'PATCH']:
        return update_device(event)
    elif http_method == 'DELETE':
        return delete_device(event)
    else:
        return error_response(405, "Method not allowed")

def register_device(event):
    """POST /api/device - Register a new device"""
    auth = authenticate_user(event)
    if not auth:
        return error_response(401, "Authentication required")

    try:
        body = json.loads(event.get('body', '{}'))

        device_name = body.get('deviceName')
        device_type = body.get('deviceType')

        if not all([device_name, device_type]):
            return error_response(400, "Missing required fields: deviceName, deviceType")

        db = DatabaseService()

        # Create device
        device_data = {
            "id": str(uuid.uuid4()),
            "user_id": auth['userId'],
            "device_name": device_name,
            "device_type": device_type,
            "location": body.get('location'),
            "status": body.get('status', 'active')
        }

        device = db.create_device(device_data)

        return api_response(201, {
            "message": "Device registered successfully",
            "device": device
        })

    except Exception as e:
        logger.exception(f"Register device error: {e}")
        return error_response(500, f"Failed to register device: {str(e)}")

def get_devices(event):
    """GET /api/devices - Get user's devices"""
    auth = authenticate_user(event)
    if not auth:
        return error_response(401, "Authentication required")

    try:
        db = DatabaseService()
        devices = db.get_user_devices(auth['userId'])

        return api_response(200, {
            "devices": devices,
            "count": len(devices)
        })

    except Exception as e:
        logger.exception(f"Get devices error: {e}")
        return error_response(500, f"Failed to get devices: {str(e)}")

def update_device(event):
    """PUT/PATCH /api/device - Update device"""
    auth = authenticate_user(event)
    if not auth:
        return error_response(401, "Authentication required")

    try:
        body = json.loads(event.get('body', '{}'))
        params = event.get('queryStringParameters', {}) or {}

        device_id = params.get('deviceId') or body.get('deviceId')
        if not device_id:
            return error_response(400, "deviceId required")

        # Remove deviceId from update data
        update_data = {k: v for k, v in body.items() if k != 'deviceId'}

        if not update_data:
            return error_response(400, "No update data provided")

        db = DatabaseService()

        # Verify ownership
        device_owner = db.find_user_by_device(device_id)
        if not device_owner or device_owner != auth['userId']:
            return error_response(403, "Device not found or not owned by user")

        updated_device = db.update_device(device_id, update_data)

        if updated_device:
            return api_response(200, {
                "message": "Device updated successfully",
                "device": updated_device
            })
        else:
            return error_response(404, "Device not found")

    except Exception as e:
        logger.exception(f"Update device error: {e}")
        return error_response(500, f"Failed to update device: {str(e)}")

def delete_device(event):
    """DELETE /api/device - Delete device"""
    auth = authenticate_user(event)
    if not auth:
        return error_response(401, "Authentication required")

    try:
        params = event.get('queryStringParameters', {}) or {}
        device_id = params.get('deviceId')

        if not device_id:
            body = json.loads(event.get('body', '{}'))
            device_id = body.get('deviceId')

        if not device_id:
            return error_response(400, "deviceId required")

        db = DatabaseService()

        # Verify ownership
        device_owner = db.find_user_by_device(device_id)
        if not device_owner or device_owner != auth['userId']:
            return error_response(403, "Device not found or not owned by user")

        success = db.delete_device(device_id)

        if success:
            return api_response(200, {"message": "Device deleted successfully"})
        else:
            return error_response(404, "Device not found")

    except Exception as e:
        logger.exception(f"Delete device error: {e}")
        return error_response(500, f"Failed to delete device: {str(e)}")
