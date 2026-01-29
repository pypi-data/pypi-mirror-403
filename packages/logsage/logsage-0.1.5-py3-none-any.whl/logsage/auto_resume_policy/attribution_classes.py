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

from collections import OrderedDict
from enum import Enum

from langchain_core.runnables import Runnable
from pydantic import BaseModel


class LRUCache:
    def __init__(self, capacity):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key):
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key, value):
        self.cache[key] = value
        self.cache.move_to_end(key)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    def length(self):
        return len(self.cache)

    def print(self):
        for key, value in self.cache.items():
            print(f"{key}: {value}")


class ApplicationData:
    """Container for application error analysis data.

    Attributes:
        application_errors_list_full: Complete list of application errors
        application_errors_list_unique: Unique application errors
        tm_text_unique: Unique text messages
        finished: Job completion status
        application_errors_list_iteration: Errors by iteration
        traceback_dict: Dictionary of tracebacks
        training_started: Training status indicator
    """

    def __init__(
        self,
        application_errors_list_full: list,
        application_errors_list_unique: list,
        tm_text_unique: list,
        finished: str,
        application_errors_list_iteration: list,
        traceback_dict: dict,
        training_started: str,
        iteration_patterns: list,
        checkpoint_saved: bool,
        original_text: list,
        progressed_indices: list,
        pattern_before_max: str,
    ):
        self.application_errors_list_full = application_errors_list_full
        self.application_errors_list_unique = application_errors_list_unique
        self.tm_text_unique = tm_text_unique
        self.finished = finished
        self.application_errors_list_iteration = application_errors_list_iteration
        self.traceback_dict = traceback_dict
        self.training_started = training_started
        self.iteration_patterns = iteration_patterns
        self.checkpoint_saved = checkpoint_saved
        self.original_text = original_text
        self.progressed_indices = progressed_indices
        self.pattern_before_max = pattern_before_max


class ErrorAttribution(BaseModel):
    application_errors_full: list = []
    application_errors_unique: list = []
    auto_resume: str
    auto_resume_verbose: str
    attribution: str


class ErrorAttributionWithJobId(BaseModel):
    application_errors_full: list = []
    application_errors_unique: list = []
    auto_resume: str
    auto_resume_verbose: str
    attribution: str
    job_id: str


class JobLogsResult(BaseModel):
    job_id: int
    cluster_name: str
    log_lines: list = []


class AppLogs(BaseModel):
    lines: list = []


class ADILog(BaseModel):
    data: list = []


class AttributionID(BaseModel):
    attribution_id: str


class AttributionRequest(BaseModel):
    attribution_id: str


class AppLogsLen(BaseModel):
    lines_len: int


class LogsRequest(BaseModel):
    attribution_id: str
    log_stream: str


class NewAttributionRequest(BaseModel):
    job_id: str


class FakeListLLM(Runnable):
    def __init__(self, batch_responses, invoke_response):
        self._batch_responses = batch_responses
        self._invoke_response = invoke_response
        self._batch_stage = 0
        self._invoke_stage = 0

    def batch(self, inputs, config=None, return_exceptions=False):
        """Simulates a batch() call — returns fixed responses."""
        response = self._batch_responses[self._batch_stage]
        self._batch_stage += 1
        return response

    def invoke(self, input=None, config=None):
        """Simulates a single LLM call after batch() has been called."""
        response = self._invoke_response[self._invoke_stage]
        self._invoke_stage += 1
        return response


class FinishedStatus(str, Enum):
    LLM_FAILURE = "LLM_FAILURE"
    SLURM_CANCELLED = "SLURM_CANCELLED"
    SLURM_CANCELLED_JOB_REQUEUE = "SLURM_CANCELLED_JOB_REQUEUE"
    TRAINING_DONE = "TRAINING_DONE"
    NO_ERRORS = "NO_ERRORS"
    WITH_ERRORS = "WITH_ERRORS"

    # pattern-based (not exact match)
    SLURM_CANCELLED_TIME_LIMIT = "SLURM_CANCELLED_TIME_LIMIT"


class AutoResumeAction(str, Enum):
    LLM_FAILURE = "LLM FAILURE"
    RESTART_IMMEDIATE = "RESTART IMMEDIATE"
    STOP_NO_RESTART = "STOP - DONT RESTART IMMEDIATE"
    ERRORS_NOT_FOUND = "ERRORS NOT FOUND"


class Attribution(str, Enum):
    LLM_FAILURE = "LLM FAILURE"
    SLURM_STEP_CANCELLED = "SLURM STEP CANCELLED"
    SLURM_STEP_CANCELLED_JOB_REQUEUE = "SLURM STEP CANCELLED JOB REQUEUE"
    TRAINING_DONE = "TRAINING DONE"
    ERRORS_NOT_FOUND = "ERRORS NOT FOUND"


class ApplicationDataState(str, Enum):
    LLM_FAILURE = "LLM_FAILURE"

    SLURM_CANCELLED = "SLURM_CANCELLED"
    SLURM_CANCELLED_JOB_REQUEUE = "SLURM_CANCELLED_JOB_REQUEUE"
