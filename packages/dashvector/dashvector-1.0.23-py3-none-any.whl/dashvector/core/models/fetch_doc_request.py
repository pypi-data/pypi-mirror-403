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
from dashvector.common.handler import RPCRequest
from dashvector.common.types import *
from dashvector.core.models.collection_meta_status import CollectionMeta
from dashvector.core.proto import dashvector_pb2


class FetchDocRequest(RPCRequest):
    def __init__(self, *, collection_meta: CollectionMeta, ids: IdsType, partition: Optional[str] = None):
        """
        collection_meta: CollectionMeta
        """
        self._collection_meta = collection_meta
        self._collection_name = collection_meta.name

        """
        ids: IdsType
        """
        self._ids, self._ids_is_single = Validator.validate_doc_ids(ids, doc_op="GetDocRequest")

        """
        partition: Optional[str]
        """
        self._partition = None
        if partition is not None:
            self._partition = Validator.validate_partition_name(partition, doc_op="GetDocRequest")

        """
        FetchDocRequest: google.protobuf.Message
        """
        fetch_request = dashvector_pb2.FetchDocRequest()
        fetch_request.ids.extend(self._ids)
        if self._partition is not None:
            fetch_request.partition = self._partition

        super().__init__(request=fetch_request)

    @property
    def collection_name(self):
        return self._collection_name

    @property
    def partition_name(self):
        return "default" if self._partition is None else self._partition

    @property
    def collection_meta(self):
        return self._collection_meta

    @property
    def ids(self):
        ids_str = ",".join(self._ids)
        return ids_str

    @property
    def ids_is_single(self):
        return self._ids_is_single
