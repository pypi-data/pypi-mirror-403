"""Tests for Result type."""

import pytest

from mm_result import Result, UnwrapErrError, UnwrapError


class TestResultCreation:
    """Tests for creating Result instances."""

    def test_ok_with_value(self) -> None:
        """Ok result stores the value."""
        result = Result.ok(42)
        assert result.value == 42
        assert result.error is None
        assert result.context is None

    def test_ok_with_value_and_context(self) -> None:
        """Ok result stores both value and context."""
        ctx = {"key": "value", "count": 5}
        result = Result.ok("data", context=ctx)
        assert result.value == "data"
        assert result.context == ctx

    def test_ok_with_none_value(self) -> None:
        """Ok result can store explicit None value."""
        result = Result.ok(None)
        assert result.value is None
        assert result.error is None
        assert result.is_ok()

    def test_err_with_string(self) -> None:
        """Err result stores string error message."""
        result: Result[int] = Result.err("something failed")
        assert result.value is None
        assert result.error == "something failed"
        assert result.context is None

    def test_err_with_exception(self) -> None:
        """Err result from exception captures type name, message, and stores exception in context."""
        exc = ValueError("bad input")
        result: Result[int] = Result.err(exc)
        assert result.error == "ValueError: bad input"
        assert result.context is not None
        assert result.context["exception"] is exc

    def test_err_with_tuple(self) -> None:
        """Err result from tuple uses custom message and stores exception in context."""
        exc = RuntimeError("internal error")
        result: Result[int] = Result.err(("custom message", exc))
        assert result.error == "custom message"
        assert result.context is not None
        assert result.context["exception"] is exc

    def test_err_with_context(self) -> None:
        """Err result stores context."""
        ctx = {"retry_count": 3, "endpoint": "/api"}
        result: Result[int] = Result.err("timeout", context=ctx)
        assert result.error == "timeout"
        assert result.context == ctx

    def test_direct_instantiation_raises(self) -> None:
        """Direct Result() instantiation raises RuntimeError."""
        with pytest.raises(RuntimeError, match="not intended to be instantiated directly"):
            Result()


class TestStateChecking:
    """Tests for is_ok() and is_err() methods."""

    def test_is_ok_returns_true_for_ok(self) -> None:
        """is_ok() returns True for Ok result."""
        result = Result.ok(42)
        assert result.is_ok() is True

    def test_is_ok_returns_false_for_err(self) -> None:
        """is_ok() returns False for Err result."""
        result: Result[int] = Result.err("error")
        assert result.is_ok() is False

    def test_is_err_returns_true_for_err(self) -> None:
        """is_err() returns True for Err result."""
        result: Result[int] = Result.err("error")
        assert result.is_err() is True

    def test_is_err_returns_false_for_ok(self) -> None:
        """is_err() returns False for Ok result."""
        result = Result.ok(42)
        assert result.is_err() is False


class TestValueExtraction:
    """Tests for value extraction methods."""

    def test_unwrap_returns_value_for_ok(self) -> None:
        """unwrap() returns value for Ok result."""
        result = Result.ok("hello")
        assert result.unwrap() == "hello"

    def test_unwrap_raises_for_err(self) -> None:
        """unwrap() raises UnwrapError for Err result."""
        result: Result[int] = Result.err("failed")
        with pytest.raises(UnwrapError, match="Called unwrap\\(\\) on a failure value: failed"):
            result.unwrap()

    def test_unwrap_with_custom_message_prefix(self) -> None:
        """unwrap() uses custom message prefix."""
        result: Result[int] = Result.err("network timeout")
        with pytest.raises(UnwrapError, match="API call failed: network timeout"):
            result.unwrap("API call failed")

    def test_unwrap_with_include_error_false(self) -> None:
        """unwrap() excludes internal error when include_error=False."""
        result: Result[int] = Result.err("internal details")
        with pytest.raises(UnwrapError, match=r"^Operation failed$"):
            result.unwrap("Operation failed", include_error=False)

    def test_unwrap_or_returns_value_for_ok(self) -> None:
        """unwrap_or() returns value for Ok result."""
        result = Result.ok(42)
        assert result.unwrap_or(0) == 42

    def test_unwrap_or_returns_default_for_err(self) -> None:
        """unwrap_or() returns default for Err result."""
        result: Result[int] = Result.err("error")
        assert result.unwrap_or(99) == 99

    def test_unwrap_err_returns_error_for_err(self) -> None:
        """unwrap_err() returns error string for Err result."""
        result: Result[int] = Result.err("something went wrong")
        assert result.unwrap_err() == "something went wrong"

    def test_unwrap_err_raises_for_ok(self) -> None:
        """unwrap_err() raises UnwrapErrError for Ok result."""
        result = Result.ok(42)
        with pytest.raises(UnwrapErrError, match="Called unwrap_err\\(\\) on a success value"):
            result.unwrap_err()

    def test_value_or_error_returns_value_for_ok(self) -> None:
        """value_or_error() returns value for Ok result."""
        result = Result.ok("success")
        assert result.value_or_error() == "success"

    def test_value_or_error_returns_error_for_err(self) -> None:
        """value_or_error() returns error for Err result."""
        result: Result[str] = Result.err("failure")
        assert result.value_or_error() == "failure"


class TestTransformations:
    """Tests for map() and chain() transformations."""

    def test_map_transforms_ok_value(self) -> None:
        """map() transforms Ok value."""
        result = Result.ok(5)
        mapped = result.map(lambda x: x * 2)
        assert mapped.unwrap() == 10

    def test_map_passes_through_err(self) -> None:
        """map() passes through Err unchanged."""
        result: Result[int] = Result.err("original error")
        mapped = result.map(lambda x: x * 2)
        assert mapped.is_err()
        assert mapped.unwrap_err() == "original error"

    def test_map_catches_exception(self) -> None:
        """map() catches exceptions and returns Err with 'map_exception'."""
        result = Result.ok(5)

        def failing_fn(_: int) -> int:
            raise ValueError("computation failed")

        mapped = result.map(failing_fn)
        assert mapped.is_err()
        assert mapped.error == "map_exception"
        assert mapped.context is not None
        assert isinstance(mapped.context["exception"], ValueError)

    def test_map_preserves_context(self) -> None:
        """map() preserves context from original result."""
        ctx = {"source": "test"}
        result = Result.ok(5, context=ctx)
        mapped = result.map(lambda x: x * 2)
        assert mapped.context == ctx

    def test_chain_transforms_ok_value(self) -> None:
        """chain() transforms Ok value with Result-returning function."""
        result = Result.ok(5)
        chained = result.chain(lambda x: Result.ok(x * 2))
        assert chained.unwrap() == 10

    def test_chain_passes_through_err(self) -> None:
        """chain() passes through Err unchanged."""
        result: Result[int] = Result.err("original error")
        chained = result.chain(lambda x: Result.ok(x * 2))
        assert chained.is_err()
        assert chained.unwrap_err() == "original error"

    def test_chain_catches_exception(self) -> None:
        """chain() catches exceptions and returns Err with 'chain_exception'."""
        result = Result.ok(5)

        def failing_fn(_: int) -> Result[int]:
            raise RuntimeError("chain failed")

        chained = result.chain(failing_fn)
        assert chained.is_err()
        assert chained.error == "chain_exception"
        assert chained.context is not None
        assert isinstance(chained.context["exception"], RuntimeError)


class TestAsyncTransformations:
    """Tests for map_async() and chain_async() transformations."""

    @pytest.mark.asyncio
    async def test_map_async_transforms_ok_value(self) -> None:
        """map_async() transforms Ok value."""
        result = Result.ok(5)

        async def double(x: int) -> int:
            return x * 2

        mapped = await result.map_async(double)
        assert mapped.unwrap() == 10

    @pytest.mark.asyncio
    async def test_map_async_passes_through_err(self) -> None:
        """map_async() passes through Err unchanged."""
        result: Result[int] = Result.err("error")

        async def double(x: int) -> int:
            return x * 2

        mapped = await result.map_async(double)
        assert mapped.is_err()
        assert mapped.unwrap_err() == "error"

    @pytest.mark.asyncio
    async def test_map_async_catches_exception(self) -> None:
        """map_async() catches exceptions."""
        result = Result.ok(5)

        async def failing_fn(_: int) -> int:
            raise ValueError("async failed")

        mapped = await result.map_async(failing_fn)
        assert mapped.is_err()
        assert mapped.error == "map_exception"
        assert mapped.context is not None
        assert isinstance(mapped.context["exception"], ValueError)

    @pytest.mark.asyncio
    async def test_chain_async_transforms_ok_value(self) -> None:
        """chain_async() transforms Ok value."""
        result = Result.ok(5)

        async def double_result(x: int) -> Result[int]:
            return Result.ok(x * 2)

        chained = await result.chain_async(double_result)
        assert chained.unwrap() == 10

    @pytest.mark.asyncio
    async def test_chain_async_passes_through_err(self) -> None:
        """chain_async() passes through Err unchanged."""
        result: Result[int] = Result.err("error")

        async def double_result(x: int) -> Result[int]:
            return Result.ok(x * 2)

        chained = await result.chain_async(double_result)
        assert chained.is_err()
        assert chained.unwrap_err() == "error"

    @pytest.mark.asyncio
    async def test_chain_async_catches_exception(self) -> None:
        """chain_async() catches exceptions."""
        result = Result.ok(5)

        async def failing_fn(_: int) -> Result[int]:
            raise RuntimeError("async chain failed")

        chained = await result.chain_async(failing_fn)
        assert chained.is_err()
        assert chained.error == "chain_exception"
        assert chained.context is not None
        assert isinstance(chained.context["exception"], RuntimeError)


class TestContextAndCopying:
    """Tests for with_value(), with_error(), and to_dict()."""

    def test_with_value_creates_new_result_preserving_context(self) -> None:
        """with_value() creates new Result preserving context."""
        ctx = {"version": "1.0"}
        original = Result.ok(42, context=ctx)
        new_result = original.with_value("hello")
        assert new_result.unwrap() == "hello"
        assert new_result.context == ctx
        # Original unchanged
        assert original.unwrap() == 42

    def test_with_error_creates_err_preserving_context(self) -> None:
        """with_error() creates Err preserving context."""
        ctx = {"version": "1.0"}
        original = Result.ok(42, context=ctx)
        error_result = original.with_error("failed")
        assert error_result.is_err()
        assert error_result.unwrap_err() == "failed"
        assert error_result.context == ctx

    def test_to_dict_returns_proper_structure(self) -> None:
        """to_dict() returns proper dictionary structure."""
        ctx = {"key": "value"}
        result = Result.ok(42, context=ctx)
        d = result.to_dict()
        assert d == {"value": 42, "error": None, "context": ctx}

    def test_to_dict_for_err(self) -> None:
        """to_dict() returns proper structure for Err."""
        result: Result[int] = Result.err("error message")
        d = result.to_dict()
        assert d["value"] is None
        assert d["error"] == "error message"

    def test_to_dict_safe_exception_converts_exception_to_string(self) -> None:
        """to_dict(safe_exception=True) converts exception to string and removes traceback."""
        exc = ValueError("bad value")
        result: Result[int] = Result.err(exc)
        d = result.to_dict(safe_exception=True)
        assert d["context"] is not None
        assert d["context"]["exception"] == "bad value"
        assert "traceback" not in d["context"]


class TestSpecialMethods:
    """Tests for __repr__, __hash__, and __eq__."""

    def test_repr_for_ok(self) -> None:
        """__repr__() for Ok result."""
        result = Result.ok(42)
        assert repr(result) == "Result(value=42)"

    def test_repr_for_err(self) -> None:
        """__repr__() for Err result."""
        result: Result[int] = Result.err("failed")
        assert repr(result) == "Result(error='failed')"

    def test_repr_with_context(self) -> None:
        """__repr__() includes context."""
        ctx = {"k": "v"}
        result = Result.ok(1, context=ctx)
        assert "context={'k': 'v'}" in repr(result)

    def test_hash_works_and_is_consistent(self) -> None:
        """__hash__() works and is consistent."""
        result1 = Result.ok(42)
        result2 = Result.ok(42)
        assert hash(result1) == hash(result2)
        # Can be used in sets
        s = {result1, result2}
        assert len(s) == 1

    def test_hash_with_context(self) -> None:
        """__hash__() works with context."""
        result = Result.ok(42, context={"a": 1})
        h = hash(result)
        assert isinstance(h, int)

    def test_eq_for_equal_results(self) -> None:
        """__eq__() for equal Results."""
        ctx = {"key": "value"}
        result1 = Result.ok(42, context=ctx)
        result2 = Result.ok(42, context=ctx)
        assert result1 == result2

    def test_eq_for_different_results(self) -> None:
        """__eq__() for different Results."""
        result1 = Result.ok(42)
        result2 = Result.ok(99)
        assert result1 != result2

    def test_eq_with_non_result_returns_false(self) -> None:
        """__eq__() with non-Result returns False."""
        result = Result.ok(42)
        assert result != 42
        assert result != "ok"
        assert result != None  # noqa: E711


class TestExceptions:
    """Tests for custom exceptions."""

    def test_unwrap_error_is_raised_correctly(self) -> None:
        """UnwrapError is raised with correct message."""
        result: Result[int] = Result.err("test error")
        with pytest.raises(UnwrapError) as exc_info:
            result.unwrap()
        assert "test error" in str(exc_info.value)

    def test_unwrap_err_error_is_raised_correctly(self) -> None:
        """UnwrapErrError is raised with correct message."""
        result = Result.ok(42)
        with pytest.raises(UnwrapErrError) as exc_info:
            result.unwrap_err()
        assert "success value" in str(exc_info.value)
