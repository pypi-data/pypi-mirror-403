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
from dataclasses import dataclass


@dataclass(frozen=True)
class PartitionMeta(object):
    """
    A Meta Instance of Partition.

    Args:
        name (str): partition name
        status (str): partition status
    """

    name: str
    status: str

    def __dict__(self):
        meta_dict = {"name": self.name, "status": self.status}
        return meta_dict

    def __str__(self):
        return json.dumps(self.__dict__())

    def __repr__(self):
        return self.__str__()


@dataclass(frozen=True)
class PartitionStats(object):
    """
    A Status Instance of Partition.

    Args:
        name (str): partition name
        total_doc_count (int): total doc count in partition
    """

    name: str
    total_doc_count: int

    def __dict__(self):
        meta_dict = {"total_doc_count": self.total_doc_count}
        return meta_dict

    def __str__(self):
        return json.dumps(self.__dict__())

    def __repr__(self):
        return self.__str__()
