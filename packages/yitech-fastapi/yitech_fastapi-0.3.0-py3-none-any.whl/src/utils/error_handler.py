"""Error handling utilities - using yitool's exception classes"""

from yitool.yi_fast.exceptions import (
    YiBadRequestException,
    YiForbiddenException,
    YiInternalServerErrorException,
    YiNotFoundException,
    YiUnauthorizedException,
)

# Create aliases for backward compatibility
CustomHTTPException = YiBadRequestException
ValidationException = YiBadRequestException
AuthenticationException = YiUnauthorizedException
PermissionException = YiForbiddenException
NotFoundException = YiNotFoundException
ServerErrorException = YiInternalServerErrorException

__all__ = [
    "CustomHTTPException",
    "ValidationException",
    "AuthenticationException",
    "PermissionException",
    "NotFoundException",
    "ServerErrorException",
    "YiBadRequestException",
    "YiUnauthorizedException",
    "YiForbiddenException",
    "YiNotFoundException",
    "YiInternalServerErrorException",
]
