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
import struct
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Tuple, Type, Union, NewType
import warnings

import numpy as np

from dashvector.common.error import DashVectorCode, DashVectorException
from dashvector.common.handler import RPCResponse
from dashvector.common.status import Status
from dashvector.util.convertor import to_json_without_ascii
from dashvector.core.proto import dashvector_pb2

long = NewType("long", int)

VectorDataType = Union[
    Type[int],
    Type[float],
    Type[bool],
    Type[np.int8],
    Type[np.int16],
    Type[np.float16],
    Type[np.bool_],
    Type[np.float32],
    Type[np.float64],
]
VectorValueType = Union[List[int], List[float], np.ndarray]
SparseValueType = Dict[int, float]

supported_type_msg = ("bool | str | int | float | long | "
                      "typing.List[str] | typing.List[int] | typing.List[float] | typing.List[long]")
# used to define schema
FieldSchemaType = Union[
    Type[long], Type[str], Type[bool], Type[int], Type[float],
    Type[List[long]], Type[List[str]], Type[List[int]], Type[List[float]]
]
# used to insert field data
FieldDataType = Union[long, str, int, float, bool, List[long], List[str], List[int], List[float]]

FieldSchemaDict = Dict[str, FieldSchemaType]
FieldDataDict = Dict[str, FieldDataType]
IdsType = Union[str, List[str]]


class DashVectorProtocol(IntEnum):
    GRPC = 0
    HTTP = 1


class DocOp(IntEnum):
    insert = 0
    update = 1
    upsert = 2
    delete = 3


class MetricStrType(str, Enum):
    EUCLIDEAN = "euclidean"
    DOTPRODUCT = "dotproduct"
    COSINE = "cosine"


class MetricType(IntEnum):
    EUCLIDEAN = 0
    DOTPRODUCT = 1
    COSINE = 2

    @staticmethod
    def get(mtype: Union[str, MetricStrType]) -> IntEnum:
        if mtype == MetricStrType.EUCLIDEAN:
            return MetricType.EUCLIDEAN
        elif mtype == MetricStrType.DOTPRODUCT:
            return MetricType.DOTPRODUCT
        elif mtype == MetricStrType.COSINE:
            return MetricType.COSINE
        else:
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK get invalid metrictype {mtype} and must be in [cosine, dotproduct, euclidean]",
            )

    @staticmethod
    def str(mtype: Union[int, IntEnum]) -> str:
        if mtype == MetricType.EUCLIDEAN:
            return MetricStrType.EUCLIDEAN.value
        elif mtype == MetricType.DOTPRODUCT:
            return MetricStrType.DOTPRODUCT.value
        elif mtype == MetricType.COSINE:
            return MetricStrType.COSINE.value
        raise DashVectorException(
            code=DashVectorCode.InvalidArgument,
            reason=f"DashVectorSDK get invalid metrictype {mtype} and must be in [cosine, dotproduct, euclidean]",
        )


class VectorStrType(str, Enum):
    FLOAT = "FLOAT"
    INT = "INT"


class VectorType(IntEnum):
    FLOAT = 0
    INT = 1

    @staticmethod
    def get(vtype: Union[str, VectorStrType]) -> 'VectorType':
        if vtype == VectorStrType.FLOAT:
            return VectorType.FLOAT
        elif vtype == VectorStrType.INT:
            return VectorType.INT
        else:
            raise DashVectorException(
                code=DashVectorCode.InvalidVectorType,
                reason=f"DashVectorSDK get invalid vectortype {vtype} and must be in [int, float]",
            )

    @staticmethod
    def str(vtype: Union[int, IntEnum]) -> str:
        if vtype == VectorType.FLOAT:
            return VectorStrType.FLOAT.value
        elif vtype == VectorType.INT:
            return VectorStrType.INT.value
        raise DashVectorException(
            code=DashVectorCode.InvalidVectorType,
            reason=f"DashVectorSDK get invalid vectortype {vtype} and must be in [int, float]]",
        )

    @staticmethod
    def get_vector_data_type(vtype: Type):
        if not isinstance(vtype, type):
            raise DashVectorException(
                code=DashVectorCode.InvalidVectorType,
                reason=f"DashVectorSDK does not support vector data type {vtype} and must be in [int, float]",
            )
        if vtype not in _vector_dtype_map:
            raise DashVectorException(
                code=DashVectorCode.InvalidVectorType,
                reason=f"DashVectorSDK does not support vector data type {vtype} and must be in [int, float]",
            )
        return _vector_dtype_map[vtype]

    @staticmethod
    def get_vector_data_format(data_type):
        if data_type not in (VectorType.INT, VectorType.FLOAT):
            raise DashVectorException(
                code=DashVectorCode.InvalidVectorType,
                reason=f"DashVectorSDK does not support vector({data_type}) to convert bytes",
            )
        return _vector_type_to_format[data_type]

    @staticmethod
    def convert_to_bytes(feature, data_type, dimension):
        if data_type not in (VectorType.INT, VectorType.FLOAT):
            raise DashVectorException(
                code=DashVectorCode.InvalidVectorType,
                reason=f"DashVectorSDK does not support auto pack feature type({data_type})",
            )
        return struct.pack(f"<{dimension}{_vector_type_to_format[data_type]}", *feature)

    @staticmethod
    def convert_to_dtype(feature, data_type, dimension):
        if data_type not in (VectorType.INT, VectorType.FLOAT):
            raise DashVectorException(
                code=DashVectorCode.InvalidVectorType,
                reason=f"DashVectorSDK does not support auto unpack feature type({data_type})",
            )
        return struct.unpack(f"<{dimension}{_vector_type_to_format[data_type]}", feature)

    @property
    def indices(self):
        return self._indices

    @property
    def values(self):
        return self._values

    def __dict__(self):
        return {"indices": self.indices, "values": self.values}

    def get_python_type(self):
        return _reverse_vector_dtype_map[self]


class FieldStrType(str, Enum):
    BOOL = "BOOL"
    STRING = "STRING"
    INT = "INT"
    FLOAT = "FLOAT"
    LONG = "LONG"

    ARRAY_STRING = "ARRAY_STRING"
    ARRAY_INT = "ARRAY_INT"
    ARRAY_FLOAT = "ARRAY_FLOAT"
    ARRAY_LONG = "ARRAY_LONG"

class FieldType(IntEnum):
    BOOL = 0
    STRING = 1
    INT = 2
    FLOAT = 3
    LONG = 4

    ARRAY_STRING = 11
    ARRAY_INT = 12
    ARRAY_FLOAT = 13
    ARRAY_LONG = 14

    @staticmethod
    def get(ftype: Union[str, FieldStrType]) -> IntEnum:
        if ftype == FieldStrType.BOOL:
            return FieldType.BOOL
        elif ftype == FieldStrType.STRING:
            return FieldType.STRING
        elif ftype == FieldStrType.INT:
            return FieldType.INT
        elif ftype == FieldStrType.FLOAT:
            return FieldType.FLOAT
        elif ftype == FieldStrType.LONG:
            return FieldType.LONG
        elif ftype == FieldStrType.ARRAY_STRING:
            return FieldType.ARRAY_STRING
        elif ftype == FieldStrType.ARRAY_INT:
            return FieldType.ARRAY_INT
        elif ftype == FieldStrType.ARRAY_FLOAT:
            return FieldType.ARRAY_FLOAT
        elif ftype == FieldStrType.ARRAY_LONG:
            return FieldType.ARRAY_LONG
        else:
            raise DashVectorException(
                code=DashVectorCode.InvalidField,
                reason=f"DashVectorSDK does not support field value type {ftype} and must be in {supported_type_msg}"
            )

    @staticmethod
    def str(ftype: Union[int, IntEnum]) -> str:
        if ftype == FieldType.BOOL:
            return FieldStrType.BOOL.value
        elif ftype == FieldType.STRING:
            return FieldStrType.STRING.value
        elif ftype == FieldType.INT:
            return FieldStrType.INT.value
        elif ftype == FieldType.FLOAT:
            return FieldStrType.FLOAT.value
        elif ftype == FieldType.LONG:
            return FieldStrType.LONG.value
        elif ftype == FieldType.ARRAY_STRING:
            return FieldStrType.ARRAY_STRING.value
        elif ftype == FieldType.ARRAY_INT:
            return FieldStrType.ARRAY_INT.value
        elif ftype == FieldType.ARRAY_FLOAT:
            return FieldStrType.ARRAY_FLOAT.value
        elif ftype == FieldType.ARRAY_LONG:
            return FieldStrType.ARRAY_LONG.value
        raise DashVectorException(
            code=DashVectorCode.InvalidField,
            reason=f"DashVectorSDK does not support field value type {ftype} and must be in {supported_type_msg}"
        )

    @staticmethod
    def get_field_data_type(dtype: FieldSchemaType):
        if dtype not in _attr_dtype_map:
            raise DashVectorException(
                code=DashVectorCode.InvalidField,
                reason=f"DashVectorSDK does not support field value type {dtype} and must be in {supported_type_msg}"
            )
        return _attr_dtype_map[dtype]

class IndexType(IntEnum):
    INVERT = 0
    NONE = 15

_vector_dtype_map = {
    float: VectorType.FLOAT,
    int: VectorType.INT,
}
_reverse_vector_dtype_map = {v: k for k,v in _vector_dtype_map.items()}

_vector_type_to_format = {
    VectorType.FLOAT: "f",
    VectorType.INT: "b",
}

_attr_dtype_map = {
    str: FieldType.STRING,
    bool: FieldType.BOOL,
    int: FieldType.INT,
    float: FieldType.FLOAT,
    long: FieldType.LONG,
    "long": FieldType.LONG,
    List[str]: FieldType.ARRAY_STRING,
    List[int]: FieldType.ARRAY_INT,
    List[float]: FieldType.ARRAY_FLOAT,
    List[long]: FieldType.ARRAY_LONG,
}


class DashVectorResponse(object):
    def __init__(self, response: Optional[RPCResponse] = None, *, exception: Optional[DashVectorException] = None):
        self._code = DashVectorCode.Unknown
        self._message = ""
        self._request_id = ""
        self._output = None
        self._usage = None

        self.__response = response
        self.__exception = exception

        if self.__response is None:
            self._code = DashVectorCode.Success

        if self.__response is not None and not self.__response.async_req:
            self.get()

        if self.__exception is not None:
            self._code = self.__exception.code
            self._message = self.__exception.message
            self._request_id = self.__exception.request_id

    def get(self):
        if self._code != DashVectorCode.Unknown:
            return self

        if self.__response is None:
            return self

        try:
            result = self.__response.get()
            self._request_id = result.request_id
            self._code = result.code
            self._message = result.message
            self._output = result.output
            self._usage = result.usage
        except DashVectorException as e:
            self._code = e.code
            self._message = e.message
            self._request_id = e.request_id

        return self

    @property
    def code(self):
        return self._code

    @property
    def message(self):
        return self._message

    @property
    def request_id(self):
        return self._request_id

    @property
    def output(self):
        return self._output

    @output.setter
    def output(self, value: Any):
        self._output = value

    @property
    def usage(self):
        return self._usage

    @property
    def response(self):
        return self.__response

    def _decorate_output(self):
        if self._output is None:
            return {"code": self.code, "message": self.message, "requests_id": self.request_id}
        elif isinstance(self._output, Status):
            return {
                "code": self.code,
                "message": self.message,
                "requests_id": self.request_id,
                "output": Status.str(self._output),
            }
        elif isinstance(self._output, (str, int, float)):
            return {
                "code": self.code,
                "message": self.message,
                "requests_id": self.request_id,
                "output": str(self._output),
            }
        elif isinstance(self._output, list):
            output_list = []
            for output_value in self._output:
                if isinstance(output_value, (str, int, float)):
                    output_list.append(str(output_value))
                elif hasattr(output_value, "__dict__"):
                    output_list.append(output_value.__dict__())
                elif hasattr(output_value, "__str__"):
                    output_list.append(output_value.__str__())
                else:
                    output_list.append(str(type(output_value)))
            return {"code": self.code, "message": self.message, "requests_id": self.request_id, "output": output_list}
        elif isinstance(self._output, dict):
            output_dict = {}
            for output_key, output_value in self._output.items():
                if isinstance(output_value, (str, int, float)):
                    output_dict[output_key] = str(output_value)
                elif hasattr(output_value, "__dict__"):
                    output_dict[output_key] = output_value.__dict__()
                elif hasattr(output_value, "__str__"):
                    output_dict[output_key] = output_value.__str__()
                else:
                    output_dict[output_key] = str(type(output_value))
            return {"code": self.code, "message": self.message, "requests_id": self.request_id, "output": output_dict}
        elif hasattr(self._output, "__dict__"):
            return {
                "code": self.code,
                "message": self.message,
                "requests_id": self.request_id,
                "output": self._output.__dict__(),
            }
        elif hasattr(self._output, "__str__"):
            return {
                "code": self.code,
                "message": self.message,
                "requests_id": self.request_id,
                "output": self._output.__str__(),
            }
        else:
            return {
                "code": self.code,
                "message": self.message,
                "requests_id": self.request_id,
                "output": str(type(self._output)),
            }

    def __dict__(self):
        obj = self._decorate_output()
        if self._usage is not None:
            obj["usage"] = self._usage.__dict__()
        return obj

    def __str__(self):
        return to_json_without_ascii(self.__dict__())

    def __repr__(self):
        return self.__str__()

    def __bool__(self):
        return self.code == DashVectorCode.Success

    def __len__(self):
        return len(self._output)

    def __iter__(self):
        return self._output.__iter__()

    def __contains__(self, item):
        if hasattr(self._output, "__contains__"):
            return self.output.__contains__(item)
        else:
            raise TypeError(f"DashVectorSDK Get argument of type '{type(self.output)}' is not iterable")

    def __getitem__(self, item):
        if hasattr(self._output, "__getitem__"):
            return self.output.__getitem__(item)
        else:
            raise TypeError(f"DashVectorSDK Get '{type(self.output)}' object is not subscriptable")


class RequestUsage(object):
    read_units: int
    write_units: int

    def __init__(self, *, read_units=None, write_units=None):
        self.read_units = read_units
        self.write_units = write_units

    @staticmethod
    def from_pb(usage: dashvector_pb2.RequestUsage):
        if usage.HasField("read_units"):
            return RequestUsage(read_units=usage.read_units)
        elif usage.HasField("write_units"):
            return RequestUsage(write_units=usage.write_units)

    @staticmethod
    def from_dict(usage: dict):
        if "read_units" in usage:
            return RequestUsage(read_units=usage["read_units"])
        elif "write_units" in usage:
            return RequestUsage(write_units=usage["write_units"])

    def __dict__(self):
        if self.read_units is None:
            if self.write_units is None:
                return {}
            else:
                return {"write_units": self.write_units}
        else:
            if self.write_units is None:
                return {"read_units": self.read_units}
            else:
                return {"read_units": self.read_units, "write_units": self.write_units}

    def __str__(self):
        return json.dumps(self.__dict__())

    def __repr__(self):
        return self.__str__()


class VectorParam:
    def __init__(self,
                dimension: int = 0,
                dtype: Union[Type[int], Type[float]] = float,
                metric: str = "cosine",
                quantize_type: str = "",
                ):
        """
        Vector param.

        Args:
            dimension (int): vector dimension in collection
            dtype (Union[Type[int], Type[float]]): vector data type in collection
            metric (str): vector metric in collection, support 'cosine', 'dotproduct' and 'euclidean', default to 'cosine'
            quantize_type (str): vector quantize type in collection, refer to https://help.aliyun.com/document_detail/2663745.html for latest support types
        """

        self._exception = None

        """
        dim: int
        """
        if not isinstance(dimension, int):
            self._exception = DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK VectorParam dimension type({type(dimension)}) is invalid and must be int",
            )
            return
        self.dimension = dimension

        """
        metric: MetricType
        """
        if not isinstance(metric, str):
            self._exception = DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK VectorParam metric Type({type(metric)}) is invalid and must be str",
            )
            return
        try:
            self._metric = MetricType.get(metric)
        except Exception as e:
            self._exception = e
            return

        """
        dtype: VectorType
        """
        if dtype is not float and metric == "cosine":
            self._exception = DashVectorException(
                code=DashVectorCode.MismatchedDataType,
                reason=f"DashVectorSDK VectorParam dtype value({dtype}) is invalid and must be [float] when metric is cosine",
            )
            return
        try:
            self._dtype = VectorType.get_vector_data_type(dtype)
        except Exception as e:
            self._exception = e
            return

        """
        quantize_type: str
        """
        if not isinstance(quantize_type, str):
            self._exception = DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK VectorParam quantize_type Type({type(quantize_type)}) is invalid and must be str",
            )
            return
        self.quantize_type = quantize_type

    def validate(self):
        if self._exception is not None:
            raise self._exception

    @staticmethod
    def from_pb(pb: dashvector_pb2.CollectionInfo.VectorParam):
        if pb.dtype == VectorType.FLOAT:
            dtype = float
        elif pb.dtype == VectorType.INT:
            dtype = int
        else:
            raise DashVectorException(f"DashVectorSDK VectorParam dtype value({pb.dtype}) is invalid")
        return VectorParam(
            dimension=pb.dimension,
            dtype=dtype,
            metric=MetricType.str(pb.metric),
            quantize_type=pb.quantize_type,
        )

    @staticmethod
    def from_dict(d: Dict[str, Any]):
        dimension = d.get("dimension")
        dtype = VectorType.get(d.get("dtype")).get_python_type()
        metric = MetricType.str(MetricType.get(d.get("metric")))
        quantize_type = d.get("quantize_type")
        return VectorParam(
            dimension=dimension,
            dtype=dtype,
            metric=metric,
            quantize_type=quantize_type
        )

    @property
    def metric(self):
        return MetricType.str(self._metric)

    @property
    def dtype(self):
        return VectorType.str(self._dtype)

    def to_dict(self):
        return {
            "dimension": self.dimension,
            "dtype": self.dtype,
            "metric": self.metric,
            'quantize_type': self.quantize_type
        }


class VectorQuery:
    def __init__(self,
                vector: VectorValueType,
                num_candidates: int = 0,
                is_linear: bool = False,
                ef: int = 0,
                radius: float = 0.0):
        """
        A vector query.

        vector (Optional[Union[List[Union[int, float, bool]], np.ndarray]]): query vector
        num_candidate (int): number of candidates for this vector query, default to collection.query.topk
        is_linear (bool): whether perform linear(brute-force) search, default to False
        ef (int): ef_search for HNSW-like algorithm, default to adaptive ef
        radius (float): perform radius nearest neighbor if radius is not 0.0,
                       i.e. return docs with score <= radius for euclidean/cosine and score >= radius for dotproduct
        """
        self.vector = vector
        self.num_candidates = num_candidates
        self.is_linear = is_linear
        self.ef = ef
        self.radius = radius

    def validate(self):
        num_candidates = self.num_candidates
        is_linear = self.is_linear
        ef = self.ef
        radius = self.radius
        if not isinstance(num_candidates, int):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK QueryDocRequest topk type({type(num_candidates)}) is invalid and must be int",
            )
        if num_candidates < 0 or num_candidates > 1024:
            raise DashVectorException(
                code=DashVectorCode.InvalidTopk,
                reason=f"DashVectorSDK GetDocRequest topk value({num_candidates}) is invalid and must be in [1, 1024]",
            )
        if not isinstance(is_linear, bool):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK QueryDocRequest ls_linear type({type(is_linear)}) is invalid and must be bool",
            )
        if not isinstance(ef, int):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK QueryDocRequest ef type({type(ef)}) is invalid and must be int",
            )
        if not (0 <= ef <= 4294967295):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK QueryDocRequest ef value({ef}) is invalid and must be in [0, 4294967295]",
            )
        if not isinstance(radius, float):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK QueryDocRequest radius type({type(radius)}) is invalid and must be float",
            )

class SparseVectorQuery:
    def __init__(self,
                sparse_vector: SparseValueType,
                num_candidates: int = 0,
                is_linear: bool = False,
                ef: int = 0,
                radius: float = 0.0):
        """
        A sparse_vector query.

        sparse_vector (Dict[int, float]): query sparse_vector
        num_candidate (int): number of candidates for this sparse_vector query, default to collection.query.topk
        is_linear (bool): whether perform linear(brute-force) search, default to False
        ef (int): ef_search for HNSW-like algorithm, default to adaptive ef
        radius (float): perform radius nearest neighbor if radius is not 0.0,
                       i.e. return docs with score <= radius for euclidean/cosine and score >= radius for dotproduct
        """
        self.vector = sparse_vector
        self.num_candidates = num_candidates
        self.is_linear = is_linear
        self.ef = ef
        self.radius = radius

    def validate(self):
        num_candidates = self.num_candidates
        is_linear = self.is_linear
        ef = self.ef
        radius = self.radius
        if not isinstance(num_candidates, int):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK QueryDocRequest topk type({type(num_candidates)}) is invalid and must be int",
            )
        if num_candidates < 0 or num_candidates > 1024:
            raise DashVectorException(
                code=DashVectorCode.InvalidTopk,
                reason=f"DashVectorSDK GetDocRequest topk value({num_candidates}) is invalid and must be in [1, 1024]",
            )
        if not isinstance(is_linear, bool):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK QueryDocRequest ls_linear type({type(is_linear)}) is invalid and must be bool",
            )
        if not isinstance(ef, int):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK QueryDocRequest ef type({type(ef)}) is invalid and must be int",
            )
        if not (0 <= ef <= 4294967295):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK QueryDocRequest ef value({ef}) is invalid and must be in [0, 4294967295]",
            )
        if not isinstance(radius, float):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason=f"DashVectorSDK QueryDocRequest radius type({type(radius)}) is invalid and must be float",
            )

class BaseRanker:
    pass

class RrfRanker(BaseRanker):
    def __init__(self, rank_constant: int = 60):
        self.rank_constant = rank_constant

    def to_pb(self):
        ranker = dashvector_pb2.Ranker()
        ranker.ranker_name = "rrf"
        ranker.ranker_params["rank_constant"] = str(self.rank_constant)
        return ranker

    def to_dict(self):
        return {
            'ranker_name': "rrf",
            'ranker_params': {
                'rank_constant': str(self.rank_constant)
            }
        }

class WeightedRanker(BaseRanker):
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights

    def to_pb(self):
        ranker = dashvector_pb2.Ranker()
        ranker.ranker_name = "weighted"
        if self.weights is not None:
            ranker.ranker_params["weights"] = json.dumps(self.weights)
        return ranker

    def to_dict(self):
        d = {
            'ranker_name': "weighted",
        }
        if self.weights is not None:
            d['ranker_params'] = {
                'weights': json.dumps(self.weights)
            }
        return d

class OrderByField:
    def __init__(self, field: str, desc: bool = False):
        if not isinstance(field, str):
            raise TypeError(f"DashVectorSDK OrderByField 'field' must be string type but got '{type(field)}'")
        if not isinstance(desc, bool):
            raise TypeError(f"DashVectorSDK OrderByField 'desc' must be bool type but got '{type(desc)}'")
        self._field: str = field
        self._desc: bool = desc

    @property
    def field(self) -> str:
        return self._field

    @property
    def desc(self) -> bool:
        return self._desc

    def to_dict(self) -> dict:
        return {"field": self._field, "desc": self._desc}

    def to_proto(self) -> dashvector_pb2.OrderByField:
        return dashvector_pb2.OrderByField(field=self._field, desc=self._desc)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
