# 第五阶段：动手复现 CVEFactory

## 总体思路

不是直接跑原版代码，而是从零开始，一步步搭出简化版。
每一步都对应 CVEFactory 的一个核心机制。

---

## 学习路线

### Lesson 1: 调用 LLM API
**对应 CVEFactory**: agent_runner.py 调 Claude API
**你要做的**: 用 Python 调 SiliconFlow API（DeepSeek），发消息、拿回复
**产出**: 一个能跟 LLM 对话的 Python 脚本

### Lesson 2: 实现 Tool Use（工具调用）
**对应 CVEFactory**: Agent 用 WebSearch、Bash、文件读写等工具
**你要做的**: 让 LLM 能调用你定义的工具（比如读文件、执行命令）
**产出**: 一个能调工具的 Agent

### Lesson 3: Agent Loop（ReAct 循环）
**对应 CVEFactory**: 每个 Agent 自主探索、调试、迭代
**你要做的**: 实现"想→调工具→看结果→继续想"的循环
**产出**: 一个完整的 Agent，能自主完成多步任务

### Lesson 4: 多 Agent + 文件通信
**对应 CVEFactory**: 6 个 Agent 通过 .md 文件传递信息
**你要做的**: 写两个 Agent，Agent A 输出文件，Agent B 读取后继续
**产出**: 双 Agent 流水线

### Lesson 5: 加入 Docker
**对应 CVEFactory**: Builder Agent 写 Dockerfile、构建镜像
**你要做的**: Agent 生成 Dockerfile 并自动构建运行
**产出**: 能操作 Docker 的 Agent

### Lesson 6: Mini CVEFactory
**对应 CVEFactory**: 完整流水线
**你要做的**: 串联 Analyzer → Generator → Builder，处理一个真实 CVE
**产出**: 简化版 CVEFactory

---

## 前置条件

- [x] API Key（SiliconFlow + 百炼，环境变量已配好）
- [ ] `pip install openai`
