from fastapi import HTTPException, status, Request
from typing import Any, Dict, Optional
import logging
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class BaseCustomException(Exception):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class AuthenticationError(BaseCustomException):
    pass

class AuthorizationError(BaseCustomException):
    pass

class ValidationError(BaseCustomException):
    pass

class NotFoundError(BaseCustomException):
    pass

class ConflictError(BaseCustomException):
    pass

class InternalServerError(BaseCustomException):
    pass

class RateLimitError(BaseCustomException):
    pass

def create_http_exception(exc: BaseCustomException) -> HTTPException:
    status_code_map = {
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
        ValidationError: status.HTTP_400_BAD_REQUEST,
        NotFoundError: status.HTTP_404_NOT_FOUND,
        ConflictError: status.HTTP_409_CONFLICT,
        RateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
        InternalServerError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    status_code = status_code_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    return HTTPException(
        status_code=status_code,
        detail={
            "message": exc.message,
            "details": exc.details,
            "type": type(exc).__name__
        }
    )

def custom_exception_handler(request: Request, exc: BaseCustomException):
    return JSONResponse(
        status_code=create_http_exception(exc).status_code,
        content={
            "message": exc.message,
            "type": exc.__class__.__name__,
            "details": exc.details,
            "request_id": getattr(request.state, "request_id", None)
        }
    )

def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True, extra={"request_id": getattr(request.state, "request_id", None)})
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error",
            "type": "InternalServerError",
            "request_id": getattr(request.state, "request_id", None)
        }
    )