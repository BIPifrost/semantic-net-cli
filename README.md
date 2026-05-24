# Semantic Network Analysis CLI Prototype

This repository is a command-line multi-agent prototype for semantic network analysis.
It takes one semantic-network JSON snapshot as input, runs a fixed LangGraph workflow with LLM-backed agents, and prints a structured terminal report.

The prototype is designed for the current research stage:

- focus on running the main analysis flow end-to-end
- keep the delivery surface as CLI only
- make the result easy to demonstrate and explain
- keep all agents connected through one shared LLM configuration file

## What This Project Does

The workflow produces three required research outputs:

- global semantic state understanding
- semantic root-cause diagnosis
- closed-loop semantic control recommendation

The current implementation includes:

- fixed JSON schema input validation
- 8 LLM-backed agents
- LangGraph workflow orchestration
- shared structured-output parsing
- terminal report formatting
- sample input snapshots for demo and testing

The current implementation does not include:

- semantic extraction from raw network telemetry
- GUI or web frontend
- real network device write-back
- automatic continuous monitoring

## Agent Pipeline

The workflow always runs in this fixed order:

1. `topology_dependency`
2. `link_quality`
3. `routing_forwarding`
4. `node_bottleneck`
5. `flow_impact`
6. `global_state`
7. `fault_domain`
8. `closed_loop_control`

The final CLI report is assembled from the last three analysis stages:

- `global_state`
- `fault_domain`
- `closed_loop_control`

## Repository Structure

Important directories and files:

- `src/semantic_net_cli/agents/`: all agent implementations
- `src/semantic_net_cli/llm/`: LLM config loading, client, prompt, and structured-output logic
- `src/semantic_net_cli/workflow/`: LangGraph workflow state and graph assembly
- `src/semantic_net_cli/reporting/`: terminal report formatting
- `sample_data/`: demo snapshot inputs
- `config/llm_config.example.json`: tracked configuration template
- `config/llm_config.local.json`: recommended local untracked runtime config

## Environment Requirements

- Python `3.11` or newer
- network access for live LLM verification
- a valid model provider API key for real runs

## Installation

Recommended setup on Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

After editable install, the project provides this CLI command:

```powershell
semantic-net-cli --help
```

If you do not want to install the package yet, you can also run from source:

```powershell
$env:PYTHONPATH="src"
python -m semantic_net_cli.cli --help
```

## Configuration

### Configuration Files

Use these two files with different purposes:

- `config/llm_config.example.json`
  - tracked template
  - safe to commit
  - must not contain real secrets
- `config/llm_config.local.json`
  - local runtime config
  - should contain your real key
  - should remain untracked

The repository already ignores `config/llm_config.local.json`.

### Minimal Workflow

1. Copy the template:

```powershell
Copy-Item config\llm_config.example.json config\llm_config.local.json
```

2. Edit `config/llm_config.local.json`
3. Fill in your real provider values
4. Run the CLI with `--config config/llm_config.local.json`

### Configuration Fields

The shared config file has this structure:

```json
{
  "global": {
    "provider": "REPLACE_PROVIDER",
    "api_format": "REPLACE_API_FORMAT",
    "model": "REPLACE_MODEL",
    "api_key": "REPLACE_WITH_REAL_API_KEY",
    "base_url": "REPLACE_BASE_URL",
    "temperature": 0.2,
    "max_tokens": 1200,
    "thinking_enabled": false,
    "reasoning_effort": null,
    "stream": false,
    "response_format": "json_object"
  },
  "agents": {
    "topology_dependency": {},
    "link_quality": {},
    "routing_forwarding": {},
    "node_bottleneck": {},
    "flow_impact": {},
    "global_state": {},
    "fault_domain": {},
    "closed_loop_control": {}
  }
}
```

Field meanings:

- `provider`: logical provider name such as `deepseek`, `openai`, or another label you use locally
- `api_format`: request style expected by the client
  - current live implementation supports `openai`
- `model`: model name exposed by the provider
- `api_key`: real secret key for live runs
- `base_url`: provider API base URL
- `temperature`: generation temperature
- `max_tokens`: output token upper bound
- `thinking_enabled`: whether to request thinking mode when the provider supports it
- `reasoning_effort`: optional provider-specific reasoning level
- `stream`: whether to use streaming
  - current CLI usage should keep this `false`
- `response_format`: recommended `json_object` for structured agent output

### Per-Agent Overrides

Every agent inherits from `global` by default.
If you want to override one agent, put partial fields under `agents.<agent_name>`.

Example:

```json
{
  "global": {
    "provider": "deepseek",
    "api_format": "openai",
    "model": "deepseek-v4-flash",
    "api_key": "YOUR_REAL_KEY",
    "base_url": "https://api.deepseek.com",
    "temperature": 0.2,
    "max_tokens": 1200,
    "thinking_enabled": false,
    "reasoning_effort": null,
    "stream": false,
    "response_format": "json_object"
  },
  "agents": {
    "fault_domain": {
      "model": "deepseek-v4-pro"
    }
  }
}
```

## Running the CLI

### Help

```powershell
semantic-net-cli --help
```

### Standard Run

After editable install:

```powershell
semantic-net-cli sample_data\flow_impacted.json --config config\llm_config.local.json
```

From source without install:

```powershell
$env:PYTHONPATH="src"
python -m semantic_net_cli.cli sample_data/flow_impacted.json --config config/llm_config.local.json
```

### CLI Arguments

- positional `snapshot`
  - path to one semantic snapshot JSON file
- optional `--config`
  - path to the shared LLM config JSON file
  - default is `config/llm_config.example.json`

### Exit Codes

- `0`: success
- `1`: missing file such as snapshot or config
- `2`: invalid JSON or invalid snapshot schema
- `3`: workflow execution failure

## Input Schema

The input snapshot must be a JSON object with exactly these top-level fields:

- `metadata`
- `nodes`
- `links`
- `paths`
- `flows`

Core conventions in this prototype:

- `semantic_state` values
  - `normal`
  - `degraded`
  - `congested`
  - `abnormal`
- node `type` values
  - `host`
  - `switch`
  - `router`
- node `role` values
  - `edge`
  - `aggregation`
  - `core`
  - `exit`
- link `type` values
  - `wired`
  - `wireless`
  - `virtual`

Shared `metrics` fields:

- `latency`
- `loss`
- `utilization`
- `cpu`
- `queue`

Some metric values may be `null`, but the metric field names should stay consistent.

## Sample Data and Demo Usage

The repository includes four demo snapshots:

- `sample_data/link_degraded.json`
  - primary condition: degraded link
- `sample_data/node_bottleneck.json`
  - primary condition: node bottleneck
- `sample_data/path_abnormal.json`
  - primary condition: path abnormality
- `sample_data/flow_impacted.json`
  - primary condition: impacted critical business flow

Recommended demo order:

1. `sample_data/link_degraded.json`
2. `sample_data/node_bottleneck.json`
3. `sample_data/path_abnormal.json`
4. `sample_data/flow_impacted.json`

Recommended demo commands:

```powershell
semantic-net-cli sample_data\link_degraded.json --config config\llm_config.local.json
semantic-net-cli sample_data\node_bottleneck.json --config config\llm_config.local.json
semantic-net-cli sample_data\path_abnormal.json --config config\llm_config.local.json
semantic-net-cli sample_data\flow_impacted.json --config config\llm_config.local.json
```

Expected high-level demo behavior:

- `link_degraded.json`
  - degraded or abnormal global state
  - root cause centered on `link-ab`
  - control suggestion around reroute or pressure relief
- `node_bottleneck.json`
  - abnormal state driven by `node-core`
  - root cause centered on node overload
  - control suggestion around load redistribution
- `path_abnormal.json`
  - path-level abnormality in the global state
  - root cause centered on `path-12`
  - control suggestion around forwarding-path adjustment
- `flow_impacted.json`
  - service degradation with business impact
  - root cause connected to upstream node and link degradation
  - control suggestion prioritizing critical flow protection

## Output Format

The CLI always prints four fixed sections in this order:

1. `Input Summary`
2. `Global Semantic State`
3. `Semantic Root-Cause Diagnosis`
4. `Closed-Loop Semantic Control`

The final report answers three questions:

- what state is the network currently in
- why did it become that state
- what control action should be taken next

## Report Term Glossary

The report contains a small set of recurring status words and field names.
Use the following meanings when reading the output.

### Status Terms

- `normal`
  - no clear abnormal signal is currently identified in that object or summary layer
- `degraded`
  - the object or the whole network is still functioning, but service quality has declined
  - typical signals include elevated latency, packet loss, congestion, overload, or impacted flows
- `congested`
  - traffic pressure is high enough to indicate congestion behavior
  - in this prototype, this usually means queueing or utilization pressure is a visible cause
- `abnormal`
  - the condition is more serious than simple quality decline
  - it usually implies a strong fault signal, unstable behavior, or a dominant bottleneck/failure condition
- `unknown`
  - the workflow continued, but that agent could not produce a valid structured conclusion
  - this does not automatically mean the network is healthy; it means the corresponding step was inconclusive

### Report Fields

- `Global Semantic State`
  - the network-wide status judgment after combining lower-level agent results
- `Semantic Root-Cause Diagnosis`
  - the explanation of why the network reached the current state
- `Closed-Loop Semantic Control`
  - the recommendation of what should be adjusted next
  - in the current prototype, this is recommendation only and does not execute real control
- `summary`
  - a short natural-language statement of the section conclusion
- `key_evidence`
  - the most important supporting objects and reasons behind a conclusion
- `primary_cause`
  - the main reason or dominant fault domain judged by the fault diagnosis stage
- `secondary_causes`
  - additional but less dominant contributing causes
- `recommended_action`
  - the single action the control stage prefers most
- `candidate_actions`
  - a list of alternative control actions considered plausible
- `target_objects`
  - the nodes, links, paths, or flows that the suggested action is mainly aimed at
- `control_reasoning`
  - the explanation for why those control suggestions were chosen

### How To Read `degraded`

In this project, `degraded` does not simply mean "wrong" or "failed".
It specifically means the object or the whole network is still operating, but with reduced quality or rising risk.

Typical examples:

- a link still forwards traffic, but with higher latency or loss
- a node is still running, but shows utilization or queue pressure
- a path still exists, but depends on degraded components
- a business flow still works, but the service quality is no longer normal

## Testing

Run the full local test suite:

```powershell
pytest
```

Run focused subsets:

```powershell
python -m pytest tests/llm/test_config_loader.py
python -m pytest tests/llm/test_client.py
python -m pytest tests/workflow/test_graph.py
python -m pytest tests/reporting/test_formatter.py
python -m pytest tests/test_cli.py
```

## Live Verification Status

Current status of the prototype:

- local contract tests are passing
- CLI workflow is implemented end-to-end
- at least one live end-to-end run has been completed with a real provider config

## Troubleshooting

### `LLM config file not found`

Check the path passed to `--config`.

### `Invalid snapshot schema`

The input JSON is present but does not match the fixed schema.
Check top-level fields and enum values.

### `Workflow execution failed: Connection error.`

This usually means one of these:

- invalid `base_url`
- invalid `api_key`
- provider-side network or DNS issue
- firewall or sandbox restriction in the current environment

### CLI prints `unknown` sections

This usually means the model responded, but the output did not satisfy the required structured JSON contract.
Check:

- model choice
- `response_format`
- prompt adherence
- whether the provider supports the requested JSON mode cleanly

## Security Notes

- never commit real API keys into tracked files
- keep real credentials in `config/llm_config.local.json`
- rotate any key that was ever pasted into chat or accidentally written into a tracked file

## Acceptance Summary

The project currently satisfies the prototype goals:

- fixed JSON input contract
- network-domain agent decomposition
- all agents routed through shared LLM configuration
- LangGraph fixed-order orchestration
- CLI-only delivery
- structured output for global state, root cause, and control recommendation
- runnable demo samples
