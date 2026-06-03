# 语义网络分析 CLI 原型

本仓库是一个面向语义孪生网络分析的命令行原型。它读取 UTF-8 JSONL 语义孪生图，运行两层 LangGraph 工作流，并在终端输出中间事实、当前状态、成因集合和优化建议。

## 工作流

运行架构如下：

```text
G_k JSONL 语义孪生输入
-> 前层分视角智能体
-> F_k^mid
-> 理解智能体 S_k
-> 分析智能体 C_k
-> 优化智能体 U_k
-> CLI 报告
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

不安装、直接从源码运行：

```powershell
$env:PYTHONPATH="src"
python -m semantic_net_cli.cli sample_data/semantic_twin_hybrid.jsonl --config config/llm_config.local.json
```

## 输出

CLI 报告固定按以下顺序输出：

1. `Input Summary`
2. `Intermediate Semantic Fact Set`
3. `Current Network State S_k`
4. `Cause Set C_k`
5. `Optimization Action U_k`

`Optimization Action U_k` 只表示优化建议，本原型不会执行真实网络控制。

## 测试

```powershell
python -m pytest -q
```

常用子集：

```powershell
python -m pytest tests/io/test_jsonl_loader.py tests/test_cli.py -q
python -m pytest tests/workflow/test_graph.py tests/reporting/test_formatter.py -q
```
