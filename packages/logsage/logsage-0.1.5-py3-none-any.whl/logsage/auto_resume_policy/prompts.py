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

template_app_error_extraction = """
Examine each sentence individually.
Respond 'yes' **only** if the sentence reports an actual error, timeout that occurred, or synchronization problem.
Respond 'no' otherwise.

Output format:
Return global **"yes"** or **"no"** — no explanations or extra text.

Do not include explanations, reasoning, or extra text.

Input: {question}
Answer:"""

template_app_error_extraction_validation = """
You are an expert in analyzing application logs.
Your task:
For each given log line, determine whether it represents an **error**.
Output:
- Return **"yes"** if the line is a confirmed error (100% certain).
- Return **"no"** if the line is not an error, is a warning, is uncertain, or matches any exclusion rule below.
Rules:
1. Return **"yes"** for confirmed **errors**.
2. Return **"no"** for **warnings**, **info**, **traceback**, or **deprecated** messages.
3. Return **"yes"** for **timeout** errors.
4. Return **"no"** for any **mpi/pmix_v** related errors.
5. Return **"no"** for **slurmstepd** errors related to **mpi/pmix**.
6. Return **"yes"** for **Python and Pytorch** errors.
7. Return **"yes"** for **CUDA** errors.
8. Return **"yes"** for **NCCL** or **OFI** errors.
9. Return **"yes"** for **Infiniband** or **port** errors.
10. Return **"no"** for specific **NCCL WARN** messages:
   - `[Service thread] Accept failed Resource temporarily unavailable`
   - `[Service thread] Could not receive type from localRank *`
   - `[Proxy Service %d] Failed to execute operation Close from rank *`
   - `[Service thread] Accept failed Success`
   - `[Service thread] Accept failed Invalid argument *`
   - `[Service thread] Error encountered progressing operation *`
11. Return **"no"** for messages containing:
    - `"frame#"`
    - `"!!! [UB]"`
    - `"*** End of error message ***"`
    - `"*** Process received signal ***"`
    - `"Signal: Aborted"`
    - `"Signal code:"`
    - `"Aborted"`
    - `"malloc_consolidate(): invalid chunk size"`
    - `"double free or corruption"`
    - `"NCCL::watchdogHandler()"`
    - `"NET/IB : Got async event : client reregistration"`
    - `"NET/IB : Got async event : port active"`
12. Return **"yes"** for **Slurm** issues (not excluded by other rules).
13. Return **"no"** if the line only contains a node name and file path (e.g., `<nodename> <filepath>`).
14. If no log is provided, return **"no"**.
15. Be **100% certain** before returning "yes". If unsure, return "no".

Do not include explanations, reasoning, or extra text.

Output format:
Return only **"yes"** or **"no"** — no explanations or extra text.

Input:
{question}
Answer:
"""

template_app_iteration = """
You are an expert in analyzing AI training logs.

For each log line, determine **with certainty** whether it reports any of the following events:
- A single training iteration/step
- The start or end of a training epoch
- A single validation iteration/step
- A single evaluation/testing iteration/step

Rules:
- Respond **"yes"** if the line clearly reports one of these events.
- Respond **"no"** if it does not or if you are unsure.
- Do **not** provide any explanations or extra text—only "yes" or "no".
- Be strict and conclusive; only lines that clearly indicate these events should return "yes".

Do not include explanations, reasoning, or extra text.

Log line: "{question}"
Answer:"""

template_app_checkpointing = """### Instruction
You are a log analysis assistant. Your task is to determine if an AI training checkpoint has finished saving successfully based on a single log line.

### Criteria for "yes"
- The log must explicitly state that the process is finished, completed, or successful.
- Examples: "Checkpoint saved," "Finished storing weights," "State dict saved successfully."

### Criteria for "no"
- The process is still in progress (e.g., "Starting save...", "Uploading...").
- The process failed or timed out.
- The message is irrelevant or ambiguous.

### Constraint
- Output ONLY the word "yes" or "no".
- Do not provide explanations, punctuation, or additional text.

Do not include explanations, reasoning, or extra text.

### Log Line to Analyze
"{question}"

### Answer"""

template_app_error_cat = """You will receive error lines from training workload applications. For each line, return the confidence score (0–100) representing how likely it is to be a hardware failure.

Guidelines:
1. Output only the confidence value (integer between 0–100). No explanations or extra text.
2. Consider hardware components: node, GPU, NIC, CPU, and networking fabric (InfiniBand, RoCE, Ethernet).
3. Software-related issues → low confidence.
4. Collective operation failures → software issue → low confidence.
5. GPU or NIC initialization failures → hardware issue.
6. Storage issues → not a hardware issue.
7. “Process down” → not a hardware issue.
8. CUDA failures → hardware issue.
9. Unreachable or unresponsive compute node → hardware issue.
10. “BrokenPipe” → not a hardware issue.
11. “Exception raised” → not a hardware issue.
12. Disk, GPU, or CPU insufficient memory → not a hardware issue.
13. “Connection reset by peer” → not a hardware issue.

This have to be the structure of your answer:
"
    <confidence>, number between 0-100 of being hardware issue.
    Don't add additional information, don't add footer, don't add header.
"

This is the application error: {question}
"""

template_application_error_check = """You will receive a log line from a training workload application.
Determine if the line represents an error.

Instructions:

If the line clearly indicates an error, return "yes".
If it does not indicate an error or lacks error content, return "no".
If the line contains "Gloo connectFullMesh failed with * no error", return "yes" — it is a real error.

Output:
'yes' or 'no'

Do not include any extra information, headers, or footers.
"""

template_hardware_category_prompt = """
You are an expert in application logs. You will be given errors related to a job running across multiple nodes.

Your task is to determine whether the evidence indicates a HARDWARE issue and assign a confidence level.

Instructions:

- Return a single confidence score (0–100) for HARDWARE.
- 0 means "definitely NOT a hardware issue".
- 100 means "definitely a hardware issue".

Classification Rules:

- GPU issues, ECC errors, NVLink failures, NIC failures, InfiniBand hardware errors → HARDWARE.
- If the error contains "Got completion from peer" → assign very high confidence to HARDWARE.
- Pay close attention to NIC and InfiniBand hardware failures.
- Ignore "Got async event: port error" completely.

Non-Hardware Rules:

- "Insufficient disk" is NOT a hardware issue.
- GPU/node out-of-memory is NOT a hardware issue.
- Configuration issues are NOT hardware issues.
- Communication configuration issues are NOT hardware issues.
- Generic connection issues are NOT hardware issues.
- Missing files or environment variables are NOT hardware issues.
- Missing files with random or temporary-looking paths are lower importance and usually NOT hardware.
- Data-loading issues are NOT hardware issues.

Reasoning Rules:

- The first clear error should increase confidence more than later errors.
- Later errors may reduce confidence if they suggest secondary or cascading failures.

Output Format:

HARDWARE: <confidence>
Don't add additional information, don't add footer or header
"""

template_policy_instructions_training_started = """
You are an expert on application logs. You will receive errors related to a job running across multiple nodes.
Your task is to determine the confidence level for each policy decision regarding whether to restart the next job.

You must decide between:
- "RESTART THE JOB IMMEDIATELY"
- "NOT RESTART THE JOB IMMEDIATELY"

Restart Policy Decision Rules:

1. Review all errors sequentially from beginning to end.
2. Consider all errors collectively when making the final decision.
3. Do not make assumptions about terminal configuration issues — only consider them if they are explicitly mentioned in the logs.
4. If training (iteration or epoch) stopped after the errors:
   - If the issue appears temporal, suggest "RESTART THE JOB IMMEDIATELY".
   - If the issue appears terminal, suggest "NOT RESTART THE JOB IMMEDIATELY".
5. If the job finishes successfully, suggest "RESTART THE JOB IMMEDIATELY".
6. Errors originating from PyTorch NCCL watchdogs (e.g., ProcessGroupNCCL.cpp) are typically
   secondary symptoms or side effects of an earlier issue and should NOT be used as the primary
   signal when determining the restart policy.
7. If NCCL watchdog or collective operation timeout errors appear **in addition to other errors**,
   ignore them when making the final restart decision and base the policy on the primary cause.
8. If NCCL watchdog or collective operation timeout errors are the **only errors present**,
   suggest "RESTART THE JOB IMMEDIATELY".
9. NCCL collective operation errors are often minor, intermittent, or synchronization-related.
10. Collective operation timeouts or hangs should generally be treated as non-terminal issues —
    suggest "RESTART THE JOB IMMEDIATELY".
11. If errors indicate a node failure (e.g., node crash, node offline, lost connection to node), these are likely intermittent — suggest "RESTART THE JOB IMMEDIATELY".
12. If a segmentation fault or "address not mapped" error is identified, suggest "RESTART THE JOB IMMEDIATELY".
13. If errors involve missing files or randomized paths:
    - If the missing file is random or temporary-looking paths in the logs, suggest "RESTART THE JOB IMMEDIATELY".
    - If the missing file is **related to Python’s multiprocessing errors**, suggest "RESTART THE JOB IMMEDIATELY", because these are artifact of closing the application and not the root cause of the failure.
    - If the missing file is **related to the model and preventing to initiate the model**, suggest "NOT RESTART THE JOB IMMEDIATELY".
14. If errors are not critical and intermittent, suggest "RESTART THE JOB IMMEDIATELY".
15. If the logs do not indicate any critical errors, suggest "RESTART THE JOB IMMEDIATELY".
16. If the logs do not indicate any critical errors that would require an immediate restart, suggest "RESTART THE JOB IMMEDIATELY".
17. If there are no errors provided to analyze the job, suggest "RESTART THE JOB IMMEDIATELY".
18. If only a secondary symptom or side effect of the issue is present, suggest "RESTART THE JOB IMMEDIATELY".
19. Identify the cause of the errors, if the exact cause is not found, suggest "RESTART THE JOB IMMEDIATELY"
20. "Aborted" is not an indication of a terminal issue — suggest "RESTART THE JOB IMMEDIATELY".
21. Exit status or exit code are not indications of a terminal issue — suggest "RESTART THE JOB IMMEDIATELY".
22. If you are identifying that the job exited with non zero exit status, this is a secondary issue hence Suggest to RESTART THE JOB IMMEDIATELY.
23. If the errors indicate about hang or timeout, suggest "RESTART THE JOB IMMEDIATELY".

"""

template_policy_instructions_training_not_started = """
You are an expert on application logs. You will receive errors related to a job running across multiple nodes.
Your task is to determine the confidence level for each policy decision regarding whether to restart the next job.

You must decide between:
- "RESTART THE JOB IMMEDIATELY"
- "NOT RESTART THE JOB IMMEDIATELY"

Restart Policy Decision Rules:

1. Review all errors sequentially from beginning to end.
2. Consider all errors collectively when making the final decision.
3. Do not make assumptions about terminal configuration issues — only consider them if they are explicitly mentioned in the logs.
4. Errors originating from PyTorch NCCL watchdogs (e.g., ProcessGroupNCCL.cpp) are typically
   secondary symptoms or side effects and should NOT be used as the primary signal
   when determining the restart policy.
5. If NCCL watchdog or collective operation timeout errors appear alongside other errors,
   ignore them for the purpose of recommending the policy and base the decision on the primary cause.
6. If NCCL watchdog or collective operation timeout errors are the ONLY errors present,
   suggest "RESTART THE JOB IMMEDIATELY".

NCCL Collective Operations:
7. NCCL collective operation errors are usually minor, intermittent, or synchronization-related
   and should generally not be treated as terminal issues.
8. Collective operation timeouts or hangs should typically result in
   "RESTART THE JOB IMMEDIATELY".
9. If errors indicate a node failure (e.g., node crash, node offline, lost connection to node), these are likely intermittent — suggest "RESTART THE JOB IMMEDIATELY".
10. If a segmentation fault or "address not mapped" error is identified, suggest "RESTART THE JOB IMMEDIATELY".
11. Insufficient GPU memory, CPU memory, disk resources - Suggest to NOT RESTART THE JOB IMMEDIATELY, Don't suggest to RESTART THE JOB IMMEDIATELY.
12. Insufficient GPU memory, CPU memory, disk resources is more critical than segmentation fault or "address not mapped" - Suggest to NOT RESTART THE JOB IMMEDIATELY, Don't suggest to RESTART THE JOB IMMEDIATELY.
13. If errors involve missing files or randomized paths:
    - If the missing file is random or temporary-looking paths in the logs, suggest "RESTART THE JOB IMMEDIATELY".
    - If the missing file is **related to Python’s multiprocessing errors**, suggest "RESTART THE JOB IMMEDIATELY", because these are artifact of closing the application and not the root cause of the failure.
    - If the missing file is **related to the model and preventing to initiate the model**, suggest "NOT RESTART THE JOB IMMEDIATELY".
14. If errors are not critical and intermittent, suggest "RESTART THE JOB IMMEDIATELY".
15. If the logs do not indicate any critical errors that would require an immediate restart, suggest "RESTART THE JOB IMMEDIATELY".
16. If there are no errors provided to analyze the job, suggest "RESTART THE JOB IMMEDIATELY".
17. If only a secondary symptom or side effect of the issue is present, suggest "RESTART THE JOB IMMEDIATELY".
18. Identify the cause of the errors, if the exact cause is not found, suggest "RESTART THE JOB IMMEDIATELY"
19. "Aborted" is not an indication of a terminal issue — suggest "RESTART THE JOB IMMEDIATELY".
20. Exit status or exit code are not indications of a terminal issue — suggest "RESTART THE JOB IMMEDIATELY".
21. If you are identifying that the job exited with non zero exit status, this is a secondary issue hence Suggest to RESTART THE JOB IMMEDIATELY.
22. If the errors indicate about hang or timeout, suggest "RESTART THE JOB IMMEDIATELY".

"""

template_policy_instructions_output_format = """
Additional Instruction:

Give confidence level for each policy. The sum of the confidences must equal 100.

Do not include explanations, reasoning, or extra text.

Your answer **must** follow this exact structure, without adding additional information:

"
    'RESTART THE JOB IMMEDIATELY': <confidence>, the confidence level value between 0-100.
    'NOT RESTART THE JOB IMMEDIATELY': <confidence>, the confidence level value between 0-100.

    'Justification: <justification> - unified justification based on all indications, mention the errors'
"

"""

template_policy_instructions_output_format = """
Additional Instructions:

1. Assign a confidence level to each policy. The sum of the confidence values must equal 100.
2. Do not include explanations, reasoning steps, or any extra text beyond the required output.
3. In the justification:
   - You MAY reference the applicable rule or instruction logic in descriptive terms.
   - Do NOT mention rule numbers, instruction numbers, or any identifiers.
   - Do NOT use phrases such as "rule 1", "instruction 2", or similar numeric references.

Your answer must follow this exact structure, without adding or removing anything:

"
    'RESTART THE JOB IMMEDIATELY': <confidence>, the confidence level value between 0-100.
    'NOT RESTART THE JOB IMMEDIATELY': <confidence>, the confidence level value between 0-100.

    'Justification: <justification> - unified justification based on all indications; mention the errors and the applied rule or instruction logic using descriptive language only, without numeric identifiers'
"
"""

template_compute_networking_prompt = """
Identify if the errors are related to 'compute' or 'networking'. Provide a confidence level for each.
The sum of the confidences must equal 100.

Do not add any headers, footers, or additional information.

Your answer **must** follow this exact structure:

"
compute: <confidence>, confidence level between 0-100.
networking: <confidence>, confidence level between 0-100.
"
"""

cordon_node_global_template_num = """
You are an expert on application logs. You will receive errors related to a job running across multiple nodes.
Based on the errors, provide a confidence level for recommending whether to cordon (make unschedulable) nodes or not.

Instructions to cordon the nodes:
1. If hardware failures related to nodes are identified, recommend cordoning the affected nodes.
2. If NCCL hardware issues or RDMA issues are identified, recommend cordoning the affected node with high confidence.
3. Multiple hardware issues on the same node indicate cordoning with high confidence.
4. Networking connection timeouts reported from a single compute node indicate cordoning with high confidence.

Instructions to not cordon the nodes:
1. Issues not related to hardware failures should return "Nodes: None" with low confidence.
2. Software issues should return "Nodes: None" with low confidence.
3. If there is no main issue and only secondary issues are present — return "Nodes: None" with low confidence.
4. Errors across multiple nodes suggest a systematic issue. In this case, return "Nodes: None" with low confidence, since it is difficult to attribute the failure to any single node.
5. GPU insufficient memory — return "Nodes: None" with low confidence.

Additional instructions:
1. Consider all errors together; if unrelated, evaluate separately.
2. Errors are in chronological order.
3. Multiple nodes with the same error should have the same confidence.
4. Return all nodes recommended to cordon.
5. Do not add headers, footers, or extra information.

Your answer **must** follow this structure exactly:

"
Nodes: <nodes>, Confidence: <confidence>, Justification: <justification>
"

<Nodes> — node<number>, can include multiple nodes.
<Confidence> — numeric value between 0-100.
<Justification> — explanation why to cordon.
"""

cordon_node_global_1o1_template_num = """
You are an expert on application logs. You will receive errors related to a job running across multiple nodes.
Based on the errors, provide a confidence level for recommending whether to cordon (make unschedulable) nodes or not.

Instructions to cordon the nodes:
1. Hardware failures related to nodes — recommend cordoning the affected nodes.
2. NCCL hardware issues or RDMA issues — recommend cordoning the affected node with high confidence.
3. Multiple hardware issues on the same node — recommend cordoning with high confidence.
4. Networking connection timeouts reported from a single compute node — recommend cordoning with high confidence.

Instructions to not cordon the nodes:
1. Issues not related to hardware failures — return "Node: None" with low confidence.
2. Software issues — return "Node: None" with low confidence.
3. If there is no main issue and only secondary issues are present — return "Node: None" with low confidence.
4. Errors across multiple nodes suggest a systematic issue. In this case, return "Node: None" with low confidence, since it is difficult to attribute the failure to any single node.
5. GPU insufficient memory — return "Node: None" with low confidence.

Additional instructions:
1. Consider all errors together; if unrelated, evaluate separately.
2. Errors are in chronological order.
3. Return all nodes recommended to cordon.
4. Do not add headers, footers, or extra information.
5. The output must be a list of all nodes to cordon, each following this structure:

"
Node: node<node>, Confidence: <confidence>, Justification: <justification>
"

<node> — node<number>
<confidence> — numeric value between 0-100.
<justification> — explanation why to cordon.

Examples:

For 1 node:
"
Node: node<node>, Confidence: <confidence>, Justification: <justification>
"

For 2 nodes:
"
Node: node<node>, Confidence: <confidence>, Justification: <justification>
Node: node<node>, Confidence: <confidence>, Justification: <justification>
"

For 3 nodes:
"
Node: node<node>, Confidence: <confidence>, Justification: <justification>
Node: node<node>, Confidence: <confidence>, Justification: <justification>
Node: node<node>, Confidence: <confidence>, Justification: <justification>
"
"""

suggest_no_checkpoint_stop = """
Follow these instructions carefully:

1. If you are identifying explicit configuration or model parameter issues — Suggest to NOT RESTART THE JOB IMMEDIATELY. This instruction has higher priority.
2. If you are identifying explicit coding or programming issues — Suggest to NOT RESTART THE JOB IMMEDIATELY. This instruction has higher priority.
3. If you are identifying errors indicating checkpointing issues related to the checkpoint destination directory (e.g., already exists, not empty, or inaccessible) — Suggest to NOT RESTART THE JOB IMMEDIATELY.
4. If you are identifying permission denied or unauthorized access — Suggest to NOT RESTART THE JOB IMMEDIATELY. This instruction has higher priority.
5. If you are identifying insufficient memory or disk resources — Suggest to NOT RESTART THE JOB IMMEDIATELY.
6. If you are identifying missing file **preventing to initiate the model** is critical, suggest "NOT RESTART THE JOB IMMEDIATELY".
7. If you are identifying that the checkpoint destination directory already exists or is not empty, Suggest to NOT RESTART THE JOB IMMEDIATELY.
9. If you are identifying a mismatch in parallelism configuration after resuming from a checkpoint  — Suggest to NOT RESTART THE JOB IMMEDIATELY.
10. If the main issue that you identified clearly requires manual intervention to be resolved — Suggest to NOT RESTART THE JOB IMMEDIATELY.
11. If based on the main issue that you identified, is likely that restarting the job will not resolve the issue and the error is not transient or intermittent — Suggest to NOT RESTART THE JOB IMMEDIATELY.
12. Identify the primary cause of the errors and distinguish any secondary symptoms or side effects of the issue to determine the appropriate policy.
13. Transient issues have lower priority in determining the appropriate policy.
"""


suggest_no_checkpoint_restart = """
Follow these instructions carefully:

1. If you are identifying timeout in the connection to storage — Suggest to RESTART THE JOB IMMEDIATELY.
2. If you are identifying broken pipe — Suggest to RESTART THE JOB IMMEDIATELY.
3. If you are identifying Numerical instability or transient hardware issues — Suggest to RESTART THE JOB IMMEDIATELY. Numerical instability (Inf/NaN gradients or loss) MUST NOT be classified as:
    - Coding or programming issue
    - Configuration issue
    - Model definition issue
    - Manual intervention required
Unless logs explicitly mention invalid code, wrong parameters, or incorrect configuration.
4. If you are identifying intermittent GPU initialization failures — Suggest to RESTART THE JOB IMMEDIATELY.
5. If you are identifying intermittent GPU driver issues — Suggest to RESTART THE JOB IMMEDIATELY.
6. If you are identifying race condition or resource busy errors — Suggest to RESTART THE JOB IMMEDIATELY.
7. If you are identifying push/receive or expected-receive mismatches — Suggest to RESTART THE JOB IMMEDIATELY.
8. If you are identifying Networking or InfiniBand-related issues — Suggest to RESTART THE JOB IMMEDIATELY.
9. If the job was cancelled due to a timeout — Suggest to RESTART THE JOB IMMEDIATELY.
10. If you are identifying that the job exited with non zero exit status, this is a secondary issue hence Suggest to RESTART THE JOB IMMEDIATELY.
11. If you are identifying missing directories, mount paths, or filesystem paths required for container startup (e.g., failed to mount, No such file or directory, container rootfs or tmp directories) AND the path is expected to be created or managed by the infrastructure or job runtime (not user code) — Suggest to RESTART THE JOB IMMEDIATELY.
12. If the logs do not indicate any critical errors  — Suggest to RESTART THE JOB IMMEDIATELY.
13. If there are Node failures or infrastructure-level issues that can be resolved by restarting — Suggest to RESTART THE JOB IMMEDIATELY.
14. If there are Collective operation timeouts in NCCL communication — Suggest to RESTART THE JOB IMMEDIATELY.
"""

suggest_yes_checkpoint_stop = """
Follow these instructions carefully:

2. If you are identifying explicit errors indicating checkpointing issues related to the checkpoint destination directory (e.g., already exists, not empty, or inaccessible) — Suggest to NOT RESTART THE JOB IMMEDIATELY.
3. If restarting the job will not produce a new checkpoint (for example, the same errors are expected to reoccur) — Suggest to NOT RESTART THE JOB IMMEDIATELY.
4. If the cause is not explicitly clear or you are not 100% certain — Suggest to RESTART THE JOB IMMEDIATELY.
5. Ignore issues from missing files with randomize file path.
"""

suggest_yes_checkpoint_stop_extension = """
6. If the are permission, authentication, or access denied errors happens in the following cases: e.g., dataset loading or non-checkpoint I/O — Suggest to RESTART THE JOB IMMEDIATELY. Is a terminal cases but still the a new checkpoint produced.
"""

suggest_yes_checkpoint_restart = """
Follow these instructions carefully:

1. If you are identifying timeout in the connection to storage — Suggest to RESTART THE JOB IMMEDIATELY.
2. If you are identifying storage connection or accessibility issues — Suggest to RESTART THE JOB IMMEDIATELY.
3. If you are identifying library or dependency loading failures — Suggest to RESTART THE JOB IMMEDIATELY.
4. If you are identifying data loading broken pipe or exhaustion — Suggest to RESTART THE JOB IMMEDIATELY.
5. If you are identifying general communication failures — Suggest to RESTART THE JOB IMMEDIATELY.
6. If you are identifying collective operation timeouts in NCCL communication — Suggest to RESTART THE JOB IMMEDIATELY.
7. If you are identifying push/receive or expected-receive mismatches — Suggest to RESTART THE JOB IMMEDIATELY.
8. If you are identifying insufficient GPU memory, CPU memory, or disk resources — Suggest to RESTART THE JOB IMMEDIATELY.
9. If you are identifying data missing, data corruption, or bad formatting — Suggest to RESTART THE JOB IMMEDIATELY.
10. If you are identifying race conditions or resource busy states — Suggest to RESTART THE JOB IMMEDIATELY.
11. If you are identifying numerical instability or transient hardware issues — Suggest to RESTART THE JOB IMMEDIATELY. Numerical instability (Inf/NaN gradients or loss) MUST NOT be classified as:
    - Coding or programming issue
    - Configuration issue
    - Model definition issue
    - Manual intervention required
Unless logs explicitly mention invalid code, wrong parameters, or incorrect configuration.
12. If you are identifying Networking or InfiniBand connectivity issues — Suggest to RESTART THE JOB IMMEDIATELY.
13. If the job was cancelled due to a timeout — Suggest to RESTART THE JOB IMMEDIATELY.
14. If you are identifying that the job exited with non zero exit status, this is a secondary issue hence Suggest to RESTART THE JOB IMMEDIATELY.
15. If the logs do not indicate any critical errors  — Suggest to RESTART THE JOB IMMEDIATELY.
16. If there are Communication issues between nodes — Suggest to RESTART THE JOB IMMEDIATELY, though other errors may take higher priority.
17. If there is a failed model saving due to connection interruptions — Suggest to RESTART THE JOB IMMEDIATELY.
18. If there are memory corruption or runtime errors such as "corrupted size vs. prev_size", "Aborted", or "double free or corruption" — Suggest to RESTART THE JOB IMMEDIATELY.
19. If there are node or infrastructure-level failures that can be resolved by restarting — Suggest to RESTART THE JOB IMMEDIATELY.
20. If the issues are secondary symptom or side effect of the issue - Suggest to RESTART THE JOB IMMEDIATELY. This instruction has higher priority.
21. If there are Collective operation timeouts in NCCL communication — Suggest to RESTART THE JOB IMMEDIATELY.
"""

proposed_solution_text = """
You are an expert on application logs. You will receive errors related to a training job and provide a unified explanation for resolving the issues.

Instructions:

1. Focus only on errors that are directly relevant and are the cause of the job failure.
2. Ignore errors that are not relevant or not the root cause.
3. Suggest configuration parameters or adjustments to solve the issue, if possible.
4. Increasing the NCCL timeout parameter is low priority. Only recommend it if there are no other actionable solutions.
5. Do not mention monitoring systems, system logs, other logs, or debugging tools.
6. The issue is not hardware-related, do not recommend checking hardware.
7. Pytorch NCCL watchdog errors have low priority; mention them only if no other issues exist.

Your output should be a clear, actionable explanation of the steps needed to resolve the failure.
"""


template_application_crash_check = """
You will get log lines from an AI training job. Determine if the job **failed** or not.
If the job failed, return 'yes'. If it did not fail, return 'no'.

Instructions:
1. Return “yes” only if you clearly see explicit errors or failure indicators showing that the job failed or crashed.
2. If you explicitly identify that the training finished, return “no”.
3. If you see that the job continues to execute after the error, return “no”.
4. If you see that the training is stuck, return “yes”.
5. If you see that the training is timeout before training finished, return “yes”.
6. If there are no explicit errors, return “no”.
7. If you identify an error related to a failed checkpoint (e.g., checkpoint save/load failure, corrupted checkpoint, missing checkpoint), return “yes”.

Do not add any additional information, headers, or footers.

Your answer must be exactly 'yes' or 'no'.
"""

template_chunk_progress_check = """
You will get a chunk of log lines from an AI training job. Determine if the job **progressed successfully** or **failed/stalled** in this chunk.
If the job progressed in this chunk, return 'progressed'. If it failed or is stuck in this chunk, return 'failed'.

Instructions:
1. Return “failed” if you clearly see explicit errors, crashes, or failure indicators in this chunk.
2. Return “failed” if the training is stuck or times out in this chunk.
3. Return “progressed” if the logs show that training continues to execute or completes successfully in this chunk.
4. If errors occur but the job continues without crashing, return “progressed”.
5. If there are no explicit errors or issues and training proceeds, return “progressed”.

Do not include explanations, reasoning, or extra text.

Your answer must be exactly 'progressed' or 'failed'.
Don't add footer or header.

Output:
'progressed' or 'failed'

Log: {question}
Answer:
"""

template_application_cause_check = """
You are an expert in analyzing application logs. You will receive the errors of a job running across multiple nodes.
Your task is to check whether the cause exists in the errors or not"

Instructions:
1. If the exact cause is specified, reply with "yes".
2. If the exact cause is not specified, reply with "no".
3. If the errors are only a secondary symptom of the issue is present, suggest "no".
4. If you are no sure 100%, reply with "yes".

Do not add any additional information, headers, or footers.

Your answer must be exactly 'yes' or 'no'.
"""


primary_secondary_lists_justification = """
Role:
You are an expert in analyzing logs from large-scale distributed training jobs (GPU, network, and system-level).

Input:
You will receive a set of error log lines from a failed job.

Task:
Determine the root cause of the job failure and distinguish it from cascading or follow-up errors.

Definitions:
- Primary issues: Errors that directly caused the job to fail. These represent the root cause and should be prioritized.
- Secondary issues: Errors that are consequences, symptoms, or side effects of the primary issue(s). Secondary issues must be causally related to the primary issue(s). Unrelated or noise errors should be ignored.

Instructions:
1. If you are not identifying primary issues, return: Primary issues: [].
2. If you are not identifying secondary issues, return: Secondary issues: [].
3. If you are not identifying error messages, return: Primary issues: [], Secondary issues: [].
4. Try to identify the errors from the main thread or main process in the logs - they are the primary issues.

Description Requirements:
1. For every primary and secondary issue, provide concise descriptive details using several exact words taken only from the raw log text. Generic description are not allowed.
2. Do not invent words or explanations that are not explicitly present in the logs.
3. When multiple log lines represent the same underlying primary or secondary issue, group them into a single entry using a few exact words from the logs. When a log line includes an exception type and error message, don't separate them, treat them as single issue.
4. Enclose each issue in the list in double quotes ("").

Output format:
"
Attribution:
Primary issues: <list_primary_issues>,
Secondary issues: <list_secondary_issues>
"

Do not include any extra information, headers, or footers.
"""


hardware_prompt = """
Role:
You are an expert in analyzing logs from large-scale distributed training jobs.

Input:
You will receive raw log lines from a failed job. The logs may include any combination of application, runtime, framework, system, networking, or environment messages.

Task:
Decide whether the failure should be considered a **hardware issue** or **not**.

Definitions:
- Hardware issue: Any failure that could reasonably classify as a problem with physical resources, including compute, memory, or networking hardware.
- Non-hardware issue: Failures that are clearly and exclusively caused by software logic, configuration, user input, or expected application behavior.

Decision Rules:
1. Return **"yes"** if there is any indication that physical resources or hardware (including networking hardware) may be involved.
2. Return **"not"** only if the logs clearly and unambiguously point to a non-hardware cause.
3. Do not speculate beyond the content of the logs; when in doubt, classify as hardware-related.

Output Format:
- Output: `yes` or `not`

Do not include explanations, punctuation, or additional text.
"""


attribution_validation = """
Role:
You are an expert in log attribution and error classification for distributed systems.

Input:
You will receive an attribution in the following format:

"
Attribution:
Primary issues: <list_primary_issues>,
Secondary issues: <list_secondary_issues>
"

Task:
- Examine each issue in the Secondary issues list.
- For each secondary issue, perform the following checks in order:

    **Literal phrase check (mandatory)**:
    - Verify that the secondary issue contains an exact **entire phrase** that appears in any issue from the Primary issues list.
    - The phrase must appear verbatim (character-for-character) inside the secondary issue.
    - If such a literal phrase exists, the secondary issue MUST be removed.

- Do NOT use semantic similarity alone without a literal phrase match.
- Do NOT modify issue text.
- Do NOT create new issues.
- Do NOT remove any other issues.
- Preserve ordering as much as possible:
  - Keep the remaining Secondary issues in their original order.
- **If no secondary issue satisfies the literal phrase check, do nothing and return the input unchanged.**

Examples:

Example 1:
Input:
Attribution:
Primary issues: [
  "error A occurred during initialization",
  "wrapper failure: error A occurred during initialization"
],
Secondary issues: [
  "background thread terminated due to error A occurred during initialization"
]

Output:
Attribution:
Primary issues: [
  "error A occurred during initialization",
  "wrapper failure: error A occurred during initialization"
],
Secondary issues: [ ]

Example 2:
Input:
Attribution:
Primary issues: ["error A"],
Secondary issues: ["runtime error A detected"]

Output:
Attribution:
Primary issues: ["error A"],
Secondary issues: ["runtime error A detected"]

Explanation (implicit, do NOT include in output):
- "error A" does NOT appear as an exact entire phrase inside "runtime error A detected".

Output:
- Return the result in the **exact same format** as the input.
- Do NOT include explanations, justifications, headers, or footers.

"
Attribution:
Primary issues: <updated_list_primary_issues>,
Secondary issues: <updated_list_secondary_issues>
"
"""
