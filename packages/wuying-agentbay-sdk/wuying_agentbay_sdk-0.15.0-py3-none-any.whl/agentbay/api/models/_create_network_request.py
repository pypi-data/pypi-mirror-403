# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
from __future__ import annotations

from darabonba.model import DaraModel


class CreateNetworkRequest(DaraModel):
    def __init__(
        self,
        authorization: str = None,
        network_id: str = None,
        login_region_id: str = None,
    ):
        self.authorization = authorization
        self.network_id = network_id
        self.login_region_id = login_region_id

    def validate(self):
        pass

    def to_map(self):
        result = dict()
        _map = super().to_map()
        if _map is not None:
            result = _map
        if self.authorization is not None:
            result["Authorization"] = self.authorization

        if self.network_id is not None:
            result["NetworkId"] = self.network_id

        if self.login_region_id is not None:
            result["LoginRegionId"] = self.login_region_id

        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get("Authorization") is not None:
            self.authorization = m.get("Authorization")

        if m.get("NetworkId") is not None:
            self.network_id = m.get("NetworkId")

        if m.get("LoginRegionId") is not None:
            self.login_region_id = m.get("LoginRegionId")

        return self


