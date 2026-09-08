"""
第五阶段 Lesson 1：调用 LLM API
================================

目标：学会用 Python 调大模型 API，理解 messages 格式
对应 CVEFactory：agent_runner.py 里调 Claude 的部分

前置：
  pip install openai
  服务器上已有 DASHSCOPE_API_KEY 环境变量（百炼平台）

百炼用 OpenAI 兼容接口，学会这个格式，换 Claude/GPT/SiliconFlow 只改一行配置。
"""

import os
from openai import OpenAI

# ============================================================
# 第一步：连接 API
# ============================================================
# 从环境变量读 key，不要硬编码（安全习惯）
# 百炼标准接口，支持 deepseek-v3、qwen-plus 等模型

client = OpenAI(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# ============================================================
# 第二步：最简单的对话 —— 发一条消息，拿回复
# ============================================================
def basic_chat():
    """最基础的 API 调用"""
    response = client.chat.completions.create(
        model="deepseek-v3",  # 或 "qwen-plus", "qwen-max"
        messages=[
            {"role": "user", "content": "用一句话解释什么是CVE"}
        ],
    )

    # response 的结构
    reply = response.choices[0].message.content
    print("模型回复:", reply)
    print()

    # 看看完整的 response 对象长什么样
    print("完整 response:")
    print(f"  model: {response.model}")
    print(f"  用了多少 token: {response.usage}")


# ============================================================
# 第三步：理解 messages —— 这是 LLM API 的核心概念
# ============================================================
def understand_messages():
    """
    messages 是一个列表，每条消息有 role 和 content：

    - system: 系统提示词，告诉模型"你是谁、该怎么做"
              → 对应 CVEFactory 的 agents/*.md
    - user:   用户的输入
              → 对应 Orchestrator 给 Agent 的指令
    - assistant: 模型的回复
              → 对应 Agent 的输出

    多轮对话就是不断往 messages 列表里追加消息。
    """
    response = client.chat.completions.create(
        model="deepseek-v3",
        messages=[
            # system prompt — CVEFactory 里每个 Agent 的 .md 文件就是这个
            {
                "role": "system",
                "content": "你是一个安全研究员，专门分析 CVE 漏洞。回答要简洁专业。"
            },
            # user message — Orchestrator 给 Agent 的指令
            {
                "role": "user",
                "content": "分析一下 CVE-2014-125066 这个漏洞的影响"
            },
        ],
    )

    print("带 system prompt 的回复:")
    print(response.choices[0].message.content)


# ============================================================
# 第四步：多轮对话 —— 把历史消息都传回去
# ============================================================
def multi_turn_chat():
    """
    LLM 本身没有记忆！每次调 API 都是全新的。
    要实现多轮对话，必须你自己维护 messages 列表，
    每次把完整历史都发过去。

    这就是为什么 CVEFactory 要做 context 隔离 ——
    Agent 的 context window 有限，塞不下所有历史。
    """
    messages = [
        {"role": "system", "content": "你是一个 Python 教学助手，用中文回答。"},
    ]

    questions = [
        "asyncio.gather 是干什么的？一句话说",
        "它和多线程有什么区别？",
        "给个最简单的例子",
    ]

    for q in questions:
        print(f">>> {q}")

        # 追加用户消息
        messages.append({"role": "user", "content": q})

        response = client.chat.completions.create(
            model="deepseek-v3",
            messages=messages,   # 每次都传完整历史！
        )

        reply = response.choices[0].message.content
        print(f"<<< {reply}\n")

        # 追加模型回复到历史（这样下一轮它能看到之前说过什么）
        messages.append({"role": "assistant", "content": reply})

    print(f"最终 messages 列表有 {len(messages)} 条消息")


# ============================================================
# 第五步：参数调节
# ============================================================
def parameters_demo():
    """
    几个常用参数：
    - temperature: 0~2，越高越随机/创意，越低越确定/稳定
      CVEFactory 用的模型需要稳定输出，一般用低 temperature
    - max_tokens: 最大输出长度
    """
    # 同一个问题，不同 temperature
    prompt = "给 Python 变量起个名字，表示'用户列表'"

    for temp in [0.0, 1.0, 2.0]:
        response = client.chat.completions.create(
            model="deepseek-v3",
            messages=[{"role": "user", "content": prompt}],
            temperature=temp,
            max_tokens=50,
        )
        reply = response.choices[0].message.content
        print(f"temperature={temp}: {reply}")


# ============================================================
# 运行
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("1. 基础对话")
    print("=" * 50)
    basic_chat()

    print("\n" + "=" * 50)
    print("2. System Prompt")
    print("=" * 50)
    understand_messages()

    print("\n" + "=" * 50)
    print("3. 多轮对话")
    print("=" * 50)
    multi_turn_chat()

    print("\n" + "=" * 50)
    print("4. Temperature 对比")
    print("=" * 50)
    parameters_demo()


# ============================================================
# 练习题
# ============================================================
"""
练习 1：换模型
  把 model 换成 "qwen-plus" 或 "qwen-max"，对比回复质量

练习 2：写一个简单的 CLI 聊天机器人
  循环读 input()，调 API，打印回复，维护 messages 列表
  输入 "quit" 退出

练习 3：模拟 CVEFactory 的 Analyzer
  写一个 system prompt，让模型扮演安全分析师
  给它一个 CVE 编号，让它输出分析报告
  （现在模型没有搜索能力，只能用它已有的知识，后面加工具后就能搜了）

练习 4（思考题）：
  CVEFactory 的 agent_runner.py 用 Claude Agent SDK 调 Claude API。
  它做的事情和我们这里的 client.chat.completions.create() 本质一样吗？

  答案：本质一样。都是"组装 messages → 发给 LLM → 拿回复"。
  SDK 只是封装了更多功能（工具调用、会话管理、流式输出等）。
"""
