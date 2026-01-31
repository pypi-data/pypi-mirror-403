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

class QueryDocRequest(RPCRequest):
    def __init__(
        self,
        *,
        collection_meta: CollectionMeta,
        vector: Union[None, VectorValueType, VectorQuery, Dict[str, VectorQuery], Dict[str, VectorValueType]] = None,
        sparse_vectors: Union[None, Dict[str, SparseVectorQuery]] = None,
        id: Optional[str] = None,
        topk: int = 10,
        filter: Optional[str] = None,
        include_vector: bool = False,
        partition: Optional[str] = None,
        output_fields: Optional[List[str]] = None,
        sparse_vector: Optional[Dict[int, float]] = None,
        rerank : Optional[BaseRanker] = None,
        order_by_fields: Optional[Union[OrderByField, List[OrderByField]]] = None,
    ):
        self._collection_meta = collection_meta
        self._collection_name = collection_meta.name
        self._field_map = collection_meta.fields_schema
        self._id = id
        self._vector_queries = {}
        self._sparse_vectors = {}
        """
        QueryRequest
        """
        query_request = dashvector_pb2.QueryDocRequest()

        """
        vector: Optional[VectorValueType] = None
        """
        if id is not None and vector is not None:
            raise DashVectorException(
                code=DashVectorCode.ExistVectorAndId,
                reason="DashVectorSDK QueryDocRequest supports passing in either or neither of the two parameters vector and id, but not both",
            )
        elif id is not None:
            query_request.id = Validator.validate_id(id, doc_op="QueryDocRequest")
            
        elif vector is not None:
            validator = ValidatorFactory.meta_create(collection_meta)
            query_request = validator.validate_query_vectors(vector=vector, top_k=topk, query_request=query_request, doc_op="QueryDocRequest")
            for vector_name, vector_query in query_request.vectors.items():
                self._vector_queries[vector_name] = convert_vector_query_from_pb(vector_query)

        """
        sparse_vectors: Dict[str, SparseVectorQuery] = None
        """
        if sparse_vectors is not None:
            self._sparse_vectors = sparse_vectors
            for vector_name, vector_query in sparse_vectors.items():
                checker = SparseVectorChecker(collection_meta, vector_name, vector_query, doc_op="QueryDocRequest")
                query_request.sparse_vectors[vector_name].CopyFrom(checker.vector_query)
        

        """
        rerank: BaseRanker
        """
        self._rerank = None
        if len(self._vector_queries) + len(self._sparse_vectors) > 1 and rerank is not None:
            rerank = Validator.validate_rerank(rerank, query_request, "QueryDocRequest")
            query_request.rerank.CopyFrom(rerank.to_pb())
            self._rerank = rerank

        """
        include_vector: bool = False,
        """
        self._include_vector = Validator.validate_include_vector(include_vector, "QueryDocRequest")
        query_request.include_vector = self._include_vector

        """
        topk: int = 10
        """
        self._topk = Validator.validate_topk(topk, include_vector, "QueryDocRequest")
        query_request.topk = self._topk

        """
        filter: Optional[str] = None,
        """
        self._filter = Validator.validate_filter(filter, "QueryDocRequest")
        if self._filter is not None:
            query_request.filter = self._filter

        """
        partition: Optional[str] = None
        """
        self._partition = None
        if partition is not None:
            self._partition = Validator.validate_partition_name(partition, "QueryDocRequest")
        if self._partition is not None:
            query_request.partition = self._partition

        """
        output_fields: Optional[List[str]] = None
        """
        self._output_fields = Validator.validate_output_fields(output_fields, "QueryDocRequest")
        if self._output_fields is not None:
            query_request.output_fields.extend(self._output_fields)

        """
        sparse_vector: Optional[Dict[int, float]] = None
        """
        self._sparse_vector = sparse_vector
        if self._sparse_vector is not None:
            if len(self.collection_meta.vectors_schema) > 1:
                raise DashVectorException(
                    code=DashVectorCode.InvalidSparseValues,
                    reason=f"DashVectorSDK supports query with sparse_vector only collection with one vector field",
                )
            metric = self.collection_meta.metric
            if metric != MetricStrType.DOTPRODUCT:
                raise DashVectorException(
                    code=DashVectorCode.InvalidSparseValues,
                    reason=f"DashVectorSDK supports query with sparse_vector only collection metric is dotproduct",
                )
            for key, value in to_sorted_sparse_vector(self._sparse_vector).items():
                query_request.sparse_vector[key] = value

        """
        order_by_fields:  Optional[Union[OrderByField, List[OrderByField]]] = None
        """
        self._order_by_fields = order_by_fields
        if self._order_by_fields is not None:
            if isinstance(self._order_by_fields, OrderByField):
                query_request.order_by_fields.append(self._order_by_fields.to_proto())
            elif isinstance(self._order_by_fields, list):
                for order_by_field in self._order_by_fields:
                    if not isinstance(order_by_field, OrderByField):
                        raise DashVectorException(
                            code=DashVectorCode.InvalidArgument,
                            reason=f"DashVectorSDK QueryDocRequest order_by_fields must be an instance of class OrderByField or a list of OrderByField, but got list[{type(order_by_field)}].",
                        )
                    query_request.order_by_fields.append(order_by_field.to_proto())
            else:
                raise DashVectorException(
                    code=DashVectorCode.InvalidArgument,
                    reason=f"DashVectorSDK QueryDocRequest order_by_fields must be an instance of class OrderByField or a list of OrderByField, but got ({type(order_by_fields)}).",
                )
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
            "topk": self._topk,
            "include_vector": self._include_vector,
        }
        if len(self._vector_queries) + len(self._sparse_vectors) > 0:
            vectors = {}
            for vector_name, vector_query in self._vector_queries.items():
                vq = {}
                vector = vector_query.vector
                if isinstance(vector, np.ndarray):
                    vector = vector.astype(np.float32).tolist()
                vq['vector'] = vector
                param_dict = {}
                if vector_query.num_candidates != 0:
                    param_dict['num_candidates'] = vector_query.num_candidates
                if vector_query.ef != 0:
                    param_dict['ef'] = vector_query.ef
                if vector_query.radius != 0.0:
                    param_dict['radius'] = vector_query.radius
                if vector_query.is_linear:
                    param_dict['is_linear'] = vector_query.is_linear
                if param_dict:
                    vq['param'] = param_dict
                vectors[vector_name] = vq
            data["vectors"] = vectors

            sparse_vectors = {}
            for vector_name, vector_query in self._sparse_vectors.items():
                sp_qry = {}
                sp_qry['sparse_vector'] = vector_query.vector
                param_dict = {}
                if vector_query.num_candidates != 0:
                    param_dict['num_candidates'] = vector_query.num_candidates
                if vector_query.ef != 0:
                    param_dict['ef'] = vector_query.ef
                if vector_query.radius != 0.0:
                    param_dict['radius'] = vector_query.radius
                if vector_query.is_linear:
                    param_dict['is_linear'] = vector_query.is_linear
                if param_dict:
                    sp_qry['param'] = param_dict
                sparse_vectors[vector_name] = sp_qry
            data['sparse_vectors'] = sparse_vectors
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
        if self._rerank is not None:
            data["rerank"] = self._rerank.to_dict()
        if self._order_by_fields is not None:
            if isinstance(self._order_by_fields, OrderByField):
                data["order_by_fields"] = [self._order_by_fields.to_dict()]
            elif isinstance(self._order_by_fields, list):
                data["order_by_fields"] = [field.to_dict() for field in self._order_by_fields]
        return json.dumps(data)
