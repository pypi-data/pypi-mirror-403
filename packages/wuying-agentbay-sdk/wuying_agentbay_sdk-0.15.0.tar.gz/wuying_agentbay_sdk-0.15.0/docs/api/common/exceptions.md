# Exceptions API Reference

## AgentBayError

```python
class AgentBayError(Exception)
```

Base exception for all AgentBay SDK errors.

### __init__

```python
def __init__(self, message=None, *args, **kwargs)
```

## AuthenticationError

```python
class AuthenticationError(AgentBayError)
```

Raised when there is an authentication error.

### __init__

```python
def __init__(self, message="Authentication failed", *args, **kwargs)
```

## APIError

```python
class APIError(AgentBayError)
```

Raised when there is an error with the API.

### __init__

```python
def __init__(self, message="API error", status_code=None, *args, **kwargs)
```

## FileError

```python
class FileError(AgentBayError)
```

Raised for errors related to file operations.

### __init__

```python
def __init__(self, message="File operation error", *args, **kwargs)
```

## CommandError

```python
class CommandError(AgentBayError)
```

Raised for errors related to command execution.

### __init__

```python
def __init__(self, message="Command execution error", *args, **kwargs)
```

## SessionError

```python
class SessionError(AgentBayError)
```

Raised for errors related to session operations.

### __init__

```python
def __init__(self, message="Session error", *args, **kwargs)
```

## OssError

```python
class OssError(AgentBayError)
```

Raised for errors related to OSS operations.

### __init__

```python
def __init__(self, message="OSS operation error", *args, **kwargs)
```

## BrowserError

```python
class BrowserError(AgentBayError)
```

Raised when there is an error with the browser.

### __init__

```python
def __init__(self, message="Browser error", *args, **kwargs)
```

## AgentError

```python
class AgentError(AgentBayError)
```

Raised for errors related to Agent actions.

### __init__

```python
def __init__(self, message="Agent action error", *args, **kwargs)
```

## ClearanceTimeoutError

```python
class ClearanceTimeoutError(AgentBayError)
```

Raised when context clearing operation times out.

### __init__

```python
def __init__(self, message="Context clearing operation timed out", *args, **kwargs)
```

## See Also

- [Synchronous vs Asynchronous API](../../../docs/guides/async-programming/sync-vs-async.md)

---

*Documentation generated automatically from source code using pydoc-markdown.*
