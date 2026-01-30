# Memory System

FlowAgent provides long-term memory capabilities powered by mem0.

## Quick Start

```python
from flowagent import MemoryManager

# Initialize memory manager
memory = MemoryManager(
    api_key="your-mem0-api-key",  # mem0 platform
    # Or use self-hosted:
    # config={"vector_store": {"provider": "qdrant", "url": "..."}}
)

# Store a memory
memory.add_text(
    "User prefers window seats on flights",
    user_id="user_123",
    agent_type="FlightAgent"
)

# Search memories
results = memory.search(
    query="seat preferences",
    user_id="user_123",
    limit=5
)
```

## Memory Operations

### Add Memory from Conversation

```python
# Add from message history
memory.add_messages(
    messages=[
        {"role": "user", "content": "I'm allergic to peanuts"},
        {"role": "assistant", "content": "I've noted your peanut allergy"}
    ],
    user_id="user_123"
)
```

### Add Text Memory

```python
memory.add_text(
    text="User's email is alice@example.com",
    user_id="user_123",
    agent_type="ContactAgent",
    metadata={"source": "profile_update"}
)
```

### Search Memories

```python
# Semantic search
results = memory.search(
    query="dietary restrictions",
    user_id="user_123",
    limit=10
)

for result in results:
    print(f"Memory: {result['text']}")
    print(f"Score: {result['score']}")
```

### Get All Memories

```python
all_memories = memory.get_all(user_id="user_123")
```

### Delete Memories

```python
# Delete specific memory
memory.delete(memory_id="mem_abc123")

# Delete all user memories
memory.delete_all(user_id="user_123")
```

## Integration with Agents

### Using MemoryMixin

```python
from flowagent import StandardAgent, MemoryMixin

class MyAgent(MemoryMixin, StandardAgent):

    async def on_running(self, msg):
        # Recall relevant memories
        memories = await self.recall_memories(msg.get_text())

        # Use memories in response
        context = "\n".join([m["text"] for m in memories])

        # Store new memory
        await self.store_memory(f"User asked about: {msg.get_text()}")

        return self.make_result(...)
```

### With Orchestrator

```python
orchestrator = Orchestrator(
    agents=[...],
    memory_manager=memory,
)

# Memory is automatically:
# 1. Recalled before agent execution
# 2. Injected into agent context
# 3. Stored after successful completion
```

## Configuration

### mem0 Platform (Hosted)

```python
memory = MemoryManager(
    api_key="your-api-key",
    org_id="your-org-id",      # Optional
    project_id="your-project"  # Optional
)
```

### Self-Hosted

```python
memory = MemoryManager(
    config={
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "url": "http://localhost:6333"
            }
        },
        "llm": {
            "provider": "openai",
            "config": {
                "model": "gpt-4",
                "api_key": "sk-..."
            }
        },
        "embedder": {
            "provider": "openai",
            "config": {
                "model": "text-embedding-3-small",
                "api_key": "sk-..."
            }
        }
    }
)
```

## Memory in Workflows

```yaml
# workflow.yaml
agents:
  FlightAgent:
    enable_memory: true
    memory_config:
      recall_limit: 10
      store_on_complete: true

  HotelAgent:
    enable_memory: true
```

## Filtering

### By Agent Type

```python
results = memory.search(
    query="preferences",
    user_id="user_123",
    agent_type="FlightAgent"  # Only FlightAgent memories
)
```

### By Metadata

```python
results = memory.search(
    query="preferences",
    user_id="user_123",
    filters={"source": "profile_update"}
)
```

## Memory Context Builder

Build context strings for LLM prompts:

```python
context = memory.build_context(
    query="book a flight",
    user_id="user_123",
    max_tokens=500
)

# Returns formatted string:
# "Relevant memories:
#  - User prefers window seats
#  - User's home airport is JFK
#  - User is allergic to peanuts"
```

## Automatic Memory Extraction

Let the LLM decide what to remember:

```python
memory.add_with_extraction(
    messages=[
        {"role": "user", "content": "My birthday is March 15th and I love Italian food"},
        {"role": "assistant", "content": "Great! I'll remember that."}
    ],
    user_id="user_123"
)

# Automatically extracts:
# - "User's birthday is March 15th"
# - "User loves Italian food"
```

## Best Practices

1. **Use specific queries** - Better semantic search results
2. **Include agent_type** - Organize memories by domain
3. **Add metadata** - For filtering and debugging
4. **Set limits** - Don't retrieve too many memories
5. **Clean up** - Remove outdated memories periodically
6. **Test relevance** - Verify memories improve responses
