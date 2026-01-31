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

from dashvector.core.index import IndexConverter, Index
from dashvector.common.types import *
from dashvector.core.models.partition_meta_status import PartitionMeta, PartitionStats
from dashvector.core.proto.dashvector_pb2 import CollectionInfo, StatsCollectionResponse


class CollectionMeta(object):
    def __init__(self, meta: Union[dict, CollectionInfo]):
        """
        meta: CollectionInfo
        """
        self._meta = None
        self._vectors = {}
        self._sparse_vectors = {}
        self._fields = {}
        self._indexes = {}
        self._partitions = {}
        if isinstance(meta, CollectionInfo):
            self._parse_pb_collectioninfo(meta)
        elif isinstance(meta, dict):
            self._parse_dict_collectioninfo(meta)
        else:
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason="DashVectorSDK parse collection meta failed and meta type must be [dict, CollectionInfo]",
            )
        self._meta = meta

    def _parse_pb_collectioninfo(self, meta: CollectionInfo):
        self._name = meta.name
        self._dimension = meta.dimension
        self._dtype = meta.dtype
        self._metric = meta.metric
        self._status = meta.status

        # fields_schema
        for field_name, field_type in meta.fields_schema.items():
            self._fields[field_name] = FieldType.str(field_type)

        # vectors_schema
        for field_name, vector_param in meta.vectors_schema.items():
            self._vectors[field_name] = VectorParam.from_pb(vector_param)

        # sparse_vectors_schema
        for field_name, vector_param in meta.sparse_vectors_schema.items():
            self._sparse_vectors[field_name] = VectorParam.from_pb(vector_param)

        # indexes
        for index_name, index in meta.indexes.items():
            self._indexes[index_name] = IndexConverter.to_index_from_pb(index)

        # partitions
        for partition_name, partition_status in meta.partitions.items():
            self._partitions[partition_name] = PartitionMeta(partition_name, Status.str(partition_status))

    def _parse_dict_collectioninfo(self, meta: dict):
        self._name = meta.get("name")
        self._dimension = meta.get("dimension")
        self._dtype = VectorType.get(meta.get("dtype"))
        self._metric = MetricType.get(meta.get("metric"))
        self._status = Status.get(meta.get("status"))

        # fields_schema
        self._fields = meta.get("fields_schema")

        # vectors_schema
        vectors = meta.get("vectors_schema")
        if vectors:
            for field_name, vector_param in vectors.items():
                self._vectors[field_name] = VectorParam.from_dict(vector_param)

        # sparse_vectors_schema
        sparse_vectors = meta.get("sparse_vectors_schema")
        if sparse_vectors:
            for field_name, vector_param in sparse_vectors.items():
                self._sparse_vectors[field_name] = VectorParam.from_dict(vector_param)

        indexes = meta.get("indexes")
        if indexes:
            for index_name, index in indexes.items():
                self._indexes[index_name] = IndexConverter.to_index_from_dict(index)

        # partitions
        partitions = meta.get("partitions")
        if partitions:
            for partition_name, partition_status in partitions.items():
                self._partitions[partition_name] = PartitionMeta(partition_name, partition_status)


    @property
    def name(self):
        return self._name

    def get_dimension(self, vector_name=None):
        if vector_name is None:
            self._check_vector_count("dimension")
            return self._dimension
        if vector_name not in self._vectors and vector_name not in self._sparse_vectors:
            raise DashVectorException(code=DashVectorCode.InvalidArgument, 
                                      reason=f"DashVectorSDK get failed, vector name {vector_name} not in vectors schema")
        if vector_name in self._vectors:
            return self._vectors[vector_name].dimension
        elif vector_name in self._sparse_vectors:
            return self._sparse_vectors[vector_name].dimension
    dimension = property(get_dimension)

    def get_dtype(self, vector_name=None):
        if vector_name is None:
            self._check_vector_count("dtype")
            return VectorType.str(self._dtype)
        if vector_name not in self._vectors and vector_name not in self._sparse_vectors:
            raise DashVectorException(code=DashVectorCode.InvalidArgument, 
                                      reason=f"DashVectorSDK get failed, vector name {vector_name} not in vectors schema")
        if vector_name in self._vectors:
            return self._vectors[vector_name].dtype
        elif vector_name in self._sparse_vectors:
            return self._sparse_vectors[vector_name].dtype
    dtype = property(get_dtype)

    def get_metric(self, vector_name=None):
        if vector_name is None:
            self._check_vector_count("metric")
            return MetricType.str(self._metric)
        if vector_name not in self._vectors and vector_name not in self._sparse_vectors:
            raise DashVectorException(code=DashVectorCode.InvalidArgument, 
                                      reason=f"DashVectorSDK get failed, vector name {vector_name} not in vectors schema")
        if vector_name in self._vectors:
            return self._vectors[vector_name].metric
        elif vector_name in self._sparse_vectors:
            return self._sparse_vectors[vector_name].metric
    metric = property(get_metric)

    @property
    def vectors_schema(self):
        return self._vectors
    
    @property
    def sparse_vectors_schema(self):
        return self._sparse_vectors

    @property
    def fields_schema(self):
        return self._fields

    @property
    def indexes(self):
        return self._indexes

    @property
    def status(self):
        return Status.str(self._status)

    @property
    def partitions(self):
        return self._partitions

    def _check_vector_count(self, op: str):
        if len(self._vectors) + len(self._sparse_vectors) > 1:
            raise DashVectorException(code=DashVectorCode.InvalidArgument, 
                                      reason=f"DashVectorSDK get_{op} should provide vector name when collection has multi vectors")

    def __dict__(self):
        # hide dimension/dtype/metric for multi-vector collection
        if len(self._vectors) + len(self._sparse_vectors) <= 1:
            meta_dict = {"name": self.name, "dimension": self.dimension, "dtype": self.dtype, "metric": self.metric}
        else:
            meta_dict = {"name": self.name}
        if self._status is not None:
            meta_dict["status"] = self.status
        if self._fields is not None:
            meta_dict["fields_schema"] = self.fields_schema
        if bool(self._indexes):
            meta_dict["indexes"] = {k: v.__dict__() for k, v in self._indexes.items()}
        if self._vectors is not None:
            meta_dict["vectors_schema"] = {k: v.to_dict() for k, v in self._vectors.items()}
        if self._sparse_vectors is not None:
            meta_dict["sparse_vectors_schema"] = {k: v.to_dict() for k, v in self._sparse_vectors.items()}
        if self._partitions is not None:
            partitions_meta = {}
            for partition_name, partition_meta in self._partitions.items():
                partitions_meta[partition_name] = partition_meta.status
            meta_dict["partitions"] = partitions_meta
        return meta_dict

    def __str__(self):
        return json.dumps(self.__dict__())

    def __repr__(self):
        return self.__str__()


class CollectionStats(object):
    def __init__(self, *, stats: Union[dict, StatsCollectionResponse.CollectionStats]):
        """
        stats: Union[dict, StatsCollectionResponse.CollectionStats]
        """
        if stats is None:
            return
        self._stats = stats
        if isinstance(stats, StatsCollectionResponse.CollectionStats):
            self._parse_pb_collectionstats()
        elif isinstance(stats, dict):
            self._parse_dict_collectionstats()
        else:
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason="DashVectorSDK parse collection stats failed and stats type must be [dict, CollectionStats]",
            )

    def _parse_pb_collectionstats(self):
        self._total_doc_count = self._stats.total_doc_count
        self._index_completeness = round(self._stats.index_completeness, 1)
        self._partitions = {}
        for partition_name, partition_stats in self._stats.partitions.items():
            self._partitions[partition_name] = PartitionStats(
                name=partition_name, total_doc_count=partition_stats.total_doc_count
            )

    def _parse_dict_collectionstats(self):
        self._total_doc_count = self._stats.get("total_doc_count")
        self._index_completeness = round(self._stats.get("index_completeness"), 1)
        partitions = self._stats.get("partitions")
        if not bool(partitions):
            return
        self._partitions = {}
        for partition_name, partition_stats in partitions.items():
            self._partitions[partition_name] = PartitionStats(
                name=partition_name, total_doc_count=partition_stats.get("total_doc_count")
            )

    @property
    def total_doc_count(self):
        return self._total_doc_count

    @property
    def index_completeness(self):
        return self._index_completeness

    @property
    def partitions(self):
        return self._partitions

    def __dict__(self):
        meta_dict = {"total_doc_count": self.total_doc_count, "index_completeness": self.index_completeness}
        partitions = {}
        if len(self._partitions) > 0:
            for partition_name, partition_stats in self._partitions.items():
                partitions[partition_name] = partition_stats.__dict__()
            meta_dict["partitions"] = partitions
        return meta_dict

    def __str__(self):
        return json.dumps(self.__dict__())

    def __repr__(self):
        return self.__str__()
