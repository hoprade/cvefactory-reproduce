import os, json
from openai import OpenAI

key = os.environ["DASHSCOPE_API_KEY"]

client = OpenAI(api_key = key, base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1")

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

messages = [{"role": "user", "content": "帮我看看 /root/mywork/learn 目录下面里有几个文件夹"}]

while True:
    response = client.chat.completions.create(
        model = "deepseek-v3", tools = tools, messages = messages
    )
    msg = response.choices[0].message
    if msg.tool_calls:
        messages.append(msg)
        tool_call = msg.tool_calls[0]
        args = json.loads(tool_call.function.arguments)

        if tool_call.function.name == "read_file":
            result = open(args["path"]).read()
        elif tool_call.function.name == "run_command":
            import subprocess
            result = subprocess.run(args["command"], shell = True, capture_output = True, text = True).stdout

        messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
    else:
        print(msg.content)
        break


