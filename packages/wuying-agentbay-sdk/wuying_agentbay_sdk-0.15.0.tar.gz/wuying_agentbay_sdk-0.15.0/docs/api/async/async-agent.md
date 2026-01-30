# AsyncAgent API Reference

> **💡 Sync Version**: This documentation covers the asynchronous API. For synchronous operations, see [`Agent`](../sync/agent.md).
>
> ⚡ **Performance Advantage**: Async API enables concurrent operations with 4-6x performance improvements for parallel tasks.

## 🤖 Related Tutorial

- [Agent Modules Guide](../../../../docs/guides/common-features/advanced/agent-modules.md) - Learn about agent modules and custom agents



## AsyncAgent

```python
class AsyncAgent(AsyncBaseService)
```

An Agent to manipulate applications to complete specific tasks.

> **⚠️ Note**: Currently, for agent services (including ComputerUseAgent, BrowserUseAgent, and MobileUseAgent), we do not provide services for overseas users registered with **alibabacloud.com**.

### __init__

```python
def __init__(self, session: "AsyncSession")
```

## Computer

```python
class Computer(_BaseTaskAgent)
```

An Agent to perform tasks on the computer.

> **⚠️ Note**: Currently, for agent services (including ComputerUseAgent, BrowserUseAgent, and MobileUseAgent), we do not provide services for overseas users registered with **alibabacloud.com**.

### __init__

```python
def __init__(self, session: "AsyncSession")
```

## Browser

```python
class Browser(_BaseTaskAgent)
```

An Agent(⚠️ Still in BETA) to perform tasks on the browser

> **⚠️ Note**: Currently, for agent services (including ComputerUseAgent, BrowserUseAgent, and MobileUseAgent), we do not provide services for overseas users registered with **alibabacloud.com**.

### __init__

```python
def __init__(self, session: "AsyncSession")
```

### execute_task

```python
async def execute_task(task: str,
                       use_vision: bool = False,
                       output_schema: Type[Schema] = None) -> ExecutionResult
```

Execute a task described in human language on a browser without waiting for completion (non-blocking).

This is a fire-and-return interface that immediately provides a task ID.
Call get_task_status to check the task status. You can control the timeout
of the task execution in your own code by setting the frequency of calling
get_task_status.

**Arguments**:

    task: Task description in human language.
    use_vision: Whether to use vision to performe the task.
    output_schema: The schema of the structured output.
  

**Returns**:

    ExecutionResult: Result object containing success status, task ID,
  task status, and error message if any.
  

**Example**:

```python
session_result = await agent_bay.create()
session = session_result.session
class WeatherSchema(BaseModel):
  city:str
  weather: str
result = await session.agent.browser.execute_task(task="Query the weather in Shanghai",use_vision=False, output_schema=WeatherSchema)
print(
  f"Task ID: {result.task_id}, Status: {result.task_status}")
status = await session.agent.browser.get_task_status(result.task_id)
print(f"Task status: {status.task_status}")
await session.delete()
```

### execute_task_and_wait

```python
async def execute_task_and_wait(
        task: str,
        timeout: int,
        use_vision: bool = False,
        output_schema: Type[Schema] = None) -> ExecutionResult
```

Execute a task described in human language on a browser synchronously.

This is a synchronous interface that blocks until the task is completed or
an error occurs, or timeout happens. The default polling interval is 3 seconds.

**Arguments**:

    task: Task description in human language.
    timeout: Maximum time to wait for task completion in seconds.
  Used to control how long to wait for task completion.
    use_vision: Whether to use vision to performe the task.
    output_schema: The schema of the structured output.
  

**Returns**:

    ExecutionResult: Result object containing success status, task ID,
  task status, and error message if any.
  

**Example**:

```python
session_result = await agent_bay.create()
session = session_result.session
class WeatherSchema(BaseModel):
  city:str
  weather: str
result = await session.agent.computer.execute_task_and_wait(task="Query the weather in Shanghai",timeout=60, use_vision=False, output_schema=WeatherSchema)
print(f"Task result: {result.task_result}")
await session.delete()
```

## Mobile

```python
class Mobile(_BaseTaskAgent)
```

An Agent to perform tasks on mobile devices.

> **⚠️ Note**: Currently, for agent services (including ComputerUseAgent, BrowserUseAgent, and MobileUseAgent), we do not provide services for overseas users registered with **alibabacloud.com**.

### __init__

```python
def __init__(self, session: "AsyncSession")
```

### execute_task

```python
async def execute_task(task: str, max_steps: int = 50) -> ExecutionResult
```

Execute a task in human language without waiting for completion
(non-blocking).

This is a fire-and-return interface that immediately provides a task ID.
Call get_task_status to check the task status. You can control the timeout
of the task execution in your own code by setting the frequency of calling
get_task_status.

**Arguments**:

    task: Task description in human language.
    max_steps: Maximum number of steps (clicks/swipes/etc.) allowed.
  Used to prevent infinite loops or excessive resource consumption.
  Default is 50.
  

**Returns**:

    ExecutionResult: Result object containing success status, task ID,
  task status, and error message if any.
  

**Example**:

```python
session_result = await agent_bay.create()
session = session_result.session
result = await session.agent.mobile.execute_task(
  "Open WeChat app", max_steps=100
)
print(f"Task ID: {result.task_id}, Status: {result.task_status}")
status = await session.agent.mobile.get_task_status(result.task_id)
print(f"Task status: {status.task_status}")
await session.delete()
```

### execute_task_and_wait

```python
async def execute_task_and_wait(task: str,
                                timeout: int,
                                max_steps: int = 50) -> ExecutionResult
```

Execute a specific task described in human language synchronously.

This is a synchronous interface that blocks until the task is
completed or an error occurs, or timeout happens. The default
polling interval is 3 seconds.

**Arguments**:

    task: Task description in human language.
    timeout: Maximum time to wait for task completion in seconds.
  Used to control how long to wait for task completion.
    max_steps: Maximum number of steps (clicks/swipes/etc.) allowed.
  Used to prevent infinite loops or excessive resource consumption.
  Default is 50.
  

**Returns**:

    ExecutionResult: Result object containing success status, task ID,
  task status, and error message if any.
  

**Example**:

```python
session_result = await agent_bay.create()
session = session_result.session
result = await session.agent.mobile.execute_task_and_wait(
  "Open WeChat app and send a message",
  timeout=180,
  max_steps=100
)
print(f"Task result: {result.task_result}")
await session.delete()
```

### get_task_status

```python
async def get_task_status(task_id: str) -> QueryResult
```

### terminate_task

```python
async def terminate_task(task_id: str) -> ExecutionResult
```

## See Also

- [Synchronous vs Asynchronous API](../../../docs/guides/async-programming/sync-vs-async.md)

**Related APIs:**
- [Session API Reference](./async-session.md)

---

*Documentation generated automatically from source code using pydoc-markdown.*
