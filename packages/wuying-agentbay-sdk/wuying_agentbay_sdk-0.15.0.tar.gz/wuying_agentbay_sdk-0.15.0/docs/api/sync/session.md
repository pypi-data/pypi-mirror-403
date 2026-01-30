# Session API Reference

> **💡 Async Version**: This documentation covers the synchronous API. For async/await support, see [`AsyncSession`](../async/async-session.md) which provides the same functionality with async methods.

## 🔧 Related Tutorial

- [Session Management Guide](../../../../docs/guides/common-features/basics/session-management.md) - Detailed tutorial on session lifecycle and management



## SessionStatusResult

```python
class SessionStatusResult(ApiResponse)
```

Result of Session.get_status() (status only).

### __init__

```python
def __init__(self, request_id: str = "",
             http_status_code: int = 0,
             code: str = "",
             success: bool = False,
             status: str = "",
             error_message: str = "")
```

### __init__

```python
def __init__(self, session_id: str = "",
             resource_url: str = "",
             app_id: str = "",
             auth_code: str = "",
             connection_properties: str = "",
             resource_id: str = "",
             resource_type: str = "",
             ticket: str = "")
```

## Session

```python
class Session()
```

Session represents a session in the AgentBay cloud environment.

### __init__

```python
def __init__(self, agent_bay: "AgentBay", session_id: str)
```

### fs

```python
@property
def fs() -> FileSystem
```

Alias of file_system.

### filesystem

```python
@property
def filesystem() -> FileSystem
```

Alias of file_system.

### files

```python
@property
def files() -> FileSystem
```

Alias of file_system.

### get_token

```python
def get_token() -> str
```

### get_link_url

```python
def get_link_url() -> str
```

### getToken

```python
def getToken() -> str
```

### getLinkUrl

```python
def getLinkUrl() -> str
```

### get_status

```python
def get_status() -> "SessionStatusResult"
```

Get basic session status asynchronously.

**Returns**:

    SessionStatusResult: Result containing session status only.

### delete

```python
def delete(sync_context: bool = False) -> DeleteResult
```

Delete this session and release all associated resources.

**Arguments**:

- `sync_context` _bool, optional_ - Whether to sync context data (trigger file uploads)
  before deleting the session. Defaults to False.
  

**Returns**:

    DeleteResult: Result indicating success or failure with request ID.
  - success (bool): True if deletion succeeded
  - error_message (str): Error details if deletion failed
  - request_id (str): Unique identifier for this API request
  

**Raises**:

    SessionError: If the deletion request fails or the response is invalid.

### set_labels

```python
def set_labels(labels: Dict[str, str]) -> OperationResult
```

Sets the labels for this session asynchronously.

### get_labels

```python
def get_labels() -> OperationResult
```

Gets the labels for this session asynchronously.

### info

```python
def info() -> OperationResult
```

Get detailed information about this session asynchronously.

### get_link

```python
def get_link(protocol_type: Optional[str] = None,
             port: Optional[int] = None,
             options: Optional[str] = None) -> OperationResult
```

Asynchronously get a link associated with the current session.

### list_mcp_tools

```python
def list_mcp_tools(image_id: Optional[str] = None)
```

List MCP tools available for this session asynchronously.

### call_mcp_tool

```python
def call_mcp_tool(tool_name: str,
                  args: Dict[str, Any],
                  read_timeout: Optional[int] = None,
                  connect_timeout: Optional[int] = None,
                  auto_gen_session: bool = False)
```

Call an MCP tool directly asynchronously.

### get_metrics

```python
def get_metrics(read_timeout: Optional[int] = None,
                connect_timeout: Optional[int] = None) -> SessionMetricsResult
```

Get runtime metrics for this session.

The underlying service returns a JSON string. This method parses it and
returns a structured result.

### beta_pause

```python
def beta_pause(timeout: int = 600,
               poll_interval: float = 2.0) -> SessionPauseResult
```

Asynchronously pause this session (beta), putting it into a dormant state.
This method waits until the session enters the PAUSED state.

### beta_pause_async

```python
def beta_pause_async() -> SessionPauseResult
```

Asynchronously initiate the pause session operation without waiting for completion.

### beta_resume

```python
def beta_resume(timeout: int = 600,
                poll_interval: float = 2.0) -> SessionResumeResult
```

Asynchronously resume this session (beta) from a paused state.
This method waits until the session enters the RUNNING state.

### beta_resume_async

```python
def beta_resume_async() -> SessionResumeResult
```

Asynchronously initiate the resume session operation without waiting for completion.

## See Also

- [Synchronous vs Asynchronous API](../../../docs/guides/async-programming/sync-vs-async.md)

**Related APIs:**
- [FileSystem API Reference](./filesystem.md)
- [Command API Reference](./command.md)
- [Context API Reference](./context.md)
- [Context Manager API Reference](./context-manager.md)
- [OSS API Reference](./oss.md)

---

*Documentation generated automatically from source code using pydoc-markdown.*
