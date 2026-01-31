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

import _thread
import asyncio
import urllib.parse

import aiohttp

from dashvector.common.error import DashVectorHTTPException
from dashvector.common.handler import RPCHandler
from dashvector.core.doc import DocBuilder, DocOpResult
from dashvector.core.group import GroupBuilder
from dashvector.core.models.collection_meta_status import *
from dashvector.core.models.create_collection_request import CreateCollectionRequest
from dashvector.core.models.create_partition_request import CreatePartitionRequest
from dashvector.core.models.delete_collection_request import DeleteCollectionRequest
from dashvector.core.models.delete_doc_request import DeleteDocRequest
from dashvector.core.models.delete_partition_request import DeletePartitionRequest
from dashvector.core.models.describe_collection_request import DescribeCollectionRequest
from dashvector.core.models.describe_partition_request import DescribePartitionRequest
from dashvector.core.models.fetch_doc_request import FetchDocRequest
from dashvector.core.models.list_partitions_request import ListPartitionsRequest
from dashvector.core.models.partition_meta_status import *
from dashvector.core.models.query_doc_group_by_request import QueryDocGroupByRequest
from dashvector.core.models.query_doc_request import QueryDocRequest
from dashvector.core.models.stats_collection_request import StatsCollectionRequest
from dashvector.core.models.stats_partition_request import StatsPartitionRequest
from dashvector.core.models.upsert_doc_request import UpsertDocRequest
from dashvector.version import __version__


class HTTPHandler(RPCHandler):
    _COLLECTION_URL_LIST_GET = "/v1/collections"
    _COLLECTION_URL_CREATE_POST = "/v1/collections"
    _COLLECTION_URL_DESCRIBE_GET = "/v1/collections/%s"
    _COLLECTION_URL_STATS_GET = "/v1/collections/%s/stats"
    _COLLECTION_URL_DELETE_DELETE = "/v1/collections/%s"
    _DOC_URL_INSERT_POST = "/v1/collections/%s/docs"
    _DOC_URL_UPDATE_PUT = "/v1/collections/%s/docs"
    _DOC_URL_DELETE_DELETE = "/v1/collections/%s/docs"
    _DOC_URL_FETCH_GET = "/v1/collections/%s/docs?ids=%s&partition=%s"
    _DOC_URL_UPSERT_POST = "/v1/collections/%s/docs/upsert"
    _DOC_URL_QUERY_POST = "/v1/collections/%s/query"
    _DOC_URL_QUERY_GROUP_BY_POST = "/v1/collections/%s/query_group_by"
    _PARTITION_URL_CREATE_POST = "/v1/collections/%s/partitions"
    _PARTITION_URL_LIST_GET = "/v1/collections/%s/partitions"
    _PARTITION_URL_DELETE_DELETE = "/v1/collections/%s/partitions/%s"
    _PARTITION_URL_DESCRIBE_GET = "/v1/collections/%s/partitions/%s"
    _PARTITION_URL_STATS_GET = "/v1/collections/%s/partitions/%s/stats"
    _VERSION_URL = "/service_version"

    class _HTTPResponse(RPCResponse):
        def __init__(self, future, *, req=None, async_req=False, attr_name=None):
            super().__init__(async_req=async_req)
            self._future = future
            self._request = req
            self._attr_name = attr_name
            self._response = None
            self._status = None
            self._headers = None
            self._body = None

        def get(self):
            if self._response is None:
                feature_result = self._future.result(timeout=3600)
                self._status = feature_result["status"] if "status" in feature_result else -1
                self._headers = feature_result["headers"] if "headers" in feature_result else {}
                if self._status != 200:
                    raise DashVectorHTTPException(code=self._status)
                self._body = feature_result["body"] if "body" in feature_result else ""

                try:
                    self._response = {} if self._body is None else json.loads(self._body)
                except Exception as e:
                    raise DashVectorException(
                        code=DashVectorCode.InvalidJson,
                        reason=f"DashVectorSDK Parse Response Failed. Text:{self._body}",
                    )

            if not bool(self._response):
                return None
            self._request_id = self._response.get("request_id")
            self._code = self._response.get("code")
            self._message = self._response.get("message")
            self._parse_output()
            self._fill_usage()
            return self

        def _parse_output(self):
            if self._code == DashVectorCode.Success:
                if self._attr_name == "get_version":
                    self._output = self._response.get("version")
                elif self._attr_name == "describe_collection":
                    self._output = CollectionMeta(self._response.get("output"))
                elif self._attr_name in ("list_collections", "list_partitions"):
                    self._output = self._response.get("output")
                elif self._attr_name == "stats_collection":
                    self._output = CollectionStats(stats=self._response.get("output"))
                elif self._attr_name == "describe_partition":
                    if isinstance(self._request, DescribePartitionRequest):
                        self._output = self._response.get("output")
                elif self._attr_name == "fetch_doc":
                    result_docs = {}
                    if isinstance(self._request, FetchDocRequest):
                        for doc_id, doc in self._response.get("output", {}).items():
                            result_docs[doc_id] = DocBuilder.from_dict(doc, self._request.collection_meta)
                    self._output = result_docs
                elif self._attr_name == "query_doc":
                    result_docs = []
                    if isinstance(self._request, QueryDocRequest):
                        for doc in self._response.get("output", []):
                            result_docs.append(DocBuilder.from_dict(doc, collection_meta=self._request.collection_meta))
                    self._output = result_docs
                elif self._attr_name == "query_doc_group_by":
                    result_groups = []
                    if isinstance(self._request, QueryDocGroupByRequest):
                        for group in self._response.get("output", []):
                            result_groups.append(GroupBuilder.from_dict(group, self._request.collection_meta))
                    self._output = result_groups
                elif self._attr_name == "stats_partition":
                    if isinstance(self._request, StatsPartitionRequest):
                        self._output = PartitionStats(
                            self._request.partition_name, self._response.get("output", {}).get("total_doc_count")
                        )
                elif self._attr_name in ("insert_doc", "update_doc", "upsert_doc", "delete_doc"):
                    doc_op_results = []
                    for doc_op_result in self._response.get("output", []):
                        doc_op_results.append(
                            DocOpResult(
                                doc_op=DocOp[doc_op_result.get("doc_op")],
                                id=doc_op_result.get("id"),
                                code=doc_op_result.get("code"),
                                message=doc_op_result.get("message"),
                            )
                        )
                    self._output = doc_op_results

        def _fill_usage(self):
            if self._response.get("code") == DashVectorCode.Success:
                if self._attr_name in (
                        "fetch_doc", "query_doc", "insert_doc", "update_doc", "upsert_doc", "delete_doc"):
                    if self._response.get("usage") is not None:
                        self._usage = RequestUsage.from_dict(self._response.get("usage"))

    class _HTTPAsyncClient(object):
        _aio_ev_loop = None

        @staticmethod
        def _start_aio_ev_thread(loop):
            loop.run_forever()

        def __init__(
            self, *, endpoint: str, headers: Optional[Dict] = None, timeout: float = 10.0, insecure_mode: bool = False
        ):
            self._endpoint = endpoint
            self._headers = {} if headers is None else headers
            self._timeout = timeout
            self._insecure_mode = insecure_mode

            if HTTPHandler._HTTPAsyncClient._aio_ev_loop is None:
                HTTPHandler._HTTPAsyncClient._aio_ev_loop = asyncio.get_event_loop()
                _thread.start_new_thread(
                    HTTPHandler._HTTPAsyncClient._start_aio_ev_thread, (HTTPHandler._HTTPAsyncClient._aio_ev_loop,)
                )
                while not HTTPHandler._HTTPAsyncClient._aio_ev_loop.is_running():
                    pass

        def _request(self, url, headers, timeout):
            url_prefix = "https://"
            if self._insecure_mode:
                url_prefix = "http://"
            url = url_prefix + self._endpoint + url
            if headers is None:
                headers = self._headers
            if timeout is None:
                timeout = self._timeout
            return url, headers, timeout

        async def _response(self, rsp):
            await rsp.read()
            rsp_status = rsp.status
            rsp_headers = {}
            for header_k, header_v in rsp.headers.items():
                rsp_headers[header_k] = header_v
            rsp_body = await rsp.text() if rsp_status == 200 else ""

            return {"status": rsp_status, "headers": rsp_headers, "body": rsp_body}

        async def _get(self, url, headers=None, timeout=None):
            url, headers, timeout = self._request(url, headers, timeout)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=timeout) as rsp:
                    return await self._response(rsp)

        async def _post(self, url, data, headers=None, timeout=None):
            url, headers, timeout = self._request(url, headers, timeout)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, headers=headers, timeout=timeout) as rsp:
                    return await self._response(rsp)

        async def _put(self, url, data, headers=None, timeout=None):
            url, headers, timeout = self._request(url, headers, timeout)
            async with aiohttp.ClientSession() as session:
                async with session.put(url, data=data, headers=headers, timeout=timeout) as rsp:
                    return await self._response(rsp)

        async def _delete(self, url, data=None, headers=None, timeout=None):
            url, headers, timeout = self._request(url, headers, timeout)
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, data=data, headers=headers, timeout=timeout) as rsp:
                    return await self._response(rsp)

        def get(self, url, *, headers=None, timeout=None, req=None, async_req=False, attr_name=None):
            a_future = asyncio.run_coroutine_threadsafe(
                self._get(url, headers, timeout), loop=HTTPHandler._HTTPAsyncClient._aio_ev_loop
            )
            return HTTPHandler._HTTPResponse(a_future, req=req, async_req=async_req, attr_name=attr_name)

        def post(self, url, data, *, headers=None, timeout=None, req=None, async_req=False, attr_name=None):
            a_future = asyncio.run_coroutine_threadsafe(
                self._post(url, data, headers, timeout), loop=HTTPHandler._HTTPAsyncClient._aio_ev_loop
            )
            return HTTPHandler._HTTPResponse(a_future, req=req, async_req=async_req, attr_name=attr_name)

        def put(self, url, data, *, headers=None, timeout=None, req=None, async_req=False, attr_name=None):
            a_future = asyncio.run_coroutine_threadsafe(
                self._put(url, data, headers, timeout), loop=HTTPHandler._HTTPAsyncClient._aio_ev_loop
            )
            return HTTPHandler._HTTPResponse(a_future, req=req, async_req=async_req, attr_name=attr_name)

        def delete(self, url, data=None, *, headers=None, timeout=None, req=None, async_req=False, attr_name=None):
            a_future = asyncio.run_coroutine_threadsafe(
                self._delete(url, data, headers, timeout), loop=HTTPHandler._HTTPAsyncClient._aio_ev_loop
            )
            return HTTPHandler._HTTPResponse(
                a_future,
                req=req,
                async_req=async_req,
                attr_name=attr_name,
            )

    def __init__(self, *, endpoint: str, api_key: str = "", timeout: float = 10.0):
        super().__init__(endpoint=endpoint, api_key=api_key, timeout=timeout)
        self._headers["Content-Type"] = "application/json"
        self._headers["x-user-agent"] = self._headers["x-user-agent"] + f";aiohttp-version:{aiohttp.__version__}"
        self._http_async_client = self._HTTPAsyncClient(
            endpoint=self._endpoint, headers=self._headers, timeout=self._timeout, insecure_mode=self._insecure_mode
        )

    def create_collection(self, create_request: CreateCollectionRequest, *, async_req: bool = False) -> RPCResponse:
        rebuild_timeout = self._timeout
        if rebuild_timeout < 30.0:
            rebuild_timeout = 30.0
        return self._http_async_client.post(
            self._COLLECTION_URL_CREATE_POST, create_request.to_json(), timeout=rebuild_timeout, async_req=async_req
        )

    def delete_collection(self, delete_request: DeleteCollectionRequest, *, async_req: bool = False) -> RPCResponse:
        rebuild_timeout = self._timeout
        if rebuild_timeout < 30.0:
            rebuild_timeout = 30.0
        return self._http_async_client.delete(
            self._COLLECTION_URL_DELETE_DELETE % delete_request.name, timeout=rebuild_timeout, async_req=async_req
        )

    def describe_collection(
        self, describe_request: DescribeCollectionRequest, *, async_req: bool = False
    ) -> RPCResponse:
        return self._http_async_client.get(
            self._COLLECTION_URL_DESCRIBE_GET % describe_request.name,
            attr_name="describe_collection",
            async_req=async_req,
        )

    def stats_collection(self, stats_request: StatsCollectionRequest, *, async_req: bool = False) -> RPCResponse:
        return self._http_async_client.get(
            self._COLLECTION_URL_STATS_GET % stats_request.name, attr_name="stats_collection", async_req=async_req
        )

    def list_collections(self, *, async_req: bool = False) -> RPCResponse:
        return self._http_async_client.get(
            self._COLLECTION_URL_LIST_GET, async_req=async_req, attr_name="list_collections"
        )

    def get_version(self, *, async_req: bool = False):
        return self._http_async_client.get(self._VERSION_URL, async_req=async_req, attr_name="get_version")

    def insert_doc(self, insert_request: UpsertDocRequest, *, async_req: bool = False) -> RPCResponse:
        return self._http_async_client.post(
            self._DOC_URL_INSERT_POST % insert_request.collection_name,
            insert_request.to_json(),
            async_req=async_req,
            attr_name="insert_doc",
        )

    def upsert_doc(self, upsert_request: UpsertDocRequest, *, async_req: bool = False) -> RPCResponse:
        return self._http_async_client.post(
            self._DOC_URL_UPSERT_POST % upsert_request.collection_name,
            upsert_request.to_json(),
            async_req=async_req,
            attr_name="upsert_doc",
        )

    def update_doc(self, update_request: UpsertDocRequest, *, async_req: bool = False) -> RPCResponse:
        return self._http_async_client.put(
            self._DOC_URL_UPDATE_PUT % update_request.collection_name,
            update_request.to_json(),
            async_req=async_req,
            attr_name="update_doc",
        )

    def delete_doc(self, delete_request: DeleteDocRequest, *, async_req: bool = False) -> RPCResponse:
        return self._http_async_client.delete(
            self._DOC_URL_DELETE_DELETE % delete_request.collection_name,
            delete_request.to_json(),
            async_req=async_req,
            attr_name="delete_doc",
        )

    def fetch_doc(self, fetch_request: FetchDocRequest, *, async_req: bool = False) -> RPCResponse:
        # id needs to be encoded as urls
        # id contains [_-!@#$%+=.]
        return self._http_async_client.get(
            self._DOC_URL_FETCH_GET
            % (fetch_request.collection_name, urllib.parse.quote(fetch_request.ids), fetch_request.partition_name),
            attr_name="fetch_doc",
            req=fetch_request,
            async_req=async_req,
        )

    def query_doc(self, query_request: QueryDocRequest, *, async_req: bool = False) -> RPCResponse:
        return self._http_async_client.post(
            self._DOC_URL_QUERY_POST % query_request.collection_name,
            query_request.to_json(),
            req=query_request,
            attr_name="query_doc",
            async_req=async_req,
        )

    def query_doc_group_by(self, query_request: QueryDocGroupByRequest, *, async_req: bool = False) -> RPCResponse:
        return self._http_async_client.post(
            self._DOC_URL_QUERY_GROUP_BY_POST % query_request.collection_name,
            query_request.to_json(),
            req=query_request,
            attr_name="query_doc_group_by",
            async_req=async_req,
        )

    def create_partition(self, create_request: CreatePartitionRequest, *, async_req: bool = False) -> RPCResponse:
        return self._http_async_client.post(
            self._PARTITION_URL_CREATE_POST % create_request.collection_name,
            create_request.to_json(),
            req=create_request,
            async_req=async_req,
        )

    def delete_partition(self, delete_request: DeletePartitionRequest, *, async_req: bool = False) -> RPCResponse:
        return self._http_async_client.delete(
            self._PARTITION_URL_DELETE_DELETE % (delete_request.collection_name, delete_request.partition_name),
            async_req=async_req,
        )

    def list_partitions(self, list_request: ListPartitionsRequest, *, async_req: bool = False) -> RPCResponse:
        return self._http_async_client.get(
            self._PARTITION_URL_LIST_GET % list_request.collection_name,
            async_req=async_req,
            attr_name="list_partitions",
        )

    def describe_partition(self, describe_request: DescribePartitionRequest, *, async_req: bool = False) -> RPCResponse:
        return self._http_async_client.get(
            self._PARTITION_URL_DESCRIBE_GET % (describe_request.collection_name, describe_request.partition_name),
            req=describe_request,
            async_req=async_req,
            attr_name="describe_partition",
        )

    def stats_partition(self, stats_request: StatsPartitionRequest, *, async_req: bool = False) -> RPCResponse:
        return self._http_async_client.get(
            self._PARTITION_URL_STATS_GET % (stats_request.collection_name, stats_request.partition_name),
            req=stats_request,
            async_req=async_req,
            attr_name="stats_partition",
        )

    def close(self) -> None:
        return None
