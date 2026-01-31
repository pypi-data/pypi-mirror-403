# Memorer Python SDK

Memory for AI agents. Remember conversations, recall context, forget when needed.

```bash
pip install memorer
```

## Usage

```python
from memorer import Memorer

client = Memorer(api_key="mem_sk_...")
user = client.for_user("user-123")

# During conversation, store what matters
user.remember("User mentioned they're allergic to shellfish")
user.remember("Has a meeting with Sarah next Friday at 2pm")
user.remember("Just adopted a dog named Biscuit")

# Before responding, recall relevant context
results = user.recall("any dietary restrictions?")
print(results.context)
# → "User is allergic to shellfish"

results = user.recall("what's on their schedule?")
print(results.context)
# → "Meeting with Sarah on Friday at 2pm"
```

## Graph Reasoning

Connect memories across conversations:

```python
results = user.recall(
    "gift ideas for them",
    use_graph_reasoning=True,
)
# → Connects: new dog + mentioned liking outdoors → dog hiking gear
```

## Resources

```python
entities = user.entities.list()
memories = user.memories.list()
communities = client.graph.communities()
```

## Links

- [Docs](https://docs.memorer.ai)
- [API Reference](https://docs.memorer.ai/api)
