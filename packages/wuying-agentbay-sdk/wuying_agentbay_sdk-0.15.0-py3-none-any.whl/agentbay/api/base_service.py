import json
from typing import Any, Dict

from .._common.exceptions import AgentBayError
from .._common.logger import (
    _log_api_call,
    _log_api_response,
    _log_api_response_with_details,
    _log_code_execution_output,
    _log_operation_error,
    get_logger,
)
from .._common.models import OperationResult, extract_request_id
from .models import CallMcpToolRequest

# Initialize _logger for this module
_logger = get_logger("base_service")


class BaseService:
    """
    Base service class that provides common functionality for all service classes.
    This class implements the common methods for calling MCP tools and parsing
    responses.
    """

    def __init__(self, session):
        """
        Initialize a BaseService object.

        Args:
            session: The Session instance that this service belongs to.
        """
        self.session = session

    def _handle_error(self, e):
        """
        Handle and convert exceptions. This method should be overridden by subclasses
        to provide specific error handling.

        Args:
            e (Exception): The exception to handle.

        Returns:
            Exception: The handled exception.
        """
        return e

    def _call_mcp_tool(
        self,
        name: str,
        args: Dict[str, Any],
        read_timeout: int = None,
        connect_timeout: int = None,
        auto_gen_session: bool = False,
    ) -> OperationResult:
        """
        Internal helper to call MCP tool and handle errors.

        Args:
            name (str): The name of the tool to call.
            args (Dict[str, Any]): The arguments to pass to the tool.
            auto_gen_session (bool): Whether to automatically generate session if not exists.

        Returns:
            OperationResult: The response from the tool with request ID.
        """
        try:
            args_json = json.dumps(args, ensure_ascii=False)

            # Non-VPC mode: use traditional API call
            request = CallMcpToolRequest(
                authorization=f"Bearer {self.session._get_api_key()}",
                session_id=self.session._get_session_id(),
                name=name,
                args=args_json,
                auto_gen_session=auto_gen_session,
            )
            response = self.session._get_client().call_mcp_tool(
                request, read_timeout=read_timeout, connect_timeout=connect_timeout
            )

            # Extract request ID
            request_id = extract_request_id(response)

            response_map = response.to_map()
            if not response_map:
                return OperationResult(
                    request_id=request_id,
                    success=False,
                    error_message="Invalid response format",
                )

            body = response_map.get("body", {})
            try:
                response_body = json.dumps(body, ensure_ascii=False, indent=2)
            except Exception:
                response_body = str(body)
            if not body:
                return OperationResult(
                    request_id=request_id,
                    success=False,
                    error_message="Invalid response body",
                )

            # Check for API-level errors before parsing Data
            if not body.get("Success", True) and body.get("Code"):
                code = body.get("Code", "Unknown")
                message = body.get("Message", "Unknown error")
                return OperationResult(
                    request_id=request_id,
                    success=False,
                    error_message=f"[{code}] {message}",
                )

            # For run_code tool, extract and log the actual code execution output BEFORE parsing
            # But only if it's not an error response
            if (
                name == "run_code"
                and body.get("Data")
                and not body.get("Data", {}).get("isError", False)
            ):
                data_str = json.dumps(body["Data"], ensure_ascii=False)
                _log_code_execution_output(request_id, data_str)

            result = self._parse_response_body(body)

            # Log API response with key details
            _log_api_response_with_details(
                api_name=f"CallMcpTool - {name}",
                request_id=request_id,
                success=True,
                key_fields={"tool": name},
                full_response=response_body,
            )

            return OperationResult(request_id=request_id, success=True, data=result)

        except AgentBayError as e:
            handled_error = self._handle_error(e)
            request_id = "" if "request_id" not in locals() else request_id
            _logger.exception(f"❌ Failed to call MCP tool {name}")
            return OperationResult(
                request_id=request_id,
                success=False,
                error_message=str(handled_error),
            )
        except Exception as e:
            handled_error = self._handle_error(e)
            request_id = "" if "request_id" not in locals() else request_id
            _logger.exception(f"❌ Failed to call MCP tool {name}")
            return OperationResult(
                request_id=request_id,
                success=False,
                error_message=f"Failed to call MCP tool {name}: {handled_error}",
            )

    def _sanitize_error(self, error_str: str) -> str:
        """
        Sanitizes error messages to remove sensitive information like API keys.

        Args:
            error_str (str): The error string to sanitize.

        Returns:
            str: The sanitized error string.
        """
        import re

        if not error_str:
            return error_str

        # Remove API key from URLs
        # Pattern: apiKey=akm-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        api_key_pattern = re.compile(r"apiKey=akm-[a-f0-9-]+")
        error_str = api_key_pattern.sub("apiKey=***REDACTED***", error_str)

        # Remove API key from Bearer tokens
        # Pattern: Bearer akm-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        bearer_pattern = re.compile(r"Bearer akm-[a-f0-9-]+")
        error_str = bearer_pattern.sub("Bearer ***REDACTED***", error_str)

        # Remove API key from query parameters
        # Pattern: &apiKey=akm-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        query_pattern = re.compile(r"&apiKey=akm-[a-f0-9-]+")
        error_str = query_pattern.sub("&apiKey=***REDACTED***", error_str)

        # Remove API key from URL paths
        # Pattern: /callTool?apiKey=akm-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        url_pattern = re.compile(r"/callTool\?apiKey=akm-[a-f0-9-]+")
        error_str = url_pattern.sub("/callTool?apiKey=***REDACTED***", error_str)

        return error_str

    def _parse_response_body(
        self, body: Dict[str, Any], parse_json: bool = False
    ) -> Any:
        """
        Parses the response body from the MCP tool.

        Args:
            body (Dict[str, Any]): The response body.
            parse_json (bool, optional): Whether to parse the text as JSON.
            Defaults to False.

        Returns:
            Any: The parsed content. If parse_json is True, returns the parsed
                 JSON object; otherwise returns the raw text.


        Raises:
            AgentBayError: If the response contains errors or is invalid.
        """
        try:
            if body.get("Data", {}).get("isError", False):
                error_content = body.get("Data", {}).get("content", [])
                try:
                    error_content_json = json.dumps(
                        error_content, ensure_ascii=False, indent=2
                    )
                    _logger.debug(f"error_content = {error_content_json}")
                except Exception:
                    _logger.debug(f"error_content: {error_content}")
                error_message = "; ".join(
                    item.get("text", "Unknown error")
                    for item in error_content
                    if isinstance(item, dict)
                )
                raise AgentBayError(f"Error in response: {error_message}")

            response_data = body.get("Data", {})
            if not response_data:
                raise AgentBayError("No data field in response")

            # Handle 'content' field for other methods
            content = response_data.get("content", [])
            if not content or not isinstance(content, list):
                raise AgentBayError("No content found in response")

            content_item = content[0]
            text_string = content_item.get("text")

            # Allow text field to be empty string
            if text_string is None:
                raise AgentBayError("Text field not found in response")

            return text_string

        except AgentBayError as e:
            # Transform AgentBayError to the expected type
            handled_error = self._handle_error(e)
            raise handled_error
        except Exception as e:
            # Transform AgentBayError to the expected type
            handled_error = self._handle_error(
                AgentBayError(f"Error parsing response body: {e}")
            )
            raise handled_error
