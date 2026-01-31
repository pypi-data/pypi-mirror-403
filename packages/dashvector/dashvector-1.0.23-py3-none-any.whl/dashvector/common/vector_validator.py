# -*- coding: utf-8 -*-

from dashvector.common.common_validator import *
from dashvector.common.types import *
from dashvector.common.error import DashVectorCode, DashVectorException
from dashvector.core.models.collection_meta_status import CollectionMeta
from dashvector.util.convertor import to_sorted_sparse_vector
from dashvector.core.proto import dashvector_pb2
from abc import abstractmethod, ABC

def convert_vector_query(vector_query, type: VectorType):
    returned_vector_query = dashvector_pb2.VectorQuery()
    if isinstance(vector_query.vector, list):
        returned_vector_query.vector.float_vector.values.extend(vector_query.vector)
    elif isinstance(vector_query.vector, bytes):
        returned_vector_query.vector.byte_vector = vector_query.vector
    elif isinstance(vector_query.vector, np.ndarray):
        if type == VectorType.INT:
            data_format_type = VectorType.get_vector_data_format(type)
            vector_query.vector = np.ascontiguousarray(vector_query.vector, dtype=f"<{data_format_type}").tobytes()
            returned_vector_query.vector.byte_vector = vector_query.vector
        else:
            vector_query.vector = list(vector_query.vector)
            returned_vector_query.vector.float_vector.values.extend(vector_query.vector)
    returned_vector_query.param.is_linear = vector_query.is_linear
    returned_vector_query.param.ef = vector_query.ef
    returned_vector_query.param.radius = vector_query.radius
    returned_vector_query.param.num_candidates = vector_query.num_candidates
    return returned_vector_query

def convert_vector_query_from_pb(vector_query: dashvector_pb2.VectorQuery):
    if vector_query.vector.HasField("float_vector"):
        vector = np.array(vector_query.vector.float_vector.values)
        returned_vector_query = VectorQuery(vector=vector)
        return returned_vector_query
    elif vector_query.vector.HasField("byte_vector"):
        data_format_type = "b"
        vector = np.frombuffer(vector_query.vector.byte_vector, dtype=f"<{data_format_type}")
        returned_vector_query = VectorQuery(vector=vector.tolist())
        return returned_vector_query
    else:
        raise DashVectorException(
            code=DashVectorCode.InvalidArgument,
            reason=f"DashVectorSDK vector_query.vector type is invalid.")

class BasicVectorValidator(ABC):
    def __init__(self, collection_meta: CollectionMeta):
        self._collection_meta = collection_meta

    @abstractmethod
    def validate_collection_vectors(
            self,
            vectors: Union[None, VectorParam, Dict[str, VectorParam]],
            sparse_vectors: Union[None, VectorParam, Dict[str, VectorParam]],
            *,
            dimension: int = 0,
            dtype: VectorDataType = None,
            metric: str = "cosine",
            doc_op: str):
        pass

    @abstractmethod
    def validate_query_vectors(self, vector, top_k: int, query_request, doc_op: str):
        pass

class ReserveVectorValidator(BasicVectorValidator):

    def __init__(self, collection_meta: CollectionMeta, vector_name: str = DASHVECTOR_VECTOR_NAME):
        if collection_meta is not None:
            super().__init__(collection_meta)
            if(vector_name != DASHVECTOR_VECTOR_NAME):
                self._dimension = self._collection_meta.get_dimension(vector_name)
                self._dtype = VectorType.get(self._collection_meta.get_dtype(vector_name))
            else:
                self._dimension = self._collection_meta.dimension
                self._dtype = VectorType.get(self._collection_meta.dtype)

    def validate_collection_vectors(
            self,
            vectors: Union[None, VectorParam, Dict[str, VectorParam]],
            sparse_vectors: Union[None, VectorParam, Dict[str, VectorParam]],
            *,
            dimension: int = 0,
            dtype: VectorDataType = None,
            metric: str = "cosine",
            doc_op: str):
        if sparse_vectors is not None:
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK {doc_op} single vector sparse_vectors type({type(sparse_vectors)}) is invalid and must be None",
            )
        if vectors is None:
            vectors = {"": VectorParam(dimension=dimension, dtype=dtype, metric=metric)}
        elif isinstance(vectors, VectorParam):
            vectors = {"": vectors}
                
        if not isinstance(vectors, dict):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK {doc_op} vectors type({type(vectors)}) is invalid and must be dict"
            )
        vectors[""].validate()
        if vectors[""].dimension <= 1 or vectors[""].dimension > 20000:
            raise DashVectorException(
                code=DashVectorCode.InvalidDimension,
                reason=f"DashVectorSDK VectorParam dimension value({vectors[''].dimension}) is invalid and must be in (1, 20000]",
            )
        return vectors, dict()

    def validate_query_vectors(self, vector, top_k: int, query_request, doc_op: str):
        if isinstance(vector, VectorQuery):
            vector.validate()
        elif isinstance(vector, list) or isinstance(vector, np.ndarray):
            vector = VectorQuery(vector=vector, num_candidates=top_k)
            vector.validate()
        else:
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK {doc_op} single vector type({type(vector)}) is invalid and must be [VectorQuery, VectorValueType]",
            )
        vector.vector = Validator.validate_dense_vector(vector.vector, self._dimension, self._dtype, doc_op)
        converted_vector_query = convert_vector_query(vector, self._dtype)
        returned_query_request = query_request
        if isinstance(returned_query_request, dashvector_pb2.QueryDocRequest):
            returned_query_request.vectors[DASHVECTOR_VECTOR_NAME].CopyFrom(converted_vector_query)
        elif isinstance(returned_query_request, dashvector_pb2.QueryDocGroupByRequest):
            returned_query_request.vector.CopyFrom(converted_vector_query.vector)
        return returned_query_request

class MultiVectorValidator(BasicVectorValidator):

    def validate_collection_vectors(
            self,
            vectors: Union[None, VectorParam, Dict[str, VectorParam]],
            sparse_vectors: Union[None, VectorParam, Dict[str, VectorParam]],
            *,
            dimension: int = 0,
            dtype: VectorDataType = None,
            metric: str = "cosine",
            doc_op: str):
        if vectors is None and sparse_vectors is None:
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK {doc_op} vectors and sparse_vectors are all empty",
            )
        if vectors is None:
            vectors = dict()

        if isinstance(vectors, dict):
            for vector_name in vectors.keys():
                Validator.validate_vector_name(vector_name, doc_op)

        if not isinstance(vectors, dict):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK {doc_op} vectors type({type(vectors)}) is invalid and must be dict"
            )
        for vector_name, vector_param in vectors.items():
            if not isinstance(vector_param, VectorParam):
                raise DashVectorException(
                    code=DashVectorCode.InvalidArgument,
                    reason=f"DashVectorSDK {doc_op} vector_param type({type(vector_param)}) is invalid and must be VectorParam",
                )
            vector_param.validate()
            if vector_param.dimension <= 1 or vector_param.dimension > 20000:
                raise DashVectorException(
                    code=DashVectorCode.InvalidDimension,
                    reason=f"DashVectorSDK VectorParam dimension value({vector_param.dimension}) is invalid and must be in (1, 20000]",
                )
        sparse_vectors = Validator.validate_sparse_vectors(sparse_vectors, doc_op)
        if len(vectors) + len(sparse_vectors) > 4:
            raise DashVectorException(
                code=DashVectorCode.InvalidField,
                reason=f"DashVectorSDK {doc_op} vectors length({len(vectors) + len(sparse_vectors)}) is invalid and must be in [0, 4]",
            )
        return vectors, sparse_vectors

    def validate_query_vectors(self, vector, top_k: int, query_request, doc_op: str):
        vector_queries = None
        if isinstance(vector, dict):
            vector_queries = vector
        else:
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK {doc_op} multi vector type({type(vector)}) is invalid and must be dict",
            )

        returned_query_request = query_request
        for vector_name, vector_query in vector_queries.items():
            if isinstance(vector_query, list) or isinstance(vector_query, np.ndarray):
                vector_query = VectorQuery(vector=vector_query)
            vector_query.validate()
            vector_query.vector = Validator.validate_dense_vector(vector_query.vector, self._collection_meta.get_dimension(vector_name),
                                                           VectorType.get(self._collection_meta.get_dtype(vector_name)), doc_op)
            converted_vector_query = convert_vector_query(vector_query, VectorType.get(self._collection_meta.get_dtype(vector_name)))
            returned_query_request.vectors[vector_name].CopyFrom(converted_vector_query)

        return returned_query_request

class ValidatorFactory:
    @staticmethod
    def meta_create(collection_meta) -> BasicVectorValidator:
        if len(collection_meta.vectors_schema) == 1 and DASHVECTOR_VECTOR_NAME in collection_meta.vectors_schema.keys():
            return ReserveVectorValidator(collection_meta)
        else:
            return MultiVectorValidator(collection_meta)

    @staticmethod
    def input_type_create(vectors, sparse_vectors) -> BasicVectorValidator:
        if isinstance(vectors, dict) or isinstance(sparse_vectors, dict):
            return MultiVectorValidator(collection_meta=None)
        else:
            return ReserveVectorValidator(collection_meta=None)

class SparseVectorChecker:
    def __init__(self, collection_meta: CollectionMeta, vector_name: str, vector_query: SparseVectorQuery, doc_op: str):
        if not vector_name:
            self._dtype = VectorType.get(collection_meta.dtype)
            self._dimension = collection_meta.dimension
        else:
            self._dtype = VectorType.get(collection_meta.get_dtype(vector_name))
            self._dimension = collection_meta.get_dimension(vector_name)

        vector_query.validate()
        self._sparse_vector = vector_query
        self.vector_query = dashvector_pb2.SparseVectorQuery()
        for key, value in to_sorted_sparse_vector(self._sparse_vector.vector).items():
            self.vector_query.sparse_vector.sparse_vector[key] = value
        if len(self.vector_query.sparse_vector.sparse_vector) == 0:
            raise DashVectorException(
                code=DashVectorCode.InvalidSparseValues,
                reason=f"DashVectorSDK {doc_op} not supports query with empty sparse_vector",
            )

        param = self.vector_query.param
        param.num_candidates = vector_query.num_candidates
        param.ef = vector_query.ef
        param.is_linear = vector_query.is_linear
        param.radius = vector_query.radius
