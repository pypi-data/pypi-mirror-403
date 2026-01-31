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

import http
from enum import IntEnum

import grpc


class DashVectorCode(IntEnum):
    Timeout = 408
    Success = 0
    Closed = -998
    Unknown = -999
    EmptyCollectionName = -2000
    EmptyColumnName = -2001
    EmptyPartitionName = -2002
    EmptyColumns = -2003
    EmptyPrimaryKey = -2004
    EmptyDocList = -2005
    EmptyDocFields = -2006
    EmptyIndexField = -2007
    InvalidRecord = -2008
    InvalidQuery = -2009
    InvalidWriteRequest = -2010
    InvalidVectorFormat = -2011
    InvalidDataType = -2012
    InvalidIndexType = -2013
    InvalidFeature = -2014
    InvalidFilter = -2015
    InvalidPrimaryKey = -2016
    InvalidField = -2017
    MismatchedIndexColumn = -2018
    MismatchedDimension = -2019
    MismatchedDataType = -2020
    InexistentCollection = -2021
    InexistentPartition = -2022
    InexistentColumn = -2023
    InexistentKey = -2024
    DuplicateCollection = -2025
    DuplicatePartition = -2026
    DuplicateKey = -2027
    DuplicateField = -2028
    UnreadyPartition = -2029
    UnreadyCollection = -2030
    UnsupportedCondition = -2031
    OrderbyNotInSelectItems = -2032
    PbToSqlInfoError = -2033
    ExceedRateLimit = -2034
    InvalidSparseValues = -2035
    InvalidBatchSize = -2036
    InvalidDimension = -2037
    InvalidExtraParam = -2038
    InvalidRadius = -2039
    InvalidLinear = -2040
    InvalidTopk = -2041
    InvalidCollectionName = -2042
    InvalidPartitionName = -2043
    InvalidFieldName = -2044
    InvalidChannelCount = -2045
    InvalidReplicaCount = -2046
    InvalidJson = -2047
    InvalidGroupBy = -2053,
    InvalidSparseIndices = -2951
    InvalidEndpoint = -2952
    ExceedIdsLimit = -2967
    InvalidVectorType = -2968
    ExceedRequestSize = -2970
    ExistVectorAndId = -2973
    InvalidArgument = -2999


class DashVectorException(Exception):
    """
    DashVector Exception
    """

    def __init__(self, code=DashVectorCode.Unknown, reason=None, request_id=None):
        self._code = code
        self._reason = "DashVectorSDK unknown exception" if reason is None else reason
        self._request_id = request_id
        super().__init__(f"{self._reason}({self._code})")

    @property
    def code(self):
        return self._code

    @property
    def message(self):
        return self._reason

    @property
    def request_id(self):
        if self._request_id is None:
            return ""
        return self._request_id


class DashVectorHTTPException(DashVectorException):
    def __new__(cls, code, reason=None, request_id=None):
        exception_code = code
        exception_reason = reason
        if isinstance(code, http.HTTPStatus):
            exception_code = code.value
            exception_reason = f"DashVectorSDK http rpc error: {code.phrase}"

        return DashVectorException(code=exception_code, reason=exception_reason, request_id=request_id)


class DashVectorGRPCException(DashVectorException):
    def __new__(cls, code, reason=None, request_id=None):
        exception_code = code
        exception_reason = reason
        if isinstance(code, grpc.StatusCode):
            exception_code = code.value[0]
            exception_reason = f"DashVectorSDK grpc rpc error: {code.value[1]}"
        return DashVectorException(code=exception_code, reason=exception_reason, request_id=request_id)
