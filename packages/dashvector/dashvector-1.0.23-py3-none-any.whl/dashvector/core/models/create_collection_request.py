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

from dashvector.common.common_validator import *
from dashvector.common.vector_validator import *
from dashvector.common.constants import *
from dashvector.common.handler import RPCRequest
from dashvector.common.types import *
from dashvector.core.index import Index, IndexConverter
from dashvector.core.proto import dashvector_pb2


class CreateCollectionRequest(RPCRequest):
    def __init__(
        self,
        *,
        name: str,
        dimension: int,
        dtype: VectorDataType = float,
        fields_schema: Optional[FieldSchemaDict] = None,
        metric: str = "cosine",
        extra_params: Optional[Dict[str, Any]] = None,
        vectors: Union[None, VectorParam, Dict[str, VectorParam]] = None,
        sparse_vectors: Union[None, VectorParam, Dict[str, VectorParam]] = None,
        indexes: Optional[Dict[str, Index]] = None,
        
    ):
        """
        name: str
        """
        self._name = Validator.validate_collection_name(name, doc_op="CreateCollectionRequest")

        """
        vectors, sparse_vectors
        """
        validator = ValidatorFactory.input_type_create(vectors, sparse_vectors)
        self._vectors, self._sparse_vectors = validator.validate_collection_vectors(
            vectors=vectors, sparse_vectors=sparse_vectors, 
            dimension=dimension, dtype=dtype, metric=metric, doc_op="CreateCollectionRequest")

        """
        fields_schema: Optional[FieldSchemaDict]
        """
        self._fields_schema = Validator.validate_fields_schema(fields_schema, doc_op="CreateCollectionRequest")
        
        """
        extra_params: Optional[Dict[str, Any]]
        """
        self._extra_params = Validator.validate_extra_params(extra_params, doc_op="CreateCollectionRequest")

        """indexes"""
        self._indexes = {}
        if indexes is not None:
            if not isinstance(indexes, dict):
                raise DashVectorException(
                    code=DashVectorCode.InvalidArgument,
                    reason=f"DashVectorSDK CreateCollectionRequest indexes type({type(indexes)}) is invalid and must be dict",
                )
            if len(indexes) > 1024:
                raise DashVectorException(
                    code=DashVectorCode.InvalidField,
                    reason=f"DashVectorSDK CreateCollectionRequest indexes length({len(indexes)}) is invalid and must be in [0, 1024]",
                )
            if not set(indexes.keys()).issubset(fields_schema.keys()):
                raise DashVectorException(
                    code=DashVectorCode.MismatchedIndexColumn,
                    reason=f"DashVectorSDK CreateCollectionRequest indexes field_name({indexes.keys() - fields_schema.keys()}) is invalid and must be in fields_schema",
                )
            self._indexes = indexes

        """
        DashVectorCollectionRequest: google.protobuf.Message
        """
        create_request = dashvector_pb2.CreateCollectionRequest()
        create_request.name = self._name

        # vectors
        for vector_name, vector_param in self._vectors.items():
            vector_pb = create_request.vectors_schema[vector_name]
            vector_pb.metric = MetricType.get(vector_param.metric)
            vector_pb.dimension = vector_param.dimension
            vector_pb.dtype = VectorType.get(vector_param.dtype)
            vector_pb.quantize_type = vector_param.quantize_type

        # sparse_vectors
        for vector_name, vector_param in self._sparse_vectors.items():
            sparse_vector_pb = create_request.sparse_vectors_schema[vector_name]
            sparse_vector_pb.metric = MetricType.get(vector_param.metric)
            sparse_vector_pb.dimension = vector_param.dimension
            sparse_vector_pb.dtype = VectorType.get(vector_param.dtype)
            sparse_vector_pb.quantize_type = vector_param.quantize_type

        # fields_schema
        if len(self._fields_schema) > 0:
            for field_name, field_dtype in self._fields_schema.items():
                create_request.fields_schema[field_name] = field_dtype

        # indexes
        if len(self._indexes) > 0:
            for index_name, index in self._indexes.items():
                create_request.indexes[index_name].index_type = IndexConverter.to_index_from_model(index).index_type

        # extra_params
        if len(self._extra_params) > 0:
            create_request.extra_params.update(self._extra_params)

        super().__init__(request=create_request)
