import json
import logging
import boto3
from datetime import datetime, timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

import sys
sys.path.insert(0, '/opt/python')

from shared.db_service import DatabaseService
from shared.auth import authenticate_user
from shared.response import api_response, error_response
from shared.config import get_config

def main(event, context):
    """Main handler for admin endpoints"""
    http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
    path = event.get('rawPath', '')

    if http_method == 'OPTIONS':
        return api_response(200, {})

    # Require admin authentication for all admin endpoints
    auth = authenticate_user(event)
    if not auth:
        return error_response(401, "Authentication required")

    if auth['userType'] != 'Admin':
        return error_response(403, "Admin access required")

    # Route based on path
    if '/users' in path:
        return get_all_users(event, auth)
    elif '/transfer-device' in path:
        return transfer_device(event, auth)
    elif '/change-user-type' in path:
        return change_user_type(event, auth)
    elif '/images' in path:
        return get_image_access(event, auth)
    else:
        return error_response(404, "Admin endpoint not found")

def get_all_users(event, auth):
    """GET /api/manage/users - List all users"""
    try:
        db = DatabaseService()
        users = db.get_all_users()

        # Remove password hashes
        for user in users:
            del user['password_hash']

        return api_response(200, {
            "users": users,
            "count": len(users)
        })

    except Exception as e:
        logger.exception(f"Get all users error: {e}")
        return error_response(500, f"Failed to get users: {str(e)}")

def change_user_type(event, auth):
    """PUT /api/manage/change-user-type - Change user type (Admin/Standard)"""
    try:
        body = json.loads(event.get('body', '{}'))
        target_user_id = body.get('userId')
        new_user_type = body.get('userType')

        if not target_user_id or not new_user_type:
            return error_response(400, "userId and userType required")

        # Validate user type
        if new_user_type not in ['Admin', 'Standard']:
            return error_response(400, "userType must be 'Admin' or 'Standard'")

        db = DatabaseService()

        # Verify target user exists
        user = db.find_user_by_id(target_user_id)
        if not user:
            return error_response(404, "User not found")

        # Prevent self-demotion
        if target_user_id == auth['userId'] and new_user_type == 'Standard':
            return error_response(403, "Cannot demote yourself")

        updated_user = db.update_user(target_user_id, {'userType': new_user_type})

        if updated_user:
            del updated_user['password_hash']
            return api_response(200, {
                "message": f"User type changed to {new_user_type}",
                "user": updated_user
            })
        else:
            return error_response(500, "Failed to change user type")

    except Exception as e:
        logger.exception(f"Change user type error: {e}")
        return error_response(500, f"Failed to change user type: {str(e)}")

def transfer_device(event, auth):
    """POST /api/manage/transfer-device - Transfer device ownership"""
    try:
        body = json.loads(event.get('body', '{}'))
        device_id = body.get('deviceId')
        new_user_id = body.get('newUserId')

        if not device_id or not new_user_id:
            return error_response(400, "deviceId and newUserId required")

        db = DatabaseService()

        # Verify device exists
        device = db.find_device_by_id(device_id)
        if not device:
            return error_response(404, "Device not found")

        # Verify new user exists
        new_user = db.find_user_by_id(new_user_id)
        if not new_user:
            return error_response(404, "Target user not found")

        transferred_device = db.transfer_device(device_id, new_user_id)

        if transferred_device:
            return api_response(200, {
                "message": "Device transferred successfully",
                "device": transferred_device
            })
        else:
            return error_response(500, "Failed to transfer device")

    except Exception as e:
        logger.exception(f"Transfer device error: {e}")
        return error_response(500, f"Failed to transfer device: {str(e)}")

def get_image_access(event, auth):
    """GET /api/manage/images - Get presigned URL for image access"""
    try:
        params = event.get('queryStringParameters', {}) or {}
        image_key = params.get('key')

        if not image_key:
            return error_response(400, "Image key required")

        config = get_config()
        s3_client = boto3.client('s3')

        # Generate presigned URL (valid for 1 hour)
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': config['S3_BUCKET'],
                'Key': image_key
            },
            ExpiresIn=3600
        )

        return api_response(200, {
            "url": presigned_url,
            "expiresIn": 3600
        })

    except Exception as e:
        logger.exception(f"Get image access error: {e}")
        return error_response(500, f"Failed to get image access: {str(e)}")
