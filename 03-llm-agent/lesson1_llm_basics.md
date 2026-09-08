# LLM 基础：大语言模型是什么

> 类比：LLM = 一个超强的"自动补全"，你给它前文，它预测下一个词

## 什么是 LLM？

LLM = Large Language Model（大语言模型），比如 ChatGPT、Claude。

核心原理很简单：**根据已有的文字，预测下一个最可能的词**。

```
输入: "中国的首都是"
模型预测: "北京" (概率最高)
```

它不是"理解"语言，而是在海量文本上训练后，学会了词与词之间的统计规律。但因为训练数据足够多、模型足够大，效果看起来像是"理解"了。

## LLM 的能力边界

| 能做 | 不能做 |
|------|--------|
| 生成文本、翻译、总结 | 执行代码（它只会写，不会跑） |
| 回答知识性问题 | 访问互联网（除非给它工具） |
| 分析代码、找 bug | 记住上次对话（除非传入历史） |
| 按指令格式化输出 | 100% 准确（会"幻觉"，编造事实） |

**关键认知：LLM 本身只是一个"文本进、文本出"的函数。**

---

## API 调用：用代码和 LLM 对话

你平时用的 ChatGPT 网页版是"聊天界面"，但在程序里我们通过 **API** 调用 LLM。

### API 是什么？

API = Application Programming Interface（应用编程接口）

类比：
- 网页版 ChatGPT = 你去餐厅坐下来点菜
- API = 你打电话给餐厅，告诉它要什么菜，它做好送过来

都是同一个厨房（同一个模型），只是交互方式不同。程序员用 API 是因为可以**自动化**——写代码批量调用，不用手动打字。

### 调用 Claude API 的代码

```python
import anthropic

# 创建客户端（需要 API Key）
client = anthropic.Anthropic(api_key="sk-ant-xxx")

# 发送消息
response = client.messages.create(
    model="claude-sonnet-5",          # 选哪个模型
    max_tokens=1024,                   # 最多生成多少 token
    messages=[
        {"role": "user", "content": "什么是缓冲区溢出漏洞？用一句话解释"}
    ]
)

# 拿到回复
print(response.content[0].text)
```

### 关键参数解释

| 参数 | 含义 | 类比 |
|------|------|------|
| `model` | 选用哪个模型 | 选哪个厨师做菜 |
| `max_tokens` | 回复的最大长度 | 限制回答字数 |
| `messages` | 对话历史 | 你和 AI 的聊天记录 |
| `api_key` | 身份认证 | 会员卡，证明你有权限调用 |

### Token 是什么？

Token ≈ 词的碎片。LLM 不按"字"处理文本，而是按 token。

```
"Hello world" → ["Hello", " world"]     = 2 tokens
"缓冲区溢出"   → ["缓冲", "区", "溢出"]  = 3 tokens（大约）
```

API 按 token 收费：输入 token + 输出 token = 总费用。

### messages 的结构

```python
messages = [
    {"role": "user", "content": "你好"},           # 用户说的
    {"role": "assistant", "content": "你好！"},     # AI 回的
    {"role": "user", "content": "1+1=?"},           # 用户又说的
]
```

LLM **没有记忆**，每次调用都是独立的。要实现"多轮对话"，就把之前的对话历史全部放进 `messages` 再发一次。

---

## 动手练习

### 练习 1：模拟 API 调用（不需要真的 API Key）

```python
# 保存为 /tmp/llm-lab/simulate_api.py

import json

def fake_llm(messages, model="claude-sonnet-5"):
    """
    模拟 LLM API 调用
    真正的 API 会把 messages 发给服务器，服务器返回 AI 的回复
    这里我们用固定回复来模拟
    """
    last_message = messages[-1]["content"]

    # 模拟 LLM 的回复逻辑
    if "漏洞" in last_message or "CVE" in last_message:
        reply = "这是一个安全漏洞，可能导致远程代码执行。建议立即更新到最新版本。"
    elif "代码" in last_message:
        reply = "```python\nprint('Hello')\n```"
    else:
        reply = f"收到你的消息：{last_message}"

    return {
        "model": model,
        "content": [{"type": "text", "text": reply}],
        "usage": {"input_tokens": len(last_message) * 2, "output_tokens": len(reply) * 2}
    }

# 单轮对话
print("=== 单轮对话 ===")
response = fake_llm([
    {"role": "user", "content": "CVE-2024-0001 是什么漏洞？"}
])
print(f"模型: {response['model']}")
print(f"回复: {response['content'][0]['text']}")
print(f"Token 用量: {response['usage']}")

# 多轮对话——把历史都传进去
print("\n=== 多轮对话 ===")
history = []

# 第一轮
history.append({"role": "user", "content": "你好"})
resp1 = fake_llm(history)
reply1 = resp1["content"][0]["text"]
history.append({"role": "assistant", "content": reply1})
print(f"User: 你好")
print(f"AI: {reply1}")

# 第二轮——history 包含了第一轮的记录
history.append({"role": "user", "content": "帮我分析一个漏洞"})
resp2 = fake_llm(history)
reply2 = resp2["content"][0]["text"]
print(f"User: 帮我分析一个漏洞")
print(f"AI: {reply2}")

print(f"\n对话历史长度: {len(history)} 条消息")
```

运行：
```bash
mkdir -p /tmp/llm-lab
# 创建文件后运行
python /tmp/llm-lab/simulate_api.py
```

### 练习 2：理解 system prompt

```python
# 保存为 /tmp/llm-lab/system_prompt.py

def fake_llm_with_system(system, messages):
    """
    system prompt = 给 AI 的"角色设定"
    它告诉 AI 应该以什么身份、什么风格回答
    """
    last_msg = messages[-1]["content"]

    # 根据不同的 system prompt，AI 的回复风格完全不同
    if "安全专家" in system:
        return f"[安全专家模式] 从安全角度分析：{last_msg} 可能存在注入风险，建议使用参数化查询。"
    elif "初学者导师" in system:
        return f"[导师模式] 简单来说，{last_msg} 就像是程序里的一个小门，坏人可以从这个门溜进来。"
    else:
        return f"收到：{last_msg}"

question = "SQL注入是什么？"

# 同一个问题，不同 system prompt
print("=== 安全专家 ===")
print(fake_llm_with_system(
    system="你是一个资深安全专家，用专业术语回答",
    messages=[{"role": "user", "content": question}]
))

print("\n=== 初学者导师 ===")
print(fake_llm_with_system(
    system="你是一个耐心的初学者导师，用简单比喻解释",
    messages=[{"role": "user", "content": question}]
))
```

真正的 API 调用中，system prompt 是这样传的：

```python
response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    system="你是一个安全漏洞分析专家",    # system prompt
    messages=[
        {"role": "user", "content": "分析 CVE-2024-0001"}
    ]
)
```

---

## 自测题

1. LLM 为什么需要把"对话历史"每次都传进去？
2. `system prompt` 的作用是什么？CVEFactory 可能用它来做什么？
3. Token 和字符的区别是什么？为什么 API 按 token 收费而不是按字？
