## Computer Take Screenshot (Async)

This example demonstrates how to take a desktop screenshot using the MCP `screenshot` tool via `AsyncComputer.beta_take_screenshot()`.

### Prerequisites

- Python 3.10+
- Set `AGENTBAY_API_KEY` environment variable

### Run

```bash
export AGENTBAY_API_KEY=your_api_key_here
python main.py
```

### What it does

- Creates a `linux_latest` session
- Takes a screenshot in `jpg` format (normalized to `jpeg`)
- Saves the result to `./tmp/computer_take_screenshot.jpg`
- Deletes the session

