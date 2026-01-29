"""Tests for Pydantic integration with Result type."""

from typing import Any

import pytest
from pydantic import BaseModel, TypeAdapter

from mm_result import Result


class ContainerModel(BaseModel):
    """Test model containing a Result field."""

    result: Result[Any]


class TestPydanticSerialization:
    """Tests for serializing Result via Pydantic."""

    def test_ok_result_serializes_to_dict(self) -> None:
        """model_dump() returns correct dict for Ok result."""
        model = ContainerModel(result=Result.ok(42))
        data = model.model_dump()
        assert data["result"] == {"value": 42, "error": None, "context": None}

    def test_err_result_serializes_to_dict(self) -> None:
        """model_dump() returns correct dict for Err result."""
        model = ContainerModel(result=Result.err("something failed"))
        data = model.model_dump()
        assert data["result"]["value"] is None
        assert data["result"]["error"] == "something failed"

    def test_result_with_context_serializes_context(self) -> None:
        """Context is included in serialized output."""
        ctx = {"response_time_ms": 150, "status_code": 200}
        model = ContainerModel(result=Result.ok("data", context=ctx))
        data = model.model_dump()
        assert data["result"]["context"] == ctx

    def test_none_value_serializes_correctly(self) -> None:
        """Ok(None) serializes properly."""
        model = ContainerModel(result=Result.ok(None))
        data = model.model_dump()
        assert data["result"]["value"] is None
        assert data["result"]["error"] is None
        assert data["result"]["context"] is None

    def test_exception_in_context_converted_to_string(self) -> None:
        """Exceptions become strings via safe_exception=True."""
        exc = ValueError("bad input")
        model = ContainerModel(result=Result.err(exc))
        data = model.model_dump()
        # Exception should be converted to string via safe_exception=True
        assert data["result"]["context"]["exception"] == "bad input"
        assert "traceback" not in data["result"]["context"]


class TestPydanticDeserialization:
    """Tests for deserializing Result via Pydantic."""

    def test_ok_dict_deserializes_to_ok_result(self) -> None:
        """model_validate() reconstructs Ok result from dict."""
        data = {"result": {"value": 42, "error": None, "context": None}}
        model = ContainerModel.model_validate(data)
        assert model.result.is_ok()
        assert model.result.unwrap() == 42

    def test_err_dict_deserializes_to_err_result(self) -> None:
        """model_validate() reconstructs Err result from dict."""
        data = {"result": {"value": None, "error": "failed", "context": None}}
        model = ContainerModel.model_validate(data)
        assert model.result.is_err()
        assert model.result.unwrap_err() == "failed"

    def test_result_with_context_deserializes_context(self) -> None:
        """Context is preserved during deserialization."""
        ctx = {"retry_count": 3, "endpoint": "/api"}
        data = {"result": {"value": "ok", "error": None, "context": ctx}}
        model = ContainerModel.model_validate(data)
        assert model.result.context == ctx

    def test_result_instance_passes_through(self) -> None:
        """Existing Result instance is returned as-is."""
        original = Result.ok("test")
        model = ContainerModel(result=original)
        # The same instance should be preserved
        assert model.result is original


class TestPydanticRoundTrip:
    """Tests for serialize → deserialize round-trips."""

    def test_ok_result_round_trip(self) -> None:
        """Serialize → deserialize preserves Ok result."""
        original = ContainerModel(result=Result.ok({"key": "value"}))
        data = original.model_dump()
        restored = ContainerModel.model_validate(data)
        assert restored.result.is_ok()
        assert restored.result.unwrap() == {"key": "value"}

    def test_err_result_round_trip(self) -> None:
        """Serialize → deserialize preserves Err result."""
        original = ContainerModel(result=Result.err("network timeout"))
        data = original.model_dump()
        restored = ContainerModel.model_validate(data)
        assert restored.result.is_err()
        assert restored.result.unwrap_err() == "network timeout"

    def test_result_with_context_round_trip(self) -> None:
        """Context survives round-trip."""
        ctx = {"cache_hit": True, "server": "prod-01"}
        original = ContainerModel(result=Result.ok("data", context=ctx))
        data = original.model_dump()
        restored = ContainerModel.model_validate(data)
        assert restored.result.context == ctx


class TestPydanticValidationErrors:
    """Tests for validation error handling."""

    def test_invalid_input_raises_type_error(self) -> None:
        """Non-dict, non-Result raises TypeError."""
        adapter: TypeAdapter[Result[Any]] = TypeAdapter(Result[Any])
        with pytest.raises(TypeError, match="Invalid value for Result"):
            adapter.validate_python("not a result")

        with pytest.raises(TypeError, match="Invalid value for Result"):
            adapter.validate_python(123)

        with pytest.raises(TypeError, match="Invalid value for Result"):
            adapter.validate_python(["list", "value"])
