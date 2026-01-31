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

import time
from typing import List, Optional, Tuple, Union

import numpy as np

from dashvector.common.handler import RPCHandler
from dashvector.common.types import *
from dashvector.core.doc import Doc
from dashvector.core.models.collection_meta_status import CollectionMeta
from dashvector.core.models.create_partition_request import CreatePartitionRequest
from dashvector.core.models.delete_doc_request import DeleteDocRequest
from dashvector.core.models.delete_partition_request import DeletePartitionRequest
from dashvector.core.models.describe_partition_request import DescribePartitionRequest
from dashvector.core.models.fetch_doc_request import FetchDocRequest
from dashvector.core.models.list_partitions_request import ListPartitionsRequest
from dashvector.core.models.query_doc_request import QueryDocRequest
from dashvector.core.models.query_doc_group_by_request import QueryDocGroupByRequest
from dashvector.core.models.stats_collection_request import StatsCollectionRequest
from dashvector.core.models.stats_partition_request import StatsPartitionRequest
from dashvector.core.models.upsert_doc_request import UpsertDocRequest

__all__ = ["Collection"]


class Collection(DashVectorResponse):
    """
    A Client for Doc and Partition Operations in a Collection
    """

    def insert(
        self,
        docs: Union[Doc, List[Doc], Tuple, List[Tuple]],
        *,
        partition: Optional[str] = None,
        async_req: bool = False,
    ) -> DashVectorResponse:
        """
        Insert one or more Docs.

        Args:
            docs (Union[Doc, List[Doc], Tuple, List[Tuple]]): one or more Docs which will insert into collection.
            partition (str): a partition name in collection. [optional]
            async_req (bool): use asynchronous operation.

        Return:
            DashVectorResponse, include code / message / request_id and a get() method,
                             code == DashVectorCode.Success means insert docs success, otherwise means failure.
                             if you use async_req, must call get() method first.

        Examples:
            [insert]
            rsp = collection.insert(("a", [0.1, 0.2], {'price': 100, 'type': "dress"}))
            if not rsp:
                raise RuntimeError(f"InsertDoc Failed, error:{rsp.code}, message:{rsp.message}")

            [insert with numpy]
            rsp = collection.insert(("a", np.array([0.1, 0.2], {'price': 100, 'type': "dress"}))
            if not rsp:
                raise RuntimeError(f"InsertDoc Failed, error:{rsp.code}, message:{rsp.message}")

            [insert with doc]
            rsp = collection.insert(Doc(id="a", vector=[0.1, 0.2], fields={'price': 100, 'type': "dress"}))
            if not rsp:
                raise RuntimeError(f"InsertDoc Failed, error:{rsp.code}, message:{rsp.message}")

            [insert multi vectors with doc]
            rsp = collection.insert(Doc(id="a", vectors={'vector1':[0.1, 0.2], 'vector2':[0.3,0.4]}, fields={'price': 100, 'type': "dress"}))
            if not rsp:
                raise RuntimeError(f"InsertDoc Failed, error:{rsp.code}, message:{rsp.message}")

            [batch insert]
            rsp = collection.insert([("a", [0.1, 0.2], {'price': 100, 'type': "dress"}), ("b", [0.3, 0.4], {'price': 80, 'type': "shirt"})])
            if not rsp:
                raise RuntimeError(f"InsertDoc Failed, error:{rsp.code}, message:{rsp.message}")

            [batch insert with doc]
            rsp = collection.insert([Doc(id="a", vector=[0.1, 0.2], fields={'price': 100, 'type': "dress"}), vector=Doc(id="b", [0.3, 0.4], fields={'price': 80, 'type': "shirt"})])
            if not rsp:
                raise RuntimeError(f"InsertDoc Failed, error:{rsp.code}, message:{rsp.message}")

            [asynchronous insert]
            rsp = collection.insert(("a", [0.1, 0.2], {'price': 100, 'type': "dress"}), async_req=True)
            if not rsp.get():
                raise RuntimeError(f"InsertDoc Failed, error:{rsp.code}, message:{rsp.message}")

            [asynchronous batch insert]
            rsp = collection.insert([("a", [0.1, 0.2], {'price': 100, 'type': "dress"}), ("b", [0.3, 0.4], {'price': 80, 'type': "shirt"})], async_req=True)
            if not rsp.get():
                raise RuntimeError(f"InsertDoc Failed, error:{rsp.code}, message:{rsp.message}")
        """

        if self._code != DashVectorCode.Success:
            return DashVectorResponse(
                None, exception=DashVectorException(code=self.code, reason=self.message, request_id=self.request_id)
            )

        try:
            insert_request = UpsertDocRequest(
                collection_meta=self._collection_meta, docs=docs, partition=partition, action="insert"
            )
        except DashVectorException as e:
            return DashVectorResponse(None, exception=e)

        return DashVectorResponse(self._handler.insert_doc(insert_request, async_req=async_req))

    def update(
        self,
        docs: Union[Doc, List[Doc], Tuple, List[Tuple]],
        *,
        partition: Optional[str] = None,
        async_req: bool = False,
    ) -> DashVectorResponse:
        """
        Update one or more Docs like Insert Operation.

        Args:
            docs (Union[Doc, List[Doc], Tuple, List[Tuple]]): one or more Docs which will insert into collection.
            partition (str): a partition name in collection. [optional]
            async_req (bool): use asynchronous operation.

        Return:
            DashVectorResponse, include code / message / request_id and a get() method,
                             code == DashVectorCode.Success means update docs success, otherwise means failure.
                             if you use async_req, must call get() method first.
        """

        if self._code != DashVectorCode.Success:
            return DashVectorResponse(
                None, exception=DashVectorException(code=self.code, reason=self.message, request_id=self.request_id)
            )

        try:
            update_request = UpsertDocRequest(
                collection_meta=self._collection_meta, docs=docs, partition=partition, action="update"
            )
        except DashVectorException as e:
            return DashVectorResponse(None, exception=e)

        return DashVectorResponse(self._handler.update_doc(update_request, async_req=async_req))

    def upsert(
        self,
        docs: Union[Doc, List[Doc], Tuple, List[Tuple]],
        *,
        partition: Optional[str] = None,
        async_req: bool = False,
    ) -> DashVectorResponse:
        """
        Update one or more Docs and do Insert Operation when Doc does not exist.

        Args:
            docs (Union[Doc, List[Doc], Tuple, List[Tuple]]): one or more docs which will update into collection.
            partition (str): a partition name in collection. [optional]
            async_req (bool): use asynchronous operation.

        Return:
            DashVectorResponse, include code / message / request_id and a get() method,
                             code == DashVectorCode.Success means update docs success, otherwise means failure.
                             if you use async_req, must call get() method first.
        """

        if self._code != DashVectorCode.Success:
            return DashVectorResponse(
                None, exception=DashVectorException(code=self.code, reason=self.message, request_id=self.request_id)
            )

        try:
            upsert_request = UpsertDocRequest(
                collection_meta=self._collection_meta, docs=docs, partition=partition, action="upsert"
            )
        except DashVectorException as e:
            return DashVectorResponse(None, exception=e)

        return DashVectorResponse(self._handler.upsert_doc(upsert_request, async_req=async_req))

    def fetch(
        self, ids: Union[str, List[str]], *, partition: Optional[str] = None, async_req: bool = False
    ) -> DashVectorResponse:
        """
        Get one or more Docs with ids(primary keys).

        Args:
           ids (Union[str, List[str]]): one or more docs primary keys.
           partition (str): a partition name in collection. [optional]
           async_req (bool): use asynchronous operation.

        Return:
           DashVectorResponse, include code / message / request_id / output and a get() method,
                            code == DashVectorCode.Success means fetch docs success, otherwise means failure.
                            if you use async_req, must call get() method first.

        Examples:
            [fetch a Doc]
            rsp = collection.fetch(ids="primary_key")
            if not rsp:
                raise RuntimeError(f"FetchDoc Failed, error:{rsp.code}, message:{rsp.message}")
            doc_meta = rsp.output
            print("doc_meta:", doc_meta)

            [fetch multiple Docs]
            rsp = collection.fetch(ids=["primary_key_1", "primary_key_2", "primary_key_3"])
            if not rsp:
                raise RuntimeError(f"FetchDoc Failed, error:{rsp.code}, message:{rsp.message}")
            doc_metas = rsp.output
            for doc_meta in doc_metas:
                print("doc_meta:", doc_meta)

            [asynchronous fetch a Doc]
            rsp = collection.fetch(ids="primary_key", async_req=True)
            if rsp.get().code != DashVectorCode.Success:
                raise RuntimeError(f"FetchDoc Failed, error:{rsp.code}, message:{rsp.message}")
            doc_meta = rsp.output
            print("doc_meta:", doc_meta)
        """

        if self._code != DashVectorCode.Success:
            return DashVectorResponse(
                None, exception=DashVectorException(code=self.code, reason=self.message, request_id=self.request_id)
            )

        try:
            fetch_request = FetchDocRequest(collection_meta=self._collection_meta, ids=ids, partition=partition)
        except DashVectorException as e:
            return DashVectorResponse(None, exception=e)

        return DashVectorResponse(self._handler.fetch_doc(fetch_request, async_req=async_req))

    def query(
        self,
        vector: Optional[Union[List[Union[int, float]], np.ndarray, VectorQuery, Dict[str, VectorQuery]]] = None,
        sparse_vectors: Union[None, Dict[str, SparseVectorQuery]] = None,
        *,
        id: Optional[str] = None,
        topk: int = 10,
        filter: Optional[str] = None,
        include_vector: bool = False,
        partition: Optional[str] = None,
        output_fields: Optional[List[str]] = None,
        async_req: bool = False,
        sparse_vector: Optional[Dict[int, float]] = None,
        rerank: Optional[BaseRanker] = None,
        order_by_fields: Optional[Union[OrderByField, List[OrderByField]]] = None,
    ) -> DashVectorResponse:
        """
        Query Docs with a vector or a doc id.

        Args:
            vector (Optional[Union[List[Union[int, float, bool]], np.ndarray, VectorQuery, Dict[str, VectorQuery]]]): a doc vector, a vector query or dict of vector query
            id (Optional[str]): a doc id.
            topk (int): return topk similarity docs, default is 10.
            filter (str): doc fields filter conditions that meet the SQL where clause specification. [optional]
            include_vector (bool): whether to has vector in return docs, default is False.
            partition (str): a partition name in collection. [optional]
            output_fields (List[str]): select fields in return docs. [optional]
            async_req (bool): use asynchronous operation, default is False.
            sparse_vector(Dict[int, float]): a sparse vector for hybrid search. [optional]

        Return:
            DashVectorResponse, include code / message / request_id / output and a get() method,
                             code == DashVectorCode.Success means query docs success, otherwise means failure.
                             if you use async_req, must call get() method first.

        Examples:
            [query with vector]
            rsp = collection.query([0.1, 0.2])
            if not rsp:
                raise RuntimeError(f"Query Failed, error:{rsp.code}, message:{rsp.message}")
            doc_metas = rsp.output
            for doc_meta in doc_metas:
                print("doc_meta:", doc_meta)

            [query with doc id]
            rsp = collection.query(id="1")
            if not rsp:
                raise RuntimeError(f"Query Failed, error:{rsp.code}, message:{rsp.message}")
            doc_metas = rsp.output
            for doc_meta in doc_metas:
                print("doc_meta:", doc_meta)

            [query with topk]
            rsp = collection.query([0.1, 0.2], topk=100")
            if not rsp:
                raise RuntimeError(f"Query Failed, error:{rsp.code}, message:{rsp.message}")
            doc_metas = rsp.output
            for doc_meta in doc_metas:
                print("doc_meta:", doc_meta)

            [query with vector and filter]
            rsp = collection.query([0.1, 0.2], topk=100, filter="price > 99")
            if not rsp:
                raise RuntimeError(f"Query Failed, error:{rsp.code}, message:{rsp.message}")
            doc_metas = rsp.output
            for doc_meta in doc_metas:
                print("doc_meta:", doc_meta)

            [query with filter]
            rsp = collection.query(topk=100, filter="price > 99")
            if not rsp:
                raise RuntimeError(f"Query Failed, error:{rsp.code}, message:{rsp.message}")
            doc_metas = rsp.output
            for doc_meta in doc_metas:
                print("doc_meta:", doc_meta)

            [query with output_fields]
            rsp = collection.query([0.1, 0.2], topk=100, output_fields=["price"],)
            if not rsp:
                raise RuntimeError(f"Query Failed, error:{rsp.code}, message:{rsp.message}")
            doc_metas = rsp.output
            for doc_meta in doc_metas:
                print("doc_meta:", doc_meta)

            [query with include_vector]
            rsp = collection.query([0.1, 0.2], topk=100, output_fields=["price"], include_vector=True)
            if not rsp:
                raise RuntimeError(f"Query Failed, error:{rsp.code}, message:{rsp.message}")
            doc_metas = rsp.output
            for doc_meta in doc_metas:
                print("doc_meta:", doc_meta)

            [query with multi vector]
            rsp = collection.query(vector={'vec1':VectorQuery([0.1, 0.2],num_candidates=10),'vec2':VectorQuery([0.3, 0.4],num_candidates=100)}, rerank=RrfRank(), topk=100)

            [query with advanced arguments]
            rsp = collection.query(vector=VectorQuery([0.1, 0.2],ef=500,is_linear=True,radius=1.0), topk=100)

            [asynchronous query]
            rsp = collection.query([0.1, 0.2], async_req=True)
            if rsp.get().code != DashVectorCode.Success:
                raise RuntimeError(f"Query Failed, error:{rsp.code}, message:{rsp.message}")
            doc_metas = rsp.output
            for doc_meta in doc_metas:
                print("doc_meta:", doc_meta)
        """

        if self._code != DashVectorCode.Success:
            return DashVectorResponse(
                None, exception=DashVectorException(code=self.code, reason=self.message, request_id=self.request_id)
            )

        try:
            query_request = QueryDocRequest(
                collection_meta=self._collection_meta,
                vector=vector,
                sparse_vectors=sparse_vectors,
                id=id,
                topk=topk,
                filter=filter,
                include_vector=include_vector,
                partition=partition,
                output_fields=output_fields,
                sparse_vector=sparse_vector,
                rerank=rerank,
                order_by_fields=order_by_fields,
            )
        except DashVectorException as e:
            return DashVectorResponse(None, exception=e)

        return DashVectorResponse(self._handler.query_doc(query_request, async_req=async_req))

    def query_group_by(
        self,
        vector: Optional[Union[List[Union[int, float]], np.ndarray]] = None,
        *,
        group_by_field: str,
        group_count: int = 10,
        group_topk: int = 10,
        id: Optional[str] = None,
        filter: Optional[str] = None,
        include_vector: bool = False,
        partition: Optional[str] = None,
        output_fields: Optional[List[str]] = None,
        async_req: bool = False,
        sparse_vector: Optional[Dict[int, float]] = None,
        vector_field: Optional[str] = None,
    ) -> DashVectorResponse:
        """
        GroupBy Query Docs with a vector or a doc id.

        Args:
            vector (Optional[Union[List[Union[int, float, bool]], np.ndarray]]): a doc vector.
            group_by_field (str): field to group by.
            group_count (int): group count, default is 10.
            group_topk (int): return topk similarity docs in each group, default is 10.
            id (Optional[str]): a doc id.
            filter (str): doc fields filter conditions that meet the SQL where clause specification. [optional]
            include_vector (bool): whether to has vector in return docs, default is False.
            partition (str): a partition name in collection. [optional]
            output_fields (List[str]): select fields in return docs. [optional]
            async_req (bool): use asynchronous operation, default is False.
            sparse_vector(Dict[int, float]): a sparse vector for hybrid search. [optional]
            vector_field(Optional[str]): specify vector field name for multi-vector collection. [optional]

        Return:
            DashVectorResponse, include code / message / request_id / output and a get() method,
                             code == DashVectorCode.Success means query docs success, otherwise means failure.
                             if you use async_req, must call get() method first.

        Examples:
            [query with vector]
            rsp = collection.query([0.1, 0.2], group_by_field="price", group_count=10, group_topk=1)
            if not rsp:
                raise RuntimeError(f"Query Failed, error:{rsp.code}, message:{rsp.message}")
            group_metas = rsp.output
            for group_meta in group_metas:
                print("group_meta:", group_meta)
        """

        if self._code != DashVectorCode.Success:
            return DashVectorResponse(
                None, exception=DashVectorException(code=self.code, reason=self.message, request_id=self.request_id)
            )

        try:
            query_request = QueryDocGroupByRequest(
                collection_meta=self._collection_meta,
                vector=vector,
                id=id,
                group_by_field=group_by_field,
                group_count=group_count,
                group_topk=group_topk,
                filter=filter,
                include_vector=include_vector,
                partition=partition,
                output_fields=output_fields,
                sparse_vector=sparse_vector,
                vector_field=vector_field,
            )
        except DashVectorException as e:
            return DashVectorResponse(None, exception=e)

        return DashVectorResponse(self._handler.query_doc_group_by(query_request, async_req=async_req))

    def delete(
        self,
        ids: Optional[Union[str, List[str]]] = None,
        *,
        delete_all: bool = False,
        partition: Optional[str] = None,
        async_req: bool = False,
    ) -> DashVectorResponse:
        """
        Delete one or more Docs with ids(Primary Keys).

        Args:
           ids (Union[str, List[str]]): one or more docs primary keys. [optional]
           delete_all (bool): delete all vectors from partition by setting delete_all is True, default is False.
           partition (str): a partition name in collection. [optional]
           async_req (bool): use asynchronous operation, default is False

        Return:
           DashVectorResponse, include code / message / request_id and a get() method,
                            code == DashVectorCode.Success means delete doc success, otherwise means failure.
                            if you use async_req, must call get() method first.

        Examples:
            [delete a doc]
            rsp = collection.delete(ids="primary_key")
            if not rsp:
                raise RuntimeError(f"Delete Failed, error:{rsp.code}, message:{rsp.message}")

            [delete multiple docs]
            rsp = collection.delete(ids=["primary_key_1", "primary_key_2", "primary_key_3"])
            if not rsp:
                raise RuntimeError(f"Delete Failed, error:{rsp.code}, message:{rsp.message}")

            [delete all docs]
            rsp = collection.delete(delete_all=True)
            if not rsp:
                raise RuntimeError(f"Delete Failed, error:{rsp.code}, message:{rsp.message}")

            [asynchronous delete a doc]
            rsp = collection.delete(ids="primary_key", async_req=True)
            if rsp.get().code != DashVectorCode.Success:
                raise RuntimeError(f"Delete Failed, error:{rsp.code}, message:{rsp.message}")
        """

        if self._code != DashVectorCode.Success:
            return DashVectorResponse(
                None, exception=DashVectorException(code=self.code, reason=self.message, request_id=self.request_id)
            )

        try:
            delete_request = DeleteDocRequest(
                collection_name=self._collection_meta.name, ids=ids, delete_all=delete_all, partition=partition
            )
        except DashVectorException as e:
            return DashVectorResponse(None, exception=e)

        return DashVectorResponse(self._handler.delete_doc(delete_request, async_req=async_req))

    def create_partition(self, name: str, *, timeout: Optional[int] = None) -> DashVectorResponse:
        """
        Create a Partition in current Collection.

        Args:
           name (str): partition name
           timeout (Optional[int]): timeout[second] for wait until the partition is ready, default is 'None' wait indefinitely


        Return:
           DashVectorResponse, include code / message / request_id,
                            code == DashVectorCode.Success means create partition success, otherwise means failure.

        Example:
            rsp = collection.create_partition("partition_name")
            if not rsp:
                raise RuntimeError(f"CreatePartition Failed, error:{rsp.code}, message:{rsp.message}")
        """

        if self._code != DashVectorCode.Success:
            return DashVectorResponse(
                None, exception=DashVectorException(code=self.code, reason=self.message, request_id=self.request_id)
            )

        try:
            create_request = CreatePartitionRequest(collection_name=self._collection_meta.name, partition_name=name)
        except DashVectorException as e:
            return DashVectorResponse(None, exception=e)

        create_response = DashVectorResponse(self._handler.create_partition(create_request, async_req=False))
        if create_response.code != DashVectorCode.Success or timeout == -1:
            return create_response

        create_partition_timeout = timeout
        rpc_error_count = 0
        while True:
            describe_response = self.describe_partition(name)

            if describe_response.code == DashVectorCode.Success:
                status = Status.get(describe_response.output)
                if status == Status.SERVING:
                    return create_response
                elif status in (Status.ERROR, Status.DROPPING):
                    return DashVectorResponse(
                        None,
                        exception=DashVectorException(
                            code=DashVectorCode.UnreadyPartition,
                            reason=f"DashVectorSDK get partition[{name}] status is {describe_response.output}",
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
                        reason=f"DashVectorSDK get partition status failed and reason is {describe_response.message}",
                        request_id=create_response.request_id,
                    ),
                )
            time.sleep(5)
            if create_partition_timeout is None:
                continue
            create_partition_timeout -= 5
            if create_partition_timeout < 0:
                return DashVectorResponse(
                    None,
                    exception=DashVectorException(
                        code=DashVectorCode.Timeout,
                        reason="DashVectorSDK create partition timeout please call the describe_partition to confirm partition status",
                        request_id=create_response.request_id,
                    ),
                )

    def delete_partition(self, name: str) -> DashVectorResponse:
        """
        Delete a Partition in current Collection.

        Args:
           name (str): partition name.

        Return:
           DashVectorResponse, include code / message / request_id,
                            code == DashVectorCode.Success means delete partition success, otherwise means failure.

        Example:
            rsp = collection.delete_partition("partition_name")
            if not rsp:
                raise RuntimeError(f"DeletePartition Failed, error:{rsp.code}, message:{rsp.message}")
        """

        if self._code != DashVectorCode.Success:
            return DashVectorResponse(
                None, exception=DashVectorException(code=self.code, reason=self.message, request_id=self.request_id)
            )

        try:
            delete_request = DeletePartitionRequest(collection_name=self._collection_meta.name, partition_name=name)
        except DashVectorException as e:
            return DashVectorResponse(None, exception=e)

        return DashVectorResponse(self._handler.delete_partition(delete_request, async_req=False))

    def describe_partition(self, name: str) -> DashVectorResponse:
        """
        Describe a Partition Meta in current Collection.

        Args:
           name (str): partition name.

        Return:
           DashVectorResponse, include code / message / request_id / output,
                            code == DashVectorCode.Success means output is a partition meta.

        Example:
            rsp = collection.describe_partition("partition_name")
            if not rsp:
                raise RuntimeError(f"DescribePartition Failed, error:{rsp.code}, message:{rsp.message}")
            partition_meta = rsp.output
            print("partition_meta:", partition_meta)
        """

        if self._code != DashVectorCode.Success:
            return DashVectorResponse(
                None, exception=DashVectorException(code=self.code, reason=self.message, request_id=self.request_id)
            )

        try:
            describe_request = DescribePartitionRequest(collection_name=self._collection_meta.name, partition_name=name)
        except DashVectorException as e:
            return DashVectorResponse(None, exception=e)

        return DashVectorResponse(self._handler.describe_partition(describe_request))

    def stats_partition(self, name: str) -> DashVectorResponse:
        """
        Get Stats Info of a Partition in current Collection.

        Args:
           name (str): partition name

        Return:
           DashVectorResponse, include code / message / request_id / output,
                            code == DashVectorCode.Success means output is a partition stats info.

        Example:
            rsp = collection.stats_partition("partition_name")
            if not rsp:
                raise RuntimeError(f"StatsPartition Failed, error:{rsp.code}, message:{rsp.message}")
            partition_stats = rsp.output
            print("partition_stats:", partition_stats)
        """

        if self._code != DashVectorCode.Success:
            return DashVectorResponse(
                None, exception=DashVectorException(code=self.code, reason=self.message, request_id=self.request_id)
            )
        try:
            stats_request = StatsPartitionRequest(collection_name=self._collection_meta.name, partition_name=name)
        except DashVectorException as e:
            return DashVectorResponse(None, exception=e)
        return DashVectorResponse(self._handler.stats_partition(stats_request))

    def list_partitions(self) -> DashVectorResponse:
        """
        List all Partition Names in current Collection.

        Return:
           DashVectorResponse, include code / message / request_id / output,
                            code == DashVectorCode.Success means output is a partition name list.

        Example:
            rsp = collection.list_partitions()
            if not rsp:
                raise RuntimeError(f"ListPartition Failed, error:{rsp.code}, message:{rsp.message}")
            partition_list = rsp.output
            print("partition_list:", partition_list)
        """

        if self._code != DashVectorCode.Success:
            return DashVectorResponse(
                None, exception=DashVectorException(code=self.code, reason=self.message, request_id=self.request_id)
            )

        try:
            list_request = ListPartitionsRequest(collection_name=self._collection_meta.name)
        except DashVectorException as e:
            return DashVectorResponse(None, exception=e)

        return DashVectorResponse(self._handler.list_partitions(list_request))

    def stats(self) -> DashVectorResponse:
        """
        Get Stats Info of current Collection.

        Return:
           DashVectorResponse, include code / message / request_id / output,
                            code == DashVectorCode.Success means output is a collection stats info dict.

        Example:
            rsp = collection.stats()
            if not rsp:
                raise RuntimeError(f"StatsCollection Failed, error:{rsp.code}, message:{rsp.message}")
            collection_stats = rsp.output
            print("collection_stats:", collection_stats)
        """

        if self._code != DashVectorCode.Success:
            return DashVectorResponse(
                None, exception=DashVectorException(code=self.code, reason=self.message, request_id=self.request_id)
            )

        try:
            stats_request = StatsCollectionRequest(name=self._collection_meta.name)
        except DashVectorException as e:
            return DashVectorResponse(None, exception=e)

        return DashVectorResponse(self._handler.stats_collection(stats_request))

    def __init__(
        self,
        response: Optional[RPCResponse] = None,
        collection_meta: Optional[CollectionMeta] = None,
        handler: Optional[RPCHandler] = None,
        exception: Optional[DashVectorException] = None,
    ):
        """
        a DashVector Collection Instance which create by DashVector.client.get("collection_name")

        Returns:
            Collection, includes a series of Doc related operations
        """

        super().__init__(response, exception=exception)
        self._collection_meta = collection_meta
        self._handler = handler

        self.get()

    def __str__(self):
        if self._collection_meta is not None:
            return self._collection_meta.__str__()
        return super().__str__()

    def __repr__(self):
        if self._collection_meta is not None:
            return self._collection_meta.__repr__()
        return super().__repr__()

    def __bool__(self):
        return self._code == DashVectorCode.Success
