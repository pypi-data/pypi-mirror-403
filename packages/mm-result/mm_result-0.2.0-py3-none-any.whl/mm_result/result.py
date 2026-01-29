"""Result type for functional error handling."""

import traceback
from collections.abc import Awaitable, Callable
from typing import Any, cast

type Context = dict[str, Any] | None
"""Type alias for optional metadata dictionary attached to Result."""


class UnwrapError(Exception):
    """Raised when unwrap() is called on an Err result."""


class UnwrapErrError(Exception):
    """Raised when unwrap_err() is called on an Ok result."""


class Result[T]:
    """Container representing either a successful result or an error.

    Use `Result.ok()` or `Result.err()` to create instances.

    The optional `context` field allows attaching arbitrary additional data:
    - HTTP response details, status codes, headers
    - Performance metrics like response times
    - Infrastructure info like proxy servers used
    - Retry attempts, circuit breaker states
    - User context, request metadata
    - Any other information relevant to your use case

    """

    value: T | None  # Success value, if any
    error: str | None  # Error message, if any
    context: Context  # Optional additional data for any purpose

    def __init__(self) -> None:
        """Raise error - use Result.ok() or Result.err() instead."""
        raise RuntimeError("Result is not intended to be instantiated directly. Use the static methods instead.")

    def is_ok(self) -> bool:
        """Return True if the result represents success."""
        return self.error is None

    def is_err(self) -> bool:
        """Return True if the result represents an error."""
        return self.error is not None

    def unwrap(self, message_prefix: str | None = None, include_error: bool = True) -> T:
        """Return the success value if Ok, otherwise raise UnwrapError.

        Args:
            message_prefix: Optional custom prefix for the error message if the Result is an error.
                            If not provided, a default message will be used.
            include_error: If True, appends the internal error message from the Result to the final exception message.

        Raises:
            UnwrapError: If the Result is an error.

        Returns:
            The success value of type T.

        """
        # Hide this frame from pytest tracebacks for cleaner test failure output
        __tracebackhide__ = True
        if not self.is_ok():
            # Use the provided message or a default fallback
            error_message = message_prefix or "Called unwrap() on a failure value"
            # Optionally append the error detail
            if include_error:
                error_message = f"{error_message}: {self.error}"
            # Raise with the final constructed message
            raise UnwrapError(error_message)
        # Return the success value if present
        return cast(T, self.value)

    def unwrap_or(self, default: T) -> T:
        """Return the success value if available, otherwise return the default."""
        if not self.is_ok():
            return default
        return cast(T, self.value)

    def unwrap_err(self) -> str:
        """Return the error message, or raise UnwrapErrError if Ok."""
        # Hide this frame from pytest tracebacks for cleaner test failure output
        __tracebackhide__ = True
        if self.is_ok():
            raise UnwrapErrError("Called unwrap_err() on a success value")
        return cast(str, self.error)

    def value_or_error(self) -> T | str:
        """Return the success value if available, otherwise return the error message."""
        if self.is_ok():
            return self.unwrap()
        return self.unwrap_err()

    def to_dict(self, safe_exception: bool = False) -> dict[str, Any]:
        """Return a dictionary representation of the result.

        Args:
            safe_exception: If True, simplifies exception data in 'context' for serialization:
                           - context['exception'] becomes str(context['exception'])
                           - context['traceback'] is removed completely
                           This makes the result safe for JSON serialization.

        Returns:
            A dictionary with 'value', 'error', and 'context' keys.

        """
        context = self.context

        if safe_exception and context:
            context = context.copy()
            if "exception" in context:
                context["exception"] = str(context["exception"])
            if "traceback" in context:
                del context["traceback"]

        return {
            "value": self.value,
            "error": self.error,
            "context": context,
        }

    def with_value[U](self, value: U) -> Result[U]:
        """Return a copy of this Result with the success value replaced by `value`."""
        return Result.ok(value, self.context)

    def with_error(self, error: str | Exception | tuple[str, Exception]) -> Result[T]:
        """Return a copy of this Result as an Err with the given `error`."""
        return Result.err(error, self.context)

    def map[U](self, fn: Callable[[T], U]) -> Result[U]:
        """Apply function to success value, returning new Result. Errors pass through unchanged."""
        if self.is_ok():
            try:
                new_value = fn(cast(T, self.value))
                return Result.ok(new_value, context=self.context)
            except Exception as e:
                return Result.err(("map_exception", e), context=self.context)
        return cast(Result[U], self)

    async def map_async[U](self, fn: Callable[[T], Awaitable[U]]) -> Result[U]:
        """Apply async function to success value."""
        if self.is_ok():
            try:
                new_value = await fn(cast(T, self.value))
                return Result.ok(new_value, context=self.context)
            except Exception as e:
                return Result.err(("map_exception", e), context=self.context)
        return cast(Result[U], self)

    def chain[U](self, fn: Callable[[T], Result[U]]) -> Result[U]:
        """Apply function that returns Result, flattening the result. Errors pass through unchanged."""
        if self.is_ok():
            try:
                return fn(cast(T, self.value))
            except Exception as e:
                return Result.err(("chain_exception", e), context=self.context)
        return cast(Result[U], self)

    async def chain_async[U](self, fn: Callable[[T], Awaitable[Result[U]]]) -> Result[U]:
        """Apply async function that returns Result."""
        if self.is_ok():
            try:
                return await fn(cast(T, self.value))
            except Exception as e:
                return Result.err(("chain_exception", e), context=self.context)
        return cast(Result[U], self)

    def __repr__(self) -> str:
        """Return string representation of the Result."""
        parts: list[str] = []
        if self.is_ok():
            parts.append(f"value={self.value!r}")
        if self.error is not None:
            parts.append(f"error={self.error!r}")
        if self.context is not None:
            parts.append(f"context={self.context!r}")
        return f"Result({', '.join(parts)})"

    def __hash__(self) -> int:
        """Return hash value for the Result."""
        return hash(
            (
                self.value,
                self.error,
                frozenset(self.context.items()) if self.context else None,
            )
        )

    def __eq__(self, other: object) -> bool:
        """Check equality with another Result."""
        if not isinstance(other, Result):
            return False
        return self.value == other.value and self.error == other.error and self.context == other.context

    @classmethod
    def _create(cls, value: T | None, error: str | None, context: Context) -> Result[T]:
        obj = object.__new__(cls)
        obj.value = value
        obj.error = error
        obj.context = context
        return obj

    @staticmethod
    def ok(value: T, context: Context = None) -> Result[T]:
        """Create a successful Result instance.

        Args:
            value: The success value to store in the Result.
            context: Optional additional data for any purpose. Examples:
                     {"response_time_ms": 150, "status_code": 200, "proxy": "proxy1.com"}
                     {"attempt": 3, "cache_hit": True}
                     {"user_id": "123", "request_id": "abc-def"}

        Returns:
            A Result instance representing success with the provided value.

        """
        return Result._create(value=value, error=None, context=context)

    @staticmethod
    def err(error: str | Exception | tuple[str, Exception], context: Context = None) -> Result[T]:
        """Create a Result instance representing a failure.

        Args:
            error: The error information, which can be:
                - A string error message
                - An Exception object (stored as error message + in context["exception"])
                - A tuple containing (error_message, exception)
            context: Optional additional data for any purpose. Examples:
                     {"response_time_ms": 5000, "status_code": 500, "retry_count": 3}
                     {"proxy": "proxy2.com", "timeout_ms": 30000}
                     {"circuit_breaker": "open", "last_success": "2024-01-01T10:00:00Z"}

        Returns:
            A Result instance representing failure with the provided error information.

        """
        final_context = context.copy() if context else {}

        if isinstance(error, tuple):
            error_msg, exception = error
            # Only add exception if user didn't provide one
            if "exception" not in final_context:
                final_context["exception"] = exception
            # Add traceback if available
            if "traceback" not in final_context and hasattr(exception, "__traceback__") and exception.__traceback__:
                final_context["traceback"] = "".join(traceback.format_tb(exception.__traceback__))
        elif isinstance(error, Exception):
            error_msg = f"{type(error).__name__}: {error}"
            # Only add exception if user didn't provide one
            if "exception" not in final_context:
                final_context["exception"] = error
            # Add traceback if available
            if "traceback" not in final_context and hasattr(error, "__traceback__") and error.__traceback__:
                final_context["traceback"] = "".join(traceback.format_tb(error.__traceback__))
        else:
            error_msg = error

        return Result._create(value=None, error=error_msg, context=final_context or None)


# Apply Pydantic integration if available
try:
    from .pydantic_support import add_pydantic_support

    add_pydantic_support(Result)
except ImportError:
    pass  # Pydantic not available
