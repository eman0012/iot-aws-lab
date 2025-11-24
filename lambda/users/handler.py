import json
import logging
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

import sys
sys.path.insert(0, '/opt/python')

from shared.db_service import DatabaseService
from shared.auth import authenticate_user, create_token, hash_password, verify_password
from shared.response import api_response, error_response

def main(event, context):
    """Main handler - routes to appropriate function based on path and method"""
    http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
    path = event.get('rawPath', '')

    logger.info(f"Users handler: {http_method} {path}")

    if http_method == 'OPTIONS':
        return api_response(200, {})

    # Route based on path
    if '/login' in path:
        return login(event)
    elif '/password' in path:
        return change_password(event)
    elif http_method == 'POST':
        return register(event)
    elif http_method == 'GET':
        return get_profile(event)
    elif http_method == 'PUT':
        return update_profile(event)
    elif http_method == 'DELETE':
        return delete_account(event)
    else:
        return error_response(405, "Method not allowed")

def register(event):
    """POST /api/user - Register new user"""
    try:
        body = json.loads(event.get('body', '{}'))

        username = body.get('username')
        email = body.get('email')
        password = body.get('password')

        if not all([username, email, password]):
            return error_response(400, "Missing required fields: username, email, password")

        db = DatabaseService()

        # Check for duplicates
        if db.find_user_by_email(email):
            return error_response(409, "Email already registered")

        if db.find_user_by_username(username):
            return error_response(409, "Username already taken")

        # Create user
        user_data = {
            "id": str(uuid.uuid4()),
            "username": username,
            "email": email,
            "password_hash": hash_password(password),
            "user_type": body.get('userType', 'Standard'),
            "first_name": body.get('firstName'),
            "last_name": body.get('lastName'),
            "notification_methods": body.get('notificationMethods', ['email'])
        }

        user = db.create_user(user_data)
        token = create_token(user['id'], user['user_type'])

        return api_response(201, {
            "message": "User registered successfully",
            "userId": str(user['id']),
            "token": token
        })

    except Exception as e:
        logger.exception(f"Registration error: {e}")
        return error_response(500, f"Registration failed: {str(e)}")

def login(event):
    """POST /api/user/login - User login"""
    try:
        body = json.loads(event.get('body', '{}'))

        identifier = body.get('email') or body.get('username')
        password = body.get('password')

        if not identifier or not password:
            return error_response(400, "Email/username and password required")

        db = DatabaseService()
        user = db.find_user_by_email_or_username(identifier)

        if not user:
            return error_response(401, "Invalid credentials")

        if not verify_password(password, user['password_hash']):
            return error_response(401, "Invalid credentials")

        token = create_token(user['id'], user['user_type'])

        return api_response(200, {
            "message": "Login successful",
            "userId": str(user['id']),
            "userType": user['user_type'],
            "token": token
        })

    except Exception as e:
        logger.exception(f"Login error: {e}")
        return error_response(500, f"Login failed: {str(e)}")

def get_profile(event):
    """GET /api/user - Get user profile"""
    auth = authenticate_user(event)
    if not auth:
        return error_response(401, "Authentication required")

    try:
        db = DatabaseService()
        user = db.find_user_by_id(auth['userId'])

        if not user:
            return error_response(404, "User not found")

        # Remove sensitive fields
        del user['password_hash']

        # Get user's devices
        devices = db.get_user_devices(auth['userId'])
        user['devices'] = devices

        return api_response(200, user)

    except Exception as e:
        logger.exception(f"Get profile error: {e}")
        return error_response(500, f"Failed to get profile: {str(e)}")

def update_profile(event):
    """PUT /api/user - Update user profile"""
    auth = authenticate_user(event)
    if not auth:
        return error_response(401, "Authentication required")

    try:
        body = json.loads(event.get('body', '{}'))

        # Prevent updating sensitive fields
        forbidden_fields = ['id', 'password_hash', 'user_type']
        if auth['userType'] != 'Admin':
            forbidden_fields.append('user_type')

        for field in forbidden_fields:
            body.pop(field, None)

        if not body:
            return error_response(400, "No valid update fields provided")

        db = DatabaseService()
        updated_user = db.update_user(auth['userId'], body)

        if updated_user:
            del updated_user['password_hash']
            return api_response(200, {
                "message": "Profile updated successfully",
                "user": updated_user
            })
        else:
            return error_response(404, "User not found")

    except Exception as e:
        logger.exception(f"Update profile error: {e}")
        return error_response(500, f"Failed to update profile: {str(e)}")

def delete_account(event):
    """DELETE /api/user - Delete user account"""
    auth = authenticate_user(event)
    if not auth:
        return error_response(401, "Authentication required")

    try:
        db = DatabaseService()

        # Delete user (cascades to devices, telemetry, conditions, alerts)
        success = db.delete_user(auth['userId'])

        if success:
            return api_response(200, {"message": "Account deleted successfully"})
        else:
            return error_response(404, "User not found")

    except Exception as e:
        logger.exception(f"Delete account error: {e}")
        return error_response(500, f"Failed to delete account: {str(e)}")

def change_password(event):
    """PATCH /api/user/password - Change password"""
    auth = authenticate_user(event)
    if not auth:
        return error_response(401, "Authentication required")

    try:
        body = json.loads(event.get('body', '{}'))

        old_password = body.get('oldPassword')
        new_password = body.get('newPassword')

        if not old_password or not new_password:
            return error_response(400, "oldPassword and newPassword required")

        db = DatabaseService()
        user = db.find_user_by_id(auth['userId'])

        if not user:
            return error_response(404, "User not found")

        if not verify_password(old_password, user['password_hash']):
            return error_response(401, "Current password is incorrect")

        new_hash = hash_password(new_password)
        success = db.update_password(auth['userId'], new_hash)

        if success:
            # Generate new token
            token = create_token(user['id'], user['user_type'])
            return api_response(200, {
                "message": "Password changed successfully",
                "token": token
            })
        else:
            return error_response(500, "Failed to update password")

    except Exception as e:
        logger.exception(f"Change password error: {e}")
        return error_response(500, f"Failed to change password: {str(e)}")
