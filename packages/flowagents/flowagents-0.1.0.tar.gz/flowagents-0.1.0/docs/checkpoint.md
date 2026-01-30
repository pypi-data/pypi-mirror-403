# Checkpoint & Replay

Save and restore agent state for debugging, recovery, and time-travel.

## Quick Start

```python
from flowagent import CheckpointManager, InMemoryCheckpointStorage

# Create checkpoint manager
storage = InMemoryCheckpointStorage()
checkpoint_mgr = CheckpointManager(storage=storage)

# Save checkpoint
checkpoint_id = await checkpoint_mgr.save(agent)

# Later: restore agent
restored_agent = await checkpoint_mgr.restore(checkpoint_id)
```

## Storage Backends

### In-Memory (Development)

```python
from flowagent import InMemoryCheckpointStorage

storage = InMemoryCheckpointStorage(max_checkpoints=1000)
```

### SQLite (Production)

```python
from flowagent import SQLiteCheckpointStorage

storage = SQLiteCheckpointStorage(
    db_path="checkpoints.db",
    max_checkpoints_per_user=100
)
```

### Custom Storage

```python
from flowagent import CheckpointStorage, Checkpoint

class MyStorage(CheckpointStorage):

    async def save(self, checkpoint: Checkpoint) -> str:
        # Save to your backend
        await self.db.insert(checkpoint.to_dict())
        return checkpoint.id

    async def load(self, checkpoint_id: str) -> Optional[Checkpoint]:
        # Load from your backend
        data = await self.db.find(checkpoint_id)
        return Checkpoint.from_dict(data) if data else None

    async def list_by_user(self, user_id: str, limit: int, offset: int) -> List[Checkpoint]:
        # List user's checkpoints
        return await self.db.find_many(user_id=user_id, limit=limit, offset=offset)
```

## Automatic Checkpointing

Enable automatic checkpoints on state changes:

```python
from flowagent import Orchestrator

orchestrator = Orchestrator(
    agents=[...],
    checkpoint_manager=checkpoint_mgr,
    auto_checkpoint=True  # Save on every state change
)
```

## Manual Checkpointing

Save at specific points:

```python
class MyAgent(StandardAgent):

    async def on_running(self, msg):
        # Do some work
        await self.expensive_operation()

        # Save checkpoint before risky operation
        if self.checkpoint_manager:
            await self.checkpoint_manager.save(self)

        # Continue with risky operation
        await self.risky_operation()
```

## Time-Travel Debugging

### List Checkpoints

```python
# Get all checkpoints for a user
checkpoints = await checkpoint_mgr.list_by_user(
    user_id="user_123",
    limit=50,
    offset=0
)

for cp in checkpoints:
    print(f"{cp.id}: {cp.status} at {cp.timestamp}")
```

### Restore to Point in Time

```python
# Find checkpoint before the error
checkpoints = await checkpoint_mgr.list_by_user("user_123")
target = next(cp for cp in checkpoints if cp.status == "RUNNING")

# Restore and retry
agent = await checkpoint_mgr.restore(target.id)
result = await agent.reply(Message(content="retry", role="user"))
```

### Compare Checkpoints

```python
# Compare two checkpoints
diff = await checkpoint_mgr.compare(checkpoint_id_1, checkpoint_id_2)

print(f"Changed fields: {diff.changed_fields}")
print(f"Status: {diff.old_status} -> {diff.new_status}")
```

## Checkpoint Data

Each checkpoint contains:

```python
@dataclass
class Checkpoint:
    id: str                    # Unique identifier
    agent_id: str              # Agent instance ID
    agent_type: str            # Agent class name
    user_id: str               # Tenant/user ID
    status: str                # Agent status at checkpoint
    collected_fields: dict     # Collected field values
    required_fields: list      # Field definitions
    context_summary: str       # Context at checkpoint
    parent_checkpoint_id: str  # Previous checkpoint (for chain)
    timestamp: datetime        # When checkpoint was created
    metadata: dict             # Custom metadata
```

## Checkpoint in Workflows

```yaml
# workflow.yaml
workflow:
  checkpoint: true

steps:
  - name: expensive_step
    agent: ExpensiveAgent
    checkpoint: true  # Save after this step

  - name: risky_step
    agent: RiskyAgent
    checkpoint: true
```

Resume workflow from checkpoint:

```python
result = await executor.run(
    workflow="workflow.yaml",
    checkpoint_id="chk_abc123"  # Resume from here
)
```

## Cleanup

```python
# Clear old checkpoints for a user
deleted_count = await checkpoint_mgr.clear_user_history(user_id="user_123")

# Clear checkpoints older than N days
await checkpoint_mgr.cleanup_old_checkpoints(max_age_days=30)
```

## Events

Subscribe to checkpoint events:

```python
@checkpoint_mgr.on("checkpoint_saved")
async def on_saved(checkpoint: Checkpoint):
    logger.info(f"Saved checkpoint: {checkpoint.id}")

@checkpoint_mgr.on("checkpoint_restored")
async def on_restored(checkpoint: Checkpoint, agent):
    logger.info(f"Restored agent from: {checkpoint.id}")
```

## Best Practices

1. **Checkpoint before risky operations** - Easy rollback on failure
2. **Use SQLite for production** - Persistent across restarts
3. **Set retention limits** - Don't store unlimited checkpoints
4. **Include metadata** - Add context for debugging
5. **Clean up regularly** - Remove old checkpoints
6. **Test restore** - Verify checkpoints work before you need them
