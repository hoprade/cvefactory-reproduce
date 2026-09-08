import os, json, subprocess
from openai import OpenAI

key = os.environ["DASHSCOPE_API_KEY"]
client = OpenAI(api_key=key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")

WORK_DIR = "/root/mywork/learn/05-reproduce/mini-cvefactory"
os.makedirs(WORK_DIR, exist_ok=True)

tools = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取指定路径的文件内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "将内容写入指定路径的文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "content": {"type": "string", "description": "要写入的内容"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "执行 shell 命令并返回输出",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要执行的命令"}
                },
                "required": ["command"]
            }
        }
    }
]

def execute_tool(name, args):
    try:
        if name == "read_file":
            return open(args["path"]).read()
        elif name == "write_file":
            os.makedirs(os.path.dirname(args["path"]), exist_ok=True)
            with open(args["path"], "w") as f:
                f.write(args["content"])
            return "文件已写入: " + args["path"]
        elif name == "run_command":
            r = subprocess.run(args["command"], shell=True, capture_output=True, text=True, timeout=120)
            output = r.stdout + r.stderr
            return output if output else "(无输出)"
    except Exception as e:
        return f"错误: {e}"

def run_agent(agent_name, system_prompt, user_message):
    print(f"\n{'=' * 50}")
    print(f"{agent_name}")
    print(f"{'=' * 50}")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    while True:
        response = client.chat.completions.create(
            model="deepseek-v3", tools=tools, messages=messages
        )
        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append(msg)
            tool_call = msg.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
            print(f"  [工具调用] {tool_call.function.name}({args})")
            result = execute_tool(tool_call.function.name, args)
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
        else:
            print(msg.content)
            return msg.content


CVE_ID = "CVE-2024-21413"

# Agent 1: Analyzer — 分析 CVE，输出分析报告
run_agent(
    agent_name="Agent 1: Analyzer",
    system_prompt="你是一个安全漏洞分析师。分析给定的 CVE，搜集漏洞类型、影响范围、受影响版本、修复版本等信息。把分析结果写入指定文件。",
    user_message=f"分析 {CVE_ID}，把分析报告写入 {WORK_DIR}/analysis.md"
)

# Agent 2: Generator — 根据分析生成测试用例和解决方案
run_agent(
    agent_name="Agent 2: Generator",
    system_prompt="你是一个安全测试生成专家。根据漏洞分析报告，生成：1) 一个漏洞检测脚本 test_vuln.py（演示漏洞存在的检测逻辑）2) 一个功能测试脚本 test_func.py（验证正常功能不受影响）3) 一个修复脚本 solution.sh（演示修复思路）",
    user_message=f"读取 {WORK_DIR}/analysis.md，生成三个文件：{WORK_DIR}/test_vuln.py、{WORK_DIR}/test_func.py、{WORK_DIR}/solution.sh"
)

# Agent 3: Builder — 构建漏洞复现的 Docker 环境
run_agent(
    agent_name="Agent 3: Builder",
    system_prompt="你是一个 Docker 构建专家。根据测试脚本搭建 Docker 环境，让漏洞检测和功能测试都能在容器中运行。",
    user_message=f"读取 {WORK_DIR}/test_vuln.py 和 {WORK_DIR}/test_func.py，在 {WORK_DIR} 下写一个 Dockerfile（基于 python:3.11-slim），把这两个测试脚本复制进去。执行 docker build -t mini-cvefactory {WORK_DIR} 构建镜像，然后用 docker run --rm mini-cvefactory python test_vuln.py 和 docker run --rm mini-cvefactory python test_func.py 分别运行。把运行结果写入 {WORK_DIR}/build_result.md"
)

# Agent 4: Validator — 验证环境是否正确
run_agent(
    agent_name="Agent 4: Validator",
    system_prompt="你是一个测试验证专家。检查构建结果，确认：1) 漏洞测试能正确检测到漏洞存在 2) 功能测试正常通过。如果有问题，指出哪里需要修正。",
    user_message=f"读取 {WORK_DIR}/build_result.md、{WORK_DIR}/test_vuln.py、{WORK_DIR}/test_func.py，验证测试结果是否符合预期。把验证报告写入 {WORK_DIR}/validate_result.md"
)

# Agent 5: Solver — 验证修复补丁有效
run_agent(
    agent_name="Agent 5: Solver",
    system_prompt="你是一个补丁验证专家。检查 solution.sh 的修复逻辑，确保补丁能修复漏洞且不破坏正常功能。如果补丁有问题就修正它。",
    user_message=f"读取 {WORK_DIR}/solution.sh、{WORK_DIR}/test_vuln.py、{WORK_DIR}/test_func.py 和 {WORK_DIR}/validate_result.md。检查修复方案是否合理，如果需要修正就更新 {WORK_DIR}/solution.sh。把验证结果写入 {WORK_DIR}/solver_result.md"
)

# Agent 6: Checker — 最终校验，确认整体质量
run_agent(
    agent_name="Agent 6: Checker",
    system_prompt="你是最终质量检查员。审查整个流水线的所有产出文件，确认：1) 分析准确 2) 测试覆盖漏洞和正常功能 3) Docker 环境能跑通 4) 补丁有效。给出最终的通过/不通过判定。",
    user_message=f"读取 {WORK_DIR} 下的所有产出文件：analysis.md、test_vuln.py、test_func.py、solution.sh、build_result.md、validate_result.md、solver_result.md。给出最终审查报告，写入 {WORK_DIR}/final_report.md"
)

print(f"\n{'=' * 50}")
print("完成！Mini CVEFactory 完整 6-Agent 流水线执行结束")
print(f"工作目录: {WORK_DIR}")
print(f"{'=' * 50}")
