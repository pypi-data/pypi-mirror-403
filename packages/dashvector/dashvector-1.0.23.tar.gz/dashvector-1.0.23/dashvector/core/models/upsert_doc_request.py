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
from typing import Tuple

from dashvector.common.constants import *
from dashvector.common.common_validator import *
from dashvector.common.handler import RPCRequest
from dashvector.common.types import *
from dashvector.core.doc import Doc, DocBuilder
from dashvector.core.models.collection_meta_status import CollectionMeta
from dashvector.core.proto import dashvector_pb2
from dashvector.util.convertor import to_sorted_sparse_vector, to_sorted_sparse_vectors
from dashvector.util.validator import vector_is_empty


class UpsertDocRequest(RPCRequest):
    def __init__(
        self,
        *,
        collection_meta: CollectionMeta,
        docs: Union[Doc, Tuple, List[Doc], List[Tuple]],
        partition: Optional[str] = None,
        action: str = "upsert",
    ):
        """
        collection_meta: CollectionMeta
        """
        self._collection_meta = collection_meta
        self._collection_name = collection_meta.name
        self._field = collection_meta.fields_schema

        """
        partition: Optional[str]
        """
        self._partition = None
        if partition is not None:
            self._partition = Validator.validate_partition_name(partition, doc_op="UpsertDocRequest")

        """
        action: str
        """
        self._action = ""
        if not isinstance(action, str):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK UpsertDocRequest action type({type(action)}) is invalid and must be str",
            )
        if action not in ("upsert", "insert", "update"):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK UpsertDocRequest action value({action}) is invalid and must be in ['insert', 'update', 'upsert']",
            )
        self._action = action

        """
        InsertDocRequest: google.protobuf.Message
        UpdateDocRequest: google.protobuf.Message
        UpsertDocRequest: google.protobuf.Message
        """
        if self._action == "upsert":
            upsert_request = dashvector_pb2.UpsertDocRequest()
        elif self._action == "insert":
            upsert_request = dashvector_pb2.InsertDocRequest()
        else:
            upsert_request = dashvector_pb2.UpdateDocRequest()

        if self._partition is not None:
            upsert_request.partition = self._partition

        """
        docs: Union[Doc, Tuple, List[Doc], List[Tuple]]
        """
        user_docs = []
        if isinstance(docs, Doc):
            id, vector, sparse_vectors, fields, sparse_vector, vectors = self._parse_doc(doc=docs)
            user_docs.append(docs)
        elif isinstance(docs, tuple):
            id, vector, fields, sparse_vector = self._parse_tuple(tup=docs, action=self._action)
            user_docs.append(Doc(vector=vector, fields=fields, sparse_vector=sparse_vector))
        elif isinstance(docs, list):
            if len(docs) <= 0 or len(docs) > 1024:
                raise DashVectorException(
                    code=DashVectorCode.InvalidBatchSize,
                    reason=f"DashVectorSDK UpsertDocRequest input docs length({len(docs)}) is invalid and must be in [1, 1024]",
                )

            for doc in docs:
                vectors = None
                sparse_vectors = None
                if isinstance(doc, Doc):
                    id, vector, sparse_vectors, fields, sparse_vector, vectors = self._parse_doc(doc=doc)
                    user_docs.append(doc)
                elif isinstance(doc, tuple):
                    id, vector, fields, sparse_vector = self._parse_tuple(tup=doc, action=self._action)
                    user_docs.append(Doc(vector=vector, fields=fields, sparse_vector=sparse_vector))
                else:
                    raise DashVectorException(
                        code=DashVectorCode.InvalidArgument,
                        reason=f"DashVectorSDK UpsertDocRequest doc type({type(doc)}) in docs is invalid and must be in [Doc, Tuple]",
                    )
        else:
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK UpsertDocRequest input type({type(docs)}) is Invalid and must be in [Doc, Tuple]",
            )
        self._docs = []
        for doc in user_docs:
            doc = Validator.validate_doc(doc, collection_meta, action, "UpsertDocRequest")
            id, vector, sparse_vectors, field_map, sparse_vector, vectors = self._parse_doc(doc=doc)
            new_doc = upsert_request.docs.add()

            # doc id
            if id:
                new_doc.id = id

            # doc vector
            if isinstance(vector, bytes):
                new_doc.vector.byte_vector = vector
            elif isinstance(vector, list):
                new_doc.vector.float_vector.values.extend(vector)
            elif isinstance(vector, np.ndarray):
                new_doc.vector.float_vector.values.extend(vector)

            # doc vectors
            if vectors is not None:
                for k, v in vectors.items():
                    vec = new_doc.vectors[k]
                    if isinstance(v, bytes):
                        vec.byte_vector = v
                    elif isinstance(v, list):
                        vec.float_vector.values.extend(v)
                    elif isinstance(v, np.ndarray):
                        vec.float_vector.values.extend(v)
            
            # doc sparse_vectors
            if sparse_vectors is not None:
                for k, v in sparse_vectors.items():
                    vec = new_doc.sparse_vectors[k]
                    for key in v:
                        vec.sparse_vector[key] = v[key]

            # doc fields
            if field_map is not None:
                for field_name, field_value in field_map.items():
                    if not isinstance(field_name, str):
                        raise DashVectorException(
                            code=DashVectorCode.InvalidArgument,
                            reason=f"DashVectorSDK UpsertDocRequest field name type({type(field_name)}) is invalid and must be str",
                        )

                    if re.search(FIELD_NAME_PATTERN, field_name) is None:
                        raise DashVectorException(
                            code=DashVectorCode.InvalidFieldName,
                            reason=f"DashVectorSDK UpsertDocRequest field name characters({field_name}) is invalid and "
                            + FIELD_NAME_PATTERN_MSG,
                        )

                    fvalue = new_doc.fields[field_name]
                    ftype_str = collection_meta.fields_schema.get(field_name)
                    if ftype_str is not None:
                        ftype = FieldType.get(ftype_str)
                        if FieldType.ARRAY_STRING <= ftype <= FieldType.ARRAY_LONG:
                            if not isinstance(field_value, list):
                                raise DashVectorException(
                                    code=DashVectorCode.InvalidFieldName,
                                    reason=f"DashVectorSDK field({field_name}) value not match the type. "
                                           f"type:{ftype_str} value:{field_value}",
                                )
                            if len(field_value) > 32:
                                raise DashVectorException(
                                    code=DashVectorCode.InvalidFieldName,
                                    reason=f"DashVectorSDK field({field_name}) array only allow len <= 32. "
                                           f"type:{ftype_str} value:{field_value}",
                                )

                    else:   # schema-free field
                        if isinstance(field_value, list):
                            raise DashVectorException(
                                code=DashVectorCode.InvalidFieldName,
                                reason=f"DashVectorSDK schema-free field({field_name}) not support array type ",
                            )
                        ftype = FieldType.get_field_data_type(type(field_value))
                    if ftype == FieldType.INT and not (MIN_INT_VALUE <= field_value <= MAX_INT_VALUE):
                        ftype = FieldType.LONG
                    try:
                        if ftype == FieldType.BOOL:
                            fvalue.bool_value = field_value
                        elif ftype == FieldType.FLOAT:
                            fvalue.float_value = field_value
                        elif ftype == FieldType.INT:
                            fvalue.int_value = field_value
                        elif ftype == FieldType.STRING:
                            fvalue.string_value = field_value
                        elif ftype == FieldType.LONG:
                            fvalue.long_value = field_value
                        elif ftype == FieldType.ARRAY_FLOAT:
                            fvalue.float_array.values.extend(field_value)
                        elif ftype == FieldType.ARRAY_INT:
                            fvalue.int_array.values.extend(field_value)
                        elif ftype == FieldType.ARRAY_LONG:
                            fvalue.long_array.values.extend(field_value)
                        elif ftype == FieldType.ARRAY_STRING:
                            fvalue.string_array.values.extend(field_value)
                    except (ValueError, TypeError) as e:
                        raise DashVectorException(
                            code=DashVectorCode.InvalidField,
                            reason=f"DashVectorSDK UpsertDocRequest field value({field_value}) is invalid and {e}",
                        )
            # doc sparse_vector
            if sparse_vector is not None:
                if len(self._collection_meta.vectors_schema) > 1:
                    raise DashVectorException(
                        code=DashVectorCode.InvalidArgument,
                        reason=f"DashVectorSDK multi-vector collection not support sparse vectors",
                    )

                metric = self._collection_meta.metric
                if metric != MetricStrType.DOTPRODUCT:
                    raise DashVectorException(
                        code=DashVectorCode.InvalidSparseValues,
                        reason=f"DashVectorSDK supports doc with sparse_vector only collection metric is dotproduct",
                    )
                for key, value in sparse_vector.items():
                    new_doc.sparse_vector[key] = value
            self._docs.append(DocBuilder.from_pb(new_doc, collection_meta=collection_meta).__dict__())

        super().__init__(request=upsert_request)

    def _parse_doc(self, doc: Optional[Doc] = None):
        if doc is not None:
            return doc.id, doc.vector, doc.sparse_vectors, doc.fields, doc.sparse_vector, doc.vectors

    def _parse_fields(self, fields):
        if isinstance(fields, dict) and all(isinstance(key, int) for key in fields.keys()):
            # return sparse_vector
            return None, fields
        elif isinstance(fields, dict):
            # return fields
            return fields, None
        return None, None

    def _parse_update_tuple(self, tup: Tuple, size: int):
        # size must in [1,3]
        # id is required when request is update
        id = tup[0]
        if size == 1:
            return id, (None,) * 3

        vector = tup[1] if isinstance(tup[1], (list, np.ndarray)) else None
        fields = sparse_vector = None
        if size == 2:
            if vector_is_empty(vector):
                fields, sparse_vector = self._parse_fields(tup[1])
        elif size == 3:
            if vector_is_empty(vector):
                fields, sparse_vector = tup[1], tup[2]
            else:
                fields, sparse_vector = self._parse_fields(tup[2])
        return id, vector, fields, sparse_vector

    def _parse_insert_or_upsert_tuple(self, tup: Tuple, size: int):
        # size must in [1,3]
        # vector is required when request in (insert, upsert)
        if size == 1:
            return None, tup[0], None, None

        id = tup[0] if isinstance(tup[0], str) else None
        vector_index = 1 if id else 0
        vector = tup[vector_index] if isinstance(tup[vector_index], (list, np.ndarray)) else None
        fields = sparse_vector = None
        if vector_is_empty(vector):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason="DashVectorSDK UpsertDocRequest vector is required and request is insert or update",
            )
        else:
            if size == 2:
                if not id:
                    fields, sparse_vector = self._parse_fields(tup[1])
            if size == 3:
                if not id:
                    fields, sparse_vector = tup[1], tup[2]
                else:
                    fields, sparse_vector = self._parse_fields(tup[2])
        return id, vector, fields, sparse_vector

    def _parse_tuple(self, tup: Tuple, action: str):
        size = len(tup)
        if size > 4 or size == 0:
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK UpsertDocRequest doc tuple length({len(tup)}) is invalid and must be in (0, 4]",
            )

        if size == 4:
            return tup
        if action in ("insert", "upsert"):
            return self._parse_insert_or_upsert_tuple(tup, size)
        elif action == "update":
            return self._parse_update_tuple(tup, size)
        return (None,) * 4

    def _format_params(
        self,
        id_list: List[str],
        vector_list: List[Optional[VectorValueType]],
        fields_list: Optional[List[FieldDataDict]] = None,
        sparse_vector_list: Optional[List[Dict[int, float]]] = None,
        vectors_list: Optional[List[Dict[str, VectorValueType]]] = None,
        sparse_vectors_list: Optional[List[Dict[str, SparseValueType]]] = None,
        action: Optional[str] = None,
    ):
        batch_size = len(id_list)

        # check doc_id
        for id in id_list:
            if id:
                if not isinstance(id, str):
                    raise DashVectorException(
                        code=DashVectorCode.InvalidArgument,
                        reason=f"DashVectorSDK UpsertDocRequest id type({type(id)}) invalid and must be str",
                    )
                if re.search(DOC_ID_PATTERN, id) is None:
                    raise DashVectorException(
                        code=DashVectorCode.InvalidPrimaryKey,
                        reason=f"DashVectorSDK UpsertDocRequest id characters({id}) is invalid and "
                        + DOC_ID_PATTERN_MSG,
                    )
            else:
                if action == "update":
                    raise DashVectorException(
                        code=DashVectorCode.InvalidPrimaryKey,
                        reason=f"DashVectorSDK UpsertDocRequest id({id}) is required when the action is update",
                    )

        # check vector
        if batch_size != len(vector_list):
            raise DashVectorException(
                code=DashVectorCode.InvalidBatchSize,
                reason=f"DashVectorSDK UpsertDocRequest batch size({batch_size}) is different between id and vector",
            )

        # check vectors
        if batch_size != len(vectors_list):
            raise DashVectorException(
                code=DashVectorCode.InvalidBatchSize,
                reason=f"DashVectorSDK UpsertDocRequest batch size({batch_size}) is different between id and vectors",
            )

        # check sparse_vector
        if batch_size != len(sparse_vector_list):
            raise DashVectorException(
                code=DashVectorCode.InvalidBatchSize,
                reason=f"DashVectorSDK UpsertDocRequest batch size({batch_size}) is different between id and sparse_vector",
            )

        # check sparse_vectors
        if batch_size != len(sparse_vectors_list):
            raise DashVectorException(
                code=DashVectorCode.InvalidBatchSize,
                reason=f"DashVectorSDK UpsertDocRequest batch size({batch_size}) is different between id and sparse_vectors",
            )

        for vector_idx in range(batch_size):
            vector_list[vector_idx] = self._vector_to_pb(vector_list[vector_idx])
            if vectors_list[vector_idx] is not None:
                for key, value in vectors_list[vector_idx].items():
                    vectors_list[vector_idx][key] = self._vector_to_pb(value, key)
            if action != "update" and (vector_list[vector_idx] is None and vectors_list[vector_idx] is None and sparse_vectors_list[vector_idx] is None):
                raise DashVectorException(
                    code=DashVectorCode.InvalidVectorFormat,
                    reason=f"DashVectorSDK UpsertDocRequest vector is required and must be in [list, numpy.ndarray] when request in [insert, upsert]",
                )

        # check fields
        if batch_size != len(fields_list):
            raise DashVectorException(
                code=DashVectorCode.InvalidBatchSize,
                reason=f"DashVectorSDK UpsertDocRequest batch size({batch_size}) is different between id and fields",
            )
        for fields_one in fields_list:
            if fields_one is None:
                continue

            if not isinstance(fields_one, dict):
                raise DashVectorException(
                    code=DashVectorCode.InvalidField,
                    reason=f"DashVectorSDK UpsertDocRequest fields type({type(fields_one)}) is invalid",
                )

            if len(fields_one) > 1024:
                raise DashVectorException(
                    code=DashVectorCode.InvalidField,
                    reason=f"DashVectorSDK UpsertDocRequest fields length({len(fields_one)}) is invalid and must be in [1, 1024]",
                )

        sort_sparse_lists = [to_sorted_sparse_vector(sparse_vector) for sparse_vector in sparse_vector_list]

        sort_sparses_lists = [to_sorted_sparse_vectors(sparse_vectors) for sparse_vectors in sparse_vectors_list]

        return id_list, vector_list, fields_list, sort_sparse_lists, vectors_list, sort_sparses_lists

    def _vector_to_pb(self, vector: VectorValueType, vector_name: Optional[str] = None):
        if vector is None:
            return vector
        if not vector_name:
            dimension = self._collection_meta.dimension
            dtype = VectorType.get(self._collection_meta.dtype)
        else:
            dimension = self._collection_meta.get_dimension(vector_name)
            dtype = VectorType.get(self._collection_meta.get_dtype(vector_name))
        if isinstance(vector, list):
            if len(vector) != dimension:
                raise DashVectorException(
                    code=DashVectorCode.MismatchedDimension,
                    reason=f"DashVectorSDK UpsertDocRequest vector length({len(vector)}) is invalid and must be same with collection dimension({dimension})",
                )
            vector_data_type = VectorType.get_vector_data_type(type(vector[0]))
            if vector_data_type != dtype:
                raise DashVectorException(
                    code=DashVectorCode.MismatchedDataType,
                    reason=f"DashVectorSDK UpsertDocRequest vector type({type(vector[0])}) is invalid and must be {VectorType.get_python_type(dtype)}",
                )
            if VectorType.INT == dtype:
                try:
                    return VectorType.convert_to_bytes(vector, dtype, dimension)
                except Exception as e:
                    raise DashVectorException(
                        code=DashVectorCode.InvalidVectorFormat,
                        reason=f"DashVectorSDK UpsertDocRequest vector value({vector}) is invalid and int value must be in [-128,127]",
                    )
        elif isinstance(vector, np.ndarray):
            if vector.ndim != 1:
                raise DashVectorException(
                    code=DashVectorCode.InvalidArgument,
                    reason=f"DashVectorSDK UpsertDocRequest vector numpy dimension({vector.ndim}) is invalid and must be 1",
                )
            if vector.shape[0] != dimension:
                raise DashVectorException(
                    code=DashVectorCode.MismatchedDimension,
                    reason=f"DashVectorSDK UpsertDocRequest vector numpy shape[0]({vector.shape[0]}) is invalid and must be same with collection dimension({dimension})",
                )
            try:
                if VectorType.INT == dtype:
                    data_format_type = VectorType.get_vector_data_format(dtype)
                    return np.ascontiguousarray(vector, dtype=f"<{data_format_type}").tobytes()
                else:
                    return vector
            except Exception as e:
                raise DashVectorException(
                    code=DashVectorCode.InvalidVectorFormat,
                    reason=f"DashVectorSDK UpsertDocRequest vector value({vector}) is invalid",
                )
        else:
            if bool(vector):
                raise DashVectorException(
                    code=DashVectorCode.InvalidVectorFormat,
                    reason=f"DashVectorSDK UpsertDocRequest vector type({type(vector)}) is invalid and must be in [List, numpy.ndarray]",
                )
        return vector

    @property
    def collection_name(self):
        return self._collection_name

    def to_json(self):
        data = {"partition": self._partition, "docs": self._docs}
        return json.dumps(data)

