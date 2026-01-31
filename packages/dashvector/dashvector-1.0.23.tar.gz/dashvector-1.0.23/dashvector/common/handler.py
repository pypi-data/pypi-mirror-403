##
#   Copyright 2021 Alibaba, Inc. and its affiliates. All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
##

# -*- coding: utf-8 -*-
import os
import platform
import re
from abc import abstractmethod

from google.protobuf.json_format import MessageToJson
from google.protobuf.message import Message

from dashvector.common.error import DashVectorCode, DashVectorException
from dashvector.util.validator import verify_endpoint
from dashvector.version import __version__


class RPCRequest(object):
    def __init__(self, *, request: Message):
        self.request = request
        self.request_str = request.SerializeToString()
        self.request_len = len(self.request_str)
        if self.request_len > (2 * 1024 * 1024):
            raise DashVectorException(
                code=DashVectorCode.ExceedRequestSize,
                reason=f"DashVectorSDK request length({self.request_len}) exceeds maximum length(2MiB) limit",
            )

    def to_json(self):
        return MessageToJson(self.request, always_print_fields_with_no_presence=True, preserving_proto_field_name=True)

    def to_proto(self):
        return self.request

    def to_string(self):
        return self.request_str


class RPCResponse(object):
    def __init__(self, *, async_req):
        self._async_req = async_req
        self._request_id = None
        self._code = DashVectorCode.Unknown
        self._message = None
        self._output = None
        self._usage = None

    @property
    def async_req(self):
        return self._async_req

    @property
    def request_id(self):
        return self._request_id

    @property
    def code(self):
        return self._code

    @property
    def message(self):
        return self._message

    @property
    def output(self):
        return self._output

    @property
    def usage(self):
        return self._usage

    @abstractmethod
    def get(self):
        pass


class RPCHandler(object):
    def __init__(self, *, endpoint: str = "", api_key: str = "", timeout: float = 10.0):
        """
        endpoint: str
        """
        if not isinstance(endpoint, str):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK RPCHandler endpoint({endpoint}) is invalid and must be str",
            )

        if not verify_endpoint(endpoint):
            raise DashVectorException(
                code=DashVectorCode.InvalidEndpoint,
                reason=f"DashVectorSDK RPCHandler endpoint({endpoint}) is invalid and cannot contain protocol header and [_]",
            )

        """
        api_key: str
        """
        if not isinstance(api_key, str):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument, reason=f"DashVectorSDK RPCHandler api_key({api_key}) is invalid"
            )

        """
        timeout: float
        """
        if isinstance(timeout, float):
            pass
        elif isinstance(timeout, int):
            timeout = float(timeout)
        else:
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument, reason=f"DashVectorSDK RPCHandler timeout({timeout}) is invalid"
            )
        if timeout <= 0.000001:
            timeout = 365.5 * 86400

        self._endpoint = endpoint
        self._timeout = timeout
        self._insecure_mode = os.getenv("DASHVECTOR_INSECURE_MODE", "False").lower() in ("true", "1")
        self._headers = {
            "dashvector-auth-token": api_key,
            "x-user-agent": f"{__version__};{platform.python_version()};{platform.platform()}",
        }

    @abstractmethod
    def create_collection(self, create_request, *, async_req=False) -> RPCResponse:
        pass

    @abstractmethod
    def delete_collection(self, delete_request, *, async_req=False) -> RPCResponse:
        pass

    @abstractmethod
    def describe_collection(self, describe_request, *, async_req=False) -> RPCResponse:
        pass

    @abstractmethod
    def list_collections(self, *, async_req=False) -> RPCResponse:
        pass

    @abstractmethod
    def stats_collection(self, stats_request, *, async_req=False) -> RPCResponse:
        pass

    @abstractmethod
    def create_partition(self, create_request, *, async_req=False) -> RPCResponse:
        pass

    @abstractmethod
    def delete_partition(self, delete_request, *, async_req=False) -> RPCResponse:
        pass

    @abstractmethod
    def describe_partition(self, describe_request, *, async_req=False) -> RPCResponse:
        pass

    @abstractmethod
    def list_partitions(self, list_request, *, async_req=False) -> RPCResponse:
        pass

    @abstractmethod
    def stats_partition(self, stats_request, *, async_req=False) -> RPCResponse:
        pass

    @abstractmethod
    def insert_doc(self, insert_request, *, async_req=False) -> RPCResponse:
        pass

    @abstractmethod
    def update_doc(self, update_request, *, async_req=False) -> RPCResponse:
        pass

    @abstractmethod
    def upsert_doc(self, upsert_request, *, async_req=False) -> RPCResponse:
        pass

    @abstractmethod
    def delete_doc(self, delete_request, *, async_req=False) -> RPCResponse:
        pass

    @abstractmethod
    def query_doc(self, query_request, *, async_req=False) -> RPCResponse:
        pass

    @abstractmethod
    def query_doc_group_by(self, query_request, *, async_req=False) -> RPCResponse:
        pass

    @abstractmethod
    def fetch_doc(self, fetch_request, *, async_req=False) -> RPCResponse:
        pass

    @abstractmethod
    def get_version(self, *, async_req) -> RPCResponse:
        pass

    @abstractmethod
    def close(self) -> None:
        pass
