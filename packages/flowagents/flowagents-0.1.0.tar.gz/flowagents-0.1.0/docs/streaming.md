# Streaming

FlowAgent supports real-time streaming for better user experience.

## Quick Start

```python
from flowagent import StreamEngine, StreamMode

engine = StreamEngine(mode=StreamMode.INCREMENTAL)

async for event in engine.stream(agent, message):
    if event.type == "message_chunk":
        print(event.content, end="", flush=True)
    elif event.type == "state_change":
        print(f"\n[State: {event.new_state}]")
```

## Stream Modes

### Incremental Mode

Streams content as it's generated:

```python
engine = StreamEngine(mode=StreamMode.INCREMENTAL)

async for event in engine.stream(agent, message):
    # Receive chunks as they arrive
    print(event.content, end="")
```

### Full Mode

Waits for complete response, then streams:

```python
engine = StreamEngine(mode=StreamMode.FULL)

async for event in engine.stream(agent, message):
    # Receive complete messages
    print(event.content)
```

## Event Types

| Event Type | Description |
|------------|-------------|
| `MESSAGE_CHUNK` | Partial message content |
| `MESSAGE_COMPLETE` | Full message finished |
| `STATE_CHANGE` | Agent state transition |
| `TOOL_CALL_START` | Tool execution started |
| `TOOL_CALL_END` | Tool execution completed |
| `ERROR` | An error occurred |
| `DONE` | Stream finished |

## Handling Events

```python
from flowagent import EventType

async for event in engine.stream(agent, message):
    match event.type:
        case EventType.MESSAGE_CHUNK:
            # Partial content
            ui.append_text(event.content)

        case EventType.STATE_CHANGE:
            # State transition
            ui.update_status(f"Status: {event.new_state}")

        case EventType.TOOL_CALL_START:
            # Tool starting
            ui.show_spinner(f"Running {event.tool_name}...")

        case EventType.TOOL_CALL_END:
            # Tool finished
            ui.hide_spinner()
            ui.show_result(event.tool_result)

        case EventType.ERROR:
            # Error occurred
            ui.show_error(event.error_message)

        case EventType.DONE:
            # Stream finished
            ui.complete()
```

## Streaming with Orchestrator

```python
orchestrator = Orchestrator(agents=[...], llm_client=client)

async for event in orchestrator.process_stream(
    message="Book a flight to Paris",
    tenant_id="user_123"
):
    handle_event(event)
```

## Streaming with LLM Clients

All built-in LLM clients support streaming:

```python
from flowagent import OpenAIClient

client = OpenAIClient(api_key="sk-xxx", model="gpt-4o-mini")

async for chunk in client.stream_completion(messages):
    print(chunk.content, end="", flush=True)
```

## Custom Stream Handler

Create a custom handler class:

```python
from flowagent import StreamHandler, StreamEvent

class MyStreamHandler(StreamHandler):

    async def on_chunk(self, event: StreamEvent):
        # Handle message chunks
        await self.websocket.send(event.content)

    async def on_state_change(self, event: StreamEvent):
        # Handle state changes
        await self.websocket.send(json.dumps({
            "type": "state",
            "state": event.new_state
        }))

    async def on_error(self, event: StreamEvent):
        # Handle errors
        await self.websocket.send(json.dumps({
            "type": "error",
            "message": event.error_message
        }))

# Use handler
handler = MyStreamHandler(websocket=ws)
await engine.stream_with_handler(agent, message, handler)
```

## WebSocket Integration

```python
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/chat")
async def chat(websocket: WebSocket):
    await websocket.accept()

    while True:
        message = await websocket.receive_text()

        async for event in orchestrator.process_stream(message):
            await websocket.send_json({
                "type": event.type.value,
                "content": event.content,
                "state": event.new_state,
            })
```

## Server-Sent Events (SSE)

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.get("/chat/stream")
async def chat_stream(message: str):
    async def event_generator():
        async for event in orchestrator.process_stream(message):
            yield f"data: {json.dumps(event.to_dict())}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

## Configuration

```python
engine = StreamEngine(
    mode=StreamMode.INCREMENTAL,
    buffer_size=100,           # Characters to buffer
    flush_interval=0.1,        # Seconds between flushes
    include_tool_calls=True,   # Include tool call events
    include_state_changes=True # Include state change events
)
```

## Best Practices

1. **Use incremental mode** - Better UX for long responses
2. **Handle all event types** - Don't ignore errors
3. **Buffer appropriately** - Balance responsiveness vs. efficiency
4. **Show progress** - Use state changes to show what's happening
5. **Graceful degradation** - Fall back to non-streaming if needed
