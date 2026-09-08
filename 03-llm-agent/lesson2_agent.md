# Agent：让 LLM 能"做事"

> 类比：LLM = 大脑，Agent = 大脑 + 手脚。光会想没用，得能动手

## 什么是 Agent？

LLM 本身只能**说**，不能**做**。

```
普通 LLM:
  你: "帮我查 CVE-2024-0001 的信息"
  AI: "好的，你可以去 NVD 网站查询..." （只是告诉你方法）

Agent:
  你: "帮我查 CVE-2024-0001 的信息"
  AI: [调用搜索工具] → [拿到结果] → "这个漏洞影响 xxx，严重程度 HIGH"
  （真的去查了，把结果给你）
```

**Agent = LLM + 工具调用能力**

## Agent 的工作循环

```
用户提问
  ↓
LLM 思考："我需要做什么？"
  ↓
决定调用哪个工具 ←────┐
  ↓                    │
执行工具，拿到结果      │
  ↓                    │
LLM 看结果："够了吗？" ─┘ 不够就继续调工具
  ↓ 够了
生成最终回答
```

这个循环叫 **ReAct 循环**（Reasoning + Acting）：想一步 → 做一步 → 看结果 → 再想。

---

## Tool Use（工具调用）

### 工具是什么？

工具 = 一个 LLM 可以调用的**函数**。你定义好函数的名字、参数、功能，告诉 LLM 有这些工具可用，LLM 会自己决定什么时候调用。

### 代码示例：定义工具

```python
# 定义工具（就是普通的 Python 函数）
def search_cve(cve_id: str) -> dict:
    """在数据库中搜索 CVE 信息"""
    # 实际会调 API，这里模拟
    fake_db = {
        "CVE-2024-0001": {"severity": "HIGH", "description": "远程代码执行"},
        "CVE-2023-44487": {"severity": "CRITICAL", "description": "HTTP/2 拒绝服务"},
    }
    return fake_db.get(cve_id, {"severity": "UNKNOWN", "description": "未找到"})

def run_docker(image: str, command: str) -> str:
    """在 Docker 容器中运行命令"""
    # 实际会调 subprocess，这里模拟
    return f"[Container {image}] Output: command executed successfully"

def read_file(path: str) -> str:
    """读取文件内容"""
    # 实际会读文件，这里模拟
    return f"[File {path}] content: some code here..."
```

### 告诉 LLM 有哪些工具

```python
# 真正的 API 调用中，工具定义长这样：
tools = [
    {
        "name": "search_cve",
        "description": "在数据库中搜索 CVE 漏洞信息",
        "input_schema": {
            "type": "object",
            "properties": {
                "cve_id": {
                    "type": "string",
                    "description": "CVE 编号，如 CVE-2024-0001"
                }
            },
            "required": ["cve_id"]
        }
    },
    {
        "name": "run_docker",
        "description": "在 Docker 容器中运行命令",
        "input_schema": {
            "type": "object",
            "properties": {
                "image": {"type": "string", "description": "Docker 镜像名"},
                "command": {"type": "string", "description": "要执行的命令"}
            },
            "required": ["image", "command"]
        }
    }
]

# API 调用时传入工具定义
response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    tools=tools,          # 告诉 LLM 有这些工具
    messages=[{"role": "user", "content": "查一下 CVE-2024-0001"}]
)

# LLM 会返回：我要调用 search_cve(cve_id="CVE-2024-0001")
# 你执行这个函数，把结果传回给 LLM
# LLM 再根据结果生成最终回答
```

---

## 动手练习

### 练习 1：模拟一个完整的 Agent 循环

```python
# 保存为 /tmp/llm-lab/simple_agent.py

import json

# ===== 第一部分：定义工具 =====
def search_cve(cve_id):
    """搜索 CVE 信息"""
    db = {
        "CVE-2024-0001": {"severity": "HIGH", "type": "RCE", "affected": "libxml2 < 2.0"},
        "CVE-2023-44487": {"severity": "CRITICAL", "type": "DoS", "affected": "HTTP/2 implementations"},
    }
    return db.get(cve_id, {"severity": "UNKNOWN"})

def check_version(package, version):
    """检查软件版本是否有漏洞"""
    vulnerable = {"libxml2": "2.0", "openssl": "3.0"}
    if package in vulnerable:
        is_vuln = version < vulnerable[package]
        return {"package": package, "version": version, "vulnerable": is_vuln}
    return {"package": package, "status": "not in database"}

def generate_report(findings):
    """生成报告"""
    return f"安全报告：发现 {len(findings)} 个问题\n" + "\n".join(
        f"  - {f}" for f in findings
    )

# 工具注册表
TOOLS = {
    "search_cve": search_cve,
    "check_version": check_version,
    "generate_report": generate_report,
}

# ===== 第二部分：模拟 LLM 的思考过程 =====
def fake_agent_think(user_input, tool_results=None):
    """
    模拟 LLM 的 Agent 思考过程
    真正的 Agent 里这部分由 LLM API 完成
    """
    if tool_results is None:
        if "CVE-" in user_input:
            cve_id = user_input.split("CVE-")[1].split(" ")[0]
            cve_id = "CVE-" + cve_id.strip("，。？")
            return {
                "thought": f"用户想了解 {cve_id}，我需要先搜索它的信息",
                "tool_call": {"name": "search_cve", "args": {"cve_id": cve_id}}
            }
        else:
            return {
                "thought": "不需要工具，直接回答",
                "answer": f"你的问题是：{user_input}。我没有对应的工具来处理这个请求。"
            }
    else:
        last_result = tool_results[-1]
        if "severity" in str(last_result) and "report" not in str(tool_results):
            return {
                "thought": "拿到了 CVE 信息，生成报告",
                "tool_call": {"name": "generate_report", "args": {"findings": [str(last_result)]}}
            }
        else:
            return {
                "thought": "信息够了，给出最终回答",
                "answer": f"分析完成。\n{last_result}"
            }

# ===== 第三部分：Agent 主循环 =====
def run_agent(user_input):
    print(f"\n{'='*50}")
    print(f"用户: {user_input}")
    print(f"{'='*50}")

    tool_results = []
    step = 0

    while step < 5:  # 最多 5 步，防止无限循环
        step += 1

        decision = fake_agent_think(user_input, tool_results if tool_results else None)
        print(f"\n[Step {step}] 思考: {decision['thought']}")

        if "answer" in decision:
            print(f"\n最终回答: {decision['answer']}")
            return decision["answer"]

        if "tool_call" in decision:
            call = decision["tool_call"]
            tool_name = call["name"]
            tool_args = call["args"]

            print(f"  → 调用工具: {tool_name}({json.dumps(tool_args, ensure_ascii=False)})")

            result = TOOLS[tool_name](**tool_args)
            print(f"  ← 工具返回: {result}")

            tool_results.append(result)

    return "达到最大步数限制"

# ===== 运行 =====
run_agent("帮我分析 CVE-2024-0001")
run_agent("今天天气怎么样")
```

运行：
```bash
mkdir -p /tmp/llm-lab
# 创建文件后运行
python /tmp/llm-lab/simple_agent.py
```

---

## Agent 的关键概念

| 概念 | 含义 | CVEFactory 中的对应 |
|------|------|---------------------|
| LLM | 负责思考和决策 | Claude API |
| Tool | LLM 可以调用的函数 | Docker 命令、文件操作、代码分析 |
| Agent Loop | 思考→调用→观察→再思考 | Orchestrator 的主循环 |
| System Prompt | 告诉 Agent 它的角色和规则 | "你是一个漏洞复现专家..." |

## CVEFactory 的 Agent 用了哪些工具？

```
CVEFactory Agent 的工具箱：
├── run_docker()        → 创建容器运行漏洞代码
├── read_file()         → 读取漏洞补丁和代码
├── write_file()        → 写入 PoC（漏洞验证代码）
├── execute_command()   → 在容器里执行命令
└── analyze_output()    → 让 LLM 分析运行结果
```

Agent 看到一个 CVE，会自己决定：
1. 先读补丁文件，理解漏洞
2. 启动 Docker 容器，搭建环境
3. 写 PoC 代码
4. 运行测试
5. 看结果，不对就修改再试

**这就是为什么叫 "coding agent"——它能自己写代码、运行、调试，像一个自动化的程序员。**

---

## 自测题

1. Agent 和普通 LLM 的核心区别是什么？
2. Agent Loop 的步骤是什么？什么时候会停止循环？
3. 为什么 CVEFactory 要用 Agent 而不是写死的脚本？
