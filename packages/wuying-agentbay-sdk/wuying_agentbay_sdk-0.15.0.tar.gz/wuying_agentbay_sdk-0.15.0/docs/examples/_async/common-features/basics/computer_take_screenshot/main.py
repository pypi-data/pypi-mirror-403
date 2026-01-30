import asyncio
import os

from agentbay import AsyncAgentBay, CreateSessionParams


async def main() -> None:
    api_key = os.environ.get("AGENTBAY_API_KEY")
    if not api_key:
        raise RuntimeError("AGENTBAY_API_KEY is not set")

    agent_bay = AsyncAgentBay(api_key=api_key)
    session = None
    try:
        params = CreateSessionParams(image_id="linux_latest")
        result = await agent_bay.create(params)
        if not result.success or not result.session:
            raise RuntimeError(f"Failed to create session: {result.error_message}")

        session = result.session
        screenshot = await session.computer.beta_take_screenshot(format="jpg")
        if not screenshot.success:
            raise RuntimeError(f"Screenshot failed: {screenshot.error_message}")

        os.makedirs("./tmp", exist_ok=True)
        out_path = "./tmp/computer_take_screenshot.jpg"
        with open(out_path, "wb") as f:
            f.write(screenshot.data)

        print(
            f"Saved screenshot to: {out_path} ({len(screenshot.data)} bytes, format={screenshot.format}, "
            f"size={screenshot.width}x{screenshot.height})"
        )
    finally:
        if session is not None:
            await session.delete()


if __name__ == "__main__":
    asyncio.run(main())

