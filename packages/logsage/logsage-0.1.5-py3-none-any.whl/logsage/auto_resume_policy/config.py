# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os


# App configuration
class Config:
    ATTRIBUTION: bool = os.environ.get("LOGSAGE_ATTRIBUTION", "true").lower() == "true"
    VERBOSE: bool = os.environ.get("LOGSAGE_VERBOSE", "true").lower() == "true"
    ISOLATION: bool = os.environ.get("LOGSAGE_ISOLATION", "true").lower() == "true"
    NVIDIA_API_KEY: str = os.environ.get("NVIDIA_API_KEY", "")
    MODEL_NAME: str = os.environ.get("MODEL_NAME", "")
    MODEL_FUNCTION_ID: str = os.environ.get("MODEL_FUNCTION_ID", "")
    PERSONAL_ENDPOINT: bool = os.environ.get("PERSONAL_ENDPOINT", "true").lower() == "true"

    @classmethod
    def validate(cls):
        """Validate critical configuration fields."""
        if not cls.NVIDIA_API_KEY:
            raise ValueError("NVIDIA_API_KEY environment variable is required but not set")
        if not cls.MODEL_NAME:
            raise ValueError("MODEL_NAME is required")
        if not cls.MODEL_FUNCTION_ID:
            raise ValueError("MODEL_FUNCTION_ID is required")
