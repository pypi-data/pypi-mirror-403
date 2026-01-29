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

from __future__ import annotations

import argparse
import logging
import os
import re
import time
import uuid
from threading import Lock
from typing import Union

from langchain_nvidia_ai_endpoints import ChatNVIDIA, Model, register_model

from logsage.auto_resume_policy.attribution_classes import (
    AppLogs,
    AppLogsLen,
    AttributionID,
    ErrorAttribution,
    ErrorAttributionWithJobId,
    LRUCache,
)
from logsage.auto_resume_policy.config import Config
from logsage.auto_resume_policy.consts import CONTEXT_SIZE, XSS_FILTERING
from logsage.auto_resume_policy.error_attribution import get_proposed_solution_cat
from logsage.auto_resume_policy.error_extraction import return_application_errors
from logsage.auto_resume_policy.utils import attribution_from_finished_status, handle_text_file, sanitize_xss

# Global cleanup lock for thread safety
logs_lock = Lock()

# Keep logs for 24 hours before auto cleanup
LOG_EXPIRY_SECONDS = 24 * 60 * 60

# Configure logging
logger = logging.getLogger(__name__)

# Initialize caches and dictionaries
cache_dict = LRUCache(1_000_000)
cache_user_dict = {}
# Each log entry now includes both logs and a timestamp
logs_dict: dict[str, dict[str, Union[float, list[str]]]] = {}
attributionid_jobid_dict: dict[str, str] = {}
attributionid_userid_dict: dict[str, str] = {}

config = Config()

# Check if DOMAIN_SIZE is set
if "DOMAIN_SIZE" not in os.environ:
    logger.error("Environment variable DOMAIN_SIZE is not set!")
else:
    domain_size = os.environ["DOMAIN_SIZE"]
    logger.info(f"DOMAIN_SIZE is set to {domain_size}")


def get_llm(config):
    """Initialize and return an LLM instance (ChatNVIDIA)."""

    def create_llm(model_name: str):
        """Helper to create a ChatNVIDIA instance with standard parameters."""
        return ChatNVIDIA(
            model=model_name,
            api_key=config.NVIDIA_API_KEY,
            temperature=0.0,
            top_p=1,
            max_tokens=CONTEXT_SIZE // 10,
        )

    if config.PERSONAL_ENDPOINT:
        register_model(
            Model(
                id=config.MODEL_NAME,
                model_type="chat",
                client="ChatNVIDIA",
                endpoint=config.MODEL_FUNCTION_ID,
            )
        )
        return create_llm(config.MODEL_NAME)

    model_name = handle_text_file(mode="read")
    if model_name == "ExceptionFile" or not model_name:
        model_name = config.MODEL_NAME

    try:
        llm = create_llm(model_name)
    except Exception as e:
        logger.error(f"Failed to initialize LLM with model '{model_name}': {e}", exc_info=True)
        # Only retry if fallback makes sense
        if model_name != config.MODEL_NAME:
            logger.info(f"Falling back to default model: {config.MODEL_NAME}")
            llm = create_llm(config.MODEL_NAME)
        else:
            return None  # Return None if fallback would use the same model

    return llm


def split_by_cycle(log_lines):
    """Split a list of log lines into chunks between 'Cycle: N' and 'Cycle: N+1'.

    Args:
        log_lines (list[str]): Lines from the log.

    Returns:
        list[list[str]]: Each sublist represents one cycle's chunk.
    """
    cycle_pattern = re.compile(r"Cycle:\s*(\d+)")
    cycle_indices = {}

    # 1️⃣ Find the FIRST occurrence index for each cycle number
    for i, line in enumerate(log_lines):
        match = cycle_pattern.search(line)
        if match:
            cycle_num = int(match.group(1))
            if cycle_num not in cycle_indices:
                cycle_indices[cycle_num] = i

    if not cycle_indices:
        return [log_lines]  # no cycles found → one big chunk

    # 2️⃣ Sort cycles numerically
    sorted_cycles = sorted(cycle_indices.items())

    # 3️⃣ Slice the logs between each cycle
    chunks = []
    for idx, (cycle_num, start_idx) in enumerate(sorted_cycles):
        # next cycle start (if exists)
        if idx + 1 < len(sorted_cycles):
            next_start_idx = sorted_cycles[idx + 1][1]
            chunk = log_lines[start_idx:next_start_idx]
        else:
            # last cycle → go until end
            chunk = log_lines[start_idx:]
        chunks.append(chunk)

    return chunks


def get_attribution_from_cycle(
    llm: ChatNVIDIA, log_lines: list[str], isolation: bool, attribution: bool, verbose: bool
) -> ErrorAttribution:
    """Function to return application logs errors and resume policy

    Args:
        log_lines: logs from cycle i
        isolation: Enable isolation mode
        attribution: Enable attribution analysis
        verbose: Enable verbose output


    Returns:
        ErrorAttribution object with analysis results
    """
    logger.info("Job processing started")
    s_time = time.time()
    app_data = return_application_errors(llm, log_lines, cache_dict)
    logger.info("error extraction latency: %s", time.time() - s_time)
    application_errors_full = [error[0] for error in app_data.application_errors_list_full]

    if XSS_FILTERING:
        application_errors_list_unique = [sanitize_xss(error) for error in app_data.application_errors_list_unique]
    else:
        application_errors_list_unique = app_data.application_errors_list_unique

    if len(app_data.application_errors_list_full) == 0:
        return attribution_from_finished_status(app_data, application_errors_list_unique)

    logger.info("Policy suggestion and Error attribution started")
    s_time = time.time()
    auto_resume_output, auto_resume_verbose, attribution_output, attribution_verbose, checkpoint_saved = (
        get_proposed_solution_cat(llm, app_data, isolation, attribution, verbose)
    )

    logger.info("error attribution latency: %s", time.time() - s_time)

    logger.info(auto_resume_output)

    if XSS_FILTERING:
        application_errors_full = [sanitize_xss(error) for error in application_errors_full]
        auto_resume_output = sanitize_xss(auto_resume_output)
        auto_resume_verbose = sanitize_xss(auto_resume_verbose)
        attribution_output = sanitize_xss(attribution_output)

    return ErrorAttribution(
        application_errors_full=application_errors_full,
        application_errors_unique=application_errors_list_unique,
        auto_resume=auto_resume_output,
        auto_resume_verbose=auto_resume_verbose,
        attribution=attribution_output,
    )


def get_attribution_from_file(log_path, isolation, attribution, verbose):
    """Function to return application logs errors and resume policy

    Args:
        log_path: Path to the log file
        isolation: Enable isolation mode
        attribution: Enable attribution analysis
        verbose: Enable verbose output


    Returns:
        ErrorAttribution object with analysis results
    """
    logger.info("Job processing started")

    if (not config.PERSONAL_ENDPOINT and (not config.MODEL_NAME or not config.NVIDIA_API_KEY)) or (
        config.PERSONAL_ENDPOINT
        and (not config.MODEL_NAME or not config.NVIDIA_API_KEY or not config.MODEL_FUNCTION_ID)
    ):
        logger.info("Missing NVIDIA endpoint env var")
        return ErrorAttribution(
            application_errors_full=[],
            application_errors_unique=[],
            auto_resume="Missing NVIDIA endpoint env var",
            auto_resume_verbose="Missing NVIDIA endpoint env var",
            attribution="Missing NVIDIA endpoint env var",
        )

    llm = get_llm(config)
    if not llm:
        return ErrorAttribution(
            application_errors_full=[],
            application_errors_unique=[],
            auto_resume="Endpoint error",
            auto_resume_verbose="Endpoint error",
            attribution="Endpoint error",
        )

    logger.info("Error extraction started")

    with open(log_path, encoding="latin-1") as f:
        log_lines = f.readlines()

    app_data = return_application_errors(llm, log_lines, cache_dict)
    application_errors_full = [error[0] for error in app_data.application_errors_list_full]

    if XSS_FILTERING:
        application_errors_list_unique = [sanitize_xss(error) for error in app_data.application_errors_list_unique]
    else:
        application_errors_list_unique = app_data.application_errors_list_unique

    if len(app_data.application_errors_list_full) == 0:
        return attribution_from_finished_status(app_data, application_errors_list_unique)

    logger.info("Policy suggestion and Error attribution started")
    auto_resume_output, auto_resume_verbose, attribution_output, attribution_verbose, checkpoint_saved = (
        get_proposed_solution_cat(llm, app_data, isolation, attribution, verbose)
    )

    logger.info(auto_resume_output)

    if XSS_FILTERING:
        application_errors_full = [sanitize_xss(error) for error in application_errors_full]
        auto_resume_output = sanitize_xss(auto_resume_output)
        auto_resume_verbose = sanitize_xss(auto_resume_verbose)
        attribution_output = sanitize_xss(attribution_output)

    return ErrorAttribution(
        application_errors_full=application_errors_full,
        application_errors_unique=application_errors_list_unique,
        auto_resume=auto_resume_output,
        auto_resume_verbose=auto_resume_verbose,
        attribution=attribution_output,
    )


def get_attribution_from_logs(llm: ChatNVIDIA, log_lines: list[str]) -> ErrorAttribution:
    """Extract error attribution from application logs.

    Args:
        llm: ChatNVIDIA instance for analysis
        log_lines: List of application log lines

    Returns:
        ErrorAttribution object containing analysis results

    Raises:
        Exception: If there's an error during attribution analysis
    """
    try:
        logger.info("Starting job processing")

        app_data = return_application_errors(llm, log_lines, cache_dict)
        application_errors_full = [error[0] for error in app_data.application_errors_list_full]

        if XSS_FILTERING:
            application_errors_list_unique = [sanitize_xss(error) for error in app_data.application_errors_list_unique]
        else:
            application_errors_list_unique = app_data.application_errors_list_unique

        if len(app_data.application_errors_list_full) == 0:
            return attribution_from_finished_status(app_data, application_errors_list_unique)

        logger.info("Policy suggestion and Error attribution started")
        auto_resume_output, auto_resume_verbose, attribution_output, attribution_verbose, checkpoint_saved = (
            get_proposed_solution_cat(llm, app_data, config.ISOLATION, config.ATTRIBUTION, config.VERBOSE)
        )

        logger.info(auto_resume_output)

        if XSS_FILTERING:
            application_errors_full = [sanitize_xss(error) for error in application_errors_full]
            auto_resume_output = sanitize_xss(auto_resume_output)
            auto_resume_verbose = sanitize_xss(auto_resume_verbose)
            attribution_output = sanitize_xss(attribution_output)

        return ErrorAttribution(
            application_errors_full=application_errors_full,
            application_errors_unique=application_errors_list_unique,
            auto_resume=auto_resume_output,
            auto_resume_verbose=auto_resume_verbose,
            attribution=attribution_output,
        )

    except Exception as e:
        logger.error(f"Error in attribution analysis: {e!s}")
        raise


# Store logs with timestamps instead of raw lists
# Example: logs_dict[attribution_id] = {"timestamp": time.time(), "logs": log_lines}


def clean_logs_dict():
    """Remove expired entries from logs_dict and related dicts."""
    now = time.time()
    with logs_lock:
        expired_keys = [
            k
            for k, v in logs_dict.items()
            if isinstance(v, dict) and "timestamp" in v and now - v["timestamp"] > LOG_EXPIRY_SECONDS
        ]
        for key in expired_keys:
            logs_dict.pop(key, None)
            attributionid_jobid_dict.pop(key, None)
            attributionid_userid_dict.pop(key, None)
            logger.info(f"Cleaned expired log entry: {key}")


def get_attribution_from_attribution_id(llm: ChatNVIDIA, attribution_id: str) -> ErrorAttributionWithJobId:
    """Get error attribution from attribution ID."""
    try:
        # 🔹 Periodic cleanup before doing anything
        clean_logs_dict()

        if attribution_id not in attributionid_jobid_dict or attribution_id not in logs_dict:
            logger.info(f"Invalid attribution ID: {attribution_id}")
            return ErrorAttributionWithJobId(
                application_errors_full=[],
                application_errors_unique=[],
                auto_resume="Bad jobid",
                auto_resume_verbose="Bad jobid",
                attribution="Bad jobid",
                job_id="Bad jobid",
            )

        logger.info(f"Processing attribution ID: {attribution_id}")

        # 🔹 Thread-safe access
        with logs_lock:
            log_entry = logs_dict.pop(attribution_id, None)

        if isinstance(log_entry, dict) and "logs" in log_entry:
            log_lines = log_entry["logs"]
        else:
            # Backward compatibility for existing format
            log_lines = log_entry

        job_id = attributionid_jobid_dict.pop(attribution_id, "Bad jobid")

        user_id = attributionid_userid_dict.pop(attribution_id, "")
        if user_id in cache_user_dict:
            cache_user = cache_user_dict[user_id]
        else:
            cache_user_dict[user_id] = LRUCache(1_000_000)
            cache_user = cache_user_dict[user_id]

        app_data = return_application_errors(llm, log_lines, cache_user)
        application_errors_full = [error[0] for error in app_data.application_errors_list_full]

        if XSS_FILTERING:
            application_errors_list_unique = [sanitize_xss(error) for error in app_data.application_errors_list_unique]
        else:
            application_errors_list_unique = app_data.application_errors_list_unique

        if not application_errors_full:
            error_attr = attribution_from_finished_status(app_data, application_errors_list_unique)
            return ErrorAttributionWithJobId(
                application_errors_full=error_attr.application_errors_full,
                application_errors_unique=error_attr.application_errors_unique,
                auto_resume=error_attr.auto_resume,
                auto_resume_verbose=error_attr.auto_resume_verbose,
                attribution=error_attr.attribution,
                job_id=job_id,
            )

        logger.info("Policy suggestion and Error attribution started")
        auto_resume_output, auto_resume_verbose, attribution_output, attribution_verbose, checkpoint_saved = (
            get_proposed_solution_cat(llm, app_data, config.ISOLATION, config.ATTRIBUTION, config.VERBOSE)
        )

        logger.info(f"Policy suggestion: {auto_resume_output}")

        if XSS_FILTERING:
            application_errors_full = [sanitize_xss(e) for e in application_errors_full]
            auto_resume_output = sanitize_xss(auto_resume_output)
            auto_resume_verbose = sanitize_xss(auto_resume_verbose)
            attribution_output = sanitize_xss(attribution_output)

        return ErrorAttributionWithJobId(
            application_errors_full=application_errors_full,
            application_errors_unique=application_errors_list_unique,
            auto_resume=auto_resume_output,
            auto_resume_verbose=auto_resume_verbose,
            attribution=attribution_output,
            job_id=job_id,
        )

    except Exception as e:
        logger.error(f"Error in attribution analysis: {e!s}")
        raise


def generate_attribution_id(job_id: str, user_id: str = "") -> AttributionID:
    """Generate a unique attribution ID for a job."""
    try:
        attribution_id = str(uuid.uuid4())
        attribution_id_obj = AttributionID(attribution_id=attribution_id)

        # Initialize entry with timestamp and empty logs list
        logs_dict[attribution_id] = {"timestamp": time.time(), "logs": []}

        attributionid_jobid_dict[attribution_id] = job_id
        attributionid_userid_dict[attribution_id] = user_id

        logger.info(f"Generated attribution ID {attribution_id} for job {job_id}")
        return attribution_id_obj

    except Exception as e:
        logger.error(f"Error generating attribution ID: {e!s}")
        raise


def append_logs(attribution_id: str, app_logs: AppLogs) -> AppLogsLen:
    """Append logs to an existing attribution ID."""
    try:
        if attribution_id not in attributionid_jobid_dict or attribution_id not in logs_dict:
            logger.info(f"Invalid attribution ID: {attribution_id}")
            return AppLogsLen(lines_len=0)

        entry = logs_dict[attribution_id]

        # ✅ Handle both new (dict) and old (list) formats for backward compatibility
        if isinstance(entry, dict):
            entry["logs"].extend(app_logs.lines)
            entry["timestamp"] = time.time()  # refresh timestamp
            lines = entry["logs"]
        else:
            # Old-style (list only)
            entry.extend(app_logs.lines)
            lines = entry

        logger.info(f"Appended {len(app_logs.lines)} logs to attribution ID {attribution_id}")
        return AppLogsLen(lines_len=len(lines))

    except Exception as e:
        logger.error(f"Error appending logs: {e!s}")
        raise


def main():
    # NVRx params:
    # ATTRIBUTION = False
    # VERBOSE = False
    # ISOLATION = False

    parser = argparse.ArgumentParser(description="Run attribution analysis on logs.")

    parser.add_argument("filepath", type=str, help="Path to the log file")
    parser.add_argument("--isolation", action="store_true", help="Enable ISOLATION")
    parser.add_argument("--attribution", action="store_true", help="Enable ATTRIBUTION")
    parser.add_argument("--verbose", action="store_true", help="Enable VERBOSE output")

    args = parser.parse_args()

    # Call your function with parsed args
    attribution = get_attribution_from_file(
        args.filepath,
        args.isolation,
        args.attribution,
        args.verbose,
    )


if __name__ == "__main__":
    main()
