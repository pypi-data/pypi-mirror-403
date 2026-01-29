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

BATCH_WIDTH = 1000  # Numbers of tokens per batch
CONTEXT_SIZE = 100_000  # Max token context length for LLM analysis window
BATCH_LLM_CALLS = 50  # Max concurrent LLM calls
NUMBER_LAST_LINES = 1_000_000  # Use -1 to process all lines

ISOLATION_COUNT = 2  # Maximum number of nodes to isolate upon hardware failure

XSS_FILTERING = True

ERROR_WORDS = [
    "runtimeerror:",
    "nvonly",
    "ibv_modify_qp",
    "nccl warn",
    "net/ib",
    "net/ofi",
    "watchdog caught collective operation timeout",
    "slurmstepd",
    "cuda failure",
    "cuda error",
    "segmentation fault",
    "userbuffers.cu",
    "checkpointingexception:",
]

HIGH_PRIO_WORDS = ["error:", "exception:", "error(", "exception(", "error", "exception", "failure", "crash"]

HARDWARE_WORDS = [
    "uncorrectable ECC error encountered",
    "CUDA error: unknown error",
    "CUDA error",
    "GPU is lost",
    "CUDA error: unspecified launch failure",
    "ibv_modify_qp failed with error No data available",
    "ibv_open_device failed",
    "NET/IB : Unable to open device",
    "Failed to initialize rdma protocol",
    "local catastrophic error",
    "NVML: Failed to get usage",
]

NOT_HARDWARE_WORDS = [
    "Watchdog caught collective operation timeout: WorkNCCL",
    "last enqueued NCCL work",
    "srun: error:",
    "slurmstepd: error:",
    "DUE TO NODE FAILURE, SEE SLURMCTLD",
    "avoid data inconsistency, we are taking the entire process down",
    "Due to the asynchronous nature of CUDA kernels, subsequent GPU operations might run on corrupted/incomplete data",
]

BENIGN_WORDS = [
    'raise SignalException(f"Process',
    "Could not receive type from localRank",
    "Accept failed Resource temporarily unavailable",
    "Failed to execute operation Close from rank",
    "Failed to execute operation Connect from rank",
    "Accept failed Success",
    "srun returned status",
    "Accept failed Invalid argument",
    "Error encountered progressing operation",
    "frame #",
    "NCCL INFO",
    "[exiting program after",
    "NVML: Failed to get Compute running procs",
    "error: Prolog hung on node",
]

JOB_STARTED_NOT_DICT = {
    "job started": "The errors happened, during the job training process",
    "job not started": "The errors happened, and before the the job training running",
}

POLICIES = ["Suggest to NOT RESTART THE JOB IMMEDIATELY", "Suggest to RESTART THE JOB IMMEDIATELY"]

HARDWARE_THR_CATEGORY = 40
HARDWARE_THR_LINE = 60

LLM_ENDPOINT_FAILED = "LLM ENDPOINT FAILED"


FILE_STACK_PATTERN = "<NUMBER> : File < TEXT > , line <NUMBER>"
