# -*- coding: utf-8 -*-

from typing import Any, Dict, List, Optional, Tuple, Type, Union, NewType
import re

import numpy as np

from dashvector.common.constants import *
from dashvector.common.types import *
from dashvector.common.error import DashVectorCode, DashVectorException
from dashvector.core.doc import Doc
from dashvector.core.models.collection_meta_status import CollectionMeta
from dashvector.util.convertor import to_sorted_sparse_vector, to_sorted_sparse_vectors
from dashvector.core.proto import dashvector_pb2

class Validator():

    @staticmethod
    def validate_dense_vector(vector, dimension: int, dtype: VectorDataType, doc_op: str):
        if isinstance(vector, list):
            if len(vector) != dimension:
                raise DashVectorException(
                    code=DashVectorCode.MismatchedDimension,
                    reason=f"DashVectorSDK {doc_op} vector list length({len(vector)}) is invalid and must be same with collection dimension({dimension})",
                )
            vector_data_type = VectorType.get_vector_data_type(type(vector[0]))
            if vector_data_type != dtype:
                raise DashVectorException(
                    code=DashVectorCode.MismatchedDataType,
                    reason=f"DashVectorSDK {doc_op} vector type({type(vector[0])}) is invalid and must be {VectorType.get_python_type(dtype)}",
                )
            if vector_data_type == VectorType.INT:
                try:
                    vector = VectorType.convert_to_bytes(vector, dtype, dimension)
                except Exception as e:
                    raise DashVectorException(
                        code=DashVectorCode.InvalidVectorFormat,
                        reason=f"DashVectorSDK {doc_op} vector value({vector}) is invalid and int value must be in [-128, 127]",
                    )
        elif isinstance(vector, np.ndarray):
            if vector.ndim != 1:
                raise DashVectorException(
                    code=DashVectorCode.InvalidArgument,
                    reason=f"DashVectorSDK {doc_op} vector numpy dimension({vector.ndim}) is invalid and must be 1",
                )
            if vector.shape[0] != dimension:
                raise DashVectorException(
                    code=DashVectorCode.MismatchedDimension,
                    reason=f"DashVectorSDK {doc_op} vector numpy shape[0]({vector.shape[0]}) is invalid and must be same with collection dimension({dimension})",
                )
        else:
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK {doc_op} vector type({type(vector)}) is invalid and must be [list, numpy.ndarray]",
            )
        return vector

    @staticmethod
    def validate_collection_name(name: str, doc_op: str):
        if not isinstance(name, str):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK {doc_op} name type({name}) is invalid and must be str",
            )

        if re.search(COLLECTION_AND_PARTITION_NAME_PATTERN, name) is None:
            raise DashVectorException(
                code=DashVectorCode.InvalidCollectionName,
                reason=f"DashVectorSDK {doc_op} name characters({name}) is invalid and "
                + COLLECTION_AND_PARTITION_NAME_PATTERN_MSG,
            )
        return name
    
    @staticmethod
    def validate_partition_name(partition_name: str, doc_op: str):
        if not isinstance(partition_name, str):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK {doc_op} partition name type({partition_name}) is invalid and must be str",
            )

        if re.search(COLLECTION_AND_PARTITION_NAME_PATTERN, partition_name) is None:
            raise DashVectorException(
                code=DashVectorCode.InvalidPartitionName,
                reason=f"DashVectorSDK {doc_op} partition characters({partition_name}) is invalid and "
                + COLLECTION_AND_PARTITION_NAME_PATTERN_MSG,
            )
        return partition_name

    @staticmethod
    def validate_vector_name(vector_name: str, doc_op: str):
        if not isinstance(vector_name, str):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK {doc_op} vector_name type({type(vector_name)}) is invalid and must be str",
            )
        if re.search(FIELD_NAME_PATTERN, vector_name) is None:
            raise DashVectorException(
                code=DashVectorCode.InvalidFieldName,
                reason=f"DashVectorSDK {doc_op} vector_name characters({vector_name}) is invalid and "
                        + FIELD_NAME_PATTERN_MSG,
            )

    @staticmethod
    def validate_sparse_vectors(sparse_vectors: Union[None, VectorParam, Dict[str, VectorParam]], doc_op: str):
        if sparse_vectors is None:
            sparse_vectors = dict()
        if isinstance(sparse_vectors, dict):
            for vector_name in sparse_vectors.keys():
                Validator.validate_vector_name(vector_name, doc_op)
        if not isinstance(sparse_vectors, dict):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK {doc_op} sparse_vectors type({type(sparse_vectors)}) is invalid and must be dict"
            )
        for vector_name, vector_param in sparse_vectors.items():
            if not isinstance(vector_param, VectorParam):
                raise DashVectorException(
                    code=DashVectorCode.InvalidArgument,
                    reason=f"DashVectorSDK {doc_op} vector_param type({type(vector_param)}) is invalid and must be VectorParam",
                )
            vector_param.validate()
            if vector_param.dimension != 0:
                raise DashVectorException(
                    code=DashVectorCode.InvalidDimension,
                    reason=f"DashVectorSDK VectorParam dimension value({vector_param.dimension}) for sparse vector is invalid and must be 0",
                )
            if(len(vector_param.quantize_type) > 0):
                raise DashVectorException(
                    code=DashVectorCode.InvalidArgument,
                    reason=f"DashVectorSDK {doc_op} vector_name({vector_name}), quantize_type({vector_param.quantize_type}) for sparse vector is invalid and must be empty",
                )
        return sparse_vectors
    
    @staticmethod
    def validate_fields_schema(fields_schema: Optional[FieldSchemaDict], doc_op: str):
        returned_fields_schema = dict()
        if fields_schema is not None:
            if not isinstance(fields_schema, dict):
                raise DashVectorException(
                    code=DashVectorCode.InvalidArgument,
                    reason=f"DashVectorSDK {doc_op} fields_schema type({type(fields_schema)}) is invalid and must be dict",
                )

            if len(fields_schema) > 1024:
                raise DashVectorException(
                    code=DashVectorCode.InvalidField,
                    reason=f"DashVectorSDK {doc_op} fields_schema length({len(fields_schema)}) is invalid and must be in [0, 1024]",
                )
            

            for field_name, field_dtype in fields_schema.items():
                if not isinstance(field_name, str):
                    raise DashVectorException(
                        code=DashVectorCode.InvalidArgument,
                        reason=f"DashVectorSDK {doc_op} field_name in fields_schema type({type(field_name)}) is invalid and must be str",
                    )

                if re.search(FIELD_NAME_PATTERN, field_name) is None:
                    raise DashVectorException(
                        code=DashVectorCode.InvalidFieldName,
                        reason=f"DashVectorSDK {doc_op} field_name in fields_schema characters({field_name}) is invalid and "
                        + FIELD_NAME_PATTERN_MSG,
                    )

                if field_name == DASHVECTOR_VECTOR_NAME:
                    raise DashVectorException(
                        code=DashVectorCode.InvalidFieldName,
                        reason=f"DashVectorSDK {doc_op} field_name in fields_schema value({DASHVECTOR_VECTOR_NAME}) is reserved",
                    )

                ftype = FieldType.get_field_data_type(field_dtype)
                returned_fields_schema[field_name] = ftype
        return returned_fields_schema

    @staticmethod
    def validate_extra_params(extra_params: Optional[Dict[str, Any]], doc_op: str):
        returned_extra_params = dict()
        if extra_params is not None:
            if not isinstance(extra_params, dict):
                raise DashVectorException(
                    code=DashVectorCode.InvalidArgument,
                    reason=f"DashVectorSDK {doc_op} extra_params type({type(extra_params)}) is invalid and must be dict",
                )

            extra_params_is_empty = True
            for extra_param_key, extra_param_value in extra_params.items():
                extra_params_is_empty = False

                if not isinstance(extra_param_key, str) or not isinstance(extra_param_value, str):
                    raise DashVectorException(
                        code=DashVectorCode.InvalidArgument,
                        reason=f"DashVectorSDK {doc_op} extra_param key/value type is invalid and must be str.",
                    )

                if len(extra_param_key) <= 0:
                    raise DashVectorException(
                        code=DashVectorCode.InvalidExtraParam,
                        reason=f"DashVectorSDK {doc_op} extra_param key is empty",
                    )

            if not extra_params_is_empty:
                returned_extra_params = extra_params
        return returned_extra_params
    
    @staticmethod
    def validate_doc_ids(ids: IdsType, doc_op: str):
        returned_ids = list()
        returned_ids_is_single = False
        if isinstance(ids, list):
            if len(ids) < 1 or len(ids) > 1024:
                raise DashVectorException(
                    code=DashVectorCode.ExceedIdsLimit,
                    reason=f"DashVectorSDK {doc_op} ids list length({len(ids)}) is invalid and must be in [1, 1024]",
                )
            for id in ids:
                if isinstance(id, str):
                    if re.search(DOC_ID_PATTERN, id) is None:
                        raise DashVectorException(
                            code=DashVectorCode.InvalidPrimaryKey,
                            reason=f"DashVectorSDK {doc_op} id in ids list characters({id}) is invalid and "
                            + DOC_ID_PATTERN_MSG,
                        )
                    returned_ids.append(id)
                else:
                    raise DashVectorException(
                        code=DashVectorCode.InvalidArgument,
                        reason=f"DashVectorSDK {doc_op} id in ids list type({type(id)}) is invalid and must be str",
                    )

        elif isinstance(ids, str):
            if re.search(DOC_ID_PATTERN, ids) is None:
                raise DashVectorException(
                    code=DashVectorCode.InvalidPrimaryKey,
                    reason=f"DashVectorSDK {doc_op} ids str characters({ids}) is invalid and "
                    + DOC_ID_PATTERN_MSG,
                )

            returned_ids.append(ids)
            returned_ids_is_single = True
        else:
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK {doc_op} ids type({type(ids)}) is invalid and must be [str, List[str]]",
            )
        return returned_ids, returned_ids_is_single
    
    @staticmethod
    def validate_id(id: str, doc_op: str):
        if isinstance(id, str):
            if re.search(DOC_ID_PATTERN, id) is None:
                raise DashVectorException(
                    code=DashVectorCode.InvalidPrimaryKey,
                    reason=f"DashVectorSDK {doc_op} id str characters({id}) is invalid and "
                    + DOC_ID_PATTERN_MSG,
                )
        else:
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK {doc_op} expect id to be <str> but actual type is ({type(id)})",
            )
        return id
    
    @staticmethod
    def validate_output_fields(output_fields: Optional[List[str]], doc_op: str):
        returned_output_fields = list()
        if output_fields is not None:
            if isinstance(output_fields, list):
                for output_field in output_fields:
                    if not isinstance(output_field, str):
                        raise DashVectorException(
                            code=DashVectorCode.InvalidArgument,
                            reason=f"DashVectorSDK {doc_op} output_field in output_fields type({type(output_field)}) is invalid and must be list[str]",
                        )

                    if re.search(FIELD_NAME_PATTERN, output_field) is None:
                        raise DashVectorException(
                            code=DashVectorCode.InvalidField,
                            reason=f"DashVectorSDK {doc_op} output_field in output_fields characters({output_field}) is invalid and "
                            + FIELD_NAME_PATTERN_MSG,
                        )

                returned_output_fields = output_fields
            else:
                raise DashVectorException(
                    code=DashVectorCode.InvalidArgument,
                    reason=f"DashVectorSDK {doc_op} output_fields type({type(output_fields)}) is invalid and must be List[str]",
                )
        return returned_output_fields
    
    @staticmethod
    def validate_rerank(rerank: BaseRanker, query_request: dashvector_pb2.QueryDocRequest, doc_op: str):
        if isinstance(rerank, WeightedRanker):
            weight_keys = sorted(rerank.weights.keys())
            query_vectors_keys = sorted(sorted(query_request.vectors.keys()) + sorted(query_request.sparse_vectors.keys()))

            if weight_keys is not None and len(weight_keys) > 0 and weight_keys != query_vectors_keys:
                raise DashVectorException(
                    code=DashVectorCode.InvalidArgument,
                    reason=f"DashVectorSDK {doc_op} expect WeightedRanker.weights({rerank.weights}) to exactly match all vector names({query_vectors_keys})"
                )
        elif isinstance(rerank, RrfRanker):
            rank_constant = rerank.rank_constant
            if not isinstance(rank_constant, int) or rank_constant < 0 or rank_constant >= 2**31:
                raise DashVectorException(
                    code=DashVectorCode.InvalidArgument,
                    reason=f"DashVectorSDK {doc_op} expect RrfRanker.rank_constant({rank_constant}) to be positive int32"
                )
        else:
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK {doc_op} expect rerank type to be WeightedRanker or RrfRanker, actual type({type(rerank)})"
            )
        return rerank
        
    @staticmethod
    def validate_include_vector(include_vector: bool, doc_op: str):
        if not isinstance(include_vector, bool):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK {doc_op} include_vector type({type(include_vector)}) is invalid and must be bool",
            )
        return include_vector
    
    @staticmethod
    def validate_topk(topk: int, include_vector: bool, doc_op: str):
        include_vector = Validator.validate_include_vector(include_vector, doc_op)
        if not isinstance(topk, int):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK {doc_op} topk type({type(topk)}) is invalid and must be int",
            )
        if topk < 1 or (include_vector and topk > 1024):
            raise DashVectorException(
                code=DashVectorCode.InvalidTopk,
                reason=f"DashVectorSDK {doc_op} topk value({topk}) is invalid and must be in [1, 1024] "
                       f"when include_vector is True",
            )
        return topk
    
    @staticmethod
    def validate_filter(filter: str, doc_op: str):
        if filter is not None:
            if not isinstance(filter, str):
                raise DashVectorException(
                    code=DashVectorCode.InvalidArgument,
                    reason=f"DashVectorSDK {doc_op} filter type({type(filter)}) is invalid and must be str",
                )

            if len(filter) > 40960:
                raise DashVectorException(
                    code=DashVectorCode.InvalidFilter,
                    reason=f"DashVectorSDK {doc_op} filter length({len(filter)}) is invalid and must be in [0, 40960]",
                )
            if len(filter) > 0:
                return filter
            else:
                return None
        else:
            return None
    
    @staticmethod
    def validate_doc(doc: Doc, meta: CollectionMeta, action: str, doc_op: str):
        if doc.id is not None:
            if not isinstance(doc.id, str):
                raise DashVectorException(
                    code=DashVectorCode.InvalidArgument,
                    reason=f"DashVectorSDK {doc_op} id type({type(doc.id)}) is invalid and must be str",
                )
            if re.search(DOC_ID_PATTERN, doc.id) is None:
                raise DashVectorException(
                    code=DashVectorCode.InvalidPrimaryKey,
                    reason=f"DashVectorSDK {doc_op} id characters({doc.id}) is invalid and "
                    + DOC_ID_PATTERN_MSG,
                )
        else:
            if action == "update":
                raise DashVectorException(
                    code=DashVectorCode.InvalidPrimaryKey,
                    reason=f"DashVectorSDK {doc_op} id({doc.id}) is required when the action is update",
                )
        returned_id = doc.id
        returned_vector = None
        if doc.vector is not None:
            returned_vector = Validator.validate_dense_vector(doc.vector, meta.get_dimension(), VectorType.get(meta.get_dtype()), doc_op)
        returned_vectors = dict()
        if doc.vectors is not None:
            for key, value in doc.vectors.items():
                returned_vectors[key] = Validator.validate_dense_vector(value, meta.get_dimension(vector_name=key), VectorType.get(meta.get_dtype(vector_name=key)), doc_op)
            if action != "update" and doc.vector is None and doc.vectors is None and doc.sparse_vectors is None:
                raise DashVectorException(
                    code=DashVectorCode.InvalidVectorFormat,
                    reason=f"DashVectorSDK {doc_op} vector is required and must be in [list, numpy.ndarray] when request in [insert, upsert]",
                )

        # check fields
        if doc.fields is None:
            pass
        elif not isinstance(doc.fields, dict):
            raise DashVectorException(
                code=DashVectorCode.InvalidField,
                reason=f"DashVectorSDK {doc_op} fields type({type(doc.fields)}) is invalid",
            )
        elif len(doc.fields) > 1024:
            raise DashVectorException(
                code=DashVectorCode.InvalidField,
                reason=f"DashVectorSDK {doc_op} fields length({len(doc.fields)}) is invalid and must be in [1, 1024]",
            )

        returned_sparse_vector = to_sorted_sparse_vector(doc.sparse_vector)

        returned_sparse_vectors = to_sorted_sparse_vectors(doc.sparse_vectors)

        return Doc(id=returned_id, vector=returned_vector, vectors=returned_vectors, fields=doc.fields, sparse_vector=returned_sparse_vector, sparse_vectors=returned_sparse_vectors)
