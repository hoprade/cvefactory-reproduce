# CVE-Factory 复现

独立复现 [CVE-Factory](https://github.com/livecvebench/CVE-Factory)（一个多 Agent 协作的自动化漏洞复现系统）的学习过程。

## 学习路线

| 阶段 | 内容 | 目录 |
|------|------|------|
| 01 | Python 工程能力（async、subprocess） | `01-python/` |
| 02 | Docker 基础（容器、Compose、DinD） | `02-docker/` |
| 03 | LLM & Agent 概念 | `03-llm-agent/` |
| 04 | 读 CVE-Factory 论文 + 源码 | `04-cvefactory/` |
| 05 | 动手复现 Mini CVE-Factory | `05-reproduce/` |

## 核心产出

`05-reproduce/task7_async.py` — Mini CVE-Factory 主程序，实现了：
- 6 Agent 串行流水线（Analyzer → Generator → Builder → Validator → Solver → Checker）
- 多 CVE 并发处理（`asyncio.gather`）
- LLM tool calling（read_file / write_file / run_command）
- 重试机制 + 超时处理（`asyncio.wait_for`）
- 结构化结果（`AgentResult` dataclass）
- 失败提前终止

## 技术栈

Python async · OpenAI API · Docker · LLM Agent orchestration
