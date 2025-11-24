import json
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

class CustomEncoder(json.JSONEncoder):
    """Custom JSON encoder for special types"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)

def api_response(status_code: int, body: dict, headers: dict = None) -> dict:
    """Create a standardized API response"""
    response_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Requested-With",
        "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    }

    if headers:
        response_headers.update(headers)

    return {
        "statusCode": status_code,
        "headers": response_headers,
        "body": json.dumps(body, cls=CustomEncoder)
    }

def error_response(status_code: int, message: str) -> dict:
    """Create a standardized error response"""
    return api_response(status_code, {"error": message})
