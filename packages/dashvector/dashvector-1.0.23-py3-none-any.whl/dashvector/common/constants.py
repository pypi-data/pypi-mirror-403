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
DASHVECTOR_VECTOR_NAME = "proxima_vector"
DASHVECTOR_LOGGING_LEVEL_ENV = "DASHVECTOR_LOGGING_LEVEL"
FIELD_NAME_PATTERN = "^[a-zA-Z0-9_-]{1,32}$"
FIELD_NAME_PATTERN_MSG = "character must be in [a-zA-Z0-9] and symbols[_, -] and length must be in [1,32]"
COLLECTION_AND_PARTITION_NAME_PATTERN = "^[a-zA-Z0-9_-]{3,32}$"
COLLECTION_AND_PARTITION_NAME_PATTERN_MSG = (
    "character must be in [a-zA-Z0-9] and symbols[_, -] and length must be in [3,32]"
)
DOC_ID_PATTERN = "^[a-zA-Z0-9_\\-!@#$%+=.]{1,64}$"
DOC_ID_PATTERN_MSG = "character must be in [a-zA-Z0-9] and symbols[_-!@#$%+=.] and length must be in [1, 64]"
GRPC_MAX_MSG_SIZE = 128 * 1024 * 1024
MAX_INT_VALUE = 2 ** 31 - 1
MIN_INT_VALUE = -2 ** 31