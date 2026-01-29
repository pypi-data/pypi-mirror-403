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

import logging
import re
import time

import pandas as pd
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from logsage.auto_resume_policy.attribution_classes import ApplicationData, FinishedStatus, LRUCache  # .
from logsage.auto_resume_policy.consts import (
    BATCH_LLM_CALLS,
    BATCH_WIDTH,
    CONTEXT_SIZE,
    LLM_ENDPOINT_FAILED,
    NUMBER_LAST_LINES,
)
from logsage.auto_resume_policy.prompts import (
    template_app_checkpointing,
    template_app_error_extraction,
    template_app_error_extraction_validation,  # .
    template_app_iteration,
    template_application_crash_check,
    template_application_error_check,
    template_chunk_progress_check,
)
from logsage.auto_resume_policy.utils import (
    add_spaces_around_punctuation,
    check_checkpoint,
    check_finished,
    check_if_iteration,
    check_slurm_cancelled,
    chunk_indices,
    compress_application_log,
    convert_hex_to_special_token,
    convert_long_words_to_special_token,
    convert_numbers_to_token,  # .
    convert_paths_to_token,
    create_batches_long,
    expand_context,
    extract_answer,
    filter_early_errors,
    find_most_frequent_pattern,
    get_domain_size,
    get_regex_errors,
    get_templating,
    get_templating_multiprocessing,
    remove_not_errors,
    replace_quoted_text_with_token,
    retry_operation,
    return_not_benign,
    split_tuples_by_index_groups,
    summarize_logs,
)

# setup logger
logger = logging.getLogger(__name__)


def extract_ranks(lines: list | None = None) -> list:
    """Helper function to extract the rank

    Args:
        lines: Log lines

    Returns:
        List of ranks
    """
    if lines is None:
        lines = []

    numbers = set()
    pattern = re.compile(r"^(?:\[rank)?(\d+)]?:")

    for line in lines:
        match = pattern.match(line)
        if match:
            numbers.add(int(match.group(1)))

    return list(numbers)


def extract_numbers(lines: list | None = None) -> list:
    """Helper function to extract the rank

    Args:
        lines: Log lines

    Returns:
        List of ranks
    """
    if lines is None:
        lines = []

    numbers = set()
    pattern = re.compile(r"^(?:\[rank)?(\d+)]?:")

    domain_size_env = get_domain_size()

    for line in lines:
        match = pattern.match(line)
        if match:
            numbers.add(int(match.group(1)) // domain_size_env)

    return list(numbers)


def replace_number_with_rank(text: str) -> str:
    """Helper function to replace the rank with node number

    Args:
        text: Log line

    Returns:
        text after replacement
    """
    text = text.strip()
    match = re.match(r"^(\d+):", text)

    domain_size_env = get_domain_size()

    if match:
        number = int(match.group(1))
        new_prefix = f"node{number // domain_size_env}"
        text = new_prefix
    return text


def get_texts_for_first_unique_cluster(texts: list | None = None, cluster_ids: list | None = None) -> list:
    """Helper function to return the first lines for clustering

    Args:
        texts: Log lines
        cluster_ids: Cluster_ids

    Returns:
        list of lines by clusters ids
    """
    if texts is None:
        texts = []
    if cluster_ids is None:
        cluster_ids = []

    unique_cluster_ids = set()
    result_texts = []
    cluster_to_text = {}

    for text, cluster_id in zip(texts, cluster_ids):
        if cluster_id not in cluster_to_text:
            cluster_to_text[cluster_id] = text
        if cluster_id not in unique_cluster_ids:
            unique_cluster_ids.add(cluster_id)
            result_texts.append(text)

    return result_texts


def create_drain_clusters(
    tm_text: list | None = None, tm_text_original: list | None = None
) -> tuple[list[str], list[str], list[str], list[str], dict, dict]:
    """Helper function to return to use Drain3 for clustering

    Args:
        tm_text: Log lines
        tm_text_original: Log lines

    Returns:
        Unique log lines, Unique log patterns
    """
    if tm_text is None:
        tm_text = []
    if tm_text_original is None:
        tm_text_original = []

    actual = []
    drain_config = TemplateMinerConfig()

    drain_config.parametrize_numeric_tokens = True
    drain_config.drain_sim_th = 0.4
    drain_config.depth = 4
    drain_config.max_clusters = 100

    # Add masking instructions for numeric patterns
    # Let drain3 handle numeric patterns naturally without explicit masking
    # This produces cleaner templates with <*> for varying parts
    drain_config.masking_instructions = []

    model = TemplateMiner(config=drain_config)

    clusters = []
    for entry in tm_text:
        cluster = model.add_log_message(entry)
        actual.append(cluster.get("template_mined", 0) if isinstance(cluster, dict) else 0)
        clusters.append(cluster.get("cluster_id", 0) if isinstance(cluster, dict) else "")

    tm_text = get_texts_for_first_unique_cluster(tm_text, clusters)

    unique_clusters = list(pd.unique(clusters))

    tm_text_cleaned = get_templating(tm_text)
    tm_text_pattern = tm_text_cleaned.copy()

    tm_text_cleaned_original = get_templating(tm_text_original)
    tm_text_pattern_original = tm_text_cleaned_original.copy()

    seen = set()
    new_text_list = []
    new_pattern_list = []

    for text, pattern in zip(tm_text, tm_text_pattern):
        if pattern not in seen:
            new_text_list.append(text)
            new_pattern_list.append(pattern)
            seen.add(pattern)

    # Return the filtered lists
    tm_text = new_text_list
    tm_text_pattern = new_pattern_list
    error_full = tm_text.copy()

    tm_text_short_original = [text[:BATCH_WIDTH] for text in tm_text_original]
    dict_text_pattern = dict(zip(tm_text_short_original, tm_text_pattern_original))
    dict_text_pattern_long = dict(zip(tm_text_original, tm_text_pattern_original))

    cluster_template_dict = {}
    for i in range(len(tm_text_cleaned)):
        cluster_template_dict[unique_clusters[i]] = tm_text_cleaned[i]

    return tm_text, tm_text_pattern, tm_text_pattern_original, error_full, dict_text_pattern, dict_text_pattern_long


def create_clusters(
    tm_text: list | None = None, tm_text_original: list | None = None
) -> tuple[list[str], list[str], list[str], list[str], dict, dict]:
    """Helper function to return to use Drain3 for clustering

    Args:
        tm_text: Log lines
        tm_text_original: Log lines

    Returns:
        Unique log lines, Unique log patterns
    """
    if tm_text is None:
        tm_text = []
    if tm_text_original is None:
        tm_text_original = []

    # tm_text_cleaned = get_templating(tm_text)
    # tm_text_pattern = tm_text_cleaned.copy()

    tm_text_cleaned_original = get_templating(tm_text_original)
    tm_text_pattern_original = tm_text_cleaned_original.copy()

    pattern_map = dict(zip(tm_text_original, tm_text_pattern_original))
    tm_text_pattern = [pattern_map[line] for line in tm_text]

    seen = set()
    new_text_list = []
    new_pattern_list = []

    for text, pattern in zip(tm_text, tm_text_pattern):
        if pattern not in seen:
            new_text_list.append(text)
            new_pattern_list.append(pattern)
            seen.add(pattern)

    # Return the filtered lists
    tm_text = new_text_list
    tm_text_pattern = new_pattern_list
    error_full = tm_text.copy()

    tm_text_short_original = [text[:BATCH_WIDTH] for text in tm_text_original]
    dict_text_pattern = dict(zip(tm_text_short_original, tm_text_pattern_original))
    dict_text_pattern_long = dict(zip(tm_text_original, tm_text_pattern_original))

    return tm_text, tm_text_pattern, tm_text_pattern_original, error_full, dict_text_pattern, dict_text_pattern_long


def create_clusters_without_drain(
    tm_text: list | None = None, tm_text_original: list | None = None
) -> tuple[list[str], list[str], list[str], list[str], dict, dict]:
    """Helper function to use Drain3 for clustering"""
    if tm_text is None:
        tm_text = []
    if tm_text_original is None:
        tm_text_original = []

    tm_text_cleaned = get_templating_multiprocessing(tm_text)
    tm_text_pattern = tm_text_cleaned.copy()

    dict_text_pattern_long = dict(zip(tm_text, tm_text_pattern))

    seen = set()
    new_text_list, new_pattern_list = [], []
    for text, pattern in zip(tm_text, tm_text_pattern):
        if pattern not in seen:
            new_text_list.append(text)
            new_pattern_list.append(pattern)
            seen.add(pattern)

    tm_text, tm_text_pattern = new_text_list, new_pattern_list

    tm_text_pattern_original = []
    for i in range(len(tm_text_original)):
        tm_text_pattern_original.append(dict_text_pattern_long[tm_text_original[i]])

    return tm_text, tm_text_pattern, tm_text_pattern_original, dict_text_pattern_long


def return_relevant_lines(errors_list: list | None = None, stacktrace_lines: list | None = None) -> list:
    """Helper function to return the relevant stacktraces

    Args:
        errors_list: List errors
        stacktrace_lines: Log lines

    Returns:
        Stacktraces lines
    """
    if errors_list is None:
        errors_list = []
    if stacktrace_lines is None:
        stacktrace_lines = []

    pattern = re.compile(r"^\d+: .+")
    return [
        line
        for line in stacktrace_lines
        if pattern.match(line) and extract_ranks([line])[0] in extract_ranks(errors_list)
    ]


def return_stacktrace(unified_errors_list: list, last_iteration_i: int, tm_text_original: list) -> dict:
    """Helper function to return the stacktraces

    Args:
        unified_errors_list: List (log, pattern, i)
        tm_text_original: Log lines

    Returns:
        Dict of stacktraces
    """
    errors_patterns_raw = {}
    errors_nodes = {}
    errors_nodes_location = {}
    for error in unified_errors_list:
        if error[1] in errors_nodes:
            errors_nodes[error[1]].append(error[0])
        else:
            errors_nodes[error[1]] = [error[0]]
        if error[1] not in errors_nodes_location:
            errors_nodes_location[error[1]] = error[2]
    errors_nodes_amount = {}
    for error in errors_nodes:
        errors_nodes_amount[error] = extract_numbers(errors_nodes[error])
    traceback_dict = {}
    for error in errors_nodes_amount:
        if len(errors_nodes_amount[error]) > 0 and len(errors_nodes_amount[error]) < 4:
            traceback_dict[error] = return_relevant_lines(
                errors_nodes[error], tm_text_original[errors_nodes_location[error] - 20 : errors_nodes_location[error]]
            )
    error_patterns_after_iteration = []
    if last_iteration_i != -1:
        for error in unified_errors_list:
            if error[2] > last_iteration_i:
                error_patterns_after_iteration.append((error[0], error[1], error[2]))
    else:
        for error in unified_errors_list:
            error_patterns_after_iteration.append((error[0], error[1], error[2]))
    if len(pd.unique([error[1] for error in error_patterns_after_iteration])) == 1:
        traceback_dict[error_patterns_after_iteration[0][1]] = return_relevant_lines(
            [error[0] for error in error_patterns_after_iteration],
            tm_text_original[error_patterns_after_iteration[0][2] - 20 : error_patterns_after_iteration[0][2]],
        )

    return traceback_dict


# Precompile regex
RANK_RE = re.compile(r"^\[rank(\d+)\]:(.*)")


def add_rank_in_beginning(tm_text: list | None = None) -> list:
    """Helper function to add rank in the beginning of the line

    Args:
        tm_text: Log lines

    Returns:
        Log lines with rank in the beginning
    """
    if tm_text is None:
        tm_text = []

    new_lines = []
    for line in tm_text:
        match = RANK_RE.match(line)
        if match:
            rank_num = match.group(1)
            rest_of_line = match.group(0)  # full matched line
            new_line = f"{rank_num}: {rest_of_line}"
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    return new_lines


def return_application_errors(llm: ChatNVIDIA, tm_text: list, cache_dict: LRUCache) -> ApplicationData:
    """Function returns application errors

    Args:
        tm_text: Log lines
        cache_dict: cache

    Returns:
        Errors log lines with dict of stacktraces
    """
    if NUMBER_LAST_LINES > -1 and len(tm_text) > NUMBER_LAST_LINES:
        logger.info("Input log exceeds NUMBER_LAST_LINES=%s; truncating tail only", NUMBER_LAST_LINES)

    if NUMBER_LAST_LINES > -1:
        tm_text = tm_text[-NUMBER_LAST_LINES:]

    tm_text = [text.rstrip("\n") for text in tm_text]
    tm_text = [text.strip() for text in tm_text]

    tm_text = add_rank_in_beginning(tm_text)

    # Precompile regex patterns
    NUM_COLON_RE = re.compile(r"^\d+:$")
    NON_WORD_RE = re.compile(r"^[^\w\s]+$")
    NUM_COLON_NONWORD_RE = re.compile(r"^\d+:[^\w\s]+$")

    # Set of substrings to ignore
    IGNORE_SUBSTRINGS = {
        "INFO:nvidia_resiliency_ext",
        "WARNING:nvidia_resiliency_ext",
        "RankShouldRestart('Interruption",
        "[workload:",
        "NCCL WARN [",
        "[ft_launcher",
        "Heimdall telemetry is enabled but package is not installed",
    }

    def filter_lines(lines):
        filtered = []
        for line in lines:
            stripped = line.replace(" ", "").strip()

            # Skip lines matching numeric or non-word patterns
            if (
                NUM_COLON_RE.fullmatch(stripped)
                or NON_WORD_RE.fullmatch(stripped)
                or NUM_COLON_NONWORD_RE.fullmatch(stripped)
            ):
                continue

            # Skip lines containing ignored substrings
            if any(substr in line for substr in IGNORE_SUBSTRINGS):
                continue

            filtered.append(line)

        return filtered

    # Apply filter
    tm_text = filter_lines(tm_text)

    # If iteration started - remove all the logs before
    tm_text_iteration = []
    tm_text_iteration_filter = []
    iteration_flag = False
    for text in tm_text:
        tm_text_iteration.append(text)
        if not iteration_flag:
            tm_text_iteration_filter.append(text)
        if check_if_iteration(text):
            if not iteration_flag:
                tm_text_iteration = [text]
                iteration_flag = True

    if not iteration_flag:
        tm_text_iteration_filter = []

    tm_text = tm_text_iteration
    tm_text_original = tm_text.copy()

    # Precompile once
    NUMBER_DIVISION_RE = re.compile(r"^\s*\d+(?:\.\d+)?\s*/\s*\d+(?:\.\d+)?\s*$")

    # Substring-like error regex (no \b boundaries)
    ERROR_RE = re.compile(
        r"(?:"
        r"err|fail|ab|critical|panic|death|close|crash|fault|oops|assert|"
        r"corrupt|illegal|out|un|over|bug|fix|broken|break|hang|hung|stuck|halt|"
        r"stop|term|dis|mis|wrong|issue|problem|down|glitch|bottleneck|flaky|de|drop|oom|"
        r"hardware|kernel|null|access|permission|connection|network|ex|quota|bad|config|"
        r"loss|fatal|dead|lock|leak|no|na|slow|delay|block|re|pause|froze|"
        r"freeze|back|off|stale|exit|lost|damage|mal|warn|forbid|broke|in|kill|checkpoint"
        r")",
        re.IGNORECASE,
    )

    def line_has_error_word(line: str) -> bool:
        """Detect numeric-division or error-indicative log lines (substring-like)."""
        stripped = line.strip()
        return bool(NUMBER_DIVISION_RE.match(stripped) or ERROR_RE.search(stripped))

    tm_text = [line for line in tm_text if line_has_error_word(line)]

    # Create templates to "unique" logs
    tm_text, tm_text_pattern, tm_text_pattern_original, error_full, dict_text_pattern, dict_text_pattern_long = (
        create_clusters(tm_text, tm_text_original)
    )

    tm_text_iteration_check = [tm_text[i] for i in range(len(tm_text)) if "<NUMBER> / <NUMBER>" in tm_text_pattern[i]]

    tm_text_iteration_pattern_check = [
        tm_text_pattern[i] for i in range(len(tm_text_pattern)) if "<NUMBER> / <NUMBER>" in tm_text_pattern[i]
    ]

    tm_text_iteration_pattern_check = [
        tm_text_iteration_pattern_check[i]
        for i in range(len(tm_text_iteration_pattern_check))
        if not check_if_iteration(tm_text_iteration_check[i])
    ]
    tm_text_iteration_check = [
        tm_text_iteration_check[i]
        for i in range(len(tm_text_iteration_check))
        if not check_if_iteration(tm_text_iteration_check[i])
    ]

    tm_text_iteration_check = tm_text_iteration_check[-BATCH_LLM_CALLS:]
    tm_text_iteration_pattern_check = tm_text_iteration_pattern_check[-BATCH_LLM_CALLS:]

    prompt_iteration = ChatPromptTemplate.from_template(template_app_iteration)

    application_llm_iteration = {"question": RunnablePassthrough()} | prompt_iteration | llm | StrOutputParser()

    # First error extraction
    s_time = time.time()
    iteration_answer_list = retry_operation(lambda: application_llm_iteration.batch(tm_text_iteration_check))
    logger.info("detect iteration latency: %s", time.time() - s_time)

    if iteration_answer_list == LLM_ENDPOINT_FAILED:
        return ApplicationData(
            application_errors_list_full=[],
            application_errors_list_unique=[],
            tm_text_unique=tm_text,
            finished=FinishedStatus.LLM_FAILURE,
            application_errors_list_iteration=[],
            traceback_dict=[],
            training_started="no",
            iteration_patterns=[],
            checkpoint_saved=False,
            original_text=tm_text_original,
            progressed_indices=[],
            pattern_before_max="",
        )

    tm_text_iteration_pattern_verify = []
    tm_text_iteration_verify = []
    for i, iteration_answer in enumerate(iteration_answer_list):
        if iteration_answer.lower() == "yes":
            tm_text_iteration_pattern_verify.append(tm_text_iteration_pattern_check[i])
            tm_text_iteration_verify.append(tm_text_iteration_check[i])

    tm_text_iteration_pattern = []
    tm_text_iteration = []
    if not iteration_flag and len(tm_text_iteration_pattern_verify) > 0:
        flag_iteration = False
        for i, line_pattern in enumerate(tm_text_pattern_original):
            if line_pattern in tm_text_iteration_pattern_verify and not flag_iteration:
                tm_text_iteration = [tm_text_original[i]]
                tm_text_iteration_pattern = [line_pattern]
                flag_iteration = True
                continue
            if flag_iteration:
                tm_text_iteration.append(tm_text_original[i])
                tm_text_iteration_pattern.append(line_pattern)

        # Keep track of seen patterns
        seen = set()
        new_text_list = []
        new_pattern_list = []

        for text, pattern in zip(tm_text_iteration, tm_text_iteration_pattern):
            if pattern not in seen:
                new_text_list.append(text)
                new_pattern_list.append(pattern)
                seen.add(pattern)

        # Return the filtered lists
        tm_text = new_text_list
        tm_text_pattern = new_pattern_list
        error_full = tm_text.copy()

        tm_text_short = [text[:BATCH_WIDTH] for text in tm_text]
        dict_text_pattern = dict(zip(tm_text, tm_text_pattern))
        dict_text_pattern_long = dict(zip(tm_text, tm_text_pattern))

    checkpointing_lines = [line for line in tm_text if "checkpoint" in line]
    checkpointing_patterns = [line for line in tm_text_pattern if "checkpoint" in line]

    checkpointing_lines = checkpointing_lines[-BATCH_LLM_CALLS:]
    checkpointing_patterns = checkpointing_patterns[-BATCH_LLM_CALLS:]

    prompt_checkpointing = ChatPromptTemplate.from_template(template_app_checkpointing)

    application_llm_checkpointing = {"question": RunnablePassthrough()} | prompt_checkpointing | llm | StrOutputParser()

    # First error extraction
    s_time = time.time()
    checkpointing_answer_list = retry_operation(lambda: application_llm_checkpointing.batch(checkpointing_lines))
    logger.info("detect checkpointing latency: %s", time.time() - s_time)

    if checkpointing_answer_list == LLM_ENDPOINT_FAILED:
        return ApplicationData(
            application_errors_list_full=[],
            application_errors_list_unique=[],
            tm_text_unique=tm_text,
            finished=FinishedStatus.LLM_FAILURE,
            application_errors_list_iteration=[],
            traceback_dict=[],
            training_started="no",
            iteration_patterns=[],
            checkpoint_saved=False,
            original_text=tm_text_original,
            progressed_indices=[],
            pattern_before_max="",
        )

    checkpointing_lines_verified = [
        checkpointing_lines[i] for i in range(len(checkpointing_lines)) if checkpointing_answer_list[i].lower() == "yes"
    ]
    checkpointing_patterns_verified = [
        checkpointing_patterns[i]
        for i in range(len(checkpointing_patterns))
        if checkpointing_answer_list[i].lower() == "yes"
    ]

    logger.info(f"Number of unique lines {len(tm_text)}")
    logger.info(f"Number of lines in cache {cache_dict.length()}")

    # Find errors based regex
    tm_text_benign_error = remove_not_errors(tm_text)

    errors_list_regex = get_regex_errors(tm_text_benign_error)

    tm_text_template_remain = [
        tm_text_pattern[i]
        for i in range(len(tm_text_pattern))
        if tm_text[i] not in errors_list_regex and tm_text[i] in tm_text_benign_error
    ]

    tm_text_remain = [
        tm_text[i]
        for i in range(len(tm_text))
        if tm_text[i] not in errors_list_regex and tm_text[i] in tm_text_benign_error
    ]

    error_list_cache = []
    error_list_cache_raw = []
    benign_list_cache = []

    # Find errors based cache
    for i, text_pattern in enumerate(tm_text_template_remain):
        if cache_dict.get(text_pattern) != -1 and cache_dict.get(text_pattern) == "yes":
            error_list_cache.append(text_pattern)
            error_list_cache_raw.append(tm_text_remain[i])
        elif cache_dict.get(text_pattern) != -1 and cache_dict.get(text_pattern) == "no":
            benign_list_cache.append(text_pattern)

    # Unknown logs - check by LLM
    tm_text_llm_pattern = [
        tm_text_template_remain[i]
        for i in range(len(tm_text_template_remain))
        if tm_text_template_remain[i] not in error_list_cache and tm_text_template_remain[i] not in benign_list_cache
    ]
    tm_text_llm = [
        tm_text_remain[i]
        for i in range(len(tm_text_remain))
        if tm_text_template_remain[i] not in error_list_cache and tm_text_template_remain[i] not in benign_list_cache
    ]

    error_list_batch = []
    batch_list = []

    # Create batches for errors extraction based LLM
    if len(tm_text_llm) > 0:
        batch_list, batch_list_pattern, batch_list_long = create_batches_long(
            tm_text_llm, tm_text_llm_pattern, max_batch_length=BATCH_WIDTH
        )

        prompt = ChatPromptTemplate.from_template(template_app_error_extraction)

        application_llm_error_extraction = {"question": RunnablePassthrough()} | prompt | llm | StrOutputParser()

        # batch_list = batch_list[-BATCH_LLM_CALLS:]

        # s_time = time.time()
        # batch_answer = retry_operation(lambda: application_llm_error_extraction.batch(batch_list))
        # logger.info("detect errors chunks latency: %s", time.time() - s_time)

        ERROR_PATTERN = re.compile(
            r"""
            ^\s*"?                                   # optional opening quote
            \d+                                     # <num>
            :
            (?:
                \s*\[rank\d+\]:\s*                  # with rank
                [A-Za-z][A-Za-z0-9_]*(Error|Exception):?
                |
                \s+
                [A-Za-z][A-Za-z0-9_]*(Error|Exception):  # no rank → colon REQUIRED
            )
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        def has_error(s: str) -> bool:
            return any(ERROR_PATTERN.search(line) for line in s.splitlines())

        batch_list = batch_list[-BATCH_LLM_CALLS:]

        batch_answer = [None] * len(batch_list)
        llm_inputs = []
        llm_indices = []

        for i, item in enumerate(batch_list):
            if has_error(item):
                batch_answer[i] = "yes"
            else:
                llm_indices.append(i)
                llm_inputs.append(item)

        if llm_inputs:
            s_time = time.time()
            llm_answers = retry_operation(lambda: application_llm_error_extraction.batch(llm_inputs))
            logger.info("detect errors chunks latency: %s", time.time() - s_time)

            for idx, ans in zip(llm_indices, llm_answers):
                batch_answer[idx] = ans

        if batch_answer == LLM_ENDPOINT_FAILED:
            return ApplicationData(
                application_errors_list_full=[],
                application_errors_list_unique=[],
                tm_text_unique=tm_text,
                finished=FinishedStatus.LLM_FAILURE,
                application_errors_list_iteration=[],
                traceback_dict=[],
                training_started="no",
                iteration_patterns=[],
                checkpoint_saved=False,
                original_text=tm_text_original,
                progressed_indices=[],
                pattern_before_max="",
            )

        # Continue just with batches with errors
        errors_list = []
        errors_list_long = []
        batch_answer_tmp = []
        for i, answer in enumerate(batch_answer):
            if "yes" in answer.lower():
                batch_answer_tmp.append(batch_list[i])
                batch_errors = [line for line in batch_list[i].split("\n") if line.strip()]
                errors_list.extend(batch_errors)
                errors_list_long.extend([line for line in batch_list_long[i].split("\n") if line.strip()])

        errors_list = [error for error in errors_list if len(error) > 3]

        # Error extraction based LLM
        prompt = ChatPromptTemplate.from_template(template_app_error_extraction_validation)
        application_llm_error_extraction_validation = (
            {"question": RunnablePassthrough()} | prompt | llm | StrOutputParser()
        )

        errors_list = errors_list[-BATCH_LLM_CALLS:]

        # Validate errors
        s_time = time.time()
        batch_answer = retry_operation(lambda: application_llm_error_extraction_validation.batch(errors_list))
        logger.info("detect errors 1-1 latency: %s", time.time() - s_time)

        if batch_answer == LLM_ENDPOINT_FAILED:
            return ApplicationData(
                application_errors_list_full=[],
                application_errors_list_unique=[],
                tm_text_unique=tm_text,
                finished=FinishedStatus.LLM_FAILURE,
                application_errors_list_iteration=[],
                traceback_dict=[],
                training_started="no",
                iteration_patterns=[],
                checkpoint_saved=False,
                original_text=tm_text_original,
                progressed_indices=[],
                pattern_before_max="",
            )

        error_list_batch = [errors_list[i] for i in range(len(errors_list)) if "yes" in batch_answer[i].lower()]
        benign_list_pattern_cache = [
            dict_text_pattern[errors_list[i]] for i in range(len(errors_list)) if "no" in batch_answer[i].lower()
        ]

        errors_list_pattern_cache = [
            dict_text_pattern[errors_list[i]] for i in range(len(errors_list)) if "yes" in batch_answer[i].lower()
        ]

        for error_pattern in errors_list_pattern_cache:
            cache_dict.put(error_pattern, "yes")

        for benign_pattern in benign_list_pattern_cache:
            cache_dict.put(benign_pattern, "no")

    # Errors from regex, cache and LLM
    errors_list = [
        error_full[i]
        for i in range(len(error_full))
        if error_full[i] in error_list_batch
        or error_full[i] in errors_list_regex
        or error_full[i] in error_list_cache_raw
    ]

    errors_list_unique = errors_list.copy()

    errors_list_pattern = [dict_text_pattern_long[errors_list_unique[i]] for i in range(len(errors_list_unique))]

    # Extract all the errors - not just unique
    unified_errors_list = []
    for l in range(len(tm_text_pattern_original)):
        if tm_text_pattern_original[l] in errors_list_pattern and return_not_benign(tm_text_original[l]):
            unified_errors_list.append((tm_text_original[l], tm_text_pattern_original[l], l))

    # Analyze the logs based slurm logs
    unified_errors_list_temp = []
    for error in unified_errors_list:
        if "slurmstepd" in error[0]:
            if "CANCELLED AT" in error[0] and "DUE TO TIME LIMIT" in error[0]:
                break
            unified_errors_list_temp.append(error)
        unified_errors_list_temp.append(error)
    unified_errors_list = unified_errors_list_temp

    if len(unified_errors_list) > 0:
        error_flag = check_real_error(llm, unified_errors_list)
    else:
        error_flag = "no"

    if error_flag == LLM_ENDPOINT_FAILED:
        error_flag = "yes"

    error_flag = error_flag.lower() == "yes"

    progressed_indices = []
    progressed_patterns = []

    if error_flag:
        indices = [error[2] for error in unified_errors_list]
        error_groups = chunk_indices(indices)
        unified_errors_error_groups = split_tuples_by_index_groups(error_groups, unified_errors_list)

        application_log_chunks = [
            summarize_logs(tm_text_original, unified_errors_error_group, [], max_len=CONTEXT_SIZE / 10)
            for unified_errors_error_group in unified_errors_error_groups
        ]

        prompt_progress = ChatPromptTemplate.from_template(template_chunk_progress_check)
        application_llm_progress = {"question": RunnablePassthrough()} | prompt_progress | llm | StrOutputParser()

        s_time = time.time()
        progress_answer_list = retry_operation(lambda: application_llm_progress.batch(application_log_chunks))
        logger.info("detect errors progressed latency: %s", time.time() - s_time)
        if progress_answer_list == LLM_ENDPOINT_FAILED:
            progress_answer_list = ["failed"] * len(application_log_chunks)

        failed_indices = [
            unified_errors_error_groups[i]
            for i in range(len(unified_errors_error_groups))
            if progress_answer_list[i].lower() != "progressed"
        ]
        progressed_indices = [
            error_groups[i] for i in range(len(error_groups)) if progress_answer_list[i].lower() == "progressed"
        ]
        progressed_indices = [x for sublist in progressed_indices for x in sublist]
        unified_errors_list = [item for sublist in failed_indices for item in sublist]
        progressed_patterns = [
            unified_errors_error_groups[i]
            for i in range(len(unified_errors_error_groups))
            if progress_answer_list[i].lower() == "progressed"
        ]
        progressed_patterns = [error[0][1] for error in progressed_patterns]

    app_log_full = "\n\n".join(tm_text_original)
    finished = check_finished(app_log_full)
    finished = "yes" in finished.lower()

    checkpoint_saved = check_checkpoint(app_log_full) or len(checkpointing_lines_verified) > 0

    # Add all the logs that are an indication for iteration
    unified_errors_iteration = unified_errors_list.copy()
    training_started = "JOB NOT STARTED"
    last_iteration_i = -1
    list_iteration_indices = []
    for i, text in enumerate(tm_text_original):
        if check_if_iteration(text) or tm_text_pattern_original[i] in tm_text_iteration_pattern_verify:
            training_started = "JOB STARTED"
            pattern = convert_paths_to_token(text)
            pattern = replace_quoted_text_with_token(pattern)
            pattern = add_spaces_around_punctuation(pattern)
            pattern = convert_hex_to_special_token(pattern)
            pattern = convert_long_words_to_special_token(pattern)
            pattern = convert_numbers_to_token(pattern)
            unified_errors_iteration.append((text, pattern, i))
            list_iteration_indices.append(i)
            last_iteration_i = i

    logger.info("Job status: " + training_started)

    unified_errors_cp = []
    unified_errors_iteration_cp = []
    last_cp_idx = -1
    for i, text in enumerate(tm_text_original):
        pattern = convert_paths_to_token(text)
        pattern = replace_quoted_text_with_token(pattern)
        pattern = add_spaces_around_punctuation(pattern)
        pattern = convert_hex_to_special_token(pattern)
        pattern = convert_long_words_to_special_token(pattern)
        pattern = convert_numbers_to_token(pattern)

        if pattern in checkpointing_patterns_verified:
            last_cp_idx = i

    list_pattern_before_cp = [
        pattern for i, pattern in enumerate(tm_text_pattern_original) if i < last_cp_idx and "NCCL WARN" in pattern
    ]

    tm_text_iteration_filter_original = tm_text_iteration_filter.copy()
    tm_text_iteration_filter = [line for line in tm_text_iteration_filter if line_has_error_word(line)]

    # Create templates to "unique" logs
    (
        tm_text_iteration_filter,
        tm_text_iteration_filter_pattern,
        tm_text_iteration_filter_pattern_original,
        error_full_filter,
        dict_text_pattern_filter,
        dict_text_pattern_long_filter,
    ) = create_clusters(tm_text_iteration_filter, tm_text_iteration_filter_original)

    for error in unified_errors_iteration:
        if "NET/" not in error[0] and error[1] in [
            pattern for pattern in progressed_patterns if "NCCL WARN" in pattern
        ]:
            continue
        if "NET/" not in error[0] and error[1] in [
            pattern for pattern in tm_text_iteration_filter_pattern if "NCCL WARN" in pattern
        ]:
            continue
        if (
            last_cp_idx == -1
            or (error[2] > last_cp_idx and error[1] not in list_pattern_before_cp)
            or (error[2] > last_cp_idx and "NET/" in error[0])
        ):
            # if last_cp_idx == -1 or error[2] > last_cp_idx:
            unified_errors_iteration_cp.append((error[0], error[1], error[2]))

    for error in unified_errors_list:
        if "NET/" not in error[0] and error[1] in [
            pattern for pattern in progressed_patterns if "NCCL WARN" in pattern
        ]:
            continue
        if "NET/" not in error[0] and error[1] in [
            pattern for pattern in tm_text_iteration_filter_pattern if "NCCL WARN" in pattern
        ]:
            continue
        if (
            last_cp_idx == -1
            or (error[2] > last_cp_idx and error[1] not in list_pattern_before_cp)
            or (error[2] > last_cp_idx and "NET/" in error[0])
        ):
            # if last_cp_idx == -1 or error[2] > last_cp_idx:
            unified_errors_cp.append((error[0], error[1], error[2]))

    unified_errors_list = sorted(unified_errors_cp, key=lambda x: x[2])
    unified_errors_iteration = sorted(unified_errors_iteration_cp, key=lambda x: x[2])

    error_before_iteration = filter_early_errors(unified_errors_list, list_iteration_indices)

    pattern_candidates = find_most_frequent_pattern(error_before_iteration)
    pattern_before_max = pattern_candidates[0] if pattern_candidates else ""

    # Add traceback
    traceback_dict = return_stacktrace(unified_errors_list, last_iteration_i, tm_text_original)

    logger.info("Error extraction ended")

    if error_flag:
        filtered_text = expand_context(tm_text_original, unified_errors_list, max_len=CONTEXT_SIZE)

        filtered_text = "\n".join(line for line in filtered_text.split("\n"))[-CONTEXT_SIZE:]
        crash_flag = check_crash(llm, filtered_text)

        if crash_flag == LLM_ENDPOINT_FAILED:
            return ApplicationData(
                application_errors_list_full=[],
                application_errors_list_unique=[],
                tm_text_unique=tm_text,
                finished=FinishedStatus.LLM_FAILURE,
                application_errors_list_iteration=[],
                traceback_dict=[],
                training_started="no",
                iteration_patterns=[],
                checkpoint_saved=checkpoint_saved,
                original_text=tm_text_original,
                progressed_indices=[],
                pattern_before_max=pattern_before_max,
            )
        compressed_app = "\n".join(tm_text_original)

        if (
            crash_flag.lower() == "no"
            and "slurmstepd" in compressed_app
            and "CANCELLED AT" in compressed_app
            and "DUE TO NODE FAILURE" not in compressed_app
        ):
            return ApplicationData(
                application_errors_list_full=[],
                application_errors_list_unique=[
                    error for error in errors_list_unique if "slurmstepd" in error and "CANCELLED AT" in error
                ],
                tm_text_unique=tm_text,
                finished=FinishedStatus.SLURM_CANCELLED,
                application_errors_list_iteration=[],
                traceback_dict=[],
                training_started="no",
                iteration_patterns=[],
                checkpoint_saved=checkpoint_saved,
                original_text=tm_text_original,
                progressed_indices=[],
                pattern_before_max=pattern_before_max,
            )

        crash_flag = crash_flag.lower() == "yes" or (
            "slurmstepd" in compressed_app
            and ("CANCELLED AT" in compressed_app or "DUE TO NODE FAILURE" in compressed_app)
            and "DUE TO TIME LIMIT" not in compressed_app
        )

    else:
        crash_flag = False

    logger.info("Error extraction ended")

    if not finished and error_flag and crash_flag:
        # unified_errors_list = [error for error in unified_errors_list if 'caught collective operation timeout:' not in error[0]]
        # unified_errors_iteration = [error for error in unified_errors_iteration if 'caught collective operation timeout:' not in error[0]]
        # errors_list_unique = [error for error in errors_list_unique if 'caught collective operation timeout:' not in error]
        return ApplicationData(
            application_errors_list_full=unified_errors_list,
            application_errors_list_unique=errors_list_unique,
            tm_text_unique=tm_text,
            finished=FinishedStatus.WITH_ERRORS,
            application_errors_list_iteration=unified_errors_iteration,
            traceback_dict=traceback_dict,
            training_started=training_started,
            iteration_patterns=tm_text_iteration_pattern_verify,
            checkpoint_saved=checkpoint_saved,
            original_text=tm_text_original,
            progressed_indices=progressed_indices,
            pattern_before_max=pattern_before_max,
        )

    finish_reason = check_slurm_cancelled(unified_errors_list, tm_text_original)
    if finished:
        finish_reason = FinishedStatus.TRAINING_DONE

    return ApplicationData(
        application_errors_list_full=unified_errors_list,
        application_errors_list_unique=errors_list_unique,
        tm_text_unique=tm_text,
        finished=finish_reason,
        application_errors_list_iteration=unified_errors_iteration,
        traceback_dict=traceback_dict,
        training_started=training_started,
        iteration_patterns=tm_text_iteration_pattern_verify,
        checkpoint_saved=checkpoint_saved,
        original_text=tm_text_original,
        progressed_indices=progressed_indices,
        pattern_before_max=pattern_before_max,
    )


def check_crash(llm: ChatNVIDIA, application_log: str) -> str:
    """Function uses LLM to decide if the errors are real errors

    Args:
        application_log: str

    Returns:
        'Yes', or 'No'
    """
    application_errors_log = application_log.replace("{", "[").replace("}", "]")

    template_application_error = (
        template_application_crash_check
        + f"""\nThese are the log lines:
"
{application_errors_log}
"
"""
    )
    prompt_application = PromptTemplate.from_template(template_application_error)

    application_app = (
        {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
        | prompt_application
        | llm
        | StrOutputParser()
    )

    s_time = time.time()
    result_app_error = retry_operation(lambda: application_app.invoke(template_application_error))
    logger.info("detect crash latency: %s", time.time() - s_time)

    result_app_error = extract_answer(result_app_error)

    return result_app_error


def check_real_error(llm: ChatNVIDIA, application_errors_list_full: list | None = None) -> str:
    """Function uses LLM to decide if the errors are real errors

    Args:
        application_errors_list_full: List (log, pattern, i)

    Returns:
        'Yes', or 'No'
    """
    if application_errors_list_full is None:
        application_errors_list_full = []

    application_log = compress_application_log(application_errors_list_full)
    application_errors_log = application_log.replace("{", "[").replace("}", "]")

    template_application_error = (
        template_application_error_check
        + f"""
                    These are the log line:
                    "
                    {application_errors_log}
                    "
                    """
    )
    prompt_application = PromptTemplate.from_template(template_application_error)

    application_app = (
        {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
        | prompt_application
        | llm
        | StrOutputParser()
    )

    s_time = time.time()
    if (
        "slurmstepd" in application_errors_log
        and "CANCELLED AT" in application_errors_log
        and "DUE TO NODE FAILURE" in application_errors_log
    ):
        result_app_error = "yes"
    else:
        result_app_error = retry_operation(lambda: application_app.invoke(template_application_error))
    logger.info("verify errors latency: %s", time.time() - s_time)

    result_app_error = extract_answer(result_app_error)

    return result_app_error
