# Copyright Jonathan AW.
# Licensed under the MIT License.

import time

import bcrypt
from src.auth.db import deactivate_user

LOCKOUT_THRESHOLD = 5
LOCKOUT_TIME = 600  # 10 minutes

login_attempts = {}


def hash_password(password: str, salt: int) -> str:
    # Generate a salt with the appropriate log rounds (cost)
    salt_bytes = bcrypt.gensalt(rounds=salt)
    # Hash the password using the generated salt
    return bcrypt.hashpw(password.encode(), salt_bytes).decode()


def verify_password(stored_password: str, provided_password: str) -> bool:
    return bcrypt.checkpw(provided_password.encode(), stored_password.encode())


def record_failed_attempt(username: str):
    """
    Records a failed login attempt for the given username.
    Parameters:
    - username (str): The username for which the login attempt failed.
    Returns:
    - None
    Raises:
    - None
    """
    if username in login_attempts:
        login_attempts[username]["count"] += 1
    else:
        login_attempts[username] = {"count": 1, "last_attempt_time": time.time()}

    if (
        login_attempts[username]["count"] >= LOCKOUT_THRESHOLD
        and time.time() - login_attempts[username]["last_attempt_time"] < LOCKOUT_TIME
    ):
        deactivate_user(username)  # Lock the account if exceeded threshold


def is_account_locked(username: str) -> bool:
    """
    Check if the account associated with the given username is locked.
    Args:
        username (str): The username of the account to check.
    Returns:
        bool: True if the account is locked, False otherwise.
    """
    if username not in login_attempts:
        return False

    attempts = login_attempts[username]
    if (
        attempts["count"] >= LOCKOUT_THRESHOLD
        and time.time() - attempts["last_attempt_time"] < LOCKOUT_TIME
    ):
        return True
    elif time.time() - attempts["last_attempt_time"] > LOCKOUT_TIME:
        login_attempts[username]["count"] = 0
        return False

    return False


def reset_failed_attempts(username: str):
    if username in login_attempts:
        login_attempts[username]["count"] = 0
