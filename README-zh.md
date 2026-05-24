# 语义化网络分析命令行原型

本仓库是一个面向语义化网络分析的命令行多智能体原型。
它接收一份语义化网络 JSON 快照作为输入，使用固定的 LangGraph 工作流调度多个接入 LLM 的 Agent，并在终端输出结构化分析报告。

这个原型服务于当前研究阶段，设计目标是：

- 先把主分析流程完整跑通
- 交付形式保持为 CLI
- 结果便于展示和解释
- 所有 Agent 通过同一份 LLM 配置文件统一接入模型

## 项目功能

该工作流输出三类核心研究结果：

- 全局语义状态理解
- 语义根因诊断
- 闭环语义控制建议

当前实现已经包含：

- 固定 JSON Schema 输入校验
- 8 个接入 LLM 的 Agent
- LangGraph 工作流编排
- 统一的结构化输出解析
- 终端报告格式化输出
- 用于演示和测试的样例输入

当前实现暂不包含：

- 原始网络遥测到语义化网络的生成过程
- GUI 或 Web 前端
- 真实网络设备写回
- 持续在线监控

## Agent 流程

工作流固定按以下顺序执行：

1. `topology_dependency`
2. `link_quality`
3. `routing_forwarding`
4. `node_bottleneck`
5. `flow_impact`
6. `global_state`
7. `fault_domain`
8. `closed_loop_control`

最终 CLI 报告主要由最后三类结果组成：

- `global_state`
- `fault_domain`
- `closed_loop_control`

## 仓库结构

主要目录和文件如下：

- `src/semantic_net_cli/agents/`：所有 Agent 实现
- `src/semantic_net_cli/llm/`：LLM 配置加载、客户端、提示词和结构化输出逻辑
- `src/semantic_net_cli/workflow/`：LangGraph 状态定义与工作流图装配
- `src/semantic_net_cli/reporting/`：终端报告格式化
- `sample_data/`：演示快照输入
- `config/llm_config.example.json`：可提交的配置模板
- `config/llm_config.local.json`：推荐的本地未跟踪运行配置

## 环境要求

- Python `3.11` 或更高版本
- 若要做真实 LLM 验证，需要具备网络访问能力
- 若要做真实运行，需要有效的模型提供方 API key

## 安装方法

Windows PowerShell 推荐安装方式：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

以可编辑模式安装后，可以直接使用如下 CLI 命令：

```powershell
semantic-net-cli --help
```

如果你暂时不想安装，也可以直接从源码运行：

```powershell
$env:PYTHONPATH="src"
python -m semantic_net_cli.cli --help
```

## 配置方法

### 配置文件说明

推荐区分以下两类配置文件：

- `config/llm_config.example.json`
  - 可提交的模板文件
  - 可以放在仓库里
  - 不能包含真实密钥
- `config/llm_config.local.json`
  - 本地运行配置
  - 应包含真实 key
  - 不应提交到仓库

仓库已经默认忽略 `config/llm_config.local.json`。

### 最简配置流程

1. 复制模板文件：

```powershell
Copy-Item config\llm_config.example.json config\llm_config.local.json
```

2. 编辑 `config/llm_config.local.json`
3. 填入真实模型服务配置
4. 运行 CLI 时使用 `--config config/llm_config.local.json`

### 配置字段说明

共享配置文件结构如下：

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

字段含义：

- `provider`：逻辑上的提供方标识，例如 `deepseek`、`openai` 等
- `api_format`：客户端请求格式
  - 当前 live 实现支持 `openai`
- `model`：模型名
- `api_key`：真实运行时使用的密钥
- `base_url`：模型服务 API 基础地址
- `temperature`：生成温度
- `max_tokens`：最大输出 token 数
- `thinking_enabled`：如果提供方支持，是否启用 thinking 模式
- `reasoning_effort`：可选的推理强度配置
- `stream`：是否开启流式输出
  - 当前 CLI 场景建议保持 `false`
- `response_format`：建议使用 `json_object`，便于结构化输出

### Per-Agent 覆盖

默认情况下，所有 Agent 都继承 `global` 配置。
如果需要对单个 Agent 做覆盖，可以在 `agents.<agent_name>` 下填写部分字段。

示例：

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

## 运行方法

### 查看帮助

```powershell
semantic-net-cli --help
```

### 标准运行

可编辑安装后运行：

```powershell
semantic-net-cli sample_data\flow_impacted.json --config config\llm_config.local.json
```

不安装、直接从源码运行：

```powershell
$env:PYTHONPATH="src"
python -m semantic_net_cli.cli sample_data/flow_impacted.json --config config/llm_config.local.json
```

### CLI 参数说明

- 位置参数 `snapshot`
  - 一份语义化网络 JSON 快照路径
- 可选参数 `--config`
  - 共享 LLM 配置文件路径
  - 默认值为 `config/llm_config.example.json`

### 退出码说明

- `0`：成功
- `1`：文件缺失，例如 snapshot 或 config 不存在
- `2`：输入 JSON 非法或 snapshot schema 不合法
- `3`：工作流执行失败

## 输入 Schema 说明

输入快照必须是一个 JSON 对象，并且包含以下五个顶层字段：

- `metadata`
- `nodes`
- `links`
- `paths`
- `flows`

当前原型中约定的核心枚举如下：

- `semantic_state`
  - `normal`
  - `degraded`
  - `congested`
  - `abnormal`
- 节点 `type`
  - `host`
  - `switch`
  - `router`
- 节点 `role`
  - `edge`
  - `aggregation`
  - `core`
  - `exit`
- 链路 `type`
  - `wired`
  - `wireless`
  - `virtual`

共享 `metrics` 字段：

- `latency`
- `loss`
- `utilization`
- `cpu`
- `queue`

部分 metric 值允许为 `null`，但字段名应保持一致。

## 样例数据与演示方式

仓库内置 4 份演示快照：

- `sample_data/link_degraded.json`
  - 主异常：链路退化
- `sample_data/node_bottleneck.json`
  - 主异常：节点瓶颈
- `sample_data/path_abnormal.json`
  - 主异常：路径异常
- `sample_data/flow_impacted.json`
  - 主异常：关键业务流受影响

推荐演示顺序：

1. `sample_data/link_degraded.json`
2. `sample_data/node_bottleneck.json`
3. `sample_data/path_abnormal.json`
4. `sample_data/flow_impacted.json`

推荐演示命令：

```powershell
semantic-net-cli sample_data\link_degraded.json --config config\llm_config.local.json
semantic-net-cli sample_data\node_bottleneck.json --config config\llm_config.local.json
semantic-net-cli sample_data\path_abnormal.json --config config\llm_config.local.json
semantic-net-cli sample_data\flow_impacted.json --config config\llm_config.local.json
```

预期高层表现：

- `link_degraded.json`
  - 全局状态应表现为 degraded 或 abnormal
  - 根因应围绕 `link-ab`
  - 控制建议应偏向 reroute 或 pressure relief
- `node_bottleneck.json`
  - 全局状态应表现为由 `node-core` 驱动的异常
  - 根因应围绕节点过载
  - 控制建议应偏向负载分担
- `path_abnormal.json`
  - 全局状态应体现路径级异常
  - 根因应围绕 `path-12`
  - 控制建议应偏向转发路径调整
- `flow_impacted.json`
  - 应体现业务退化与服务影响
  - 根因应连接上游节点和链路退化
  - 控制建议应优先保护关键业务流

## 输出格式

CLI 总是按以下固定顺序输出四个 section：

1. `Input Summary`
2. `Global Semantic State`
3. `Semantic Root-Cause Diagnosis`
4. `Closed-Loop Semantic Control`

这四段回答了三个核心问题：

- 当前网络处于什么状态
- 为什么会变成这个状态
- 下一步建议采取什么控制动作

## 报告名词解释

报告中会反复出现一些固定状态词和字段名。
阅读输出时，建议按下面的含义理解。

### 状态词解释

- `normal`
  - 当前没有明显识别到异常信号
  - 对象或该层总结结果整体处于正常状态
- `degraded`
  - 对象或整个网络仍然在工作，但服务质量已经下降
  - 常见表现包括时延升高、丢包上升、拥塞增强、负载升高、业务流受影响
- `congested`
  - 流量压力已经明显达到拥塞状态
  - 在本原型里，这通常表示 queue 或 utilization 压力已经成为主要问题
- `abnormal`
  - 比一般质量下降更严重的异常状态
  - 通常表示存在很强的故障信号、明显的不稳定行为，或者已经出现主导性的瓶颈/故障对象
- `unknown`
  - 工作流继续执行了，但该 Agent 没能给出合法、确定的结构化结论
  - 这不等于“网络正常”，而是表示该步骤当前结论不确定

### 报告字段解释

- `Global Semantic State`
  - 汇总底层 Agent 结果后得到的全网状态判断
- `Semantic Root-Cause Diagnosis`
  - 对“为什么会变成当前状态”的解释
- `Closed-Loop Semantic Control`
  - 对“下一步应该怎么调整网络”的建议
  - 当前原型只输出建议，不会真正执行物理网络控制
- `summary`
  - 该部分结论的简要自然语言总结
- `key_evidence`
  - 支撑该结论的关键对象和理由
- `primary_cause`
  - 根因诊断阶段判定的主要原因或主故障域
- `secondary_causes`
  - 次要但仍有贡献的原因
- `recommended_action`
  - 控制阶段最优先推荐的动作
- `candidate_actions`
  - 可选的候选控制动作列表
- `target_objects`
  - 建议动作主要针对的节点、链路、路径或业务流对象
- `control_reasoning`
  - 选择这些控制建议的原因说明

### 如何理解 `degraded`

在本项目里，`degraded` 不是简单的“错误”或“完全故障”。
它更准确地表示：对象或整个网络还在运行，但质量已经下降，或者已经进入风险上升状态。

典型例子包括：

- 链路还能转发流量，但时延或丢包明显升高
- 节点仍然在线，但利用率、CPU 或队列压力已经偏高
- 路径仍然存在，但依赖了已经退化的组件
- 业务流还能跑通，但服务质量已经不再正常

## 测试方法

运行完整本地测试：

```powershell
pytest
```

运行常用子集：

```powershell
python -m pytest tests/llm/test_config_loader.py
python -m pytest tests/llm/test_client.py
python -m pytest tests/workflow/test_graph.py
python -m pytest tests/reporting/test_formatter.py
python -m pytest tests/test_cli.py
```

## Live 验证状态

当前原型状态：

- 本地契约测试已通过
- CLI 主流程已完整实现
- 已使用真实模型配置完成至少一次 live 端到端运行

## 常见问题

### `LLM config file not found`

请检查 `--config` 后面的路径是否正确。

### `Invalid snapshot schema`

说明输入 JSON 文件存在，但不符合固定 schema。
请检查顶层字段和枚举值是否正确。

### `Workflow execution failed: Connection error.`

通常表示以下问题之一：

- `base_url` 错误
- `api_key` 错误
- 提供方网络或 DNS 问题
- 当前环境存在防火墙或沙箱限制

### CLI 输出大量 `unknown`

这通常表示模型有返回，但没有严格满足项目要求的结构化 JSON 输出。
建议排查：

- 模型选择是否合适
- `response_format` 是否正确
- 提示词约束是否被遵守
- 该提供方是否稳定支持当前 JSON 输出模式

## 安全说明

- 不要把真实 API key 提交到仓库
- 真实凭证放在 `config/llm_config.local.json`
- 任何曾经在聊天窗口或错误文件中明文暴露过的 key 都建议轮换

## 当前验收结论

当前项目已经满足原型阶段目标：

- 固定 JSON 输入协议
- 网络垂直领域 Agent 拆分
- 所有 Agent 通过统一 LLM 配置接入
- LangGraph 固定顺序编排
- CLI-only 交付
- 输出全局状态、根因诊断与控制建议
- 提供可直接演示的样例数据
