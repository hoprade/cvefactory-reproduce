import os, json, subprocess, asyncio, time
from openai import AsyncOpenAI
from dataclasses import dataclass
from typing import Optional

key = os.environ["DASHSCOPE_API_KEY"]
client = AsyncOpenAI(api_key=key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")

@dataclass
class AgentResult:
    success: bool
    agent_name: str
    content: Optional[str] = None   # agent 的回复
    error: Optional[str] = None     # 失败原因
    attempts: int = 1               # 第几次尝试成功的
    duration: float = 0.0           # 耗时(秒)

    @staticmethod
    def ok(name, content, attempts=1, duration=0.0):
        return AgentResult(True, name, content=content, attempts=attempts, duration=duration)

    @staticmethod
    def fail(name, error, attempts=1, duration=0.0):
        return AgentResult(False, name, error=error, attempts=attempts, duration=duration)

MAX_RETRIES = 3        # 每个 agent 最多重试几次
AGENT_TIMEOUT = 120    # 每次 LLM 调用的超时(秒)

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
    """工具执行（这部分不需要 async，因为是本地操作）"""
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


async def _single_agent_run(agent_name, messages):
    """单次 agent 执行（tool loop），可能被超时打断。

    这个函数只负责"跑一次"，不管重试。
    类比 ACM：这是"跑一个测试点"，外面的 run_agent 是"跑整个题"。
    """
    while True:
        response = await client.chat.completions.create(
            model="deepseek-v3", tools=tools, messages=messages
        )
        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append(msg)
            tool_call = msg.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
            print(f"  [{agent_name}] 工具调用: {tool_call.function.name}({list(args.keys())})")
            result = execute_tool(tool_call.function.name, args)
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
        else:
            print(f"  [{agent_name}] 完成 ✓")
            return msg.content


async def run_agent(agent_name, system_prompt, user_message) -> AgentResult:
    """带重试 + 超时的 agent 执行。

    源码对应: async_orchestrator.py 的 _run_agent (line 385)
    核心逻辑:
      for attempt in 1..max_retries:
          try:
              await wait_for(执行, timeout)   # 限时
          except TimeoutError:
              continue                         # 超时→重试
          if 成功: return ok
      return fail  # 全部失败
    """
    print(f"\n{'=' * 50}")
    print(f"{agent_name}")
    print(f"{'=' * 50}")

    last_error = None
    start_time = time.time()

    for attempt in range(1, MAX_RETRIES + 1):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        # 重试时告诉 agent 上次失败了
        if attempt > 1:
            print(f"  [{agent_name}] 第 {attempt}/{MAX_RETRIES} 次重试 (上次错误: {last_error})")
            messages.append({
                "role": "user",
                "content": f"上次执行失败了: {last_error}\n请重新尝试完成任务。"
            })

        try:
            # 超时就抛 TimeoutError，不会无限等下去
            content = await asyncio.wait_for(
                _single_agent_run(agent_name, messages),
                timeout=AGENT_TIMEOUT
            )
            duration = time.time() - start_time
            return AgentResult.ok(agent_name, content, attempts=attempt, duration=duration)

        except asyncio.TimeoutError:
            last_error = f"超时 ({AGENT_TIMEOUT}s)"
            print(f"  [{agent_name}] ⏰ 超时！")

        except Exception as e:
            last_error = str(e)
            print(f"  [{agent_name}] ❌ 错误: {last_error}")

    # 所有重试都失败了
    duration = time.time() - start_time
    print(f"  [{agent_name}] 💀 {MAX_RETRIES} 次重试全部失败")
    return AgentResult.fail(agent_name, last_error, attempts=MAX_RETRIES, duration=duration)


async def process_cve(cve_id):
    """一个 CVE 的完整流水线。

    改进: agent 失败时提前终止（后面的 agent 依赖前面的输出）
    源码对应: async_orchestrator.py 的 process_cve
    """
    work_dir = f"/root/mywork/learn/05-reproduce/mini-cvefactory/{cve_id}"
    os.makedirs(work_dir, exist_ok=True)

    print(f"\n{'#' * 60}")
    print(f"  开始处理: {cve_id}")
    print(f"{'#' * 60}")

    # 流水线定义：(agent名, system_prompt, user_message)
    pipeline = [
        (f"[{cve_id}] Analyzer",
         "你是一个安全漏洞分析师。分析给定的 CVE，搜集漏洞类型、影响范围、受影响版本、修复版本等信息。把分析结果写入指定文件。",
         f"分析 {cve_id}，把分析报告写入 {work_dir}/analysis.md"),
        (f"[{cve_id}] Generator",
         "你是一个安全测试生成专家。根据漏洞分析报告，生成：1) 一个漏洞检测脚本 test_vuln.py 2) 一个功能测试脚本 test_func.py 3) 一个修复脚本 solution.sh",
         f"读取 {work_dir}/analysis.md，生成三个文件：{work_dir}/test_vuln.py、{work_dir}/test_func.py、{work_dir}/solution.sh"),
        (f"[{cve_id}] Builder",
         "你是一个 Docker 构建专家。根据测试脚本搭建 Docker 环境。",
         f"读取 {work_dir}/test_vuln.py 和 {work_dir}/test_func.py，在 {work_dir} 下写一个 Dockerfile（基于 python:3.11-slim），把测试脚本复制进去。执行 docker build -t mini-{cve_id.lower()} {work_dir} 构建镜像，然后分别运行两个测试。把结果写入 {work_dir}/build_result.md"),
        (f"[{cve_id}] Validator",
         "你是一个测试验证专家。检查构建结果，确认漏洞测试和功能测试是否符合预期。",
         f"读取 {work_dir}/build_result.md、{work_dir}/test_vuln.py、{work_dir}/test_func.py，验证结果。写入 {work_dir}/validate_result.md"),
        (f"[{cve_id}] Solver",
         "你是一个补丁验证专家。检查修复方案是否合理，如果有问题就修正。",
         f"读取 {work_dir}/solution.sh、{work_dir}/validate_result.md。检查并完善修复方案。写入 {work_dir}/solver_result.md"),
        (f"[{cve_id}] Checker",
         "你是最终质量检查员。审查所有产出，给出通过/不通过判定。",
         f"读取 {work_dir} 下所有产出文件，给出最终审查报告，写入 {work_dir}/final_report.md"),
    ]

    results = []
    for name, sys_prompt, user_msg in pipeline:
        result = await run_agent(name, sys_prompt, user_msg)
        results.append(result)

        # 失败时提前终止——后面的 agent 依赖前面的输出，继续跑没意义
        if not result.success:
            print(f"\n  ✗ {cve_id} 流水线在 {name} 阶段失败，跳过后续步骤")
            return cve_id, results

    print(f"\n  ✓ {cve_id} 流水线完成！")
    return cve_id, results


async def main():
    cve_list = [
        "CVE-2024-21413",
        "CVE-2024-3094",
    ]

    print(f"并发处理 {len(cve_list)} 个 CVE...")
    print(f"每个 CVE 内部串行（6 Agent 流水线）")
    print(f"不同 CVE 之间并发（asyncio.gather）")
    print(f"配置: 最大重试={MAX_RETRIES}, 超时={AGENT_TIMEOUT}s\n")

    all_results = await asyncio.gather(*[process_cve(cve) for cve in cve_list])

    print(f"\n{'=' * 60}")
    print(f"执行摘要")
    print(f"{'=' * 60}")
    for cve_id, results in all_results:
        all_ok = all(r.success for r in results)
        status = "PASS" if all_ok else "FAIL"
        print(f"\n  {cve_id}: {status}")
        for r in results:
            flag = "✓" if r.success else "✗"
            retry_info = f" (重试{r.attempts}次)" if r.attempts > 1 else ""
            time_info = f" [{r.duration:.1f}s]" if r.duration > 0 else ""
            err_info = f" — {r.error}" if r.error else ""
            print(f"    {flag} {r.agent_name}{retry_info}{time_info}{err_info}")
    print(f"{'=' * 60}")


asyncio.run(main())
