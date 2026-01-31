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

from dataclasses import dataclass
from typing import Optional

from dashvector.common.types import *
from dashvector.core.models.collection_meta_status import CollectionMeta
from dashvector.core.proto import dashvector_pb2
from dashvector.core.doc import Doc, DocBuilder

__all__ = ["GroupBuilder", "Group"]


@dataclass(frozen=True)
class Group(object):
    """
    A Group Instance.

    Args:
        group_id (str): a group identifier.
        docs (List[Doc]): a list of docs in the group.

    Examples
        a_group = Group(group_id="foo", docs=[Doc(id="a", vector=[0.1, 0.2]), Doc(id="b", vector=[0.2, 0.3])])
    """

    group_id: str
    docs: List[Doc]

    def __dict__(self):
        meta_dict = {}
        if self.group_id is not None:
            meta_dict["group_id"] = self.group_id
        if self.docs is not None:
            meta_dict["docs"] = [doc.__dict__() for doc in self.docs]
        return meta_dict

    def __str__(self):
        return to_json_without_ascii(self.__dict__())

    def __repr__(self):
        return self.__str__()


class GroupBuilder(object):
    @staticmethod
    def from_pb(group: dashvector_pb2.GroupResult, collection_meta: CollectionMeta):
        if not isinstance(group, dashvector_pb2.GroupResult):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason="DashVectorSDK get invalid group and type must be dashvector_pb2.GroupResult",
            )
        if not isinstance(collection_meta, CollectionMeta):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason="DashVectorSDK get invalid collection_meta and type must be CollectionMeta",
            )

        group_id = group.group_id
        docs = [DocBuilder.from_pb(doc, collection_meta) for doc in group.docs]
        return Group(group_id=group_id, docs=docs)

    @staticmethod
    def from_dict(group: dict, collection_meta: Optional[CollectionMeta] = None):
        if not isinstance(group, dict):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument, reason="DashVectorSDK get invalid group and type must be dict"
            )
        if not isinstance(collection_meta, CollectionMeta):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason="DashVectorSDK get invalid collection_meta and type must be CollectionMeta",
            )
        """
        group_id: str
        """
        group_id = group.get("group_id", "")
        if not isinstance(group_id, str):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument, reason="DashVectorSDK get invalid group_id and type must be str"
            )
        docs = [DocBuilder.from_dict(doc, collection_meta) for doc in group.get("docs", [])]
        return Group(group_id=group_id, docs=docs)