import asyncio
from typing import TYPE_CHECKING, Optional

from .._common.logger import get_logger
from .._common.models.network import NetworkResult, NetworkStatusResult
from .._common.models.response import extract_request_id
from ..api.models import CreateNetworkRequest, DescribeNetworkRequest

_logger = get_logger("beta_network")

if TYPE_CHECKING:
    from .agentbay import AsyncAgentBay


class AsyncBetaNetworkService:
    """
    Beta network service (trial feature).
    """

    def __init__(self, agent_bay: "AsyncAgentBay"):
        self._agent_bay = agent_bay

    async def get_network_bind_token(self, network_id: Optional[str] = None) -> NetworkResult:
        try:
            request = CreateNetworkRequest(
                authorization=f"Bearer {self._agent_bay.api_key}",
                network_id=network_id,
                login_region_id=self._agent_bay.region_id,
            )
            response = await self._agent_bay.client.create_network_async(request)
            request_id = extract_request_id(response) or ""

            if response is None or getattr(response, "body", None) is None:
                return NetworkResult(
                    request_id=request_id,
                    success=False,
                    error_message="Invalid response from CreateNetwork API",
                )

            body = response.body
            if getattr(body, "success", None) is None or not body.success:
                error_msg = getattr(body, "message", None) or "Unknown error"
                code = getattr(body, "code", None)
                if code:
                    error_msg = f"[{code}] {error_msg}"
                return NetworkResult(
                    request_id=request_id,
                    success=False,
                    error_message=error_msg,
                )

            if getattr(body, "data", None) is None:
                return NetworkResult(
                    request_id=request_id,
                    success=False,
                    error_message="Network data not found in response",
                )

            data = body.data
            return NetworkResult(
                request_id=request_id,
                success=True,
                network_id=getattr(data, "network_id", "") or "",
                network_token=getattr(data, "network_token", "") or "",
                error_message="",
            )
        except Exception as e:
            _logger.debug(f"CreateNetwork(beta) failed: {e}")
            return NetworkResult(
                request_id="",
                success=False,
                error_message=f"Failed to create network: {e}",
            )

    async def describe(self, network_id: str) -> NetworkStatusResult:
        if not network_id:
            return NetworkStatusResult(
                request_id="",
                success=False,
                online=False,
                error_message="network_id is required",
            )

        max_attempts = 3
        delay_s = 0.2
        for attempt in range(1, max_attempts + 1):
            try:
                request = DescribeNetworkRequest(
                    authorization=f"Bearer {self._agent_bay.api_key}",
                    network_id=network_id,
                )
                response = await self._agent_bay.client.describe_network_async(request)
                request_id = extract_request_id(response) or ""

                if response is None or getattr(response, "body", None) is None:
                    return NetworkStatusResult(
                        request_id=request_id,
                        success=False,
                        online=False,
                        error_message="Invalid response from DescribeNetwork API",
                    )

                body = response.body
                if getattr(body, "success", None) is None or not body.success:
                    error_msg = getattr(body, "message", None) or "Unknown error"
                    code = getattr(body, "code", None)
                    if code:
                        error_msg = f"[{code}] {error_msg}"
                    return NetworkStatusResult(
                        request_id=request_id,
                        success=False,
                        online=False,
                        error_message=error_msg,
                    )

                online = False
                if getattr(body, "data", None) is not None and getattr(body.data, "online", None) is not None:
                    online = bool(body.data.online)

                return NetworkStatusResult(
                    request_id=request_id,
                    success=True,
                    online=online,
                    error_message="",
                )
            except Exception as e:
                error_str = str(e)
                request_id = ""
                if attempt < max_attempts and (
                    "ServiceUnavailable" in error_str or "statusCode': 503" in error_str or "code: 503" in error_str
                ):
                    await asyncio.sleep(delay_s)
                    delay_s *= 2
                    continue
                if "NotFound" in error_str:
                    return NetworkStatusResult(
                        request_id=request_id,
                        success=False,
                        online=False,
                        error_message=f"Network {network_id} not found",
                    )
                return NetworkStatusResult(
                    request_id=request_id,
                    success=False,
                    online=False,
                    error_message=f"Failed to describe network: {e}",
                )



