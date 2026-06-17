# 语义网络分析 CLI 原型

本仓库是一个面向语义孪生网络分析的命令行原型。它读取 UTF-8 JSONL 语义孪生图，运行两层 LangGraph 工作流，模拟闭环控制动作执行，将反馈写回语义孪生图，并在终端输出简洁摘要。

## 工作流

运行架构如下：

```text
G_k JSONL 语义孪生输入
-> 前层分视角智能体
-> F_k^mid
-> 理解智能体 S_k
-> 分析智能体 C_k
-> 优化智能体 U_k
-> 模拟控制动作执行
-> 反馈更新后的语义孪生图 G_k+1
-> CLI 摘要和结果文件
```

前层智能体只抽取中间语义事实：

- `topology_agent`
- `routing_agent`
- `traffic_agent`
- `performance_agent`
- `node_semantic_agent`

后层任务智能体严格串行执行：

- `understanding_agent` 输出 `S_k`
- `analysis_agent` 输出 `C_k`
- `optimization_agent` 输出 `U_k`

控制执行阶段采用模拟执行。本原型会把结构化反馈记录追加到目标孪生对象的 `actions[]` 和 `attributes.control_feedback` 中。本版只记录指标观测，不传播某个指标变化对其他关联指标的影响。前层 5 个分视角智能体本版仍然串行执行；并行化留作后续版本评估。

## 输入契约

输入必须是 JSONL，而不是一个大的 JSON 对象。每个非空行必须表示一个真实网络实体孪生体，并包含：

- `id`
- `type`
- `attributes`
- `relations`
- `actions`

允许的 `type` 基类只有：

- `node:*`
- `interface:*`
- `channel:*`

CLI 会拒绝独立的 `path:*`、`route:*`、`transmission:*`、`event:*` 类型。路径和路由信息应写在 `relations.routes_to[].channels` 中；业务流量需求应写在 `relations.transmits_to[]` 中；事件和告警应写在实体 `actions[]` 或状态、指标变化中。

## 安装

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

## 配置

复制配置模板，并填入你的模型服务参数：

```powershell
Copy-Item config\llm_config.example.json config\llm_config.local.json
```

配置文件中的 `global` 字段会被所有 agent 继承。需要单独覆盖时，可以在 `agents` 下使用新的 5+3 agent 名称添加局部配置。

## 运行

可编辑安装后运行：

```powershell
semantic-net-cli sample_data\semantic_twin_hybrid.jsonl --config config\llm_config.local.json
```

运行多轮闭环，并写出最终更新后的拓扑：

```powershell
semantic-net-cli sample_data\semantic_twin_hybrid.jsonl --config config\llm_config.local.json --max-iterations 3 --result-dir result --updated-graph-output sample_data\semantic_twin_hybrid.next.jsonl
```

不安装、直接从源码运行：

```powershell
$env:PYTHONPATH="src"
python -m semantic_net_cli.cli sample_data/semantic_twin_hybrid.jsonl --config config/llm_config.local.json
```

## 输出

终端输出简洁闭环摘要：

```text
Closed-Loop Run Summary
run_dir: result/20260607-120000
iteration_count: 3

[1/3] S_k=degraded | C_k=wireless degradation | U_k=adjust channel | execution=succeeded | changed_objects=1

final_graph: result/20260607-120000/final_graph.jsonl
```

每轮详细结果写入 `result/<运行时间>/iteration_001/`：

- `input_graph.jsonl`
- `intermediate_fact_set.json`
- `network_state.json`
- `cause_set.json`
- `optimization_action.json`
- `control_execution.json`
- `topology_changes.json`
- `updated_graph.jsonl`
- `report.txt`

每轮 `report.txt` 固定按以下顺序输出：

1. `Input Summary`
2. `Intermediate Semantic Fact Set`
3. `Current Network State S_k`
4. `Cause Set C_k`
5. `Optimization Action U_k`
6. `Control Action Execution`
7. `Feedback To Semantic Twin G_k+1`

本原型不会执行真实网络设备控制。

## 测试

```powershell
python -m pytest -q
```

常用子集：

```powershell
python -m pytest tests/io/test_jsonl_loader.py tests/test_cli.py -q
python -m pytest tests/workflow/test_graph.py tests/reporting/test_formatter.py -q
```
