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
import json
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Optional

from dashvector.common.types import IndexType

__all__ = ["Index", "IndexConverter"]

from dashvector.core.proto import dashvector_pb2


@dataclass(frozen=True)
class Index:
    index_type: Optional[IndexType] = IndexType.INVERT

    def __dict__(self):
        return {"index_type": self.index_type.name}

    def __str__(self):
        return json.dumps(self.__dict__())


class IndexConverter:
    @staticmethod
    def to_index_from_pb(index: dashvector_pb2.CollectionInfo.Index) -> Index:
        return Index(index_type=IndexType[dashvector_pb2.CollectionInfo.IndexType.Name(index.index_type)])

    @staticmethod
    def to_index_from_model(index: Index) -> dashvector_pb2.CollectionInfo.Index:
        index_type_pb = dashvector_pb2.CollectionInfo.IndexType.Value(index.index_type.name)
        return dashvector_pb2.CollectionInfo.Index(index_type=index_type_pb)

    @staticmethod
    def to_index_from_dict(index: dict) -> Index:
        index_type = IndexType[index["index_type"]]
        return Index(index_type=index_type)
