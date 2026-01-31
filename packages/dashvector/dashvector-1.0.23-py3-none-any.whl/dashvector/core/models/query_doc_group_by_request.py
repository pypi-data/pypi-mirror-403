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

import re

from dashvector.common.constants import *
from dashvector.common.common_validator import *
from dashvector.common.vector_validator import *
from dashvector.common.handler import RPCRequest
from dashvector.common.types import *
from dashvector.core.models.collection_meta_status import CollectionMeta
from dashvector.core.proto import dashvector_pb2
from dashvector.util.convertor import to_sorted_sparse_vector


class QueryDocGroupByRequest(RPCRequest):
    def __init__(
        self,
        *,
        collection_meta: CollectionMeta,
        vector: Optional[VectorValueType] = None,
        id: Optional[str] = None,
        group_by_field: Optional[str] = None,
        group_topk: int = 10,
        group_count: int = 10,
        filter: Optional[str] = None,
        include_vector: bool = False,
        partition: Optional[str] = None,
        output_fields: Optional[List[str]] = None,
        sparse_vector: Optional[Dict[int, float]] = None,
        vector_field: Optional[str] = None,
    ):
        self._collection_meta = collection_meta
        self._collection_name = collection_meta.name
        if not vector_field:
            self._dtype = VectorType.get(collection_meta.dtype)
            self._dimension = collection_meta.dimension
            self._metric = collection_meta.metric
        else:
            self._dtype = VectorType.get(collection_meta.get_dtype(vector_field))
            self._dimension = collection_meta.get_dimension(vector_field)
            self._metric = collection_meta.get_metric(vector_field)
        self._field_map = collection_meta.fields_schema
        self._origin_vector = vector
        self._id = id
        self._vector_field = vector_field
        """
        QueryDocGroupByRequest
        """
        query_request = dashvector_pb2.QueryDocGroupByRequest()

        """
        group_topk: int = 10,
        """
        if not isinstance(group_topk, int):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK QueryDocGroupByRequest group_topk type({type(group_topk)}) is invalid and must be int",
            )
        if group_topk < 1 or (include_vector and group_topk > 16):
            raise DashVectorException(
                code=DashVectorCode.InvalidGroupBy,
                reason=f"DashVectorSDK QueryDocGroupByRequest group_topk value({group_topk}) is invalid and must be in [1, 16] when include_vector is true",
            )
        self._group_topk = group_topk
        query_request.group_topk = group_topk

        """
        vector: Optional[VectorValueType] = None
        """
        self._vector = vector
        if id is not None and vector is not None:
            raise DashVectorException(
                code=DashVectorCode.ExistVectorAndId,
                reason="DashVectorSDK QueryDocGroupByRequest supports passing in either vector or id, but not both",
            )
        elif id is not None:
            query_request.id = Validator.validate_id(id, doc_op="QueryDocGroupByRequest")

        elif vector is not None:
            validator = ReserveVectorValidator(collection_meta, vector_field)
            query_request = validator.validate_query_vectors(vector=vector, top_k=group_topk, query_request=query_request, doc_op="QueryDocGroupByRequest")

        elif sparse_vector is None:
            raise DashVectorException(
                code=DashVectorCode.UnsupportedCondition,
                reason="DashVectorSDK QueryDocGroupByRequest requires passing in either vector or id",
            )

        """
        group_by_field: Optional[str] = None,
        """
        if not group_by_field or not isinstance(group_by_field, str):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK QueryDocGroupByRequest group_by_field type({type(group_by_field)}) is invalid and must be str",
            )
        self._group_by_field = group_by_field
        query_request.group_by_field = group_by_field
        """
        group_count: int = 10
        """
        if not isinstance(group_count, int):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK QueryDocGroupByRequest group_count type({type(group_count)}) is invalid and must be int",
            )
        if group_count < 1 or (include_vector and group_count > 64):
            raise DashVectorException(
                code=DashVectorCode.InvalidGroupBy,
                reason=f"DashVectorSDK QueryDocGroupByRequest group_count value({group_count}) is invalid and must be in [1, 64]",
            )
        self._group_count = group_count
        query_request.group_count = group_count

        """
        filter: Optional[str] = None,
        """
        self._filter = Validator.validate_filter(filter, "QueryDocGroupByRequest")
        if self._filter is not None:
            query_request.filter = self._filter

        """
        include_vector: bool = False,
        """
        self._include_vector = Validator.validate_include_vector(include_vector, "QueryDocGroupByRequest")
        query_request.include_vector = self._include_vector

        """
        partition: Optional[str] = None
        """
        self._partition = None
        if partition is not None:
            self._partition = Validator.validate_partition_name(partition, doc_op="QueryDocGroupByRequest")
        if self._partition is not None:
            query_request.partition = self._partition

        """
        output_fields: Optional[List[str]] = None
        """
        self._output_fields = Validator.validate_output_fields(output_fields, "QueryDocGroupByRequest")
        if self._output_fields is not None:
            query_request.output_fields.extend(self._output_fields)

        """
        sparse_vector: Optional[Dict[int, float]] = None
        """
        self._sparse_vector = sparse_vector
        if self._sparse_vector is not None:
            if self._metric != MetricStrType.DOTPRODUCT:
                raise DashVectorException(
                    code=DashVectorCode.InvalidSparseValues,
                    reason=f"DashVectorSDK supports query with sparse_vector only collection metric is dotproduct",
                )
            for key, value in to_sorted_sparse_vector(self._sparse_vector).items():
                query_request.sparse_vector[key] = value

        """
        vector_field: Optional[str] = None
        """
        if self._vector_field is not None:
            query_request.vector_field = self._vector_field

        super().__init__(request=query_request)

    @property
    def collection_meta(self):
        return self._collection_meta

    @property
    def collection_name(self):
        return self._collection_name

    @property
    def include_vector(self):
        return self._include_vector

    def to_json(self):
        data = {
            "include_vector": self._include_vector,
            "group_by_field": self._group_by_field,
            "group_topk": self._group_topk,
            "group_count": self._group_count,
        }
        if self._origin_vector is not None:
            vector = self._origin_vector
            if isinstance(vector, np.ndarray):
                vector = vector.astype(np.float32).tolist()
            data["vector"] = vector
        else:
            data["id"] = self._id
        if self._filter is not None:
            data["filter"] = self._filter
        if self._partition is not None:
            data["partition"] = self._partition
        if self._sparse_vector is not None:
            data["sparse_vector"] = self._sparse_vector
        if self._output_fields is not None:
            data["output_fields"] = self._output_fields
        if self._vector_field is not None:
            data["vector_field"] = self._vector_field

        return json.dumps(data)
