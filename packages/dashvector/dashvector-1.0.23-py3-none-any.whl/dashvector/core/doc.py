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

from dataclasses import dataclass, field
from typing import Optional

from dashvector.common.types import *
from dashvector.core.models.collection_meta_status import CollectionMeta
from dashvector.core.proto import dashvector_pb2

__all__ = ["DocBuilder", "Doc", "DocOpResult"]


@dataclass(frozen=True)
class Doc(object):
    """
    A Doc Instance.

    Args:
        id (str): a primary key for a unique doc.
        vector (Union[List[Union[int, float]]): a vector for a doc.
        sparse_vector(Dict[int, float]): sparse vector for hybrid serarch
        vectors (Optional[Dict[str, VectorValueType]: multi vectors for a doc
        sparse_vectors (Optional[Dict[str, SparseValueType]: sparse multi vectors for a doc
        fields (Optional[Dict[str, Union[str, int, float, bool, long, List[long], List[str], List[int], List[float]]]]): additional attributes of a doc. [optional]
        score (float): a correlation score when use doc query api, default is 0.0.

    Examples
        a_doc_with_float = Doc(id="a", vector=[0.1, 0.2])
        a_doc_with_int = Doc(id="a", vector=[1, 2])
        a_doc_with_fields = Doc(id="a", vector=[0.1, 0.2], fields={'price': 100, 'type': "dress"})
        a_doc_with_multi_vecs = Doc(id="a", vectors={'vec1': [0.1, 0.2], 'vec2': [0.3, 0.4]})
        a_doc_with_sparse_multi_vecs = Doc(id="a", vectors={'vec1': {1: 0.1, 3: 0.2, 5: 0.3, 7: 0.4}})
    """

    id: Optional[str] = None
    vector: Optional[VectorValueType] = None
    vectors: Optional[Dict[str, VectorValueType]] = None
    sparse_vectors: Optional[Dict[str, SparseValueType]] = None
    sparse_vector: Optional[Dict[int, float]] = None
    fields: Optional[FieldDataDict] = None
    score: float = 0.0

    def __dict__(self):
        meta_dict = {}
        if self.id is not None:
            meta_dict["id"] = self.id
        if self.vector is not None:
            if isinstance(self.vector, np.ndarray):
                meta_dict["vector"] = self.vector.astype(np.float32).tolist()
            elif isinstance(self.vector, list):
                meta_dict["vector"] = self.vector
        if self.vectors is not None:
            d = {}
            for k, v in self.vectors.items():
                if isinstance(v, np.ndarray):
                    d[k] = v.astype(np.float32).tolist()
                elif isinstance(v, list):
                    d[k] = v
            meta_dict["vectors"] = d
        if self.sparse_vectors is not None:
            meta_dict["sparse_vectors"] = self.sparse_vectors
        if self.sparse_vector is not None:
            meta_dict["sparse_vector"] = self.sparse_vector
        if self.fields is not None:
            meta_dict["fields"] = self.fields
        if self.score is not None:
            meta_dict["score"] = self.score
        return meta_dict

    def __str__(self):
        return to_json_without_ascii(self.__dict__())

    def __repr__(self):
        return self.__str__()


@dataclass(frozen=True)
class DocOpResult(object):
    doc_op: DocOp
    id: str
    code: int
    message: str

    def __dict__(self):
        return {"doc_op": self.doc_op.name, "id": self.id, "code": self.code, "message": self.message}

    def __str__(self):
        return json.dumps(self.__dict__())

    def __repr__(self):
        return self.__str__()

def _parse_vector(vector: dashvector_pb2.Vector, vector_type:IntEnum, dimension:int):
    vtype = vector.WhichOneof("value_oneof")
    if vtype == "byte_vector":
        vector = list(VectorType.convert_to_dtype(vector.byte_vector, vector_type, dimension))
        if bool(vector):
            if isinstance(vector[0], bytes) and vector_type == VectorType.INT:
                vector = [int(v) for v in vector]
            if isinstance(vector[0], bytes) and vector_type == VectorType.FLOAT:
                vector = [float(v) for v in vector]
    else:
        vector = list(vector.float_vector.values)
    return vector

def _parse_vector_http(vector: Optional[list], vector_type:IntEnum, dimension:int):
    if vector is None:
        return None
    if not isinstance(vector, list):
        raise DashVectorException(
            code=DashVectorCode.InvalidArgument,
            reason="DashVectorSDK get invalid doc vector and type must be list",
        )
    if len(vector) != dimension:
        raise DashVectorException(
            code=DashVectorCode.MismatchedDimension,
            reason="DashVectorSDK get invalid doc vector and length is different from dimension",
        )
    vtype = VectorType.get_vector_data_type(type(vector[0]))
    if vtype != vector_type:
        raise DashVectorException(
            code=DashVectorCode.MismatchedDataType,
            reason=f"DashVectorSDK get invalid doc vector type and must be same with {vector_type}",
        )
    return vector

def _parse_field_value(field_value: dashvector_pb2.FieldValue) -> Optional[FieldDataType]:
    field_type: str = field_value.WhichOneof("value_oneof")
    if field_type is None:
        return None
    actual_value = getattr(field_value, field_type)
    # no need to convert to long, for long is int actually
    # mapper = (lambda x: x) if not field_type.startswith("long") else (lambda x: long(x))
    if field_type.endswith("_array"):
        return list(actual_value.values)
    else:
        return actual_value

class DocBuilder(object):
    @staticmethod
    def from_pb(doc: dashvector_pb2.Doc, collection_meta: CollectionMeta):
        if not isinstance(doc, dashvector_pb2.Doc):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason="DashVectorSDK get invalid doc and type must be dashvector_pb2.Doc",
            )
        if not isinstance(collection_meta, CollectionMeta):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason="DashVectorSDK get invalid collection_meta and type must be CollectionMeta",
            )

        id = doc.id
        score = round(doc.score, 4)

        # vectors
        vectors = None
        sparse_vectors = None
        vector = None
        if len(doc.vectors) + len(doc.sparse_vectors) > 0:
            vectors = {}
            sparse_vectors = {}
            for vector_name, vector_value in doc.vectors.items():
                vector_type = VectorType.get(collection_meta.get_dtype(vector_name))
                dimension = collection_meta.get_dimension(vector_name)
                vectors[vector_name] = _parse_vector(vector_value, vector_type, dimension)
            for vector_name, vector_value in doc.sparse_vectors.items():
                sparse_vectors[vector_name] = dict(vector_value.sparse_vector)
        elif doc.HasField("vector"):
            vector_type = VectorType.get(collection_meta.dtype)
            dimension = collection_meta.dimension
            vector = _parse_vector(doc.vector, vector_type, dimension)

        # sparse_vector
        sparse_vector = None
        if bool(doc.sparse_vector):
            sparse_vector = dict(doc.sparse_vector)

        # fields
        fields: FieldDataDict = {}
        if bool(doc.fields):
            for field_name, field_value in doc.fields.items():
                fields[field_name] = _parse_field_value(field_value)

        return Doc(id=id, vector=vector, vectors=vectors, sparse_vectors=sparse_vectors, sparse_vector=sparse_vector, score=score, fields=fields)

    @staticmethod
    def from_dict(doc: dict, collection_meta: Optional[CollectionMeta] = None):
        if not isinstance(doc, dict):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument, reason="DashVectorSDK get invalid doc and type must be dict"
            )
        if not isinstance(collection_meta, CollectionMeta):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason="DashVectorSDK get invalid collection_meta and type must be CollectionMeta",
            )

        """
        id: str
        """
        id = doc.get("id")
        if not isinstance(id, str):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument, reason="DashVectorSDK get invalid id and type must be str"
            )
        """
        vectors: dict[str, VectorValueType]
        """
        vectors = doc.get("vectors")
        if vectors:
            if not isinstance(vectors, dict):
                raise DashVectorException(
                    code=DashVectorCode.InvalidArgument,
                    reason="DashVectorSDK get invalid doc vectors and type must be dict",
                )
            for vector_name, vector_value in vectors.items():
                vector_type = VectorType.get(collection_meta.get_dtype(vector_name))
                dimension = collection_meta.get_dimension(vector_name)
                vectors[vector_name] = _parse_vector_http(vector_value, vector_type, dimension)
        else:
            vectors = None

        sparse_vectors = doc.get("sparse_vectors")
        if sparse_vectors:
            if not isinstance(sparse_vectors, dict):
                raise DashVectorException(
                    code=DashVectorCode.InvalidArgument,
                    reason="DashVectorSDK get invalid doc vectors and type must be dict",
                )
            for vector_name, vector_value in sparse_vectors.items():
                sparse_vectors[vector_name] = dict(sorted(vector_value.items()))
        else:
            sparse_vectors = None


        """
        vector: VectorValueType
        """
        vector = doc.get("vector")
        if vectors is not None and len(vectors) == 1 and sparse_vectors is not None and len(sparse_vectors) == 0:
            # multi-vector collection may return one vector, it's impossible to known its name from single `vector` field
            vector = next(iter(vectors.values()))
        elif "vector" in doc:
            vector_type = VectorType.get(collection_meta.dtype)
            dimension = collection_meta.dimension
            vector = _parse_vector_http(vector, vector_type, dimension)
        else:
            vector = None

        """
        fields: FieldSchemaDict
        """
        fields = doc.get("fields")

        """
        score: float
        """
        if "score" in doc:
            score = round(float(doc["score"]), 4)

        """
        sparse_vector: Dict[int, float]
        """
        sparse_vector = None
        if "sparse_vector" in doc:
            sparse_map = doc.get("sparse_vector")
            if isinstance(sparse_map, dict):
                sparse_vector = dict(sorted(sparse_map.items()))
        return Doc(id=id, vector=vector, vectors=vectors, sparse_vectors=sparse_vectors, sparse_vector=sparse_vector, score=score, fields=fields)

