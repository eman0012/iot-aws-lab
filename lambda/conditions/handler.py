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
    """Main handler for condition endpoints"""
    http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')

    if http_method == 'OPTIONS':
        return api_response(200, {})
    elif http_method == 'POST':
        return create_condition(event)
    elif http_method == 'GET':
        return get_conditions(event)
    elif http_method == 'PUT':
        return update_condition(event)
    elif http_method == 'DELETE':
        return delete_condition(event)
    else:
        return error_response(405, "Method not allowed")

def create_condition(event):
    """POST /api/conditions - Create alert condition"""
    auth = authenticate_user(event)
    if not auth:
        return error_response(401, "Authentication required")

    try:
        body = json.loads(event.get('body', '{}'))

        condition_name = body.get('conditionName')
        parameter = body.get('parameter')
        operator = body.get('operator')
        threshold = body.get('threshold')

        if not all([condition_name, parameter, operator, threshold is not None]):
            return error_response(400, "Missing required fields: conditionName, parameter, operator, threshold")

        # Validate operator
        valid_operators = ['>', '<', '>=', '<=', '==', '!=']
        if operator not in valid_operators:
            return error_response(400, f"Invalid operator. Use: {', '.join(valid_operators)}")

        db = DatabaseService()

        # If deviceId provided, verify ownership
        device_id = body.get('deviceId')
        if device_id:
            device_owner = db.find_user_by_device(device_id)
            if not device_owner or device_owner != auth['userId']:
                return error_response(403, "Device not found or not owned by user")

        condition_data = {
            "id": str(uuid.uuid4()),
            "user_id": auth['userId'],
            "device_id": device_id,
            "condition_name": condition_name,
            "parameter": parameter,
            "operator": operator,
            "threshold": threshold,
            "notification_methods": body.get('notificationMethods', ['email']),
            "is_active": body.get('isActive', True)
        }

        condition = db.create_condition(condition_data)

        return api_response(201, {
            "message": "Condition created successfully",
            "condition": condition
        })

    except Exception as e:
        logger.exception(f"Create condition error: {e}")
        return error_response(500, f"Failed to create condition: {str(e)}")

def get_conditions(event):
    """GET /api/conditions - List alert conditions"""
    auth = authenticate_user(event)
    if not auth:
        return error_response(401, "Authentication required")

    try:
        db = DatabaseService()
        conditions = db.get_user_conditions(auth['userId'])

        return api_response(200, {
            "conditions": conditions,
            "count": len(conditions)
        })

    except Exception as e:
        logger.exception(f"Get conditions error: {e}")
        return error_response(500, f"Failed to get conditions: {str(e)}")

def update_condition(event):
    """PUT /api/conditions - Update alert condition"""
    auth = authenticate_user(event)
    if not auth:
        return error_response(401, "Authentication required")

    try:
        body = json.loads(event.get('body', '{}'))
        params = event.get('queryStringParameters', {}) or {}

        condition_id = params.get('conditionId') or body.get('conditionId')

        if not condition_id:
            return error_response(400, "conditionId required")

        update_data = {k: v for k, v in body.items() if k != 'conditionId'}

        if not update_data:
            return error_response(400, "No update data provided")

        # Validate operator if provided
        if 'operator' in update_data:
            valid_operators = ['>', '<', '>=', '<=', '==', '!=']
            if update_data['operator'] not in valid_operators:
                return error_response(400, f"Invalid operator. Use: {', '.join(valid_operators)}")

        db = DatabaseService()
        updated_condition = db.update_condition(condition_id, auth['userId'], update_data)

        if updated_condition:
            return api_response(200, {
                "message": "Condition updated successfully",
                "condition": updated_condition
            })
        else:
            return error_response(404, "Condition not found or access denied")

    except Exception as e:
        logger.exception(f"Update condition error: {e}")
        return error_response(500, f"Failed to update condition: {str(e)}")

def delete_condition(event):
    """DELETE /api/conditions - Delete alert condition"""
    auth = authenticate_user(event)
    if not auth:
        return error_response(401, "Authentication required")

    try:
        params = event.get('queryStringParameters', {}) or {}
        condition_id = params.get('conditionId')

        if not condition_id:
            body = json.loads(event.get('body', '{}'))
            condition_id = body.get('conditionId')

        if not condition_id:
            return error_response(400, "conditionId required")

        db = DatabaseService()
        success = db.delete_condition(condition_id, auth['userId'])

        if success:
            return api_response(200, {"message": "Condition deleted successfully"})
        else:
            return error_response(404, "Condition not found or access denied")

    except Exception as e:
        logger.exception(f"Delete condition error: {e}")
        return error_response(500, f"Failed to delete condition: {str(e)}")
