import json
import inspect
from typing import Any, AsyncGenerator, Generator, Optional, Union, cast
from fastapi.responses import StreamingResponse


class ServerSentEvent:
    """
    Helper to format data as Server-Sent Events (SSE).
    """

    def __init__(
        self,
        data: Any,
        event: Optional[str] = None,
        id: Optional[str] = None,
        retry: Optional[int] = None,
    ) -> None:
        self.data = data
        self.event = event
        self.id = id
        self.retry = retry

    def encode(self) -> str:
        buffer = ""
        if self.id is not None:
            buffer += f"id: {self.id}\n"
        if self.event is not None:
            buffer += f"event: {self.event}\n"
        if self.retry is not None:
            buffer += f"retry: {self.retry}\n"

        # Handle Data Serialization
        if isinstance(self.data, (dict, list, bool)):
            data_str = json.dumps(self.data)
        else:
            data_str = str(self.data)

        buffer += f"data: {data_str}\n\n"
        return buffer


async def sse_generator(
    generator: Union[AsyncGenerator, Generator],
    transform_fn=None
) -> AsyncGenerator[str, None]:
    """
    Wraps a generator to yield formatted SSE strings.
    """
    # Helper to process a single item
    def process_item(item):
        if isinstance(item, ServerSentEvent):
            return item.encode()
        # Default: treat raw yield as a data message
        return ServerSentEvent(data=item).encode()

    # Type Guard Logic:
    # Pyright doesn't know inspect.isasyncgen narrows the type automatically.
    # We use cast() to explicitly tell it what the type is in each branch.

    if inspect.isasyncgen(generator):
        async_gen = cast(AsyncGenerator, generator)
        async for item in async_gen:
            yield process_item(item)
    else:
        sync_gen = cast(Generator, generator)
        for item in sync_gen:
            yield process_item(item)


class SSE(StreamingResponse):
    """
    A StreamingResponse pre-configured for Server-Sent Events.
    Usage: return SSE(my_generator())
    """

    def __init__(
        self,
        content: Union[AsyncGenerator, Generator],
        status_code: int = 200,
        headers: Optional[dict] = None,
        media_type: str = "text/event-stream",
        background=None,
    ) -> None:
        # Merge default SSE headers
        _headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no",  # Nginx no-buffer
        }
        if headers:
            _headers.update(headers)

        super().__init__(
            content=sse_generator(content),
            status_code=status_code,
            headers=_headers,
            media_type=media_type,
            background=background
        )
