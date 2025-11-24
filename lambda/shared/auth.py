import jwt
import bcrypt
import logging
from datetime import datetime, timedelta, timezone
from .config import get_config

logger = logging.getLogger()

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification failed: {e}")
        return False

def create_token(user_id: str, user_type: str = "user") -> str:
    """Create a JWT token"""
    config = get_config()

    payload = {
        "userId": str(user_id),
        "userType": user_type,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=config["JWT_EXPIRY_HOURS"])
    }

    return jwt.encode(payload, config["JWT_SECRET"], algorithm=config["JWT_ALGORITHM"])

def authenticate_user(event: dict) -> dict:
    """
    Authenticate user from JWT in Authorization header.
    Returns dict with userId and userType on success.
    Returns None on failure.
    """
    config = get_config()

    # Get Authorization header
    headers = event.get('headers', {}) or {}
    auth_header = headers.get('Authorization') or headers.get('authorization')

    if not auth_header:
        return None

    # Extract token
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
    else:
        token = auth_header

    try:
        payload = jwt.decode(
            token,
            config["JWT_SECRET"],
            algorithms=[config["JWT_ALGORITHM"]]
        )

        return {
            "userId": payload.get("userId"),
            "userType": payload.get("userType", "user")
        }

    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
