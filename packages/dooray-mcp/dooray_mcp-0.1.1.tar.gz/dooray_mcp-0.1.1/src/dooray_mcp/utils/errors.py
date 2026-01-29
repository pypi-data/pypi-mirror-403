from enum import Enum


class ErrorType(Enum):
    AUTH_MISSING = "AUTH_MISSING"
    AUTH_INVALID = "AUTH_INVALID"
    API_ERROR = "API_ERROR"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNEXPECTED_ERROR = "UNEXPECTED_ERROR"


class DoorayError(Exception):
    def __init__(
        self,
        message: str,
        error_type: ErrorType,
        status_code: int | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(message)
        self.error_type = error_type
        self.status_code = status_code
        self.original_error = original_error

    def __str__(self) -> str:
        parts = [f"[{self.error_type.value}] {self.args[0]}"]
        if self.status_code:
            parts.append(f"(HTTP {self.status_code})")
        return " ".join(parts)


def create_auth_missing_error() -> DoorayError:
    return DoorayError(
        "DOORAY_API_KEY environment variable is not set",
        ErrorType.AUTH_MISSING,
    )


def create_auth_invalid_error(message: str) -> DoorayError:
    return DoorayError(message, ErrorType.AUTH_INVALID, status_code=401)


def create_not_found_error(resource: str, resource_id: str) -> DoorayError:
    return DoorayError(
        f"{resource} not found: {resource_id}",
        ErrorType.NOT_FOUND,
        status_code=404,
    )


def create_api_error(message: str, status_code: int) -> DoorayError:
    return DoorayError(message, ErrorType.API_ERROR, status_code=status_code)


def create_validation_error(message: str) -> DoorayError:
    return DoorayError(message, ErrorType.VALIDATION_ERROR)
