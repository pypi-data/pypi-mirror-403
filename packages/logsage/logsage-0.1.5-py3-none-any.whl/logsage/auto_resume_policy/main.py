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

"""Auto-Resume-Policy: Command-line interface for analyzing GPU cluster job logs.

This tool analyzes log files from GPU cluster job failures, extracts error patterns,
attributes them to root causes, and recommends appropriate remediation actions.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from logsage.auto_resume_policy.error_attribution import (
    get_cordon_nodes,
    get_proposed_solution_cat,
    get_proposed_solution_policies,
)

# Import project modules
from logsage.auto_resume_policy.error_extraction import return_application_errors

# setup logger
logger = logging.getLogger(__name__)


def setup_argparse():
    """Configure command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Auto-Resume-Policy: Analyze GPU cluster job logs and recommend actions."
    )

    parser.add_argument("-a", "--app-log", help="Path to application log file", type=str, required=True)

    parser.add_argument("-s", "--sys-log", help="Path to system log file (optional)", type=str, required=False)

    parser.add_argument(
        "-o", "--output", help="Output file path for analysis results (JSON format)", type=str, required=False
    )

    parser.add_argument(
        "--api-key", help="NVIDIA API Key for LLM access (overrides environment variable)", type=str, required=False
    )

    parser.add_argument(
        "--full-analysis", help="Perform comprehensive analysis (slower but more detailed)", action="store_true"
    )

    parser.add_argument("--cordon-check", help="Check if any nodes should be cordoned", action="store_true")

    return parser


def read_log_file(file_path):
    """Read a log file and return its contents as a list of lines."""
    try:
        with open(file_path, encoding="utf-8") as f:
            return f.readlines()
    except Exception as e:
        logger.error(f"Error reading log file {file_path}: {e}")
        sys.exit(1)


def analyze_logs(app_log_path, sys_log_path=None, full_analysis=False, cordon_check=False):
    """Analyze application and system logs."""
    # Read application log
    app_log_lines = read_log_file(app_log_path)
    logger.info(f"Read {len(app_log_lines)} lines from application log.")

    # Extract errors from application log
    logger.info("Extracting errors from application log...")
    app_errors, unique_errors, batch_list, hardware_errors, hardware_unique, tm_text, finished, iteration_errors = (
        return_application_errors(app_log_lines, file_path=app_log_path)
    )

    results = {
        "application_log": app_log_path,
        "error_count": len(app_errors),
        "unique_error_count": len(unique_errors),
        "training_finished": finished,
        "iteration_error_count": len(iteration_errors),
    }

    # If no errors were found, return early
    if len(app_errors) == 0:
        logger.info("No errors found in application log.")
        results["recommendation"] = "No errors detected, no action needed."
        return results

    # Get error categorization
    sys_errors = []
    logger.info("Analyzing errors and determining root causes...")
    error_analysis = get_proposed_solution_cat(app_errors, sys_errors, tm_text, unique_errors, iteration_errors, False)

    results["error_analysis"] = error_analysis

    # Check if any nodes should be cordoned (for hardware issues)
    if cordon_check:
        logger.info("Checking for nodes that should be cordoned...")
        cordon_nodes = get_cordon_nodes(
            app_errors, unique_errors, [error[1] for error in app_errors], finished, "\n".join(tm_text[:100]), []
        )
        results["cordon_recommendation"] = cordon_nodes

    # Get full remediation policy recommendation
    if full_analysis:
        logger.info("Generating detailed policy recommendation...")
        policies = ["RESTART", "STOP"]  # Only two policies are supported
        error_category = error_analysis.get("error_category", {})
        trace_list_text = "\n".join(tm_text[:200])  # First 200 lines for context

        policy_recommendation = get_proposed_solution_policies(
            app_errors, sys_errors, tm_text, policies, finished, error_category, trace_list_text, []
        )
        results["policy_recommendation"] = policy_recommendation

    return results


def main():
    """Main entry point for the CLI tool."""
    parser = setup_argparse()
    args = parser.parse_args()

    # Set API key if provided via command line
    if args.api_key:
        os.environ["NVIDIA_API_KEY"] = args.api_key
        logger.info("Using API key from command line arguments")

    # Check if API key exists in environment
    if "NVIDIA_API_KEY" not in os.environ:
        logger.warning(
            "Warning: NVIDIA_API_KEY not set. Please provide it with --api-key or set the environment variable."
        )
        return 1

    logger.info(f"Starting analysis of log file: {args.app_log}")

    # Analyze logs
    results = analyze_logs(args.app_log, args.sys_log, args.full_analysis, args.cordon_check)

    # Print summary to console
    logger.info("\n===== ANALYSIS SUMMARY =====")
    logger.info(f"Found {results['error_count']} errors in application log")

    if "error_analysis" in results:
        if "error_category" in results["error_analysis"]:
            logger.info("\nError Categories (confidence scores):")
            for category, score in results["error_analysis"]["error_category"].items():
                logger.info(f"  - {category}: {score}")

        if "restart_recommendation" in results["error_analysis"]:
            logger.info(f"\nRecommended Action: {results['error_analysis']['restart_recommendation']}")

    if "cordon_recommendation" in results:
        if results["cordon_recommendation"].get("Nodes") and results["cordon_recommendation"]["Nodes"] != "None":
            logger.info(f"\nNodes to cordon: {results['cordon_recommendation']['Nodes']}")

    # Save results to file if output path provided
    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"\nFull analysis saved to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
