# CVE-Factory 复现

用一周时间从零开始理解并独立复现 [CVE-Factory](https://github.com/livecvebench/CVE-Factory)。

## 学习历程

### 前置知识补充

最初的目标是能读懂 CVE-Factory 的源码，所以先补了两块基础：

**Python 工程能力**（`01-python/`）—— 我有 C++ 和 ACM 基础，Python 语法本身不难，主要学了之前没接触过的：`subprocess` 调外部命令、`async/await` 异步编程、`asyncio.gather` 并发。这些都是 CVE-Factory 的核心依赖。

**Docker**（`02-docker/`）—— 从镜像/容器的基本概念开始，到 Dockerfile 构建自定义镜像，最后学了 Docker Compose 和 DinD（Docker in Docker）。DinD 是 CVE-Factory 的核心架构——每个 CVE 的复现环境都跑在独立容器里，互不干扰。

### LLM Agent 基础知识

接着补了 Agent 相关的概念（`03-llm-agent/`）：tool calling 是什么、agent loop（LLM 自主决定调用工具还是停止）、ReAct 模式（reasoning + acting 交替）、system prompt 的作用、multi-agent 协作模式。这些是理解 CVE-Factory 设计的前提。

### 精读 CVE-Factory 论文和源码

然后完整读了论文原文，把源码过了一遍（`04-cvefactory/`）。CVE-Factory 本质上是一个**多 Agent 流水线系统**：给定一个 CVE 编号，由 10 个不同角色的 Agent（分析、生成测试、构建环境、验证、修复……）按阶段协作，自动完成漏洞分析→测试生成→Docker 环境搭建→漏洞验证→补丁验证的全流程。核心机制包括：Agent 之间通过文件传递信息、每个阶段有重试和反馈循环、用 asyncio.gather + Semaphore 实现多 CVE 并发。

### 动手复现

理解了原理之后开始自己写（`05-reproduce/`），经历了 6 个迭代：

**task2** —— 最简单的起点：一次 LLM API 调用 + 一个 read_file 工具。手动执行工具、手动把结果喂回去。目的是搞懂 tool calling 的基本流程：LLM 不直接执行工具，它只是告诉你"我想调 read_file"，你执行完再把结果还给它。

**task3** —— 加入了 while 循环（agent loop）。LLM 自己决定什么时候调工具、什么时候给出最终回答。加了 run_command 工具让它能执行 shell 命令。这就是最简单的 ReAct 模式——LLM 在"思考→行动→观察"的循环里自主工作。

**task4** —— 第一个多 Agent 版本。把 agent loop 封装成 `run_agent()` 函数，串联了 2 个 Agent（Analyzer → Reporter），一个分析 CVE 写文件，一个读文件写报告。加了 write_file 工具。这是 CVE-Factory 流水线模式的最小原型：Agent 之间通过文件传递信息。

**task5** —— 单独实现了一个 Docker Builder Agent：生成 Dockerfile、构建镜像、运行容器，全部由 LLM 自主完成。给 execute_tool 加了 try/except 错误处理和 timeout。

**task6** —— 完整的 6 Agent 流水线：Analyzer → Generator → Builder → Validator → Solver → Checker，对标 CVE-Factory 的核心 6 阶段。每个 Agent 有独立的 system prompt 和职责，串行执行，通过文件交接成果。跑通之后能对一个 CVE 自动完成从分析到最终审查的全流程。

**task7** —— 最终版本。三个关键改进：（1）同步改异步（`AsyncOpenAI` + `async/await`），用 `asyncio.gather` 让多个 CVE 的流水线并发执行；（2）加入重试机制和超时处理（`asyncio.wait_for`），对标源码的 `_run_agent` 重试循环；（3）引入 `AgentResult` dataclass 做结构化结果，agent 失败时提前终止流水线。

## 目录结构

```
01-python/       # Python 基础：变量、subprocess、async/await
02-docker/       # Docker：镜像、Dockerfile、Compose、DinD
03-llm-agent/    # LLM Agent 概念：tool calling、ReAct、multi-agent
04-cvefactory/   # CVE-Factory 论文精读笔记 + 源码分析
05-reproduce/    # 复现代码（task2 → task7 逐步演进）
```
