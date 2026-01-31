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

import logging
import os

from dashvector.common.constants import DASHVECTOR_LOGGING_LEVEL_ENV

logger = logging.getLogger("dashvector")


def enable_logging():
    level = os.environ.get(DASHVECTOR_LOGGING_LEVEL_ENV, None)
    if level is not None:  # set logging level.
        if level not in ["info", "debug"]:
            # set logging level env, but invalid value, use default.
            level = "info"
        if level == "info":
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.DEBUG)
        # set default logging handler
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(filename)s - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s"
            # noqa E501
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)


# in release disable dashscope log
# you can enable dashscope log for debugger.
enable_logging()
