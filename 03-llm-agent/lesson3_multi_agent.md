# Multi-Agent：多个 Agent 协作

> 类比：一个 Agent = 一个程序员，Multi-Agent = 一个开发团队

## 为什么需要多个 Agent？

一个 CVE 的复现流程很复杂，一个 Agent 全做太慢。CVEFactory 的方案：**多个 Agent 并行处理不同的 CVE**。

```
                    Orchestrator（项目经理）
                   /        |        \
              Agent-1    Agent-2    Agent-3
              CVE-001    CVE-002    CVE-003
              (容器1)    (容器2)    (容器3)
```

还记得第一阶段学的 `asyncio.gather()` 吗？这就是它的应用场景。

## CVEFactory 的完整架构

```
用户输入 CVE 列表
      ↓
Orchestrator（编排器）
      ↓
┌─────────────────────────────────────────┐
│  对每个 CVE，asyncio.gather 并发执行：    │
│                                          │
│  async def process_cve(cve_id):          │
│    1. 创建 Docker 容器                    │
│    2. 挂载漏洞代码 (-v)                   │
│    3. Agent 在容器里工作：                 │
│       a. 调 LLM API → "分析这个补丁"     │
│       b. LLM 返回 → "我要写一个 PoC"     │
│       c. 调 write_file 工具 → 写 PoC     │
│       d. 调 run_docker 工具 → 运行测试    │
│       e. 调 LLM API → "结果对吗？"       │
│       f. 重复 b-e 直到成功或超时          │
│    4. 收集结果                            │
│    5. 销毁容器 (--rm)                     │
└─────────────────────────────────────────┘
      ↓
汇总所有 CVE 的复现结果
```

## 技术栈对应关系

把你学过的所有东西连起来：

| 你学的技术 | 在 CVEFactory 中的角色 |
|-----------|----------------------|
| Python 基础 | 整个项目的编程语言 |
| subprocess | 调用 Docker 命令 |
| asyncio.gather | 并发处理多个 CVE |
| Docker run | 创建漏洞复现环境 |
| Docker -v | 挂载漏洞代码和补丁 |
| Docker -e | 传入 CVE 配置信息 |
| Dockerfile | 构建包含工具的基础镜像 |
| DinD | 让主容器能创建子容器 |
| LLM API | Agent 的"大脑" |
| Tool Use | Agent 调用 Docker、文件操作等 |
| System Prompt | 定义 Agent 的角色和行为规则 |

---

## 动手练习

### 练习 1：模拟 CVEFactory 的多 Agent 架构

```python
# 保存为 /tmp/llm-lab/multi_agent.py

import asyncio
import json
import time

# ===== 模拟 LLM API 调用 =====
async def call_llm(system_prompt, user_message):
    """模拟调用 LLM API（真实场景用 anthropic 库）"""
    await asyncio.sleep(0.5)  # 模拟网络延迟

    if "分析补丁" in user_message:
        return "这个补丁修复了一个整数溢出漏洞。攻击者可以通过发送超大数值触发溢出。"
    elif "写 PoC" in user_message:
        return 'print("Sending oversized value: " + "A" * 10000)'
    elif "判断结果" in user_message:
        return "漏洞复现成功：程序崩溃，返回 segfault"
    else:
        return f"已处理：{user_message}"

# ===== 模拟工具 =====
async def tool_run_in_docker(cve_id, command):
    """模拟在 Docker 容器中运行命令"""
    await asyncio.sleep(0.3)
    return f"[Container-{cve_id}] $ {command}\n→ Output: execution completed"

async def tool_write_file(cve_id, filename, content):
    """模拟写文件到容器"""
    await asyncio.sleep(0.1)
    return f"[Container-{cve_id}] Wrote {filename} ({len(content)} chars)"

# ===== 单个 CVE 的 Agent =====
async def cve_agent(cve_id, patch_info):
    """
    处理一个 CVE 的完整 Agent
    这就是 CVEFactory 中每个 CVE 对应的 Agent
    """
    print(f"\n[{cve_id}] Agent 启动")

    # Step 1: 让 LLM 分析补丁
    print(f"[{cve_id}] Step 1: 分析补丁...")
    analysis = await call_llm(
        system_prompt="你是安全漏洞分析专家",
        user_message=f"分析补丁：{patch_info}"
    )
    print(f"[{cve_id}]   LLM 分析: {analysis[:50]}...")

    # Step 2: 让 LLM 写 PoC
    print(f"[{cve_id}] Step 2: 生成 PoC...")
    poc_code = await call_llm(
        system_prompt="你是安全漏洞分析专家",
        user_message=f"根据分析结果写 PoC: {analysis}"
    )
    print(f"[{cve_id}]   LLM 生成: {poc_code[:50]}...")

    # Step 3: 用工具把 PoC 写入容器
    print(f"[{cve_id}] Step 3: 写入 PoC 文件...")
    write_result = await tool_write_file(cve_id, "poc.py", poc_code)
    print(f"[{cve_id}]   {write_result}")

    # Step 4: 在容器里运行 PoC
    print(f"[{cve_id}] Step 4: 运行 PoC...")
    run_result = await tool_run_in_docker(cve_id, "python poc.py")
    print(f"[{cve_id}]   {run_result}")

    # Step 5: 让 LLM 判断结果
    print(f"[{cve_id}] Step 5: 判断结果...")
    verdict = await call_llm(
        system_prompt="你是安全漏洞分析专家",
        user_message=f"判断结果：{run_result}"
    )
    print(f"[{cve_id}]   结论: {verdict[:50]}...")

    return {
        "cve_id": cve_id,
        "status": "reproduced",
        "verdict": verdict
    }

# ===== Orchestrator =====
async def orchestrator(cve_list):
    """
    CVEFactory 的 Orchestrator
    用 asyncio.gather 并发处理所有 CVE
    """
    print("=" * 60)
    print("CVEFactory Orchestrator 启动")
    print(f"待处理 CVE: {len(cve_list)} 个")
    print("=" * 60)

    start = time.time()

    # 核心：asyncio.gather 并发！
    tasks = [
        cve_agent(cve["id"], cve["patch"])
        for cve in cve_list
    ]
    results = await asyncio.gather(*tasks)

    elapsed = time.time() - start

    # 汇总结果
    print(f"\n{'=' * 60}")
    print(f"全部完成！耗时 {elapsed:.1f} 秒")
    print(f"{'=' * 60}")
    for r in results:
        print(f"  {r['cve_id']}: {r['status']}")

    return results

# ===== 运行 =====
cve_list = [
    {"id": "CVE-2024-0001", "patch": "fix integer overflow in parse_input()"},
    {"id": "CVE-2024-0002", "patch": "fix buffer overread in process_header()"},
    {"id": "CVE-2024-0003", "patch": "fix use-after-free in handle_connection()"},
]

asyncio.run(orchestrator(cve_list))
```

运行：
```bash
python /tmp/llm-lab/multi_agent.py
```

观察输出：三个 Agent **同时工作**，交替打印进度。这就是 CVEFactory 的核心架构。

---

## 你已经学完了所有前置知识！

```
✅ 第一阶段 Python     → subprocess, asyncio, JSON
✅ 第二阶段 Docker     → 镜像, 容器, -v/-e/--rm, DinD
✅ 第三阶段 LLM+Agent  → API 调用, Tool Use, Agent Loop, Multi-Agent

下一步 → 读 CVEFactory 论文 + 代码，你会发现每个概念都见过！
```

---

## 自测题

1. CVEFactory 的 Orchestrator 用什么技术实现并发？
2. 每个 CVE Agent 的工作流程是什么？（列出主要步骤）
3. 把 CVEFactory 的技术栈和你学过的知识对应起来（至少 5 个）
