"""File Operations Patterns Example"""
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from agentbay import AsyncAgentBay
from agentbay import CreateSessionParams


async def main():
    print("=== File Operations Patterns ===\n")
    client = AsyncAgentBay()
    session = None

    try:
        session_result = await client.create(CreateSessionParams(image_id="linux_latest"))
        session = session_result.session

        # Write file
        await session.fs.write("/tmp/test.txt", "Hello World")
        print("1. File written")

        # Read file
        result = await session.fs.read("/tmp/test.txt")
        print(f"2. File content: {result.content}")

        # Check file exists
        result = await session.command.run("ls -la /tmp/test.txt")
        print(f"3. File exists: {result.success}")

        print("\n=== Completed ===")

    finally:
        if session:
            await client.delete(session)


if __name__ == "__main__":
    asyncio.run(main())

