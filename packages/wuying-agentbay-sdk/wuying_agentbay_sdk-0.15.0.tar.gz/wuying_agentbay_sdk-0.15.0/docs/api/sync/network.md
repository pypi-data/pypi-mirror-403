# Network API Reference

> **💡 Async Version**: This documentation covers the synchronous API. For async/await support, see [`AsyncNetwork`](../async/async-network.md) which provides the same functionality with async methods.

## 🌐 Related Tutorial

- [Network (Beta) Guide](../../../../docs/guides/common-features/advanced/network.md) - Redirect cloud traffic through your local network

## Overview

The Network module provides network redirection between your local environment and the AgentBay cloud runtime.
It allows a cloud session to use your local network egress, which can help reduce risk-control issues in certain websites or mobile apps.




## SyncBetaNetworkService

```python
class SyncBetaNetworkService()
```

Beta network service (trial feature).

### __init__

```python
def __init__(self, agent_bay: "AgentBay")
```

### get_network_bind_token

```python
def get_network_bind_token(network_id: Optional[str] = None) -> NetworkResult
```

### describe

```python
def describe(network_id: str) -> NetworkStatusResult
```

## Best Practices

1. Keep network tokens secure and never commit them to source control
2. Ensure the local binding process is running and reachable while the session is active
3. Check network readiness before creating sessions bound to it
4. Use a dedicated custom image when required by your environment policy

## See Also

- [Synchronous vs Asynchronous API](../../../docs/guides/async-programming/sync-vs-async.md)

**Related APIs:**
- [AgentBay API Reference](./agentbay.md)
- [Session Params API Reference](./session-params.md)
- [Session API Reference](./session.md)
- [Command API Reference](./command.md)

---

*Documentation generated automatically from source code using pydoc-markdown.*
