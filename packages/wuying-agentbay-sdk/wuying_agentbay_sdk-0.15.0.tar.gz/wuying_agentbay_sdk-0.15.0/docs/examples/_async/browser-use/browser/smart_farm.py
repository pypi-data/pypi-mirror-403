"""
示例：农业物联网平台自动化操作
功能：实现自动登录农场管理系统、多步骤复杂 UI 交互以及环境数据分析提取。
重点：利用自然语言指令编排动作、基于视觉（use_vision）的图标与位置识别、以及页面关键信息的智能提取。
"""

import os
import asyncio
import json
from typing import Optional
from pydantic import BaseModel, Field
from agentbay import AsyncAgentBay as AgentBay
from agentbay import CreateSessionParams, BrowserOption, ActOptions, ExtractOptions


class PageContent(BaseModel):
    title: str = Field(..., description="this is the title of the page")
    summary: Optional[str] = Field(..., description="A summary of the page content.")


async def main():
    api_key = os.getenv("AGENTBAY_API_KEY")

    agent_bay = AgentBay(api_key=api_key)
    params = CreateSessionParams(image_id="browser_latest")
    session_result = await agent_bay.create(params)

    if session_result.success:
        session = session_result.session
        await session.browser.initialize(BrowserOption())
        agent = session.browser.agent

        await agent.navigate("https://cphengshuifarm10.connect.farmonline.net/")
        await agent.act_async(
            ActOptions(action="输入用户名 'guest' 密码不用输，点击 login按钮登录")
        )

        await agent.act(
            ActOptions(
                action="点击网页最右侧蓝色背景条上的绿色眼睛图标按钮，并点击搜索结果中的第一项",
                use_vision=True,
            )
        )
        await agent.act(ActOptions(action="在页面中点击 '气候' 选项"))
        await agent.act(ActOptions(action="点击 'CO2' 选项，然后点击页面空白处"))
        await agent.act(
            ActOptions(action="点击 'CO2' 下方的 'CO2' 文本区域", use_vision=True)
        )
        await agent.act(
            ActOptions(
                action="点击页面弹窗中间位置的蓝色矩形 '>' 箭头按钮，将关键字添加到右侧框",
                use_vision=True,
            )
        )
        await agent.act(ActOptions(action="点击 OK 按钮"))
        ok, data = await agent.extract(
            ExtractOptions(
                instruction="总结并分析当前网页中的环境监测数据和页面信息",
                schema=PageContent,
            )
        )
        if ok:
            print(f"Summary: {data.summary}")

        await asyncio.sleep(2)

    await agent.close()
    await agent_bay.delete(session)


if __name__ == "__main__":
    asyncio.run(main())
