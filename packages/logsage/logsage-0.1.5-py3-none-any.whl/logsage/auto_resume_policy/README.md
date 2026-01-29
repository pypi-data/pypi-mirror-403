# Auto-Resume-Policy

Auto resume policy is a system that extracts errors from AI training job logs, attributes root causes,
and recommends recovery actions. It reduces downtime and manual intervention for large GPU clusters by analyzing logs,
classifying failures, and suggesting whether to restart a job, stop it for investigation,
or temporarily isolate faulty GPU nodes.

## Overview

Auto-Resume-Policy analyzes SLURM job logs using classical parsing and NVIDIA LLMs to:

1. Extract and de-duplicate error patterns
2. Attribute errors to root causes with confidence
3. Recommend actions (restart/stop)
4. Identify nodes or ranks likely responsible for failures

Main modules:
- `error_extraction.py`: Extracts application errors and key traces
- `error_attribution.py`: Assigns error categories and recommends actions
- `log_sage.py`: logsage pipeline process
- `config.py`: Strongly-typed settings via environment variables
- `attribution_classes.py`: Pydantic models for requests/responses
- `utils.py`, `prompts.py`: Helper utilities and LLM prompts

## Configuration

The service reads configuration from environment variables (via `config.py`). A `LOGSAGE_` prefix is used by default, but some fields override the prefix for convenience.

- `NVIDIA_API_KEY` (required in production): API key for NVIDIA AI Endpoints
- `FAST_API_ROOT_PATH` (optional): Root path behind a proxy; default empty
- `LOGSAGE_DEBUG` (optional): `true`/`false`; default `true` locally, set `false` in production
- `DOMAIN_SIZE` (required in production): Number of GPUs per domain (Hopper: 8, Grace-Blackwell: 4), if is not set, the default value is 1

Notes:
- `Settings` also supports `LOGSAGE_DEBUG`, etc. See `config.py` for details.
- In production (`DEBUG=false`), the service validates that `NVIDIA_API_KEY` are present.

## Constants:

The following constants are defined and used across the system for batching, trace limits, and isolation logic:

- `BATCH_WIDTH` = 1000        # Numbers of tokens per batch
- `BATCH_LLM_CALLS` = 50      # Max concurrent LLM calls
- `NUMBER_LAST_LINES` = 1_000_000    # Use -1 to process all lines
- `CONTEXT_SIZ` = 100_000    # Max token context length for LLM analysis window

- `ISOLATION_COUNT` = 2       # Maximum number of nodes to isolate upon hardware failure

- `XSS_FILTERING` = True           # Enable XSS filtering
- `PERSONAL_ENDPOINT` = True       # Use NVIDIA NIM personal endpoint

## Key Functionalities

1. LLM Initialization

- Function: `get_llm()`

  Initializes and returns an instance of the NVIDIA Chat LLM (ChatNVIDIA) for text-based analysis.

- Supports:

  Personal endpoints via registered custom model endpoints.

  Fallback model logic in case of failure.

  Automatic configuration through Config and environment variables.

  Ensures stable LLM setup with retry logic and logging.

2. Log Analysis & Attribution

   - From Log Files

     Function: `get_attribution_from_file(log_path, isolation, attribution, verbose)`
     
     Reads and analyzes log files directly from disk.

     Performs:

     Error extraction using `return_application_errors()`.
   
     Resume policy and attribution inference via `get_proposed_solution_cat()`.
   
     Returns structured results in an `ErrorAttribution` object including:
   
     - Full and unique errors.
     
     - Suggested auto-resume policy. 
     
     - Attribution metadata.
     
     Includes optional XSS sanitization for web-safe display.

   - From Memory (Logs Dict)

     Function: `get_attribution_from_attribution_id(llm, attribution_id)`

     Retrieves and analyzes logs that were previously stored in memory under a unique attribution ID.
   
     Produces an ErrorAttributionWithJobId object, linking analysis results to a job ID.
   
     Performs periodic cleanup of expired entries to maintain memory hygiene.

   - From Log Lines

     Function: `get_attribution_from_logs(llm, log_lines)`

     Provides direct in-memory attribution for logs supplied as a Python list.

     Ideal for streaming or interactive analysis scenarios.

3. Log Storage and Management

   - Attribution ID Generation

   Function: `generate_attribution_id(job_id, user_id="")`

   Creates a unique attribution identifier using UUID.

   Initializes a new entry in the global logs dictionary (`logs_dict`).

   Associates the attribution ID with a specific job and user.

   - Log Appending

   Function: `append_logs(attribution_id, app_logs)`

   Appends incoming log lines to an existing attribution entry.

   Automatically updates the entry timestamp.

   Supports both legacy list-based and new dict-based formats.

   Returns the total number of lines currently stored.

   - Log Cleanup

   Function: `clean_logs_dict()`

   Automatically removes entries older than 24 hours (`LOG_EXPIRY_SECONDS`).

   Ensures memory efficiency and prevents stale data accumulation.

   Cleans associated mappings (`attributionid_jobid_dict`, `attributionid_userid_dict`).

4. Log Parsing Utility

   Function: `split_by_cycle(log_lines)`

   Splits logs into chunks based on Cycle: N markers.

   Useful for analyzing logs that represent iterative training cycles or repeated execution loops.

   Returns a list of log chunks, each corresponding to one cycle.

5. Command-Line Interface (CLI)

   Entry Point: `main()`

   Enables execution from the command line for direct log analysis.

   Accepts:

      `filepath` – Path to the log file to analyze.

      `--isolation` – Enable isolation mode.

      `--attribution` – Enable attribution mode.

      `--verbose` – Enable verbose output.

   Produces `ErrorAttribution` results for further processing or display.

## Supporting Components

- Global Structures:

  `logs_dict`: Stores active logs and timestamps per attribution ID.

  `attributionid_jobid_dict`: Maps attribution IDs to job IDs.

  `attributionid_userid_dict`: Maps attribution IDs to user IDs.

  `cache_dict and cache_user_dict`: LRU caches to optimize repeated LLM queries.

- Thread Safety:

  Protected by a global Lock (logs_lock) to prevent race conditions during concurrent updates.

- Security Features:

  1. XSS Filtering: Sanitizes model outputs before display. 
  
  2. Path Safety: Prevents unsafe log path construction. 
  
  3. Access Control: Uses unique attribution IDs for user/job isolation.

## Notes on Models

Defined in `attribution_classes.py`:
- `NewAttributionRequest`: `{ job_id: str }`
- `AttributionID`: `{ attribution_id: str }`
- `LogsRequest`: `{ attribution_id: str, log_stream: str }`
- `AppLogsLen`: `{ lines_len: int }`
- `ErrorAttribution` / `ErrorAttributionWithJobId`:
  - `application_errors_full`, `application_errors_unique`
  - `auto_resume`, `auto_resume_verbose`
  - `attribution`,
  - `job_id` (with `ErrorAttributionWithJobId`)
- `JobLogsResult`: `{ job_id: int, cluster_name: str, log_lines: list[str] }`

## License

SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
