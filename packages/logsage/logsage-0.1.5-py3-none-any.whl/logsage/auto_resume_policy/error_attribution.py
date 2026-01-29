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

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from logsage.auto_resume_policy.attribution_classes import ApplicationData  # .
from logsage.auto_resume_policy.consts import (
    CONTEXT_SIZE,
    HARDWARE_THR_LINE,
    ISOLATION_COUNT,
    LLM_ENDPOINT_FAILED,
    POLICIES,  # .
)
from logsage.auto_resume_policy.prompts import (
    attribution_validation,
    cordon_node_global_1o1_template_num,
    cordon_node_global_template_num,
    hardware_prompt,
    primary_secondary_lists_justification,
    suggest_no_checkpoint_restart,
    suggest_no_checkpoint_stop,
    suggest_yes_checkpoint_restart,
    suggest_yes_checkpoint_stop,
    template_policy_instructions_output_format,
    template_policy_instructions_training_not_started,
    template_policy_instructions_training_started,
)
from logsage.auto_resume_policy.utils import (
    add_instruction_rule,
    add_instruction_rule_at_index,
    check_if_iteration,
    check_less_three,
    extract_attribution_explanation,  # .
    get_gpu_rank,
    get_hardware_regex_errors,
    node_to_rank,
    retry_operation,
    sanitize_log_text,
    summarize_logs,
)

# setup uvicorn logger
logger = logging.getLogger(__name__)


def check_end_iteration(application_log, application_errors_list_iteration, iteration_patterns):
    application_log_lines = application_log.split("\n")
    # Check if all lines return True
    line_to_pattern = {line: pattern for line, pattern, _ in application_errors_list_iteration}
    list_items = [
        check_if_iteration(line, line_to_pattern[line], iteration_patterns)
        for line in application_log_lines
        if line in line_to_pattern
    ]
    all_iteration = all(list_items)
    return all_iteration and len(list_items) > 0


def parse_text_to_dict(text: str) -> dict:
    """Parses a formatted text into a dictionary.

    Args:
        text (str): The input text containing key-value pairs.

    Returns:
        dict: Parsed dictionary with categories as keys and their corresponding values.
    """
    pattern = r"'(.*?)':\s*(\d+)"  # Regex pattern to extract key-value pairs
    parsed_dict = {match[0]: int(match[1]) for match in re.findall(pattern, text)}
    return parsed_dict


def get_first_strings(tuples_list: list | None = None) -> tuple[list, list]:
    """Helper function returns error lines and patterns

    Args:
        tuples_list: List (log, pattern, i)

    Returns:
        2 lists: errors, patterns
    """
    if tuples_list is None:
        tuples_list = []

    unique_templates = {}

    for string, template, i in tuples_list:
        if template not in unique_templates:
            unique_templates[template] = string  # Store first occurrence

    return list(unique_templates.values()), list(unique_templates.keys())


def get_attribution_infra(llm, app_data):
    # Create the log based errors, iterations and stacktraces to LLM context size
    application_log = summarize_logs(
        app_data.original_text,
        app_data.application_errors_list_full,
        app_data.progressed_indices,
        max_len=CONTEXT_SIZE,
        attr=True,
    )
    application_log = sanitize_log_text(application_log)

    # Find indices
    error_indices = [-1] + [
        i for i, line in enumerate(app_data.original_text) if "port error" in line and "NET/IB" in line
    ]
    active_indices = [-1] + [
        i for i, line in enumerate(app_data.original_text) if "port active" in line and "NET/IB" in line
    ]

    # Check if any 'port active' comes after any 'port error'
    result = max(error_indices) > max(active_indices)

    primary_secondary_lists_justification_total = primary_secondary_lists_justification

    application_log_low = application_log.lower()

    new_rule = "If you are identifying hardware issues in the logs, it has higher importance than other issues."
    primary_secondary_lists_justification_total = add_instruction_rule_at_index(
        primary_secondary_lists_justification_total,
        new_rule,
        index=1,
    )
    if "segmentation" in application_log_low:
        new_rule = (
            "If you are identifying segmentation fault in the logs, it's a secondary issue and not a primary issue"
        )
        primary_secondary_lists_justification_total = add_instruction_rule(
            primary_secondary_lists_justification_total, new_rule
        )
    if ("ib" in application_log_low and "qp" in application_log_low) or (
        "net/" in application_log_low and "qp" in application_log_low
    ):
        new_rule = "If you are identifying ib qp in the logs, it has higher importance than other issues."
        primary_secondary_lists_justification_total = add_instruction_rule(
            primary_secondary_lists_justification_total, new_rule
        )

    if "filenotfound" in application_log_low:
        new_rule = "If you are identifying any FileNotFoundError or “No such file or directory” error with random or temporary-looking paths (e.g., /tmp, wildcard paths, pymp-*) is ALWAYS secondary issue, and not primary issues. Do not list or mention them under primary issues under any circumstances."
        primary_secondary_lists_justification_total = add_instruction_rule(
            primary_secondary_lists_justification_total, new_rule
        )
    if "watchdog" in application_log_low:
        new_rule = "If you are identifying Watchdog collective operation timeout in the logs, they are secondary issues and not primary issues; classify them as secondary issues and don't mention them under primary issues."
        primary_secondary_lists_justification_total = add_instruction_rule(
            primary_secondary_lists_justification_total, new_rule
        )
    if "port error" in application_log_low:
        new_rule = 'If you are identifying port error, evaluate port errors by their final state: if the last related event is "port active", the port error is a secondary symptom; if the last related event is a port error with no later "port active", the port error is the primary issue.'
        primary_secondary_lists_justification_total = add_instruction_rule(
            primary_secondary_lists_justification_total, new_rule
        )
    if "exit" in application_log_low:
        new_rule = "If you are identifying exit errors or exit codes in the logs, they are secondary issues and not primary issues; classify them as secondary issues and don't mention them under primary issues."
        primary_secondary_lists_justification_total = add_instruction_rule(
            primary_secondary_lists_justification_total, new_rule
        )

    if (
        result
        and "port error" in application_log
        and "Got completion from peer" in application_log
        and "DUE TO NODE FAILURE" not in application_log
    ):
        new_rule = "If you are identifying NET/IB port error and NET/IB Got completion from peer in the logs, the port error is the primary issue, and NET/IB is the secondary issue"
        primary_secondary_lists_justification_total = add_instruction_rule(
            primary_secondary_lists_justification_total, new_rule
        )
        messages = [
            SystemMessage(content=(primary_secondary_lists_justification_total)),
            HumanMessage(content=f"""These are the application errors:\n{application_log}"""),
        ]
    elif "DUE TO NODE FAILURE" in application_log and "NET/IB" in application_log:
        new_rule = "If you are identifying NODE FAILURE and NET/IB Got completion from peer in the logs, the NODE FAILURE is the primary issue, NET/IB is the secondary issue"
        primary_secondary_lists_justification_total = add_instruction_rule(
            primary_secondary_lists_justification_total, new_rule
        )
        messages = [
            SystemMessage(content=(primary_secondary_lists_justification_total)),
            HumanMessage(content=f"""These are the application errors:\n{application_log}"""),
        ]
    else:
        messages = [
            SystemMessage(content=(primary_secondary_lists_justification_total)),
            HumanMessage(content=f"""These are the application errors:\n{application_log}"""),
        ]
    s_time = time.time()
    result_proposed_sol = retry_operation(lambda: llm.invoke(messages))
    logger.info("generate attribution infra latency: %s", time.time() - s_time)

    if result_proposed_sol == LLM_ENDPOINT_FAILED:
        return LLM_ENDPOINT_FAILED, "", LLM_ENDPOINT_FAILED, "", app_data.checkpoint_saved

    if hasattr(result_proposed_sol, "content"):
        result_proposed_sol = result_proposed_sol.content.strip().lstrip("{").rstrip("}").strip()

    messages = [
        SystemMessage(content=(attribution_validation)),
        HumanMessage(content=f"""This is the input:\n{result_proposed_sol}"""),
    ]
    s_time = time.time()
    result_proposed_pri = retry_operation(lambda: llm.invoke(messages))
    logger.info("refine attribution infra latency: %s", time.time() - s_time)

    if hasattr(result_proposed_pri, "content"):
        result_proposed_pri = result_proposed_pri.content.strip().lstrip("{").rstrip("}").strip()

    result_proposed_pri = result_proposed_pri.replace('"RuntimeError", ', "").replace('"RuntimeError"', "")

    if result_proposed_pri != LLM_ENDPOINT_FAILED:
        result_proposed_sol = result_proposed_pri

    logger.info("Policy suggestion ended")

    result_proposed_sol = result_proposed_sol.replace("<", "").replace(">", "")

    attribution_dict = extract_attribution_explanation(result_proposed_sol)

    return attribution_dict


def get_proposed_solution_cat(
    llm: ChatNVIDIA,
    app_data: ApplicationData,
    isolation: bool = False,
    attribution: bool = True,
    verbose: bool = True,
) -> tuple[str, str, str, str, str]:
    """Function return category of the errors

    Args:
        app_data: ApplicationData:
            application_errors_list_full: List (log, pattern, i)
            application_errors_list_iteration: List (log, pattern, i), with iteration signatures
            traceback_dict: Dict of stacktraces
            training_started: Training status

    Returns:
        job resume-policy and cordon ambiguous nodes
    """
    if not isolation:
        result_output = get_proposed_solution_policies(llm, POLICIES, app_data, attribution, verbose)
    else:
        # identify the faulty node
        uniques, patterns = get_first_strings(app_data.application_errors_list_full)
        # Find cordon nodes
        result_isolation = (
            get_cordon_nodes(llm, app_data, uniques, patterns, isolation, attribution, verbose),
            app_data.checkpoint_saved,
        )
        attribution_output = ""
        if "TEMPORAL ISOLATION" in result_isolation[0]:
            if attribution:
                attribution_output = "Infrastructure"

        attribution_explanation = ""

        if isinstance(result_isolation[0], tuple):
            auto_resume_output = result_isolation[0][0]
            auto_resume_explanation = result_isolation[0][1]
            if attribution:
                attribution_output = result_isolation[0][2]
                attribution_explanation = result_isolation[0][3]
        else:
            auto_resume_output = result_isolation[0].split("\n")[0]
            auto_resume_explanation = result_isolation[0].split("\n")[1]
            if attribution:
                attribution_dict = get_attribution_infra(llm, app_data)
                attribution_output = attribution_dict["attribution"]
                attribution_explanation = attribution_dict["explanation"]

        if verbose:
            result_output = (
                auto_resume_output,
                auto_resume_explanation,
                attribution_output,
                attribution_explanation,
                result_isolation[1],
            )
        else:
            result_output = auto_resume_output, "", attribution_output, "", result_isolation[1]

    return result_output


def check_restart_or_stop(log_text: str) -> str:
    """Helper function to extract if the recommendation is stop ir restart immediate

    Args:
        log_text: Text of log

    Returns:
        'RESTART IMMEDIATE' and 'STOP - DONT RESTART IMMEDIATE'
    """
    # Extract values using regex
    restart_match = re.search(r"'RESTART THE JOB IMMEDIATELY':\s*(\d+)", log_text.upper())
    stop_match = re.search(r"'NOT RESTART THE JOB IMMEDIATELY':\s*(\d+)", log_text.upper())

    # Get values (default to None if not found)
    restart_value = int(restart_match.group(1)) if restart_match else None
    stop_value = int(stop_match.group(1)) if stop_match else None

    if restart_value is not None and stop_value is None:
        stop_value = 100 - restart_value
    if restart_value is None and stop_value is not None:
        restart_value = 100 - stop_value

    if restart_value is not None and stop_value is not None:
        bigger = (
            "STOP - DONT RESTART IMMEDIATE" if stop_value > restart_value and stop_value > 80 else "RESTART IMMEDIATE"
        )
        return bigger
    return "RESTART IMMEDIATE"


def get_proposed_solution_policies(
    llm: ChatNVIDIA,
    policies: list,
    app_data: ApplicationData,
    attribution: bool = True,
    verbose: bool = True,
) -> tuple[str, str, bool]:
    """Function to recommend resume policy

    Args:
        policies: Policies
        training_started: Status training
        application_errors_list_iteration: List (log, pattern, i), with iteration signatures
        traceback_dict: Dict stacktraces

    Returns:
        'RESTART IMMEDIATE' and 'STOP - DONT RESTART IMMEDIATE'
    """
    logger.info("Policy suggestion started")

    # Create the log based errors, iterations and stacktraces to LLM context size
    application_log = summarize_logs(
        app_data.original_text,
        app_data.application_errors_list_full,
        app_data.progressed_indices,
        max_len=CONTEXT_SIZE,
        attr=True,
    )
    application_log = sanitize_log_text(application_log)

    policies_dict = {}

    logger.info(f"Checkpointing status: {app_data.checkpoint_saved}")
    logger.info(f"Training status: {app_data.training_started}")

    # if not app_data.checkpoint_saved and app_data.training_started == "JOB NOT STARTED":
    if not app_data.checkpoint_saved:
        policies_dict["Suggest to NOT RESTART THE JOB IMMEDIATELY"] = suggest_no_checkpoint_stop
        policies_dict["Suggest to RESTART THE JOB IMMEDIATELY"] = suggest_no_checkpoint_restart
    else:
        policies_dict["Suggest to NOT RESTART THE JOB IMMEDIATELY"] = suggest_yes_checkpoint_stop
        policies_dict["Suggest to RESTART THE JOB IMMEDIATELY"] = suggest_yes_checkpoint_restart

    # General instructions
    if app_data.checkpoint_saved:  # app_data.training_started == "JOB STARTED" or app_data.checkpoint_saved:
        template_policy_instructions = template_policy_instructions_training_started
    else:
        template_policy_instructions = template_policy_instructions_training_not_started

    template_policy_instructions += "\n".join(
        f"{policy}, in the following cases:\n{policies_dict[policy]}" for policy in policies
    )

    template_policy_instructions = template_policy_instructions + template_policy_instructions_output_format

    messages = [
        SystemMessage(content=(template_policy_instructions)),
        HumanMessage(
            content=f"""
    These are the application errors: {application_log}
    """
        ),
    ]
    s_time = time.time()
    result_sol = retry_operation(lambda: llm.invoke(messages))
    logger.info("generate auto-resume latency: %s", time.time() - s_time)

    if hasattr(result_sol, "content"):
        result_sol = result_sol.content

    if result_sol == LLM_ENDPOINT_FAILED:
        return LLM_ENDPOINT_FAILED, "", LLM_ENDPOINT_FAILED, "", app_data.checkpoint_saved

    restart_or_stop = check_restart_or_stop(result_sol)
    # Regex pattern to extract the first occurrence after "Justification:" until the next newline or the end of text
    pattern = r"Justification:\s*([^\n]+)"

    # Find the first match
    match = re.search(pattern, result_sol)

    justification = ""
    if match:
        justification = match.group(1)
    result_output = restart_or_stop + "\n"
    result_output += justification

    result_proposed_sol = ""
    result_proposed_pri = ""

    if attribution:
        messages = [
            SystemMessage(content=(hardware_prompt)),
            HumanMessage(content=f"""These are the application errors:\n{application_log}"""),
        ]

        s_time = time.time()
        hw_category = retry_operation(lambda: llm.invoke(messages))
        logger.info("generate hw category for attribution latency: %s", time.time() - s_time)

        if hasattr(hw_category, "content"):
            hw_category = hw_category.content

        # Find indices
        error_indices = [-1] + [
            i for i, line in enumerate(app_data.original_text) if "port error" in line and "NET/IB" in line
        ]
        active_indices = [-1] + [
            i for i, line in enumerate(app_data.original_text) if "port active" in line and "NET/IB" in line
        ]

        # Check if any 'port active' comes after any 'port error'
        result = max(error_indices) > max(active_indices)

        primary_secondary_lists_justification_total = primary_secondary_lists_justification

        application_log_low = application_log.lower()

        if hw_category.lower() == "yes":
            new_rule = "If you are identifying hardware issues in the logs, it has higher importance than other issues."
            primary_secondary_lists_justification_total = add_instruction_rule_at_index(
                primary_secondary_lists_justification_total,
                new_rule,
                index=1,
            )
            if "segmentation" in application_log_low:
                new_rule = "If you are identifying segmentation fault in the logs, it's a secondary issue and not a primary issue"
                primary_secondary_lists_justification_total = add_instruction_rule(
                    primary_secondary_lists_justification_total, new_rule
                )
            if ("ib" in application_log_low and "qp" in application_log_low) or (
                "net/" in application_log_low and "qp" in application_log_low
            ):
                new_rule = "If you are identifying ib qp in the logs, it has higher importance than other issues."
                primary_secondary_lists_justification_total = add_instruction_rule(
                    primary_secondary_lists_justification_total, new_rule
                )

        if "filenotfound" in application_log_low:
            new_rule = "If you are identifying any FileNotFoundError or “No such file or directory” error with random or temporary-looking paths (e.g., /tmp, wildcard paths, pymp-*) is ALWAYS secondary issue, and not primary issues. Do not list or mention them under primary issues under any circumstances."
            primary_secondary_lists_justification_total = add_instruction_rule(
                primary_secondary_lists_justification_total, new_rule
            )
        if "watchdog" in application_log_low:
            new_rule = "If you are identifying Watchdog collective operation timeout in the logs, they are secondary issues and not primary issues; classify them as secondary issues and don't mention them under primary issues."
            primary_secondary_lists_justification_total = add_instruction_rule(
                primary_secondary_lists_justification_total, new_rule
            )
        if "port error" in application_log_low:
            new_rule = 'If you are identifying port error, evaluate port errors by their final state: if the last related event is "port active", the port error is a secondary symptom; if the last related event is a port error with no later "port active", the port error is the primary issue.'
            primary_secondary_lists_justification_total = add_instruction_rule(
                primary_secondary_lists_justification_total, new_rule
            )
        if "exit" in application_log_low:
            new_rule = "If you are identifying exit errors or exit codes in the logs, they are secondary issues and not primary issues; classify them as secondary issues and don't mention them under primary issues."
            primary_secondary_lists_justification_total = add_instruction_rule(
                primary_secondary_lists_justification_total, new_rule
            )

        if (
            result
            and "port error" in application_log
            and "Got completion from peer" in application_log
            and "DUE TO NODE FAILURE" not in application_log
        ):
            new_rule = "If you are identifying NET/IB port error and NET/IB Got completion from peer in the logs, the port error is the primary issue, and NET/IB is the secondary issue"
            primary_secondary_lists_justification_total = add_instruction_rule(
                primary_secondary_lists_justification_total, new_rule
            )
            messages = [
                SystemMessage(content=(primary_secondary_lists_justification_total)),
                HumanMessage(content=f"""These are the application errors:\n{application_log}"""),
            ]
        elif "DUE TO NODE FAILURE" in application_log and "NET/IB" in application_log:
            new_rule = "If you are identifying NODE FAILURE and NET/IB Got completion from peer in the logs, the NODE FAILURE is the primary issue, NET/IB is the secondary issue"
            primary_secondary_lists_justification_total = add_instruction_rule(
                primary_secondary_lists_justification_total, new_rule
            )
            messages = [
                SystemMessage(content=(primary_secondary_lists_justification_total)),
                HumanMessage(content=f"""These are the application errors:\n{application_log}"""),
            ]
        else:
            slurm_lines = [line for line in application_log.split("\n") if "slurmstepd" in line]
            if (
                "not" in hw_category
                and "STOP" not in restart_or_stop
                and "DUE TO NODE FAILURE" not in application_log
                and ("Error:" not in application_log or "filenotfound" in application_log_low)
                and slurm_lines  # ensures there is at least one slurmstepd line
                and all("CANCELLED AT" in line for line in slurm_lines)
            ):
                new_rule = "If the primary issue is SLURM CANCELLED AT that caused the job to fail, return: Primary issues: [SLURM STEP CANCELLED], Secondary issues: []."
                primary_secondary_lists_justification_total = add_instruction_rule(
                    primary_secondary_lists_justification_total, new_rule
                )
            messages = [
                SystemMessage(content=(primary_secondary_lists_justification_total)),
                HumanMessage(content=f"""These are the application errors:\n{application_log}"""),
            ]
        s_time = time.time()
        result_proposed_sol = retry_operation(lambda: llm.invoke(messages))
        logger.info("generate attribution latency: %s", time.time() - s_time)

        if result_proposed_sol == LLM_ENDPOINT_FAILED:
            result_output_split = result_output.split("\n")
            return (
                result_output_split[0],
                result_output_split[1],
                LLM_ENDPOINT_FAILED,
                "",
                app_data.checkpoint_saved,
            )

        if hasattr(result_proposed_sol, "content"):
            result_proposed_sol = result_proposed_sol.content.strip().lstrip("{").rstrip("}").strip()

        messages = [
            SystemMessage(content=(attribution_validation)),
            HumanMessage(content=f"""This is the input:\n{result_proposed_sol}"""),
        ]

        s_time = time.time()
        result_proposed_pri = retry_operation(lambda: llm.invoke(messages))
        logger.info("refine attribution latency: %s", time.time() - s_time)

        if hasattr(result_proposed_pri, "content"):
            result_proposed_pri = result_proposed_pri.content.strip().lstrip("{").rstrip("}").strip()

        result_proposed_pri = result_proposed_pri.replace('"RuntimeError", ', "").replace('"RuntimeError"', "")

        if result_proposed_pri != LLM_ENDPOINT_FAILED:
            result_proposed_sol = result_proposed_pri

    logger.info("Policy suggestion ended")

    result_proposed_sol = result_proposed_sol.replace("<", "").replace(">", "")

    attribution_dict = extract_attribution_explanation(result_proposed_sol)

    result_output_split = result_output.split("\n")

    if verbose:
        return (
            result_output_split[0],
            result_output_split[1],
            attribution_dict["attribution"],
            attribution_dict["explanation"],
            app_data.checkpoint_saved,
        )
    return result_output_split[0], "", attribution_dict["attribution"], "", app_data.checkpoint_saved


def categorize_errors(unique_application_errors: list | None = None) -> list:
    """Helper function to give score for each line of being the hardware error

    Args:
        unique_application_errors: unique application errors

    Returns:
        List of hardware issues
    """
    if unique_application_errors is None:
        unique_application_errors = []

    unique_application_errors_confidence = dict.fromkeys(unique_application_errors, 0)

    unique_application_errors_hw_regex = get_hardware_regex_errors(unique_application_errors)
    for error in unique_application_errors_hw_regex:
        unique_application_errors_confidence[error] = 100

    return list(unique_application_errors_confidence.values())


def get_cordon_nodes(
    llm: ChatNVIDIA,
    app_data: ApplicationData,
    unique_application_errors: list | None = None,
    patterns_errors: list | None = None,
    isolation: bool = True,
    attribution: bool = True,
    verbose: bool = True,
) -> str:
    """Function to use LLM to detect ambiguous bad nodes

    Args:
        app_data: ApplicationData:
            application_errors_list_full: List (log, pattern, i)
            application_errors_list_iteration: List (log, pattern, i), with iteration signatures
            traceback_dict: Dict of stacktraces
            training_started: Training status
        unique_application_errors: unique application errors
        patterns_errors: errors patterns

    Returns:
        Ambiguous bad nodes
    """
    if unique_application_errors is None:
        unique_application_errors = []
    if patterns_errors is None:
        patterns_errors = []

    logger.info("Nodes cordoning started")

    application_errors_list_full = app_data.application_errors_list_full

    # Categorize the hardware application errors
    batch_conf = categorize_errors(unique_application_errors)

    errors_list_hardware_patterns = [
        patterns_errors[i] for i in range(len(patterns_errors)) if batch_conf[i] >= HARDWARE_THR_LINE
    ]

    application_errors_list_hw = [
        application_errors_list_full[i]
        for i in range(len(application_errors_list_full))
        if application_errors_list_full[i][1] in errors_list_hardware_patterns
    ]

    if len(application_errors_list_hw) > 0:
        ranks_list = [rank for line in application_errors_list_hw if (rank := get_gpu_rank(line[0])) != ""]

        application_log_hardware = summarize_logs(
            app_data.original_text,
            application_errors_list_hw,
            [],
            CONTEXT_SIZE,
            True,
            ranks_list,
        )

        application_log_hardware = sanitize_log_text(application_log_hardware)

        cordon_node_global_text = cordon_node_global_template_num
        template_application_isolation = (
            cordon_node_global_text
            + f"""
This are the errors: {application_log_hardware}"""
        )
        prompt_application_isolation = PromptTemplate.from_template(template_application_isolation)

        application_isolation_chain = (
            {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
            | prompt_application_isolation
            | llm
            | StrOutputParser()
        )
        # Return the nodes that are potential faulty nodes
        s_time = time.time()
        result_isolate = retry_operation(lambda: application_isolation_chain.invoke(template_application_isolation))
        logger.info("cordon nodes global latency: %s", time.time() - s_time)

        result_isolate_first = result_isolate
        if result_isolate == LLM_ENDPOINT_FAILED:
            return LLM_ENDPOINT_FAILED

        def parse_confidence(text: str) -> int | None:
            """Helper function to parse confidence

            Args:
                text: log

            Returns:
                Confidence
            """
            # Define a regex pattern to find the confidence value
            pattern = r"Confidence:\s*(\d+)"

            # Search for the pattern in the given text
            match = re.search(pattern, text)

            if match:
                confidence = int(match.group(1))  # Extract the confidence as an integer
                confidence_extraction = confidence
            else:
                return None, None

            # Extract the content between "Nodes:" and "Confidence:"
            match = re.search(r"Nodes:\s*(.*?)\s*,\s*Confidence:", text)

            if match:
                nodes = [node.strip() for node in match.group(1).split(",")]
                nodes_extraction = nodes
            else:
                return None, None

            return nodes_extraction, confidence_extraction

        nodes_list, confidence = parse_confidence(result_isolate)
        if confidence is not None and nodes_list is not None:
            confidence = int(confidence)
            # If the confidence of hardware is less than 80 or the amount or nodes are above 3 - don't cordon the nodes
            if confidence < 80 or len(nodes_list) > ISOLATION_COUNT:
                # Propose auto-resume based LLM

                result_sol = get_proposed_solution_policies(llm, POLICIES, app_data, attribution, verbose)

                return result_sol
            # Otherwise - provide confidence for cordoning per node
            cordon_node_global = cordon_node_global_1o1_template_num

            cordon_node_global_text = cordon_node_global
            template_application_isolation = (
                cordon_node_global_text
                + f"""
This are the errors: {application_log_hardware}"""
            )
            prompt_application_isolation = PromptTemplate.from_template(template_application_isolation)

            application_isolation_chain = (
                {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
                | prompt_application_isolation
                | llm
                | StrOutputParser()
            )

            # Return the nodes that are potential faulty nodes
            s_time = time.time()
            result_isolate = retry_operation(lambda: application_isolation_chain.invoke(template_application_isolation))
            logger.info("cordon nodes 1-1 latency: %s", time.time() - s_time)

            if result_isolate == LLM_ENDPOINT_FAILED:
                return LLM_ENDPOINT_FAILED

            pattern = r"Node: (\S+), Confidence: (\d+)"
            cordon_nodes = {
                match[0]: int(match[1]) for match in re.findall(pattern, result_isolate) if int(match[1]) >= 80
            }
            if len(cordon_nodes) == 0:
                # Split only the first 3 fields, and treat the rest as justification
                # Extract nodes
                nodes_match = re.search(r"Nodes:\s*(.*?)\s*,\s*Confidence:", result_isolate_first)
                nodes = [n.strip() for n in nodes_match.group(1).split(",")] if nodes_match else []

                # Extract confidence
                confidence_match = re.search(r"Confidence:\s*(\d+)", result_isolate_first)
                confidence = int(confidence_match.group(1)) if confidence_match else None

                # Extract justification
                justification_match = re.search(r"Justification:\s*(.+)", result_isolate_first)
                justification = justification_match.group(1).strip() if justification_match else ""

                # Create both dictionaries
                cordon_nodes = dict.fromkeys(nodes, confidence)
                cordon_justification = dict.fromkeys(nodes, justification)
            else:
                pattern = r"Node:\s*(\S+),.*?Justification:\s*([^\n]+)"
                matches = re.findall(pattern, result_isolate)
                cordon_justification = {node: justification for node, justification in matches}

            if 100 in cordon_nodes.values():
                # Remove all keys with value <= 80
                cordon_nodes = {k: v for k, v in cordon_nodes.items() if v > 80}
            else:
                cordon_nodes = {k: v for k, v in cordon_nodes.items() if v >= 80}
            if check_less_three(cordon_nodes):
                result_isolate = "TEMPORAL ISOLATION + RESTART\n"
                for node in cordon_nodes:
                    if node in cordon_justification:
                        result_isolate += node_to_rank(node) + ", " + cordon_justification[node] + "\n"

            return result_isolate
        result_sol = get_proposed_solution_policies(llm, POLICIES, app_data, attribution, verbose)
        return result_sol
    result_sol = get_proposed_solution_policies(llm, POLICIES, app_data, attribution, verbose)
    return result_sol
