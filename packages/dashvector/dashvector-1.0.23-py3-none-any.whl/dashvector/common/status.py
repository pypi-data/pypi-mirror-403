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

from enum import Enum, IntEnum
from typing import Union

from dashvector.common.error import DashVectorCode, DashVectorException


class StrStatus(str, Enum):
    INITIALIZED = "INITIALIZED"
    SERVING = "SERVING"
    DROPPING = "DROPPING"
    ERROR = "ERROR"


class Status(IntEnum):
    INITIALIZED = 0
    SERVING = 1
    DROPPING = 2
    ERROR = 3

    @staticmethod
    def get(cs: Union[str, StrStatus]) -> IntEnum:
        if cs == StrStatus.INITIALIZED:
            return Status.INITIALIZED
        elif cs == StrStatus.SERVING:
            return Status.SERVING
        elif cs == StrStatus.DROPPING:
            return Status.DROPPING
        elif cs == StrStatus.ERROR:
            return Status.ERROR
        raise DashVectorException(code=DashVectorCode.InvalidArgument, reason=f"DashVectorSDK get invalid status {cs}")

    @staticmethod
    def str(cs: Union[int, IntEnum]) -> str:
        if cs == Status.INITIALIZED:
            return StrStatus.INITIALIZED.value
        elif cs == Status.SERVING:
            return StrStatus.SERVING.value
        elif cs == Status.DROPPING:
            return StrStatus.DROPPING.value
        elif cs == Status.ERROR:
            return StrStatus.ERROR.value
        raise DashVectorException(code=DashVectorCode.InvalidArgument, reason=f"DashVectorSDK get invalid Status {cs}")
