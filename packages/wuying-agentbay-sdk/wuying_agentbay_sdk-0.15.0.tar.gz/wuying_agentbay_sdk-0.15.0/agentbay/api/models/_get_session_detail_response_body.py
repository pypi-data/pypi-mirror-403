# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
from __future__ import annotations

from agentbay.api import models as main_models
from darabonba.model import DaraModel


class GetSessionDetailResponseBody(DaraModel):
    def __init__(
        self,
        code: str = None,
        data: main_models.GetSessionDetailResponseBodyData = None,
        http_status_code: int = None,
        message: str = None,
        request_id: str = None,
        success: bool = None,
    ):
        self.code = code
        self.data = data
        self.http_status_code = http_status_code
        self.message = message
        self.request_id = request_id
        self.success = success

    def validate(self):
        if self.data:
            self.data.validate()

    def to_map(self):
        result = dict()
        _map = super().to_map()
        if _map is not None:
            result = _map
        if self.code is not None:
            result["Code"] = self.code

        if self.data is not None:
            result["Data"] = self.data.to_map()

        if self.http_status_code is not None:
            result["HttpStatusCode"] = self.http_status_code

        if self.message is not None:
            result["Message"] = self.message

        if self.request_id is not None:
            result["RequestId"] = self.request_id

        if self.success is not None:
            result["Success"] = self.success

        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get("Code") is not None:
            self.code = m.get("Code")

        if m.get("Data") is not None:
            temp_model = main_models.GetSessionDetailResponseBodyData()
            self.data = temp_model.from_map(m.get("Data"))

        if m.get("HttpStatusCode") is not None:
            self.http_status_code = m.get("HttpStatusCode")

        if m.get("Message") is not None:
            self.message = m.get("Message")

        if m.get("RequestId") is not None:
            self.request_id = m.get("RequestId")

        if m.get("Success") is not None:
            self.success = m.get("Success")

        return self


class GetSessionDetailResponseBodyData(DaraModel):
    def __init__(
        self,
        aliuid: str = None,
        apikey_id: str = None,
        app_instance_group_id: str = None,
        app_instance_id: str = None,
        app_user_id: str = None,
        biz_type: int = None,
        end_reason: str = None,
        id: int = None,
        image_id: str = None,
        image_type: str = None,
        is_deleted: int = None,
        policy_id: str = None,
        region_id: str = None,
        resource_config_id: str = None,
        status: str = None,
    ):
        self.aliuid = aliuid
        self.apikey_id = apikey_id
        self.app_instance_group_id = app_instance_group_id
        self.app_instance_id = app_instance_id
        self.app_user_id = app_user_id
        self.biz_type = biz_type
        self.end_reason = end_reason
        self.id = id
        self.image_id = image_id
        self.image_type = image_type
        self.is_deleted = is_deleted
        self.policy_id = policy_id
        self.region_id = region_id
        self.resource_config_id = resource_config_id
        self.status = status

    def validate(self):
        pass

    def to_map(self):
        result = dict()
        _map = super().to_map()
        if _map is not None:
            result = _map
        if self.aliuid is not None:
            result["Aliuid"] = self.aliuid

        if self.apikey_id is not None:
            result["ApikeyId"] = self.apikey_id

        if self.app_instance_group_id is not None:
            result["AppInstanceGroupId"] = self.app_instance_group_id

        if self.app_instance_id is not None:
            result["AppInstanceId"] = self.app_instance_id

        if self.app_user_id is not None:
            result["AppUserId"] = self.app_user_id

        if self.biz_type is not None:
            result["BizType"] = self.biz_type

        if self.end_reason is not None:
            result["EndReason"] = self.end_reason

        if self.id is not None:
            result["Id"] = self.id

        if self.image_id is not None:
            result["ImageId"] = self.image_id

        if self.image_type is not None:
            result["ImageType"] = self.image_type

        if self.is_deleted is not None:
            result["IsDeleted"] = self.is_deleted

        if self.policy_id is not None:
            result["PolicyId"] = self.policy_id

        if self.region_id is not None:
            result["RegionId"] = self.region_id

        if self.resource_config_id is not None:
            result["ResourceConfigId"] = self.resource_config_id

        if self.status is not None:
            result["Status"] = self.status

        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get("Aliuid") is not None:
            self.aliuid = m.get("Aliuid")

        if m.get("ApikeyId") is not None:
            self.apikey_id = m.get("ApikeyId")

        if m.get("AppInstanceGroupId") is not None:
            self.app_instance_group_id = m.get("AppInstanceGroupId")

        if m.get("AppInstanceId") is not None:
            self.app_instance_id = m.get("AppInstanceId")

        if m.get("AppUserId") is not None:
            self.app_user_id = m.get("AppUserId")

        if m.get("BizType") is not None:
            self.biz_type = m.get("BizType")

        if m.get("EndReason") is not None:
            self.end_reason = m.get("EndReason")

        if m.get("Id") is not None:
            self.id = m.get("Id")

        if m.get("ImageId") is not None:
            self.image_id = m.get("ImageId")

        if m.get("ImageType") is not None:
            self.image_type = m.get("ImageType")

        if m.get("IsDeleted") is not None:
            self.is_deleted = m.get("IsDeleted")

        if m.get("PolicyId") is not None:
            self.policy_id = m.get("PolicyId")

        if m.get("RegionId") is not None:
            self.region_id = m.get("RegionId")

        if m.get("ResourceConfigId") is not None:
            self.resource_config_id = m.get("ResourceConfigId")

        if m.get("Status") is not None:
            self.status = m.get("Status")

        return self


