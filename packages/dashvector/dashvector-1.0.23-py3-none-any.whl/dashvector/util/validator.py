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
from typing import Dict, List, Optional, Union

import numpy as np

from dashvector.common.error import DashVectorCode, DashVectorException

ENDPOINT_PATTERN = "^([a-zA-Z0-9-.]+)\.([a-z\.]{2,6})\/?$"
UINT32_MAXVALUE = 2**32 - 1


def verify_endpoint(endpoint: Optional[str]) -> bool:
    """Verify endpoint is valid

    verify_endpoint("dashvector.cn-hangzhou.aliyuncs.com") -> True
    """
    return endpoint and re.search(ENDPOINT_PATTERN, endpoint) is not None


def verify_sparse_vector(sparse_vector: Dict[int, float]):
    """Verify sparse vector

    Verify sparse vector type and indices exceed max value of uint32
    """
    # TODO
    #  1. SDK错误码需要重新开一个区间，解决gateway和sdk维护同区间错误码带来的混乱。
    #  2. model下的参数校验收敛到该文件中实现复用
    # 1. check sparse vector type
    if not isinstance(sparse_vector, dict):
        raise DashVectorException(
            code=DashVectorCode.InvalidArgument,
            reason=f"DashVectorSDK sparse_vector type({type(sparse_vector)}) is invalid and must be Dict[int, float]",
        )

    for key, value in sparse_vector.items():
        # 2. check sparse vector key and value type (dict:[int, float])
        if not isinstance(key, int) or not isinstance(value, float):
            raise DashVectorException(
                code=DashVectorCode.InvalidArgument,
                reason="DashVectorSDK sparse_vector is invalid and must be Dict[int, float]",
            )

        # 3. check sparse indices exceed max value of uint32
        if key > UINT32_MAXVALUE or key < 0:
            raise DashVectorException(
                code=DashVectorCode.InvalidSparseIndices,
                reason=f"Sparse vector indices({key}) is invalid and must be in [0, {UINT32_MAXVALUE}]",
            )


def vector_is_empty(vector: Union[List[int], List[float], np.ndarray]) -> bool:
    """Verify vector is empty"""
    if isinstance(vector, list):
        return not vector
    if isinstance(vector, np.ndarray):
        return vector.size == 0
    return True
