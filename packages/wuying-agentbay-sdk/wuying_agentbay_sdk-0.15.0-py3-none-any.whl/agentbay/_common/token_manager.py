import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Callable
from dataclasses import dataclass
import httpx
from .logger import get_logger

_logger = get_logger("token_manager")

BASE_URL = "https://wyota.cn-hangzhou.aliyuncs.com"
MILLIS_PER_DAY = 24 * 60 * 60 * 1000


@dataclass
class StsToken:
    """STS Token information."""
    access_key_id: str
    access_key_secret: str
    security_token: str
    expiration: str


@dataclass
class TraceSlsInfo:
    """Trace SLS information."""
    project: str
    log_store: str
    log_store_path: str
    log_store_url: str
    server_url: str


@dataclass
class ApiResponse:
    """API response containing token and SLS info."""
    code: str
    request_id: str
    success: bool
    sts_token: Optional[StsToken] = None
    trace_sls_info: Optional[TraceSlsInfo] = None
    token_ready_time: Optional[int] = None


class TokenManager:
    def __init__(self):
        self.uuid = str(uuid.uuid4())
        self.client = httpx.AsyncClient(timeout=30.0)
        self.is_token_requesting = False
        self.success_time = 0
        self.on_success: Optional[Callable[[ApiResponse], None]] = None
        self.on_failure: Optional[Callable[[int, str], None]] = None

    async def destroy(self):
        await self.client.aclose()
        _logger.info("TokenManager destroyed")

    def get_uuid(self) -> str:
        return self.uuid

    def is_token_invalid(self) -> bool:
        """Check if the token is invalid (older than 24 hours)."""
        import time
        current_time = int(time.time() * 1000)
        elapsed = current_time - self.success_time
        return elapsed >= MILLIS_PER_DAY

    def set_on_token_received_listener(
        self,
        on_success: Optional[Callable[[ApiResponse], None]] = None,
        on_failure: Optional[Callable[[int, str], None]] = None,
    ):
        """Set callbacks for token request results."""
        self.on_success = on_success
        self.on_failure = on_failure

    def _get_gmt_time(self) -> str:
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%dT%H:%M:%SZ")

    async def request_token(self):
        if self.is_token_requesting:
            _logger.info("requestToken: isTokenRequesting")
            if self.on_failure:
                self.on_failure(-1, "Already requesting token")
            return

        self.is_token_requesting = True
        _logger.info("requestToken: Starting...")

        try:
            form_data = {
                "Format": "json",
                "Version": "2021-04-20",
                "product": "wyota",
                "Timestamp": self._get_gmt_time(),
                "Action": "GetTerminalReportToken",
                "Uuid": self.uuid,
                "NetworkType": "internet",
            }

            response = await self.client.post(BASE_URL, data=form_data)
            body = response.text

            api_result = ApiResponse(
                code="",
                request_id="unknown",
                success=False,
            )

            parsed = self._parse_sts_response(body, api_result)

            if parsed and api_result.success:
                import time
                api_result.token_ready_time = int(time.time() * 1000)
                _logger.info(f"RequestId: {api_result.request_id}")
                _logger.info(f"Success: true")

                if self.on_success:
                    self.on_success(api_result)
                self.success_time = int(time.time() * 1000)
            else:
                _logger.warning("parse response failed: %s", body)
                if self.on_failure:
                    self.on_failure(response.status_code, body)

        except Exception as e:
            _logger.error(f"Request failed: {e}", exc_info=True)
            if self.on_failure:
                self.on_failure(0, str(e))
        finally:
            self.is_token_requesting = False

    def _parse_sts_response(self, json_str: str, result: ApiResponse) -> bool:
        try:
            root = json.loads(json_str)

            if "Code" not in root or "Data" not in root:
                _logger.warning("Invalid JSON: missing Code or Data")
                return False

            result.code = root.get("Code", "")
            result.request_id = root.get("RequestId", "unknown")
            result.success = root.get("Success", False)

            data = root.get("Data", {})
            if "StsToken" not in data:
                _logger.warning("Missing StsToken in Data")
                return False

            token_obj = data["StsToken"]

            result.sts_token = StsToken(
                access_key_id=token_obj.get("AccessKeyId", ""),
                access_key_secret=token_obj.get("AccessKeySecret", ""),
                security_token=token_obj.get("SecurityToken", ""),
                expiration=token_obj.get("Expiration", ""),
            )

            if "TraceSlsInfo" in token_obj:
                sls_obj = token_obj["TraceSlsInfo"]
                result.trace_sls_info = TraceSlsInfo(
                    project=sls_obj.get("Project", ""),
                    log_store=sls_obj.get("LogStore", ""),
                    log_store_path=sls_obj.get("LogStorePath", ""),
                    log_store_url=sls_obj.get("LogStoreUrl", ""),
                    server_url=sls_obj.get("ServerUrl", ""),
                )
            else:
                result.trace_sls_info = TraceSlsInfo(
                    project="",
                    log_store="",
                    log_store_path="",
                    log_store_url="",
                    server_url="",
                )

            return True
        except Exception as e:
            _logger.error(f"JSON parse error: {e}", exc_info=True)
            return False

