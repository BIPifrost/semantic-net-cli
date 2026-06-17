# Semantic Network Analysis CLI Prototype

This repository is a command-line prototype for semantic twin network analysis. It accepts a UTF-8 JSONL semantic twin graph, runs a two-layer LangGraph workflow, simulates closed-loop control execution, writes feedback into the semantic twin graph, and prints a compact terminal summary.

## Workflow

The runtime architecture is:

```text
G_k JSONL semantic twin input
-> front-layer perspective agents
-> F_k^mid
-> Understanding Agent S_k
-> Analysis Agent C_k
-> Optimization Agent U_k
-> simulated control execution
-> feedback-updated semantic twin graph G_k+1
-> CLI summary and result artifacts
```

Front-layer agents only extract intermediate facts:

- `topology_agent`
- `routing_agent`
- `traffic_agent`
- `performance_agent`
- `node_semantic_agent`

Back-layer task agents run strictly in series:

- `understanding_agent` produces `S_k`
- `analysis_agent` produces `C_k`
- `optimization_agent` produces `U_k`

Control execution is simulated. The prototype appends structured feedback records to target twin objects as `actions[]` and `attributes.control_feedback`. It records metric observations, but this version does not propagate one metric change into other related metrics. The five front-layer agents remain serial in this version; parallel front-layer execution is reserved for future evaluation.

## Input Contract

Input must be JSONL, not one large JSON object. Every non-empty line must be one semantic twin object with:

- `id`
- `type`
- `attributes`
- `relations`
- `actions`

Allowed `type` bases are exactly:

- `node:*`
- `interface:*`
- `channel:*`

The CLI rejects standalone `path:*`, `route:*`, `transmission:*`, and `event:*` twin object types. Route/path information belongs in `relations.routes_to[].channels`; traffic demand belongs in `relations.transmits_to[]`; events and alarms belong in entity `actions[]` or status/metric changes.

## Installation

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

## Configuration

Copy the template and fill in your provider settings:

```powershell
Copy-Item config\llm_config.example.json config\llm_config.local.json
```

The shared config uses a `global` section inherited by all agents. Agent-specific overrides can be added under the new 5+3 agent names.

## Running

After editable install:

```powershell
semantic-net-cli sample_data\semantic_twin_hybrid.jsonl --config config\llm_config.local.json
```

Run multiple closed-loop iterations and write the final updated graph:

```powershell
semantic-net-cli sample_data\semantic_twin_hybrid.jsonl --config config\llm_config.local.json --max-iterations 3 --result-dir result --updated-graph-output sample_data\semantic_twin_hybrid.next.jsonl
```

From source:

```powershell
$env:PYTHONPATH="src"
python -m semantic_net_cli.cli sample_data/semantic_twin_hybrid.jsonl --config config/llm_config.local.json
```

## Output

The terminal prints a compact closed-loop summary:

```text
Closed-Loop Run Summary
run_dir: result/20260607-120000
iteration_count: 3

[1/3] S_k=degraded | C_k=wireless degradation | U_k=adjust channel | execution=succeeded | changed_objects=1

final_graph: result/20260607-120000/final_graph.jsonl
```

Detailed per-iteration artifacts are written under `result/<run-timestamp>/iteration_001/`:

- `input_graph.jsonl`
- `intermediate_fact_set.json`
- `network_state.json`
- `cause_set.json`
- `optimization_action.json`
- `control_execution.json`
- `topology_changes.json`
- `updated_graph.jsonl`
- `report.txt`

Each `report.txt` contains these sections in order:

1. `Input Summary`
2. `Intermediate Semantic Fact Set`
3. `Current Network State S_k`
4. `Cause Set C_k`
5. `Optimization Action U_k`
6. `Control Action Execution`
7. `Feedback To Semantic Twin G_k+1`

The prototype does not execute real network device changes.

## Testing

```powershell
python -m pytest -q
```

Focused checks:

```powershell
python -m pytest tests/io/test_jsonl_loader.py tests/test_cli.py -q
python -m pytest tests/workflow/test_graph.py tests/reporting/test_formatter.py -q
```
