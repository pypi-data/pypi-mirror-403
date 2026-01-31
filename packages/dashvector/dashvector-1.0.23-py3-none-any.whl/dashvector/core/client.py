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

import json
import time
from typing import Any, Dict, Optional, Type, Union

from dashvector.common.error import DashVectorCode, DashVectorException
from dashvector.common.status import Status
from dashvector.common.types import DashVectorProtocol, DashVectorResponse, VectorParam, FieldSchemaDict
from dashvector.core.collection import Collection
from dashvector.core.index import Index
from dashvector.core.models.create_collection_request import CreateCollectionRequest
from dashvector.core.models.delete_collection_request import DeleteCollectionRequest
from dashvector.core.models.describe_collection_request import DescribeCollectionRequest

__all__ = ["Client"]


class Client(object):
    """
    A Client for interacting with DashVector Server
    """

    def __init__(
        self,
        *,
        api_key: str,
        endpoint: str,
        timeout: float = 10.0,
        protocol: DashVectorProtocol = DashVectorProtocol.GRPC,
    ):
        """
        Create a new DashVector Client and Connect to DashVector Server.

        Args:
            api_key (str): access key provided by dashvector server.
            endpoint (str): dashvector server endpoint.
            timeout (str): dashvector server remote procedure call timeout in second. [optional]
                           default is 10.0 seconds, 0.0 means infinite timeout.
            protocol (DashVectorProtocol): dashvector server remote procedure call protocol. [optional]
                                        default is DashVectorProtocol.GRPC, DashVectorProtocol.HTTP is also supported.

        Return:
            Client, includes a series of Collection related operations

        Example:
            client = Client(api_key="test")
            if not client:
                raise RuntimeError(f"Client initialize Failed, error:{client.code}, message:{client.message}")
        """

        """
        api_key: str
        """
        self._api_key = api_key
        """
        endpoint: str
        """
        self._endpoint = endpoint
        """
        timeout: float = 10.0,
        """
        self._timeout = timeout
        """
        protocol: DashVectorProtocol = DashVectorProtocol.GRPC
        """
        self._protocol = protocol
        """
        _version: str
        """
        self._version = None
        """
        _handler: RPCHandler
        """
        self._handler = None
        """
        _code: str
        _message: str
        _request_id: str
        """
        self._code = DashVectorCode.Unknown
        self._message = ""
        self._request_id = ""
        """
        _cache: dict
        """
        self._cache = {}
        try:
            if self._protocol == DashVectorProtocol.GRPC:
                from dashvector.core.handler.grpc_handler import GRPCHandler

                self._handler = GRPCHandler(endpoint=self._endpoint, api_key=self._api_key, timeout=self._timeout)
            elif self._protocol == DashVectorProtocol.HTTP:
                from dashvector.core.handler.http_handler import HTTPHandler

                self._handler = HTTPHandler(endpoint=self._endpoint, api_key=self._api_key, timeout=self._timeout)
            else:
                self._code = DashVectorCode.InvalidArgument
                self._message = f"DashVectorSDK Client protocol({protocol}) is invalid, only support DashVectorProtocol.GRPC or DashVectorProtocol.HTTP"
                return
        except DashVectorException as e:
            self._code = e.code
            self._message = e.message
            self._request_id = e.request_id
            return

        check_version_rsp = self._check_version()
        self._code = check_version_rsp.code
        self._message = check_version_rsp.message
        self._request_id = check_version_rsp.request_id
        if check_version_rsp.code == DashVectorCode.Success:
            self._version = check_version_rsp.output

    def create(
        self,
        name: str,
        dimension: int = 0,
        *,
        dtype: Union[Type[int], Type[float]] = float,
        fields_schema: Optional[FieldSchemaDict] = None,
        metric: str = "cosine",
        extra_params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        vectors: Union[None, VectorParam, Dict[str, VectorParam]] = None,
        sparse_vectors: Union[None, VectorParam, Dict[str, VectorParam]] = None,
        indexes: Optional[Dict[str, Index]] = None,
    ) -> DashVectorResponse:
        """
        Create a Collection.

        Args:
            name (str): collection name
            dimension (Optional[int]): vector dimension in collection
            dtype (Union[Type[int], Type[float], Type[bool]]): vector data type in collection
            fields_schema (Optional[Dict[str, Union[str, Type[str], Type[int], Type[float], Type[bool], Type[long], List[long], List[str], List[int], List[float]]]): attribute fields in vector
            metric (str): vector metric in collection, support 'cosine', 'dotproduct' and 'euclidean', default is 'cosine'
            extra_params (Optional[Dict[str, Any]]): extra params for collection
            timeout (Optional[int]): timeout[second] for wait until the collection is ready, default is 'None' wait indefinitely
            vectors (Union[None, VectorParam, Dict[str, VectorParam]]): multi-vectors or advanced vector configuration
            sparse_vectors (Union[None, VectorParam, Dict[str, VectorParam]]): multi-vectors or advanced sparse_vector configuration
            indexes (Optional[Dict[str, Index]]):  indexes for collection


        Return:
            DashVectorResponse, include code / message / request_id,
                             code == DashVectorCode.Success means create collection success, otherwise means failure.
        """

        if self._code != DashVectorCode.Success:
            return DashVectorResponse(
                None, exception=DashVectorException(code=self._code, reason=self._message, request_id=self._request_id)
            )

        try:
            create_request = CreateCollectionRequest(
                name=name,
                dimension=dimension,
                dtype=dtype,
                fields_schema=fields_schema,
                metric=metric,
                extra_params=extra_params,
                vectors=vectors,
                sparse_vectors=sparse_vectors,
                indexes=indexes,
            )
        except DashVectorException as e:
            return DashVectorResponse(None, exception=e)

        create_response = DashVectorResponse(self._handler.create_collection(create_request))
        if create_response.code != DashVectorCode.Success or timeout == -1:
            return create_response

        create_collection_timeout = timeout
        rpc_error_count = 0
        while True:
            describe_response = self.describe(name)

            if describe_response.code == DashVectorCode.Success:
                status = Status.get(describe_response.output.status)
                if status == Status.SERVING:
                    return create_response
                elif status in (Status.ERROR, Status.DROPPING):
                    return DashVectorResponse(
                        None,
                        exception=DashVectorException(
                            code=DashVectorCode.UnreadyCollection,
                            reason=f"DashVectorSDK get collection[{name}] status is {describe_response.output.status}",
                            request_id=create_response.request_id,
                        ),
                    )
            else:
                rpc_error_count += 1

            if rpc_error_count > 3:
                return DashVectorResponse(
                    None,
                    exception=DashVectorException(
                        code=describe_response.code,
                        reason=f"DashVectorSDK get collection status failed and reason is {describe_response.message}",
                        request_id=create_response.request_id,
                    ),
                )
            time.sleep(5)
            if create_collection_timeout is None:
                continue
            create_collection_timeout -= 5
            if create_collection_timeout < 0:
                return DashVectorResponse(
                    None,
                    exception=DashVectorException(
                        code=DashVectorCode.Timeout,
                        reason="DashVectorSDK get collection status timeout please call the describe_collection to confirm collection status",
                        request_id=create_response.request_id,
                    ),
                )

    def delete(self, name: str) -> DashVectorResponse:
        """
        Delete a Collection.

        Args:
            name (str): collection name

        Return:
            DashVectorResponse, include code / message / request_id,
                             code == DashVectorCode.Success means Delete Collection success, otherwise means failure.
        """

        if self._code != DashVectorCode.Success:
            return DashVectorResponse(
                None, exception=DashVectorException(code=self._code, reason=self._message, request_id=self._request_id)
            )

        try:
            delete_request = DeleteCollectionRequest(name=name)
        except DashVectorException as e:
            return DashVectorResponse(None, exception=e)

        delete_response = DashVectorResponse(self._handler.delete_collection(delete_request))
        if delete_response.code == DashVectorCode.Success:
            if name in self._cache:
                self._cache.pop(name)
        return delete_response

    def describe(self, name: str) -> DashVectorResponse:
        """
        Describe a Collection.

        Args:
            name (str): collection name

        Return:
            DashVectorResponse, include code / message / request_id / output,
                             code == DashVectorCode.Success means describe collection success and output include a collection meta, otherwise means failure.

        Example:
            rsp = self.client.describe("collection_name")
            if not rsp:
                raise RuntimeError(f"DescribeCollection Failed, error:{rsp.code}, message:{rsp.message}")
            collection_meta = rsp.output
            print("collection_meta:", collection_meta)
        """

        if self._code != DashVectorCode.Success:
            return DashVectorResponse(
                None, exception=DashVectorException(code=self._code, reason=self._message, request_id=self._request_id)
            )

        try:
            describe_request = DescribeCollectionRequest(name=name)
        except DashVectorException as e:
            return DashVectorResponse(None, exception=e)

        return DashVectorResponse(self._handler.describe_collection(describe_request))

    def get(self, name: str) -> Collection:
        """
        Get a Collection Instance with a series of Doc related operations.

        Args:
            name (str): collection name

        Return:
            Collection or DashVectorResponse, include code / message / request_id.
            if code == DashVectorCode.Success means a collection instance is obtained and include a series of doc related operations.
            otherwise means failure and a DashVectorResponse instance is obtained.

        Example:
            collection = self.client.get("collection_name")
            if not collection:
                raise RuntimeError(f"GetCollection Failed, error:{collection.code}, message:{collection.message}")
            print("collection:", collection)
        """

        if self._code != DashVectorCode.Success:
            return Collection(
                exception=DashVectorException(code=self._code, reason=self._message, request_id=self._request_id)
            )

        if name in self._cache:
            return self._cache[name]

        try:
            describe_request = DescribeCollectionRequest(name=name)
        except DashVectorException as e:
            return Collection(exception=e)

        describe_response = DashVectorResponse(self._handler.describe_collection(describe_request))
        if describe_response.code != DashVectorCode.Success:
            return Collection(response=describe_response.response)

        try:
            collection_meta = describe_response.output
            self._cache[name] = Collection(
                response=describe_response.response, collection_meta=collection_meta, handler=self._handler
            )
            return self._cache[name]
        except DashVectorException as e:
            return Collection(exception=e)

    def list(self) -> DashVectorResponse:
        """
        Get a Collection Name List from DashVector Server.

        Return:
            DashVectorResponse, include code / message / request_id / output,
                             code == DashVectorCode.Success means output is a collection name List

        Example:
            rsp = self.client.list()
            if not rsp:
                raise RuntimeError(f"ListCollection Failed, error:{rsp.code}, message:{rsp.message}")
            collection_list = rsp.output
            print("collection_list:", collection_list)
        """

        if self._code != DashVectorCode.Success:
            return DashVectorResponse(
                None, exception=DashVectorException(code=self._code, reason=self._message, request_id=self._request_id)
            )

        return DashVectorResponse(self._handler.list_collections())

    def close(self) -> None:
        """
        Close a DashVector Client

        Return: None
        """

        if self._code != DashVectorCode.Success:
            return None

        self._code = DashVectorCode.Closed
        self._cache = {}

        try:
            self._handler.close()
        except Exception as e:
            return None

    def _check_version(self) -> DashVectorResponse:
        version_response = DashVectorResponse(self._handler.get_version())
        if version_response.code != DashVectorCode.Success:
            return version_response
        return version_response

    @property
    def code(self):
        return self._code

    @property
    def request_id(self):
        return self._request_id

    @property
    def message(self):
        return self._message

    @property
    def version(self):
        if self._version is None:
            return ""
        return self._version

    def __dict__(self):
        return {"code": self.code, "message": self.message, "request_id": self.request_id, "version": self.version}

    def __str__(self):
        return json.dumps(self.__dict__())

    def __repr__(self):
        return self.__str__()

    def __bool__(self):
        return self._code == DashVectorCode.Success

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
