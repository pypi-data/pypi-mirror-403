"""Password utilities - using yitool's security_utils"""

from yitool.utils.security_utils import hash_password, verify_password

__all__ = ["hash_password", "verify_password"]
