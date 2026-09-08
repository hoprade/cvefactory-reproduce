# 第四阶段：读 CVEFactory 论文 + 代码

## 论文概览

**标题**: CVE-Factory: Scaling Expert-Level Agentic Tasks for Code Security Vulnerability

**一句话总结**: 一个多 Agent 系统，自动把 CVE 漏洞信息变成可执行的漏洞复现环境，质量达到人类专家水平。

---

## 论文核心内容（用你学过的知识理解）

### 它解决什么问题？
评估 AI 的安全能力需要大量漏洞复现任务，但靠人工做太慢太贵。CVEFactory 用 Multi-Agent 自动化这个过程。

### 它怎么做的？

6 个 Agent 组成流水线，每个 Agent 有自己的角色（System Prompt）：

```
CVE 信息输入
    ↓
Phase 1（不需要 Docker）：
    ① Analyzer  — 上网搜索 CVE 相关资料，下载代码和补丁
    ② Generator — 根据分析结果，写测试代码和修复脚本
    ↓
Phase 2（需要 Docker）：
    ③ Builder   — 写 Dockerfile，搭建漏洞环境
    ④ Validator  — 检查环境是否能跑通
    ⑤ Solver    — 验证修复方案是否有效
    ⑥ Checker   — 最终检查，确保一切正确
```

### 和你学的知识的对应

| 你学过的 | 论文里的 |
|---------|---------|
| System Prompt | 每个 Agent 的 .md 文件就是它的 system prompt |
| Tool Use | Analyzer 用 web_search/web_fetch，Builder 用 Docker 命令 |
| Agent Loop (ReAct) | 每个 Agent 自主探索、调试、迭代 |
| asyncio.gather | Orchestrator 并发处理多个 CVE |
| Docker / Dockerfile | Builder 创建漏洞容器环境 |
| docker-compose | 多容器编排（漏洞应用 + 数据库等） |
| DinD | 隔离漏洞容器，不影响主机 |
| subprocess | 运行 Docker 命令、执行测试脚本 |

---

## 代码结构导读

代码在 `/tmp/CVE-Factory/`，核心目录：

```
CVE-Factory/
├── orchestrator/           ← 核心！编排器
│   ├── async_orchestrator.py  ← 主流程，asyncio 并发调度
│   ├── agent_runner.py        ← 运行单个 Agent
│   ├── tool_controller.py     ← 控制 Agent 能用哪些工具
│   ├── script_executor.py     ← 执行测试脚本
│   ├── models.py              ← 数据结构定义
│   └── run.py                 ← 入口
│
├── agents/                 ← 每个 Agent 的 System Prompt
│   ├── analyzer.md            ← 分析器：上网搜 CVE 资料
│   ├── generator.md           ← 生成器：写测试和修复脚本
│   ├── builder.md             ← 构建器：写 Dockerfile 搭环境
│   ├── validator.md           ← 验证器：检查环境能否运行
│   ├── solver.md              ← 解决器：验证修复方案
│   └── checker.md             ← 检查器：最终验收
│
├── cve_tasks/              ← 生成的 CVE 任务（1000+ 个）
│   └── cve-2024-xxxx/
│       ├── task.yaml          ← 任务描述
│       ├── Dockerfile         ← 漏洞环境
│       ├── docker-compose.yaml
│       ├── solution.sh        ← 修复脚本
│       └── test/              ← 测试代码
│
├── config.yaml             ← 配置文件（并发数、超时、模型选择）
├── dev-env/                ← DinD 开发环境
└── scripts/                ← 辅助脚本
```

---

## 建议阅读顺序

### 第一步：看 Agent 的角色定义（最直观）
这些就是 System Prompt，读完就知道每个 Agent 干什么：
1. `agents/analyzer.md` — 搜集资料
2. `agents/generator.md` — 写测试和修复
3. `agents/builder.md` — 搭 Docker 环境

### 第二步：看一个真实的 CVE 任务输出
随便挑一个 `cve_tasks/` 下的目录，看看最终产出长什么样：
- `task.yaml` — 任务描述
- `Dockerfile` — 怎么搭环境
- `test/` — 测试代码

### 第三步：看 Orchestrator 核心代码
- `orchestrator/async_orchestrator.py` — 整个流水线怎么调度
- `orchestrator/agent_runner.py` — 怎么运行单个 Agent
- `orchestrator/models.py` — Phase 定义

### 第四步：看配置
- `config.yaml` — 并发数、超时、模型设置

---

## 阅读时带着这些问题

1. 每个 Agent 被允许用哪些工具？不被允许用哪些？为什么？
2. Orchestrator 怎么决定一个 CVE 是"成功复现"还是"失败"的？
3. 如果一个 Agent 失败了，系统怎么处理？会重试吗？
4. 为什么 Builder 不能看到 tests/ 和 solution.sh？
