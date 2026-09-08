import os, json, subprocess
from openai import OpenAI

key = os.environ["DASHSCOPE_API_KEY"]
client = OpenAI(api_key=key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")

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
    if name == "read_file":
        return open(args["path"]).read()
    elif name == "write_file":
        with open(args["path"], "w") as f:
            f.write(args["content"])
        return "文件已写入: " + args["path"]
    elif name == "run_command":
        return subprocess.run(args["command"], shell=True, capture_output=True, text=True).stdout

def run_agent(system_prompt, user_message):
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
            result = execute_tool(tool_call.function.name, args)
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
        else:
            print(msg.content)
            return msg.content


print("=" * 50)
print("Agent 1: Analyzer")
print("=" * 50)

run_agent(
    system_prompt="你是一个安全分析师。分析给定的 CVE 列表，把分析结果写入指定文件。",
    user_message="读取 /root/mywork/learn/01-python/cve_list.txt，分析里面的 CVE 编号，把分析结果写入 /root/mywork/learn/05-reproduce/analysis.md"
)

print("\n" + "=" * 50)
print("Agent 2: Reporter")
print("=" * 50)

run_agent(
    system_prompt="你是一个安全报告撰写员。根据分析文件生成简洁的中文总结报告。",
    user_message="读取 /root/mywork/learn/05-reproduce/analysis.md，生成一份简洁的总结报告（不超过5行）"
)
