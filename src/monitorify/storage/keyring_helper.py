import logging
from typing import Optional

logger = logging.getLogger(__name__)
SERVICE_NAME = "monitorify"


def _make_key(host_id: int) -> str:
    return f"host_{host_id}"


def set_host_password(host_id: int, password: str) -> bool:
    """Store host password in system keyring."""
    try:
        import keyring

        keyring.set_password(SERVICE_NAME, _make_key(host_id), password)
        return True
    except Exception as e:
        logger.warning(f"Failed to store password in keyring: {e}")
        return False


def get_host_password(host_id: int) -> Optional[str]:
    """Retrieve host password from system keyring."""
    try:
        import keyring

        return keyring.get_password(SERVICE_NAME, _make_key(host_id))
    except Exception as e:
        logger.warning(f"Failed to retrieve password from keyring: {e}")
        return None


def delete_host_password(host_id: int) -> bool:
    """Delete host password from system keyring."""
    try:
        import keyring
        from keyring.errors import PasswordDeleteError

        try:
            keyring.delete_password(SERVICE_NAME, _make_key(host_id))
            return True
        except PasswordDeleteError:
            return True
    except Exception as e:
        logger.warning(f"Failed to delete password from keyring: {e}")
        return False
