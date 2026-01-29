"""mm-result: Functional error handling for Python using Result types.

A Result[T] represents either a successful value (Ok) or an error (Err).
Each result can carry additional metadata in the `context` field.

Basic usage:
    from mm_result import Result

    def fetch_user(user_id: int) -> Result[dict]:
        if user_id <= 0:
            return Result.err("Invalid user ID")
        return Result.ok({"id": user_id, "name": "John"})

    result = fetch_user(123)
    if result.is_ok():
        print(result.unwrap())

Using context for metadata:
    def fetch_data(url: str) -> Result[bytes]:
        try:
            response = httpx.get(url)
            return Result.ok(response.content, context={
                "status_code": response.status_code,
                "elapsed_ms": response.elapsed.total_seconds() * 1000,
            })
        except httpx.RequestError as e:
            return Result.err(e, context={"url": url})

    result = fetch_data("https://example.com")
    if result.is_ok():
        print(f"Got {len(result.unwrap())} bytes in {result.context['elapsed_ms']:.0f}ms")
"""

from .result import Result as Result
from .result import UnwrapErrError as UnwrapErrError
from .result import UnwrapError as UnwrapError
