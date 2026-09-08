import os
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
    }
]

response = client.chat.completions.create(
    model = "deepseek-v3", 
    messages = [{"role": "user", "content": "帮我看看 /root/mywork/learn/01-python/cve_list.txt 里有几个CVE"}],
    tools = tools
)

print(response.choices[0].message)

tool_call = response.choices[0].message.tool_calls[0]
print(tool_call.function.name)
print(tool_call.function.arguments)

import json
args = json.loads(tool_call.function.arguments)
path = args["path"]
result = open(path).read()
print(result)

messages = [
    {"role": "user", "content": "帮我看看 /root/mywork/learn/01-python/cve_list.txt 里有几个CVE"},
    response.choices[0].message,
    {"role": "tool", "tool_call_id": tool_call.id, "content": result}
]

response2 = client.chat.completions.create(
    model="deepseek-v3",
    messages=messages,
    tools=tools
)

print(response2.choices[0].message.content)
