"""
示例：百度资讯搜索结果分页抽取
打开 baidu.com -> 搜索“小米手机” -> 点击“资讯” -> 多页抽取标题与链接
重点：extract 传 max_page 实现多页数据自动采集
"""

import asyncio
import os
import logging
from typing import List

from pydantic import BaseModel, Field

from agentbay import AsyncAgentBay as AgentBay
from agentbay import CreateSessionParams
from agentbay import BrowserOption
from agentbay import ActOptions, ExtractOptions


class PageLinkItem(BaseModel):
    title: str = Field(..., description="news title")
    link: str = Field(..., description="news url")


class PageLinkList(BaseModel):
    results: List[PageLinkItem] = Field(default_factory=list)


async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("baidu_news_extract")

    api_key = os.getenv("AGENTBAY_API_KEY")
    agent_bay = AgentBay(api_key=api_key)

    params = CreateSessionParams(image_id="browser_latest")
    session_result = await agent_bay.create(params)
    assert session_result.success and session_result.session is not None
    session = session_result.session

    try:
        assert await session.browser.initialize(BrowserOption())
        agent = session.browser.agent
        await agent.navigate(url="https://www.baidu.com/")

        await agent.act(ActOptions(action="搜索框输入小米手机，并回车"))
        await agent.act(ActOptions(action="点击 资讯（或 新闻/资讯 tab）"))

        ok, results = await agent.extract(
            ExtractOptions(
                instruction="提取搜索结果中所有的标题和链接",
                schema=PageLinkList,
                max_page=6,
            )
        )
        assert ok, "extract failed"

        logger.info("Final extract results count=%d", len(results.results))

        await asyncio.sleep(1)
        await agent.close()

    finally:
        await agent_bay.delete(session)


if __name__ == "__main__":
    asyncio.run(main())
