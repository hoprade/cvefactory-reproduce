# 第四阶段学习笔记：CVEFactory 论文 + 代码

## 论文核心

**CVEFactory 是什么**: 一个 Multi-Agent 系统，自动把 CVE 漏洞描述变成可运行的漏洞复现环境，用于评估 AI 修漏洞的能力。

**为什么需要它**: 评估 AI 的安全能力需要大量高质量的漏洞复现任务（benchmark），靠人工做太慢太贵，所以用 Multi-Agent 自动化生产。

**关键概念**:
- reproduce（复现）= 把漏洞从文字描述变成可运行的环境，能亲手触发漏洞
- LiveCVEBench = CVEFactory 生产出来的持续更新的漏洞评测集，用来给 AI "考试"

---

## 6 个 Agent 流水线

```
Phase 1（不需要 Docker）：
  ① Analyzer  — 上网搜 CVE 资料，输出分析文档（5 个 md 文件）
  ② Generator — 生成测试代码、修复脚本、任务描述

Phase 2（需要 Docker）：
  ③ Builder   — 写 Dockerfile，搭建漏洞环境
  ④ Validator  — 验证环境能否正常运行，漏洞是否存在
  ⑤ Solver    — 验证修复方案，调试测试/脚本问题
  ⑥ Checker   — 最终质检，检查整个任务质量
```

### 每个 Agent 的输出

| Agent | 核心输出 |
|-------|---------|
| Analyzer | public.md + 4 个 for_xxx.md（分析文档） |
| Generator | task.yaml, tests/, solution.sh, docker_requirements.md |
| Builder | Dockerfile, docker-compose.yaml |
| Validator | 验证环境状态 |
| Solver | 修复测试/脚本问题 |
| Checker | 最终质检结果 |

### Generator 产出的文件详解

- **task.yaml** — 任务描述，像 bug 报告，不暴露 CVE 编号（防数据泄漏）
- **test_vuln.py** — 漏洞测试：修复前失败（漏洞存在），修复后通过
- **test_func.py** — 功能测试：修复前后都应该通过（保证不破坏正常功能）
- **solution.sh** — 修复脚本，直接改代码修漏洞
- 测试必须真正运行程序去测（executable validation），不能只检查代码文本

### 为什么需要测试和修复脚本

CVEFactory 不只是"出题"，还要"自动判卷"：
- 漏洞环境 = 考题
- solution.sh = 标准答案
- tests/ = 评分标准

没有 tests 就无法自动评估 AI 修漏洞的能力。

---

## 关键设计

### Context 隔离
每个 Agent 的 context window 有限，不能塞所有信息。Agent 之间通过 .md 文件传递关键信息：
- public.md → 所有 Agent 共享
- for_generator.md → 只给 Generator
- for_builder.md → 只给 Builder

### Blind Building
Builder 故意看不到 tests/ 和 solution.sh，防止搭环境时受测试影响导致数据泄漏。

### 三个信号机制（Agent ↔ Orchestrator）
- **success** — 做完了，进入下一个 Agent
- **pause** — 缺信息，反馈给上游 Agent 补充，然后重跑当前 Agent
- **error** — 彻底失败，整个 CVE 任务跳过

### Agent 自主性 vs 控制
- 自主性：Agent 像 Claude 一样自己决定调什么工具、怎么做
- 控制：Orchestrator 限制每个 Agent 能用哪些工具（如 Analyzer 能上网，Builder 不能）

### Orchestrator vs Checker
- Orchestrator = 流水线传送带（代码逻辑，看信号做调度）
- Checker = 质检员（LLM Agent，看懂内容判断质量）

---

## 论文验证方法

用 215 个真实 CVE（来自 CVElistV5）测试，三种交叉验证：

| 验证类型 | 验证什么 | 方法 |
|---------|---------|------|
| Solution Validation | 机器的修复脚本对不对 | 机器修复 + 人类测试 |
| Test Validation | 机器的测试代码对不对 | 人类修复 + 机器测试 |
| Environment Validation | Docker 环境对不对 | 人类专家直接检查 |

---

## 代码结构

```
CVE-Factory/
├── agents/*.md              ← 每个 Agent 的 System Prompt
├── orchestrator/
│   ├── async_orchestrator.py ← 核心：process_cve() 跑流水线
│   │                           process_multiple_cves() 用 asyncio.gather 并发
│   ├── agent_runner.py       ← 运行单个 Agent
│   └── tool_controller.py    ← 控制 Agent 可用工具
├── cve_tasks/                ← 生成的 CVE 任务
└── config.yaml               ← 配置：并发数、超时、模型
```

### 核心代码逻辑
- `process_cve()`: 单个 CVE 依次跑 analyzer → generator → builder → validator → solver → checker
- `process_multiple_cves()`: 多个 CVE 用 `asyncio.gather()` 并发，`Semaphore` 限流（最多同时 5 个）
- config.yaml: 参数设置（并发数、超时时间、用哪个 LLM 模型）

---

## 和之前学的知识对应

| 之前学的 | CVEFactory 里的应用 |
|---------|-------------------|
| System Prompt | agents/*.md 就是每个 Agent 的 system prompt |
| Tool Use | Analyzer 用 WebSearch，Builder 用 Docker 命令 |
| Agent Loop (ReAct) | 每个 Agent 自主探索、调试、迭代 |
| asyncio.gather | Orchestrator 并发处理多个 CVE |
| Semaphore | 限制最大并发数 |
| Docker / Dockerfile | Builder 创建漏洞容器环境 |
| subprocess | 执行 Docker 命令、运行测试脚本 |

---

## 读论文方法（第一次实践）

1. **第一轮（10 分钟）**：读摘要、看图表、每大节首尾段 → 抓大意
2. **第二轮（30 分钟）**：重点读 Method → 理解怎么做的
3. **第三轮**：细节和实验结果
4. Related Work 可以跳过
5. 论文读不懂的地方，去代码里找对应实现
