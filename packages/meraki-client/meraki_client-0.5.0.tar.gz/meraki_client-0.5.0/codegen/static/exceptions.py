"""Exceptions for the SDK."""

from typing import Any

import httpx
import pydantic


class _ErrorResponse(pydantic.BaseModel):
    """Error response from the API."""

    errors: list[str] = []

    @pydantic.model_validator(mode="before")
    @classmethod
    def _normalize_errors(cls, data: Any) -> Any:
        """Some endpoints return "error" instead of "errors"."""
        if isinstance(data, dict) and "error" in data and "errors" not in data:
            data["errors"] = [data.pop("error")]
        return data


class MerakiException(Exception):
    """Base exception for all Meraki API exceptions."""

    def __init__(self, *args: Any, cause: dict[str, Any] | Exception | None = None) -> None:
        """Initialize MerakiError with cause.

        Args:
            *args: Arguments to pass to the exception.
            cause: Exception that caused the exception if available.

        """
        self.cause: dict[str, Any] | Exception | None = cause
        super().__init__(*args)


class MerakiHTTPError(MerakiException):
    """Request failed due to an unexpected HTTP status."""

    def __init__(
        self,
        *args: Any,
        cause: dict[str, Any] | Exception | None = None,
        response: httpx.Response | None = None,
    ) -> None:
        """Initialize MerakiHTTPError with cause.

        Args:
            *args: Arguments to pass to the exception.
            cause: Exception that caused the exception if available.
            response: HTTP Response object.

        """
        self.cause: dict[str, Any] | Exception | None = cause
        self.response: httpx.Response | None = response
        self.status_code: int | None = None
        self.reason: str | None = None
        self.errors: list[str] | None = None

        if response:
            self.status_code = response.status_code
            self.reason = response.reason_phrase
            try:
                self.errors = _ErrorResponse.model_validate_json(response.text).errors
            except pydantic.ValidationError:
                self.errors = None
        super().__init__(*args, cause=cause)

    def __str__(self) -> str:
        """Return the exception message."""
        if self.errors:
            errors = "\n".join(self.errors)
            return f"{self.__class__.__name__}: {self.status_code} {self.reason}\n{errors}"
        return f"{self.__class__.__name__}: {self.status_code} {self.reason}"


class InvalidRequestError(MerakiHTTPError):
    """API returned HTTP status 400."""


class UnauthorizedError(MerakiHTTPError):
    """API returned HTTP status 401."""


class PermissionDeniedError(MerakiHTTPError):
    """API returned HTTP status 403."""


class ResourceNotFoundError(MerakiHTTPError):
    """API returned HTTP status 404."""


class RateLimitError(MerakiHTTPError):
    """API returned HTTP status 429."""


class ServerError(MerakiHTTPError):
    """API returned HTTP status 5xx."""


class InvalidResponseError(MerakiException):
    """Response payload failed schema validation."""

    def __init__(
        self,
        message: str,
        *,
        cause: pydantic.ValidationError | None = None,
        response_body: Any = None,
    ) -> None:
        """Initialize InvalidResponseError.

        Args:
            message: Error message describing the validation failure.
            cause: The pydantic ValidationError that caused this exception.
            response_body: The raw response body that failed validation.

        """
        self.validation_error: pydantic.ValidationError | None = cause
        self.response_body: Any = response_body
        super().__init__(message, cause=cause)

    def __str__(self) -> str:
        """Return the exception message with validation error details."""
        if self.validation_error:
            errors = self.validation_error.errors()
            details = "; ".join(f"{e['loc']}: {e['msg']}" for e in errors[:5])
            if len(errors) > 5:
                details += f" ... and {len(errors) - 5} more errors"
            return f"InvalidResponseError: {details}"
        return f"InvalidResponseError: {self.args[0] if self.args else 'Unknown error'}"


class MerakiConnectionError(MerakiException):
    """Connection failed to the API."""


class MerakiTimeoutError(MerakiException):
    """Total request timeout exceeded including retries."""


def _raise_http_error(response: httpx.Response) -> MerakiHTTPError:
    """Raise the appropriate HTTP error based on the response."""
    match response.status_code:
        case 400:
            return InvalidRequestError(response=response)
        case 401:
            return UnauthorizedError(response=response)
        case 403:
            return PermissionDeniedError(response=response)
        case 404:
            return ResourceNotFoundError(response=response)
        case 429:
            return RateLimitError(response=response)
        case status if 500 <= status < 600:
            return ServerError(response=response)
        case _:
            return MerakiHTTPError(response=response)
