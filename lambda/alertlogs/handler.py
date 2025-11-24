import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

import sys
sys.path.insert(0, '/opt/python')

from shared.db_service import DatabaseService
from shared.auth import authenticate_user
from shared.response import api_response, error_response

def main(event, context):
    """Main handler for alert logs endpoints"""
    http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')

    if http_method == 'OPTIONS':
        return api_response(200, {})
    elif http_method == 'GET':
        return get_alert_logs(event)
    elif http_method == 'DELETE':
        return delete_alert_log(event)
    else:
        return error_response(405, "Method not allowed")

def get_alert_logs(event):
    """GET /api/alertlogs - Get alert history"""
    auth = authenticate_user(event)
    if not auth:
        return error_response(401, "Authentication required")

    try:
        params = event.get('queryStringParameters', {}) or {}

        # Pagination
        limit = int(params.get('limit', 100))
        offset = int(params.get('offset', 0))

        db = DatabaseService()
        logs = db.get_user_alert_logs(auth['userId'], limit, offset)

        return api_response(200, {
            "alertLogs": logs,
            "count": len(logs),
            "limit": limit,
            "offset": offset
        })

    except Exception as e:
        logger.exception(f"Get alert logs error: {e}")
        return error_response(500, f"Failed to get alert logs: {str(e)}")

def delete_alert_log(event):
    """DELETE /api/alertlogs - Delete/clear alert log"""
    auth = authenticate_user(event)
    if not auth:
        return error_response(401, "Authentication required")

    try:
        params = event.get('queryStringParameters', {}) or {}
        alert_log_id = params.get('alertLogId')

        if not alert_log_id:
            body = json.loads(event.get('body', '{}'))
            alert_log_id = body.get('alertLogId')

        if not alert_log_id:
            return error_response(400, "alertLogId required")

        db = DatabaseService()
        success = db.delete_alert_log(alert_log_id, auth['userId'])

        if success:
            return api_response(200, {"message": "Alert log deleted successfully"})
        else:
            return error_response(404, "Alert log not found")

    except Exception as e:
        logger.exception(f"Delete alert log error: {e}")
        return error_response(500, f"Failed to delete alert log: {str(e)}")
