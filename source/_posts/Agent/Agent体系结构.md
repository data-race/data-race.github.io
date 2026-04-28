---
categories:
  - Agent
title: Agent体系结构
tags:
  - agent
date:
---

现代 LLM Agent 体系结构，核心是**以大语言模型（LLM）为认知中枢**，通过 **Prompt、Skill、Tool、Harness** 四大工程化模块协同，构成一套可规划、可执行、可记忆、可控制的闭环智能系统。

核心公式可概括为：
**Agent = LLM \(大脑\) \+ Prompt \(指令\) \+ Skill \(能力\) \+ Tool \(手脚\) \+ Harness \(控制系统\)**
### 一、LLM：认知中枢（Brain）

LLM 是 Agent 的核心，负责理解、推理、决策与生成。
- **核心作用**
- 自然语言理解（NLU）：解析用户意图、任务拆解
- 推理与规划（Reasoning/Planning）：多步思考、策略选择

- 工具调用决策：判断何时 / 如何调用外部能力

- 自然语言生成（NLG）：结果汇总、对话反馈

  

- **选型维度**

- 推理能力（CoT、ReAct、GoT 兼容度）

- 函数调用 / Tool Calling 原生支持

- 上下文窗口长度（长记忆需求）

- 速度、成本、可控性、隐私合规

  

- **典型代表**

- 闭源：GPT\-4o、Claude 3、Gemini Advanced

- 开源：Llama 3、Qwen、Mistral Large

  

### 二、Prompt Engineering：指令与上下文层

  

**Prompt 是 LLM 的 “操作系统指令”**，定义 Agent 的身份、规则、能力边界与输出格式。

  

- **核心组成**

1. **System Prompt（系统提示）**

- 设定角色、目标、约束、行为准则

- 示例：“你是专业数据分析助手，严格按步骤调用工具，输出 JSON 格式”

  

2. **Task Prompt（任务指令）**

- 用户输入 \+ 历史上下文 \+ 工具返回结果

- 动态注入：工具描述、记忆片段、RAG 检索知识

  

3. **格式约束（Format Prompt）**

- 强制输出结构化数据（JSON/XML），便于后续解析执行

  

- **关键技术**

- **Few\-shot/CoT**：提供范例、引导分步思考

- **ReAct**：融合 “思考 → 行动 → 观察” 循环

- **Self\-Consistency**：多路径投票提升可靠性

- **Prompt Tuning**：轻量适配，比全微调成本更低

  

### 三、Tool：外部交互接口（手脚）

  

**Tool 是 Agent 与现实世界交互的 API 集合**，突破 LLM 知识截止、计算、联网、操作限制。

  

- **核心分类**

- **计算工具**：计算器、Python 解释器、数学引擎

- **信息工具**：搜索引擎、数据库、RAG、API

- **操作工具**：文件读写、代码执行、系统命令、设备控制

- **专业工具**：SQL 查询、图表生成、数据分析、机器人控制

  

- **调用机制**

- **Function Calling**（原生）：LLM 输出结构化函数参数

- **Tool Schema**：定义工具名、入参、描述、返回格式

- **Tool Router**：匹配任务 → 选择最优工具

  

- **典型框架**

- LangChain Tools、LlamaIndex Tools、AutoGPT Plugins

  

### 四、Skill：模块化能力单元

  

**Skill = 封装好的 “任务模板 \+ Prompt \+ Tool 组合”**，是可复用、可插拔的高级能力单元。

  

- **与 Tool 的区别**

- **Tool**：原子操作（如 “搜索”“计算”）

- **Skill**：复合任务（如 “写周报”“订机票”“数据分析报告”）

  

- **Skill 结构（标准模板）**

```Plain Text

Skill: 财务报表分析

├─ 目标：生成季度营收分析报告

├─ 步骤：

1. 读取财报CSV

2. 计算同比/环比

3. 搜索行业基准

4. 生成图表与结论

├─ 依赖工具：文件IO、Pandas、搜索引擎、Matplotlib

├─ 输出：PDF报告 + 数据摘要

```

  

- **价值**

- 降低 Prompt 复杂度

- 提升稳定性、可复用、可维护

- 支持 Skill 库、动态装配

  

### 五、Harness Engineering：运行控制与治理框架

  

**Harness 是 Agent 的 “操作系统 \+ 监管层”**，解决长期运行、稳定性、安全性、可控性问题。

  

- **核心定义**

> 设计并实现一套系统，**约束 Agent 能做什么、告知该做什么、验证是否正确、出错时自动纠正**。

>

  

- **核心组件**

1. **执行引擎（Orchestrator）**

- 主循环：**Think → Act → Observe → Update → Repeat**

- 任务调度、子任务管理、状态机

  

2. **记忆系统（Memory）**

- 短期：对话历史、上下文窗口

- 长期：向量库、文档库、经验总结

- 工作记忆：任务进度、中间结果

  

3. **监控与校验（Guardrails）**

- 输入校验、输出审核、安全过滤

- 事实一致性检查、幻觉检测

  

4. **容错与恢复**

- 失败重试、回滚、人工介入

- 日志、审计、可解释性

  

5. **部署与服务（Runtime）**

- 多会话、并发、资源调度、API 服务

  

- **代表实践**

- Anthropic Constitution AI、OpenAI Assistants API、LangGraph、AutoGen

  

### 六、完整架构：五层协同模型

  

现代生产级 Agent 通常分为五层，自上而下协同工作：

  

1. **接口层（Interface）**：用户输入、CLI/API、多模态接入

  

2. **推理层（Reasoning）**：LLM \+ Prompt \+ Planning

  

3. **能力层（Capability）**：Skill 库 \+ Tool 库

  

4. **控制层（Harness）**：Orchestrator \+ Memory \+ Guardrails

  

5. **执行层（Execution）**：外部系统、API、设备、文件、数据库

  

### 七、演进路径（2022–2026）

  

`Prompt Engineering → RAG → Function Calling → Skill → Harness`

  

- **Prompt**：单轮指令，无状态

- **RAG**：外接知识库，解决知识过时

- **Tool/Function Calling**：可调用外部能力

- **Skill**：模块化、可复用复杂能力

- **Harness**：长期自治、可控、稳定运行

  

### 总结

  

- **LLM** 提供智能内核

- **Prompt** 定义行为与规则

- **Tool** 提供对外交互能力

- **Skill** 封装可复用任务流

- **Harness** 保障系统稳定、安全、可控

  

需要我帮你把这套体系整理成一份可直接套用的 **LLM Agent 架构设计清单** 吗？

  

> （注：文档部分内容可能由 AI 生成）