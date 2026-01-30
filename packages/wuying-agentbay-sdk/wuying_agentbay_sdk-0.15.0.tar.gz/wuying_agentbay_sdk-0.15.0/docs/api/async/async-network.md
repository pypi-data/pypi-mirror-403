# AsyncNetwork API Reference

> **💡 Sync Version**: This documentation covers the asynchronous API. For synchronous operations, see [`Network`](../sync/network.md).
>
> ⚡ **Performance Advantage**: Async API enables concurrent operations with 4-6x performance improvements for parallel tasks.

## 🌐 Related Tutorial

- [Network (Beta) Guide](../../../../docs/guides/common-features/advanced/network.md) - Redirect cloud traffic through your local network

## Overview

The Network module provides network redirection between your local environment and the AgentBay cloud runtime.
It allows a cloud session to use your local network egress, which can help reduce risk-control issues in certain websites or mobile apps.




## AsyncBetaNetworkService

```python
class AsyncBetaNetworkService()
```

Beta network service (trial feature).

### __init__

```python
def __init__(self, agent_bay: "AsyncAgentBay")
```

### get_network_bind_token

```python
async def get_network_bind_token(
        network_id: Optional[str] = None) -> NetworkResult
```

### describe

```python
async def describe(network_id: str) -> NetworkStatusResult
```

## Best Practices

1. Keep network tokens secure and never commit them to source control
2. Ensure the local binding process is running and reachable while the session is active
3. Check network readiness before creating sessions bound to it
4. Use a dedicated custom image when required by your environment policy

## See Also

- [Synchronous vs Asynchronous API](../../../docs/guides/async-programming/sync-vs-async.md)

**Related APIs:**
- [AgentBay API Reference](./async-agentbay.md)
- [Session Params API Reference](./async-session-params.md)
- [Session API Reference](./async-session.md)
- [Command API Reference](./async-command.md)

---

*Documentation generated automatically from source code using pydoc-markdown.*
