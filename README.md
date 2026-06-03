# Semantic Network Analysis CLI Prototype

This repository is a command-line prototype for semantic twin network analysis. It accepts a UTF-8 JSONL semantic twin graph, runs a two-layer LangGraph workflow, and prints a terminal-readable report with intermediate facts, current state, causes, and recommended optimization actions.

## Workflow

The runtime architecture is:

```text
G_k JSONL semantic twin input
-> front-layer perspective agents
-> F_k^mid
-> Understanding Agent S_k
-> Analysis Agent C_k
-> Optimization Agent U_k
-> CLI report
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

From source:

```powershell
$env:PYTHONPATH="src"
python -m semantic_net_cli.cli sample_data/semantic_twin_hybrid.jsonl --config config/llm_config.local.json
```

## Output

The report prints these sections in order:

1. `Input Summary`
2. `Intermediate Semantic Fact Set`
3. `Current Network State S_k`
4. `Cause Set C_k`
5. `Optimization Action U_k`

`Optimization Action U_k` is a recommendation only. The prototype does not execute real network control.

## Testing

```powershell
python -m pytest -q
```

Focused checks:

```powershell
python -m pytest tests/io/test_jsonl_loader.py tests/test_cli.py -q
python -m pytest tests/workflow/test_graph.py tests/reporting/test_formatter.py -q
```
