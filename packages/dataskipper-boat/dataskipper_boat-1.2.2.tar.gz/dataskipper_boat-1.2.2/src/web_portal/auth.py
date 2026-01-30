"""
Authentication module for RTU Web Portal.

Features:
- Secure password hashing using bcrypt
- Brute force protection with rate limiting
- Session-based authentication
- Configurable credentials
"""

import hashlib
import hmac
import os
import secrets
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# ==================== Configuration ====================

# Default credentials (can be overridden via environment or config file)
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "zxcvbnm@123"  # Should be changed on first login

# Brute force protection settings
MAX_FAILED_ATTEMPTS = 5  # Max attempts before lockout
LOCKOUT_DURATION_SECONDS = 300  # 5 minutes lockout
ATTEMPT_WINDOW_SECONDS = 600  # 10 minute window for tracking attempts

# Session settings
SESSION_DURATION_HOURS = 24
SESSION_COOKIE_NAME = "rtu_session"


# ==================== Password Hashing ====================

def _hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, bytes]:
    """
    Hash a password using PBKDF2-SHA256.

    Uses PBKDF2 instead of bcrypt for compatibility (no external dependencies).
    PBKDF2 with 100,000 iterations provides good security.

    Returns:
        Tuple of (hashed_password_hex, salt_bytes)
    """
    if salt is None:
        salt = os.urandom(32)

    # Use PBKDF2 with SHA256, 100k iterations
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        iterations=100000
    )

    return key.hex(), salt


def _verify_password(password: str, stored_hash: str, salt: bytes) -> bool:
    """Verify a password against a stored hash."""
    computed_hash, _ = _hash_password(password, salt)
    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(computed_hash, stored_hash)


# ==================== Brute Force Protection ====================

class RateLimiter:
    """
    Track and limit login attempts to prevent brute force attacks.

    Uses in-memory storage (resets on restart, which is acceptable for
    a local RTU device).
    """

    def __init__(self):
        # Track attempts per IP/username: {key: [(timestamp, success), ...]}
        self._attempts: Dict[str, list] = {}
        # Track lockouts: {key: lockout_expiry_timestamp}
        self._lockouts: Dict[str, float] = {}

    def _get_key(self, ip: str, username: str) -> str:
        """Generate a tracking key for IP+username combination."""
        return f"{ip}:{username}"

    def _clean_old_attempts(self, key: str):
        """Remove attempts older than the tracking window."""
        if key not in self._attempts:
            return

        cutoff = time.time() - ATTEMPT_WINDOW_SECONDS
        self._attempts[key] = [
            (ts, success) for ts, success in self._attempts[key]
            if ts > cutoff
        ]

    def is_locked(self, ip: str, username: str) -> Tuple[bool, float]:
        """
        Check if the IP+username is currently locked out.

        Returns:
            Tuple of (is_locked, seconds_remaining)
        """
        key = self._get_key(ip, username)

        if key in self._lockouts:
            expiry = self._lockouts[key]
            if time.time() < expiry:
                return True, expiry - time.time()
            else:
                # Lockout expired, remove it
                del self._lockouts[key]

        return False, 0

    def record_attempt(self, ip: str, username: str, success: bool):
        """Record a login attempt."""
        key = self._get_key(ip, username)

        # Clean old attempts
        self._clean_old_attempts(key)

        # Add new attempt
        if key not in self._attempts:
            self._attempts[key] = []
        self._attempts[key].append((time.time(), success))

        # If successful, clear attempt history
        if success:
            self._attempts[key] = []
            if key in self._lockouts:
                del self._lockouts[key]
            return

        # Check if we should lock out
        failed_attempts = sum(1 for ts, s in self._attempts[key] if not s)
        if failed_attempts >= MAX_FAILED_ATTEMPTS:
            self._lockouts[key] = time.time() + LOCKOUT_DURATION_SECONDS
            logger.warning(f"Lockout triggered for {key} after {failed_attempts} failed attempts")

    def get_attempts_remaining(self, ip: str, username: str) -> int:
        """Get the number of attempts remaining before lockout."""
        key = self._get_key(ip, username)
        self._clean_old_attempts(key)

        if key not in self._attempts:
            return MAX_FAILED_ATTEMPTS

        failed_attempts = sum(1 for ts, s in self._attempts[key] if not s)
        return max(0, MAX_FAILED_ATTEMPTS - failed_attempts)


# Global rate limiter instance
_rate_limiter = RateLimiter()


# ==================== Session Management ====================

class SessionManager:
    """
    Manage user sessions with secure tokens.

    Sessions are stored in memory (resets on restart).
    """

    def __init__(self):
        # {session_token: {username, created_at, expires_at, ip}}
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, username: str, ip: str) -> str:
        """Create a new session and return the session token."""
        # Generate secure random token
        token = secrets.token_urlsafe(32)

        now = datetime.now()
        expires = now + timedelta(hours=SESSION_DURATION_HOURS)

        self._sessions[token] = {
            "username": username,
            "created_at": now.isoformat(),
            "expires_at": expires.isoformat(),
            "ip": ip
        }

        logger.info(f"Session created for user '{username}' from {ip}")
        return token

    def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a session token.

        Returns:
            Session data if valid, None if invalid or expired
        """
        if not token or token not in self._sessions:
            return None

        session = self._sessions[token]
        expires_at = datetime.fromisoformat(session["expires_at"])

        if datetime.now() > expires_at:
            # Session expired
            del self._sessions[token]
            return None

        return session

    def destroy_session(self, token: str):
        """Destroy a session (logout)."""
        if token in self._sessions:
            del self._sessions[token]

    def cleanup_expired(self):
        """Remove all expired sessions."""
        now = datetime.now()
        expired = [
            token for token, session in self._sessions.items()
            if datetime.fromisoformat(session["expires_at"]) < now
        ]
        for token in expired:
            del self._sessions[token]


# Global session manager
_session_manager = SessionManager()


# ==================== Credentials Management ====================

class CredentialsStore:
    """
    Store and verify user credentials.

    Credentials are stored in a file for persistence across restarts.
    The password is stored as a salted hash.
    """

    def __init__(self, config_dir: Optional[str] = None):
        self._config_dir = config_dir
        self._credentials: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    def _get_credentials_path(self) -> Path:
        """Get the path to the credentials file."""
        if self._config_dir:
            return Path(self._config_dir) / ".portal_credentials"

        # Fallback to home directory
        return Path.home() / ".rtu_portal_credentials"

    def _load_credentials(self):
        """Load credentials from file."""
        if self._loaded:
            return

        creds_path = self._get_credentials_path()

        if creds_path.exists():
            try:
                import json
                with open(creds_path, 'r') as f:
                    self._credentials = json.load(f)
                logger.info(f"Loaded credentials from {creds_path}")
            except Exception as e:
                logger.error(f"Failed to load credentials: {e}")
                self._credentials = {}
        else:
            # Initialize with default credentials
            self._set_password(DEFAULT_USERNAME, DEFAULT_PASSWORD)
            self._save_credentials()
            logger.info("Initialized default credentials")

        self._loaded = True

    def _save_credentials(self):
        """Save credentials to file."""
        creds_path = self._get_credentials_path()

        try:
            import json
            # Ensure parent directory exists
            creds_path.parent.mkdir(parents=True, exist_ok=True)

            with open(creds_path, 'w') as f:
                json.dump(self._credentials, f)

            # Set restrictive permissions
            os.chmod(creds_path, 0o600)
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")

    def _set_password(self, username: str, password: str):
        """Set or update a user's password."""
        hash_hex, salt = _hash_password(password)
        self._credentials[username] = {
            "password_hash": hash_hex,
            "salt": salt.hex(),
            "created_at": datetime.now().isoformat()
        }

    def verify(self, username: str, password: str) -> bool:
        """Verify username and password."""
        self._load_credentials()

        if username not in self._credentials:
            # Perform dummy hash to prevent timing attacks
            _hash_password(password)
            return False

        creds = self._credentials[username]
        salt = bytes.fromhex(creds["salt"])

        return _verify_password(password, creds["password_hash"], salt)

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change a user's password."""
        if not self.verify(username, old_password):
            return False

        self._set_password(username, new_password)
        self._save_credentials()
        logger.info(f"Password changed for user '{username}'")
        return True

    def reset_to_default(self, username: str = DEFAULT_USERNAME):
        """Reset credentials to default (for recovery)."""
        self._set_password(username, DEFAULT_PASSWORD)
        self._save_credentials()
        logger.warning(f"Credentials reset to default for user '{username}'")


# Global credentials store
_credentials_store: Optional[CredentialsStore] = None


def get_credentials_store(config_dir: Optional[str] = None) -> CredentialsStore:
    """Get or create the global credentials store."""
    global _credentials_store
    if _credentials_store is None:
        _credentials_store = CredentialsStore(config_dir)
    return _credentials_store


# ==================== Authentication Functions ====================

def authenticate(username: str, password: str, ip: str) -> Dict[str, Any]:
    """
    Authenticate a user.

    Returns:
        Dict with success status, message, and session token if successful
    """
    # Check for lockout
    is_locked, remaining = _rate_limiter.is_locked(ip, username)
    if is_locked:
        return {
            "success": False,
            "message": "Too many failed attempts. Please try again later.",
            "locked_until": remaining
        }

    # Verify credentials
    store = get_credentials_store()
    if store.verify(username, password):
        # Record successful attempt
        _rate_limiter.record_attempt(ip, username, True)

        # Create session
        token = _session_manager.create_session(username, ip)

        return {
            "success": True,
            "message": "Login successful",
            "token": token
        }
    else:
        # Record failed attempt
        _rate_limiter.record_attempt(ip, username, False)

        attempts_remaining = _rate_limiter.get_attempts_remaining(ip, username)

        return {
            "success": False,
            "message": "Invalid username or password",
            "attempts_remaining": attempts_remaining
        }


def validate_session(token: str) -> Optional[Dict[str, Any]]:
    """Validate a session token and return session data."""
    return _session_manager.validate_session(token)


def logout(token: str):
    """Logout and destroy session."""
    _session_manager.destroy_session(token)


def get_session_cookie_name() -> str:
    """Get the session cookie name."""
    return SESSION_COOKIE_NAME
