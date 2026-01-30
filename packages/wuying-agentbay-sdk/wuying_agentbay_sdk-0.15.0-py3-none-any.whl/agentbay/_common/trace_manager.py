import json
import time
import secrets
import platform
from datetime import datetime
from typing import Optional, Dict, Any
from collections import deque
from threading import Lock
import asyncio
import threading

from aliyun.log import LogClient
from aliyun.log.putlogsrequest import PutLogsRequest
from aliyun.log.logitem import LogItem

from .token_manager import TokenManager, ApiResponse, StsToken, TraceSlsInfo
from .logger import get_logger

_logger = get_logger("trace_manager")

MAX_CACHED_LOGS = 100
MAX_LOG_LENGTH = 8192
MAX_ERROR_COUNT = 5

def generate_trace_id() -> str:
    """Generate a 32-character hexadecimal trace_id."""
    trace_id_bytes = secrets.token_bytes(16)
    return trace_id_bytes.hex()

def generate_span_id() -> str:
    """Generate a 16-character hexadecimal span_id."""
    span_id_bytes = secrets.token_bytes(8)
    return span_id_bytes.hex()


class TraceManager:
    _instance: Optional["TraceManager"] = None
    _lock = Lock()

    def __init__(self):
        self.token_manager: Optional[TokenManager] = None
        self.response: Optional[ApiResponse] = None
        self.client: Optional[LogClient] = None
        self.is_destroyed = False
        self.is_ready = False
        self.pending_logs: deque = deque()
        self.pending_logs_lock = Lock()
        self.error_count = 0
        self.trace_id_map: Dict[str, str] = {}
        self.parent_span_id_map: Dict[str, str] = {}
        self.trace_map_lock = Lock()

    @classmethod
    def get_instance(cls) -> "TraceManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _get_token_manager(self) -> TokenManager:
        if self.token_manager is None:
            self.token_manager = TokenManager()
            self.token_manager.set_on_token_received_listener(
                on_success=self._on_token_success,
                on_failure=self._on_token_failure,
            )
            # Request token asynchronously in background
            self._request_token_async()
        return self.token_manager

    def _request_token_async(self):
        def _run_in_thread():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.token_manager.request_token())
                loop.close()
            except Exception as e:
                _logger.error(f"Failed to request token in background: {e}", exc_info=True)

        thread = threading.Thread(target=_run_in_thread, daemon=True)
        thread.start()

    def destroy(self):
        if self.token_manager:
            self.token_manager.set_on_token_received_listener(None, None)
        self.is_destroyed = True
        self.client = None
        self.response = None
        _logger.info("TraceManager destroyed")

    def _on_token_success(self, result: ApiResponse):
        _logger.info(f"onSuccess isDestroyed: {self.is_destroyed}")
        if self.is_destroyed:
            return

        self.response = result
        if self.client is None:
            self._init_producer()
        else:
            self._update_access_key(
                result.sts_token.access_key_id,
                result.sts_token.access_key_secret,
                result.sts_token.security_token,
            )

    def _on_token_failure(self, status_code: int, message: str):
        _logger.info("onFailure")
        self.response = None

    def _init_producer(self):
        try:
            _logger.info("initProducer")
            if not self.response or not self.response.trace_sls_info:
                _logger.error("No trace SLS info available")
                return

            sls_info = self.response.trace_sls_info
            endpoint = f"https://{sls_info.server_url}"
            project = sls_info.project
            logstore = sls_info.log_store

            # Create LogClient with STS credentials
            self.client = LogClient(
                endpoint=endpoint,
                accessKeyId=self.response.sts_token.access_key_id,
                accessKey=self.response.sts_token.access_key_secret,
                securityToken=self.response.sts_token.security_token,
            )

            self.is_ready = True
            self._flush_pending_logs()

        except Exception as e:
            _logger.error(f"Failed to init producer: {e}", exc_info=True)

    def _update_access_key(
        self, access_key_id: str, access_key_secret: str, security_token: str
    ):
        _logger.info("updateAccessKey")
        if self.client is None:
            return

        try:
            # Recreate client with new credentials
            if not self.response or not self.response.trace_sls_info:
                return

            sls_info = self.response.trace_sls_info
            endpoint = f"https://{sls_info.server_url}"

            self.client = LogClient(
                endpoint=endpoint,
                accessKeyId=access_key_id,
                accessKey=access_key_secret,
                securityToken=security_token,
            )

            self._flush_pending_logs()
        except Exception as e:
            _logger.error(f"Failed to update access key: {e}", exc_info=True)

    def _is_ready(self) -> bool:
        return (
            self.client is not None
            and self.response is not None
            and self.response.success
            and self.is_ready
        )

    def send_track(self, owner: str, track_data: Dict[str, Any]) -> int:
        if not owner or not owner.strip():
            _logger.warning("sendTrack: invalid owner")
            return -1

        log_data = {
            "owner": owner,
            "ext": track_data,
        }
        return self._add_log(log_data)

    def send_trace(
        self,
        owner: str,
        trace_data: Dict[str, Any],
        span_key: str,
        biz_index: int,
        extra: str,
        is_start: bool = False,
    ) -> int:
        if not owner or not owner.strip():
            _logger.warning("sendTrace: invalid owner")
            return -1

        trace_key = f"{biz_index}{extra}"

        with self.trace_map_lock:
            if is_start:
                # Clear existing trace info for this key
                self.trace_id_map.pop(trace_key, None)
                self.parent_span_id_map.pop(trace_key, None)

            # Get or generate trace_id
            trace_id = self.trace_id_map.get(trace_key)
            if trace_id is None:
                trace_id = generate_trace_id()
                self.trace_id_map[trace_key] = trace_id

            # Generate new span_id
            span_id = generate_span_id()

            # Get parent_span_id
            parent_span_id = self.parent_span_id_map.get(trace_key)
            if parent_span_id is None:
                parent_span_id = span_id

            # Update parent_span_id for next span
            self.parent_span_id_map[trace_key] = span_id

        trace_data["traceId"] = trace_id
        trace_data["parentSpanId"] = parent_span_id
        trace_data["spanId"] = span_id
        trace_data["spanName"] = span_key
        trace_data["is_start"] = is_start

        log_data = {
            "owner": owner,
            "ext": trace_data,
        }
        return self._add_log(log_data)

    def get_trace_id(self, biz_index: int, extra: str) -> Optional[str]:
        trace_key = f"{biz_index}{extra}"
        with self.trace_map_lock:
            return self.trace_id_map.get(trace_key)

    def _add_log(self, log_data: Dict[str, Any]) -> int:
        log_item = self._create_log_item(log_data)

        # Try to send log first without holding the lock
        if self._send_log(log_item):
            return 0
        else:
            # Only acquire lock when adding to cache
            lock_acquired = self.pending_logs_lock.acquire(timeout=2.0)
            if not lock_acquired:
                _logger.warning("_add_log: failed to acquire lock within 2 seconds, dropping log")
                return 0
            try:
                self._add_to_cache(log_item)
            finally:
                self.pending_logs_lock.release()
            return 0

    def _create_log_item(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        token_manager = self._get_token_manager()
        log_item = {
            "uuid": token_manager.get_uuid(),
            "os": "python",
            "appName": "agentbay",
            "ts": self._get_now(),
            "sw": self._get_system_version(),
        }
        log_item.update(log_data)
        return log_item

    def _send_log(self, log_item: Dict[str, Any]) -> bool:
        if not self._is_ready():
            return False

        try:
            if not self.response or not self.response.trace_sls_info:
                return False

            sls_info = self.response.trace_sls_info
            project = sls_info.project
            logstore = sls_info.log_store

            # Create LogItem
            log = LogItem()
            for key, value in log_item.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False, indent=2)
                else:
                    value = str(value)
                # Truncate if too long
                if len(value) > MAX_LOG_LENGTH:
                    value = value[:MAX_LOG_LENGTH]
                log.push_back(key, value)

            # Create PutLogsRequest
            request = PutLogsRequest(
                project=project,
                logstore=logstore,
                topic="python_sdk_trace",
                source="",
                logitems=[log],
            )
            try:
                self.client.put_logs(request)
                self.error_count = 0
                return True
            except Exception as send_error:
                error_str = str(send_error).lower()
                self.error_count += 1
                is_auth_error = '401' in error_str or '403' in error_str or 'unauthorized' in error_str or 'forbidden' in error_str
                # Request new token if unauthorized or too many errors
                if is_auth_error or self.error_count > MAX_ERROR_COUNT:
                    token_manager = self._get_token_manager()
                    if token_manager.is_token_invalid() or self.response is None:
                        self.error_count = 0
                        self._request_token_async()
                    else:
                        self._update_access_key(
                            self.response.sts_token.access_key_id,
                            self.response.sts_token.access_key_secret,
                            self.response.sts_token.security_token,
                        )
                
                return False
        except Exception as e:
            _logger.error(f"Error sending log: {e}", exc_info=True)
            self.error_count += 1
            return False

    def _add_to_cache(self, log_item: Dict[str, Any]):
        if len(self.pending_logs) >= MAX_CACHED_LOGS:
            self.pending_logs.popleft()
            _logger.warning("addLog: cache full, dropped oldest")
        self.pending_logs.append(log_item)

    def _flush_pending_logs(self):
        logs_to_send = []
        # Quickly acquire lock and copy logs to send
        lock_acquired = self.pending_logs_lock.acquire(timeout=2.0)
        if not lock_acquired:
            _logger.warning("flushPendingLogs: failed to acquire lock within 2 seconds, skipping flush")
            return
            
        try:
            while self.pending_logs:
                logs_to_send.append(self.pending_logs.popleft())
        except Exception as e:
            _logger.error(f"flushPendingLogs: error copying logs: {e}", exc_info=True)
        finally:
            self.pending_logs_lock.release()

        # Send all copied logs
        for log_item in logs_to_send:
            try:
                self._send_log(log_item)
            except Exception as e:
                _logger.error(f"Failed to send cached log: {e}", exc_info=True)

    @staticmethod
    def _get_now() -> str:
        """Get current time as string."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _get_system_version() -> str:
        """Get system version information."""
        system = platform.system()
        version = platform.version()
        return f"{system} {version}"

