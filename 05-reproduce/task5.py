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
    try:
        if name == "read_file":
            return open(args["path"]).read()
        elif name == "write_file":
            with open(args["path"], "w") as f:
                f.write(args["content"])
            return "文件已写入: " + args["path"]
        elif name == "run_command":
            r = subprocess.run(args["command"], shell=True, capture_output=True, text=True, timeout=120)
            output = r.stdout + r.stderr
            return output if output else "(无输出)"
    except Exception as e:
        return f"错误: {e}"

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
            print(f"  [工具调用] {tool_call.function.name}({args})")
            result = execute_tool(tool_call.function.name, args)
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
        else:
            print(msg.content)
            return msg.content


WORK_DIR = "/root/mywork/learn/05-reproduce/build"
os.makedirs(WORK_DIR, exist_ok=True)

print("=" * 50)
print("Builder Agent")
print("=" * 50)

run_agent(
    system_prompt="你是一个 Docker 构建专家。你的任务是根据用户需求生成 Dockerfile，构建镜像并运行容器。",
    user_message=f"""
在 {WORK_DIR} 目录下完成以下任务：
1. 写一个 Python 脚本 test.py，内容是打印 "Hello from Docker! CVE analysis agent is working."
2. 写一个 Dockerfile，基于 python:3.11-slim 镜像，把 test.py 复制进去并运行
3. 执行 docker build -t lesson5-test {WORK_DIR} 构建镜像
4. 执行 docker run --rm lesson5-test 运行容器
5. 告诉我运行结果
"""
)
