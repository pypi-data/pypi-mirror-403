# mm-result

Functional error handling for Python using Result types inspired by Rust.

A `Result[T]` represents either a successful value (`Ok`) or an error (`Err`), enabling functional programming patterns for error handling without exceptions. Each result can optionally carry additional metadata in the `context` field for context like performance metrics, HTTP details, or debugging information.

## Quick Start

```python
from mm_result import Result
import time

def fetch_user_data(user_id: int) -> Result[dict]:
    start_time = time.time()

    if user_id <= 0:
        return Result.err("Invalid user ID", context={
            "user_id": user_id,
            "validation_rule": "user_id > 0"
        })

    # Simulate API call
    if user_id == 999:
        return Result.err("User not found", context={
            "user_id": user_id,
            "response_time_ms": round((time.time() - start_time) * 1000),
            "status_code": 404
        })

    user_data = {"id": user_id, "name": f"User {user_id}"}
    return Result.ok(user_data, context={
        "response_time_ms": round((time.time() - start_time) * 1000),
        "cache_hit": False,
        "status_code": 200
    })

# Using explicit success checking
result = fetch_user_data(123)
if result.is_ok():
    user = result.unwrap()
    print(f"Success: {user['name']}")
    print(f"Response time: {result.context['response_time_ms']}ms")
else:
    error = result.unwrap_err()
    print(f"Error: {error}")
    if "status_code" in result.context:
        print(f"HTTP Status: {result.context['status_code']}")
```

## Core Features

### Creating Results

```python
# Success values
result = Result.ok(42)
result = Result.ok(None)  # Ok with None value
result = Result.ok("data", context={"metadata": "info"})

# Error values
result = Result.err("Something went wrong")
result = Result.err("Network timeout", context={"retry_count": 3, "endpoint": "/api/users"})
result = Result.err(ValueError("Bad input"))  # From exception
result = Result.err(("Custom error", exc))    # Custom message + exception
```

### Checking Results

```python
result = Result.ok(42)

result.is_ok()    # True
result.is_err()   # False

if result.is_ok():  # Explicit way to check success
    print("Success!")
```

### Extracting Values

```python
result = Result.ok(42)

# Extract value (raises UnwrapError if error)
value = result.unwrap()                    # 42
value = result.unwrap("Custom message")    # With custom error message

# Extract value with fallback
value = result.unwrap_or(0)               # 42, or 0 if error

# Extract error (raises UnwrapErrError if success)
error = Result.err("oops").unwrap_err() # "oops"

# Get either value or error
content = result.value_or_error()         # Returns T | str
```

### Transforming Results

```python
# Map over success values
result = Result.ok(5)
doubled = result.map(lambda x: x * 2)     # Result.ok(10)

# Chain operations
result = Result.ok(5)
chained = result.chain(lambda x: Result.ok(x * 2))  # Result.ok(10)

# Async versions
async def async_double(x):
    return x * 2

doubled = await result.map_async(async_double)
```

### Error Handling with Context Data

The `context` field allows attaching arbitrary metadata:

```python
# HTTP request context
result = Result.err("Network timeout", context={
    "status_code": 408,
    "response_time_ms": 5000,
    "retry_count": 3,
    "endpoint": "/api/data"
})

# Performance metrics
result = Result.ok(data, context={
    "cache_hit": True,
    "query_time_ms": 15,
    "server": "prod-01"
})

# Exception details (automatic)
try:
    risky_operation()
except Exception as e:
    result = Result.err(e)  # Auto-captures exception + traceback in context
```

### JSON Serialization

By default, `Result.to_dict()` may contain non-serializable objects like exceptions. Use `safe_exception=True` for JSON-safe output:

```python
import json

try:
    data = json.loads("invalid json")
except json.JSONDecodeError as e:
    result = Result.err(e)

# This would fail - exception objects aren't JSON serializable
# json.dumps(result.to_dict())  # TypeError!

# This works - converts exceptions to strings
safe_dict = result.to_dict(safe_exception=True)
json_string = json.dumps(safe_dict)  # ✅ Success

# safe_dict contains:
# {
#     "value": None,
#     "error": "JSONDecodeError: Expecting value...",
#     "context": {"exception": "Expecting value..."}  # String, not object
#     # "traceback" is removed completely
# }
```

## Advanced Usage

### Exception Safety

Operations like `map()` and `chain()` automatically catch exceptions:

```python
def might_fail(x):
    if x < 0:
        raise ValueError("Negative input")
    return x * 2

result = Result.ok(-5)
safe_result = result.map(might_fail)  # Captures exception safely
# safe_result.is_err() == True
# safe_result.context["exception"] contains the ValueError
```

### Working with Copies

```python
original = Result.ok(42, context={"version": "1.0"})

# Create new result with different value, preserving context
new_result = original.with_value("hello")
# new_result.unwrap() == "hello"
# new_result.context == {"version": "1.0"}

# Create error from success, preserving context
error_result = original.with_error("Something failed")
```

## Pydantic Integration

Works automatically when pydantic is installed:

```python
from pydantic import BaseModel
from mm_result import Result

class ApiResponse(BaseModel):
    result: Result[dict]
    timestamp: str

# Serialization
response = ApiResponse(
    result=Result.ok({"key": "value"}),
    timestamp="2024-01-01T00:00:00Z"
)
data = response.model_dump()
# {
#     "result": {"value": {"key": "value"}, "error": None, "context": None},
#     "timestamp": "2024-01-01T00:00:00Z"
# }

# Deserialization
response2 = ApiResponse.model_validate(data)
assert response2.result.is_ok()
assert response2.result.unwrap() == {"key": "value"}
```

## API Reference

### Result[T]

#### Class Methods
- `Result.ok(value: T, context: dict = None) -> Result[T]` - Create success result
- `Result.err(error: str | Exception | tuple, context: dict = None) -> Result[T]` - Create error result

#### Instance Methods
- `is_ok() -> bool` - Check if result is success
- `is_err() -> bool` - Check if result is error
- `unwrap(message_prefix: str = None, include_error: bool = True) -> T` - Extract value or raise
- `unwrap_or(default: T) -> T` - Extract value or return default
- `unwrap_err() -> str` - Extract error message or raise
- `value_or_error() -> T | str` - Extract value or error
- `map(fn: Callable[[T], U]) -> Result[U]` - Transform success value
- `chain(fn: Callable[[T], Result[U]]) -> Result[U]` - Chain operations
- `map_async(fn: Callable[[T], Awaitable[U]]) -> Result[U]` - Async transform
- `chain_async(fn: Callable[[T], Awaitable[Result[U]]]) -> Result[U]` - Async chain
- `with_value(value: U) -> Result[U]` - Copy with new value
- `with_error(error) -> Result[T]` - Copy as error
- `to_dict(safe_exception: bool = False) -> dict[str, Any]` - Dictionary representation

#### Custom Exceptions
- `UnwrapError` - Raised when `unwrap()` is called on an Err result
- `UnwrapErrError` - Raised when `unwrap_err()` is called on an Ok result
