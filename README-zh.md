# 语义网络分析 CLI

本项目是一个用于语义孪生网络分析与闭环控制反馈的命令行原型。它读取 UTF-8 JSONL 格式的语义拓扑图，通过 5+3 多智能体工作流理解当前网络状态、分析故障原因、生成优化建议、模拟控制动作执行，并把执行反馈写回语义孪生图。每一轮闭环过程都会记录在 `result/` 目录下。

本项目面向研究和实验验证，不会执行真实网络设备命令。

## 项目在做什么

给定一张语义孪生网络图 `G_k`，CLI 会执行下面的闭环流程：

```text
G_k 语义孪生图
-> 前层事实抽取智能体
-> F_k^mid 中间语义事实
-> 理解智能体：S_k 当前网络状态
-> 分析智能体：C_k 原因集合
-> 优化智能体：U_k 优化建议
-> 模拟控制动作执行
-> 控制效果传播
-> 反馈更新后的语义孪生图 G_k+1
-> 稳定性评估
-> 进入下一轮或停止
```

通俗地说，它会做这些事：

- 读取由节点、接口、信道、指标、关系、历史动作组成的网络图。
- 抽取拓扑、路由、流量、性能、节点语义等事实。
- 判断当前网络是正常还是退化。
- 解释网络退化的可能原因。
- 给出优化建议。
- 只做模拟执行，不会真的控制设备。
- 把动作历史、指标变化、反馈信息写回语义孪生图。
- 根据配置的最大轮数继续循环，或者在稳定/震荡时提前停止。

## 系统架构

项目采用 5+3 agent 结构。

### 前层 5 个智能体

前层智能体只负责抽取中间事实，不直接给最终结论。

- `topology_agent`：连接关系、关键链路、拓扑变化、潜在孤立区域。
- `routing_agent`：路由、下一跳、路径可用性。
- `traffic_agent`：流量需求、流量集中点、热点链路。
- `performance_agent`：时延、丢包、吞吐量、利用率、重传率、SNR/RSSI、队列长度。
- `node_semantic_agent`：节点角色、接口状态、部署关系、历史动作/事件。

### 后层 3 个智能体

后层智能体在事实聚合后串行执行：

- `understanding_agent`：输出 `S_k`，即当前网络状态。
- `analysis_agent`：输出 `C_k`，即原因集合。
- `optimization_agent`：输出 `U_k`，即优化建议。

当前版本中，前层和后层 agent 都是串行执行。前层并行执行可以作为后续版本的实验方向。

## 闭环控制反馈

控制阶段是模拟执行。系统会生成一个 `ControlExecutionRecord`，然后把确定性的反馈写入语义孪生图。

反馈阶段会做这些事：

- 给目标对象的 `actions[]` 追加 `control_execution` 记录；
- 写入 `attributes.control_feedback`；
- 修改 `attributes.metrics` 中的耦合指标；
- 把控制效果传播到关系相连的对象；
- 对比 `G_k` 和 `G_k+1`，保存拓扑和指标变化。

以无线信道调整为例，原型可能会保守地模拟：

- 降低丢包率；
- 降低重传率；
- 提高 SNR 和吞吐量；
- 降低时延和利用率；
- 改善相关无线接口的指标。

所有指标变化都有边界约束，并支持阻尼模式。

## 稳定性与阻尼模式

每轮闭环都会生成稳定性评估：

- `improving`：还在变化，暂未发现震荡。
- `stable`：网络在配置窗口内保持正常稳定状态。
- `damped`：检测到 A-B-A-B 模式，进入阻尼模式，减小控制效果。
- `oscillating`：阻尼后仍然震荡，循环停止。

常见终止原因：

- `stable_state_reached`
- `oscillation_persisted_after_damping`
- `max_iterations_reached`

## 主要技术

- Python 3.11+
- LangGraph：组织多 agent 工作流
- OpenAI-compatible Chat Completions API：调用大模型
- Pydantic v2：数据结构和输出校验
- JSONL：语义孪生图输入/输出
- Pytest：自动化测试

安装后可使用的命令是：

```text
semantic-net-cli
```

## 项目结构

```text
config/                  LLM 配置模板
sample_data/             示例语义孪生 JSONL 输入
src/semantic_net_cli/
  agents/                5+3 agent 实现
  control/               模拟执行、反馈、效果传播、闭环、稳定性
  io/                    JSONL 读取和写出
  llm/                   LLM 客户端、配置加载、输出解析
  models/                Pydantic 数据模型
  reporting/             结果日志和 report.txt 生成
  workflow/              LangGraph 工作流装配
tests/                   pytest 测试
result/                  本地运行输出，不是源码数据
```

## 安装

在项目根目录执行：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

## LLM 配置

复制配置模板：

```powershell
Copy-Item config\llm_config.example.json config\llm_config.local.json
```

然后编辑 `config\llm_config.local.json`：

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

`global` 中的配置会被所有 agent 继承。如果某个 agent 需要单独设置模型、温度或 token 上限，可以在 `agents` 中覆盖。

## 使用方法

运行一轮分析：

```powershell
semantic-net-cli sample_data\semantic_twin_hybrid.jsonl --config config\llm_config.local.json
```

最多运行三轮闭环，写出结果目录，并导出最终图：

```powershell
semantic-net-cli sample_data\semantic_twin_hybrid.jsonl --config config\llm_config.local.json --max-iterations 3 --result-dir result --updated-graph-output sample_data\semantic_twin_hybrid.next.jsonl
```

如果没有安装命令行脚本，也可以从源码直接运行：

```powershell
$env:PYTHONPATH="src"
python -m semantic_net_cli.cli sample_data\semantic_twin_hybrid.jsonl --config config\llm_config.local.json
```

## 命令行参数

```text
semantic-net-cli SNAPSHOT [--config PATH] [--updated-graph-output PATH] [--max-iterations N] [--result-dir PATH]
```

- `snapshot`：必填，语义孪生图 JSONL 文件路径。
- `--config`：LLM 配置文件路径，默认 `config/llm_config.example.json`。
- `--updated-graph-output`：可选，最终 `G_k+1` JSONL 输出路径。
- `--max-iterations`：最大闭环轮数，默认 `1`。
- `--result-dir`：带时间戳的结果目录根路径，默认 `result`。

## 输入格式

输入必须是 JSONL。每个非空行是一条语义孪生对象：

```json
{"id":"r1","type":"node:router","attributes":{},"relations":{},"actions":[]}
```

每个对象必须包含：

- `id`
- `type`
- `attributes`
- `relations`
- `actions`

允许的基础类型：

- `node:*`
- `interface:*`
- `channel:*`

项目会拒绝独立的 `path:*`、`route:*`、`transmission:*`、`event:*` 对象。路径/路由信息应放在 `relations.routes_to[]` 中；流量需求应放在 `relations.transmits_to[]` 中；事件应放在 `actions[]` 或状态/指标字段中。

## 输出文件

每次运行会创建：

```text
result/<运行时间>/
```

每个成功完成的迭代会创建：

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

一次完整运行结束后还会生成：

```text
run_summary.json
final_graph.jsonl
```

`report.txt` 是适合人阅读的总结报告，包含：

1. `Input Summary`
2. `Intermediate Semantic Fact Set`
3. `Current Network State S_k`
4. `Cause Set C_k`
5. `Optimization Action U_k`
6. `Control Action Execution`
7. `Control Effect Propagation`
8. `Loop Stability Assessment`
9. `Feedback To Semantic Twin G_k+1`

## 调试 LLM 输出

如果某个 agent 返回了不完整或非法 JSON，CLI 会报出具体 agent 名称，并保存原始 LLM 输出：

```text
Workflow execution failed: agent=performance_agent: Unterminated string ...
Raw LLM output saved under: result\<run-timestamp>\debug\raw_llm_outputs
Relative debug path: debug/raw_llm_outputs
```

调试文件位置：

```text
result/<运行时间>/debug/raw_llm_outputs/iteration_XXX/
  <agent_name>.txt
  parse_error.json
```

这通常说明 LLM 输出 JSON 时被截断，或者没有正确闭合字符串/括号。如果频繁出现，可以提高 `max_tokens`、减少每个 agent 的输出事实数量，或者把某个大 agent 拆成更小任务。

## 注意事项

- 本项目是原型，不是生产级网络控制器。
- 不会执行真实网络设备命令。
- 输出质量依赖所配置的大模型。
- `response_format: "json_object"` 能减少格式跑偏，但不能防止输出 token 不够导致截断。
- `max_tokens` 需要足够大，尤其是让模型输出结构化 JSON 时。
- `result/` 是本地运行产物，通常不应提交到 Git。
- 闭环指标传播是确定性、保守的模拟，不是完整物理网络仿真器。

## 测试

运行完整测试：

```powershell
python -m pytest -q
```

常用局部测试：

```powershell
python -m pytest tests/test_cli.py -q
python -m pytest tests/control/test_loop.py -q
python -m pytest tests/reporting/test_formatter.py -q
```
