# Semantic Network Analysis CLI

This project is a command-line prototype for semantic twin network analysis and closed-loop control feedback. It reads a UTF-8 JSONL semantic topology graph, asks a 5+3 multi-agent workflow to understand the network state, analyzes likely causes, generates optimization suggestions, simulates control execution, writes feedback into the semantic twin graph, and records each loop iteration under `result/`.

The prototype is designed for research and experimentation. It does not execute real network-device commands.

## What It Does

Given a semantic twin graph `G_k`, the CLI performs this loop:

```text
G_k semantic twin graph
-> front-layer fact extraction agents
-> F_k^mid intermediate semantic facts
-> understanding agent: S_k current network state
-> analysis agent: C_k cause set
-> optimization agent: U_k optimization suggestion
-> simulated control execution
-> control effect propagation
-> feedback-updated semantic twin graph G_k+1
-> stability assessment
-> next iteration or stop
```

In plain terms:

- It reads a network described as nodes, interfaces, channels, metrics, relations, and historical actions.
- It extracts topology, routing, traffic, performance, and node-semantic facts.
- It decides whether the network is normal or degraded.
- It explains the likely cause of degradation.
- It suggests a control action.
- It simulates the action instead of touching real devices.
- It updates the semantic twin graph with action history, metric changes, and feedback metadata.
- It repeats for a configured number of iterations or stops early when stable or oscillating.

## Architecture

The workflow uses a 5+3 agent structure.

### Front-Layer Agents

These agents extract intermediate facts only. They do not make final decisions.

- `topology_agent`: connectivity, key links, topology changes, possible isolation.
- `routing_agent`: routes, next hops, path availability.
- `traffic_agent`: traffic demands, traffic concentration, hotspots.
- `performance_agent`: delay, loss, throughput, utilization, retransmission, SNR/RSSI, queue length.
- `node_semantic_agent`: node roles, interface status, deployment relations, action/event history.

### Back-Layer Agents

These agents run after fact aggregation:

- `understanding_agent`: produces `S_k`, the current network state.
- `analysis_agent`: produces `C_k`, the cause set.
- `optimization_agent`: produces `U_k`, the optimization suggestion.

The current implementation runs these agents serially. Parallel front-layer execution is reserved for future evaluation.

## Closed-Loop Control Feedback

The control stage is simulated. It produces a `ControlExecutionRecord`, then applies deterministic feedback into the semantic twin graph.

The feedback stage can:

- append `control_execution` records to target objects' `actions[]`;
- write `attributes.control_feedback`;
- update coupled metrics under `attributes.metrics`;
- propagate effects to relation-connected objects;
- compare `G_k` and `G_k+1` and save topology/metric changes.

For wireless channel adjustment, the prototype may conservatively:

- reduce loss rate;
- reduce retransmission rate;
- increase SNR and throughput;
- reduce delay and utilization;
- improve connected wireless interface metrics.

All metric effects are bounded and can be damped.

## Stability And Damped Mode

Each loop iteration receives a stability assessment:

- `improving`: the loop is still changing and no oscillation was detected.
- `stable`: the network stayed normal for the configured stability window.
- `damped`: an A-B-A-B pattern was detected and the loop applies a smaller control effect.
- `oscillating`: oscillation persisted after damping, so the loop stops.

Typical terminal reasons:

- `stable_state_reached`
- `oscillation_persisted_after_damping`
- `max_iterations_reached`

## Main Technologies

- Python 3.11+
- LangGraph for workflow orchestration
- OpenAI-compatible Chat Completions API for LLM calls
- Pydantic v2 for schema validation
- JSONL for semantic twin graph input/output
- Pytest for automated tests

The CLI package is installed as:

```text
semantic-net-cli
```

## Repository Layout

```text
config/                  LLM configuration templates
sample_data/             Example semantic twin JSONL inputs
src/semantic_net_cli/
  agents/                5+3 agent implementations
  control/               simulated execution, feedback, propagation, loop, stability
  io/                    JSONL loading and writing
  llm/                   LLM client, config loader, output parser
  models/                Pydantic data models
  reporting/             result logger and text report sections
  workflow/              LangGraph workflow assembly
tests/                   pytest test suite
result/                  local runtime outputs, not source data
```

## Installation

From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

## LLM Configuration

Copy the example configuration:

```powershell
Copy-Item config\llm_config.example.json config\llm_config.local.json
```

Then edit `config\llm_config.local.json`:

```json
{
  "global": {
    "provider": "your_provider",
    "api_format": "openai",
    "model": "your_model_name",
    "api_key": "your_api_key",
    "base_url": "https://your-llm-endpoint.example.com",
    "temperature": 0.2,
    "max_tokens": 10000,
    "thinking_enabled": false,
    "reasoning_effort": null,
    "stream": false,
    "response_format": "json_object"
  },
  "agents": {
    "topology_agent": {},
    "routing_agent": {},
    "traffic_agent": {},
    "performance_agent": {},
    "node_semantic_agent": {},
    "understanding_agent": {},
    "analysis_agent": {},
    "optimization_agent": {}
  }
}
```

`global` settings are inherited by every agent. You can override settings for a specific agent under `agents`.

## Usage

Run one iteration:

```powershell
semantic-net-cli sample_data\semantic_twin_hybrid.jsonl --config config\llm_config.local.json
```

Run up to three closed-loop iterations, write result artifacts, and export the final graph:

```powershell
semantic-net-cli sample_data\semantic_twin_hybrid.jsonl --config config\llm_config.local.json --max-iterations 3 --result-dir result --updated-graph-output sample_data\semantic_twin_hybrid.next.jsonl
```

Run from source without installing the console script:

```powershell
$env:PYTHONPATH="src"
python -m semantic_net_cli.cli sample_data\semantic_twin_hybrid.jsonl --config config\llm_config.local.json
```

## CLI Parameters

```text
semantic-net-cli SNAPSHOT [--config PATH] [--updated-graph-output PATH] [--max-iterations N] [--result-dir PATH]
```

- `snapshot`: required JSONL semantic twin graph path.
- `--config`: LLM config path. Default: `config/llm_config.example.json`.
- `--updated-graph-output`: optional final `G_k+1` JSONL output path.
- `--max-iterations`: maximum closed-loop iterations. Default: `1`.
- `--result-dir`: directory for timestamped run artifacts. Default: `result`.

## Input Format

Input must be JSONL. Each non-empty line must be one semantic twin object:

```json
{"id":"r1","type":"node:router","attributes":{},"relations":{},"actions":[]}
```

Each object requires:

- `id`
- `type`
- `attributes`
- `relations`
- `actions`

Allowed base types:

- `node:*`
- `interface:*`
- `channel:*`

Standalone `path:*`, `route:*`, `transmission:*`, and `event:*` objects are intentionally rejected. Route/path information should live inside `relations.routes_to[]`; traffic demand should live inside `relations.transmits_to[]`; events should live inside `actions[]` or status/metric fields.

## Output Files

Each run creates:

```text
result/<run-timestamp>/
```

Each successful iteration creates:

```text
iteration_001/
  input_graph.jsonl
  intermediate_fact_set.json
  network_state.json
  cause_set.json
  optimization_action.json
  control_execution.json
  effect_propagation.json
  stability_assessment.json
  topology_changes.json
  updated_graph.jsonl
  report.txt
```

At the end of a successful run:

```text
run_summary.json
final_graph.jsonl
```

`report.txt` is the human-readable summary. It contains:

1. `Input Summary`
2. `Intermediate Semantic Fact Set`
3. `Current Network State S_k`
4. `Cause Set C_k`
5. `Optimization Action U_k`
6. `Control Action Execution`
7. `Control Effect Propagation`
8. `Loop Stability Assessment`
9. `Feedback To Semantic Twin G_k+1`

## Debugging LLM Output

If an agent returns malformed or truncated JSON, the CLI reports the failing agent name and saves the raw LLM output:

```text
Workflow execution failed: agent=performance_agent: Unterminated string ...
Raw LLM output saved under: result\<run-timestamp>\debug\raw_llm_outputs
Relative debug path: debug/raw_llm_outputs
```

Debug files are written under:

```text
result/<run-timestamp>/debug/raw_llm_outputs/iteration_XXX/
  <agent_name>.txt
  parse_error.json
```

This is useful when an LLM response is cut off before the JSON object closes. If this happens often, increase `max_tokens`, reduce requested fact volume, or split an agent into smaller tasks.

## Important Notes

- The project is a prototype, not a production network controller.
- It does not run real network commands.
- Output quality depends on the configured LLM.
- `response_format: "json_object"` helps, but it cannot prevent truncation if the model runs out of output tokens.
- `max_tokens` should be large enough for structured JSON output.
- `result/` contains local run artifacts and should usually not be committed.
- The closed-loop metric propagation model is deterministic and conservative; it is not a full physical network simulator.

## Testing

Run the full test suite:

```powershell
python -m pytest -q
```

Common focused checks:

```powershell
python -m pytest tests/test_cli.py -q
python -m pytest tests/control/test_loop.py -q
python -m pytest tests/reporting/test_formatter.py -q
```
