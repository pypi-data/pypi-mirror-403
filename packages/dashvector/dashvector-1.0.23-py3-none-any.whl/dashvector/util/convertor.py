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
import collections
import json

# -*- coding: utf-8 -*-
from typing import Dict, Optional

from dashvector.util.validator import verify_sparse_vector


def to_sorted_sparse_vector(sparse_vector: Optional[Dict[int, float]]) -> Optional[Dict[int, float]]:
    if sparse_vector is None:
        return
    verify_sparse_vector(sparse_vector)
    return dict(sorted(sparse_vector.items()))

def to_sorted_sparse_vectors(sparse_vectors: Optional[Dict[str, Dict[int, float]]]) -> Optional[Dict[str, Dict[int, float]]]:
    if sparse_vectors is None:
        return
    sorted_sparse_vectors = dict()
    for key in sparse_vectors.keys():
        sparse_vector = sparse_vectors[key]
        verify_sparse_vector(sparse_vector)
        sorted_sparse_vectors[key] = dict(sorted(sparse_vector.items()))

    return sorted_sparse_vectors

def to_json_without_ascii(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)
