"""Utilities module - using yitool's comprehensive utilities"""

from yitool.utils.arr_utils import ArrUtils
from yitool.utils.dict_utils import DictUtils
from yitool.utils.random_utils import RandomUtils
from yitool.utils.security_utils import generate_otp, hash_password, verify_password
from yitool.utils.str_utils import StrUtils
from yitool.utils.validator_utils import ValidatorUtils

# Create aliases for utility functions
remove_none_values = lambda d: {k: v for k, v in d.items() if v is not None}
truncate_string = lambda s, max_length, suffix='...': s[:max_length - len(suffix)] + suffix if len(s) > max_length else s
paginate_list = lambda data, page, page_size: {
    "items": data[(page - 1) * page_size:page * page_size],
    "total": len(data),
    "page": page,
    "page_size": page_size,
    "total_pages": (len(data) + page_size - 1) // page_size
}

__all__ = [
    # Password (using yitool's implementation)
    "hash_password",
    "verify_password",
    # Helpers (using yitool's implementation)
    "generate_otp",
    "remove_none_values",
    "deep_merge_dicts",
    "paginate_list",
    "truncate_string",
    "generate_random_string",
    # Validators (using yitool's implementation)
    "validate_email",
    "validate_password_strength",
    "validate_username",
    "validate_phone",
    "validate_url",
    # Utility classes (from yitool)
    "ArrUtils",
    "DictUtils",
    "RandomUtils",
    "StrUtils",
    "ValidatorUtils",
]

# From yitool static methods
generate_random_string = RandomUtils.random_str
deep_merge_dicts = DictUtils.deep_merge

# Validator aliases
validate_email = ValidatorUtils.is_email
validate_password_strength = ValidatorUtils.is_password_strong
validate_username = ValidatorUtils.is_username
validate_phone = ValidatorUtils.is_phone
validate_url = ValidatorUtils.is_url
