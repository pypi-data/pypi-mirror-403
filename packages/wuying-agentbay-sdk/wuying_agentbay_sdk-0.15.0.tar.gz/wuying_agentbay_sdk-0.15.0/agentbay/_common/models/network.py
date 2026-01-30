"""
Network API response models for AgentBay SDK.
"""

from .response import ApiResponse


class NetworkResult(ApiResponse):
    def __init__(
        self,
        request_id: str = "",
        success: bool = False,
        network_id: str = "",
        network_token: str = "",
        error_message: str = "",
    ):
        super().__init__(request_id)
        self.success = success
        self.network_id = network_id
        self.network_token = network_token
        self.error_message = error_message


class NetworkStatusResult(ApiResponse):
    def __init__(
        self,
        request_id: str = "",
        success: bool = False,
        online: bool = False,
        error_message: str = "",
    ):
        super().__init__(request_id)
        self.success = success
        self.online = online
        self.error_message = error_message


