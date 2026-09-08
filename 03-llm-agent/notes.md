# Phase 3 学习笔记：LLM & Agent 基础

## LLM 基础

### 什么是 LLM
- LLM = Large Language Model（大语言模型）
- 核心原理：根据已有文字，预测下一个最可能的词
- 本质是一个"文本进、文本出"的函数

### API 调用
- API = 用代码和 LLM 对话（vs 网页版手动打字）
- 优势：可以被程序自动化调用，批量处理
- 代码写在 `.py` 文件里，终端用 `python xxx.py` 运行

### 关键概念
| 概念 | 含义 |
|------|------|
| `model` | 选哪个模型 |
| `max_tokens` | 回复最大长度 |
| `messages` | 对话历史（JSON 数组） |
| `api_key` | 身份认证 |
| `token` | LLM 的最小处理单位，≈ 词的碎片 |

### messages 结构
```python
messages = [
    {"role": "user", "content": "你好"},        # 用户说的
    {"role": "assistant", "content": "你好！"},  # AI 回的
]
```
- LLM 没有记忆，每次都要传入完整对话历史
- `role` 只有两种：`user`（用户）和 `assistant`（AI）

### System Prompt
- 给 AI 的"角色设定"，告诉它是谁、该干啥、什么不能干
- 优先级高于普通 messages，AI 会严格遵守
- CVEFactory 用它定义 Agent 为"漏洞复现专家"

---

## Agent

### 什么是 Agent
- Agent = LLM + 工具调用能力
- LLM 只能"说"，Agent 能"做"

### 工具（Tool）
- 工具 = 程序员写的 Python 函数
- 用 JSON 格式（input_schema）告诉 LLM 怎么调用
  - `name`: 工具名
  - `description`: 给 LLM 看的说明书
  - `properties`: 参数列表和类型
  - `required`: 必填参数

### ReAct 循环（Agent Loop）
```
用户提问 → LLM 思考 → 调用工具 → 看结果 → 再思考 → ...
                                                ↓ 够了
                                           生成最终回答
```
- LLM 自己决定调哪个工具、调几次
- 停止条件：信息够了 或 达到最大步数限制
- 不是写死的触发规则，LLM 理解语义后自行判断

### Agent vs 脚本
- 脚本：写死的流程，遇到意外就卡住
- Agent：根据结果动态调整，能自己改代码重试

---

## Multi-Agent

### 为什么需要多 Agent
- 一个 CVE 的复现流程复杂，一个 Agent 全做太慢
- 多个 Agent 并行处理不同的 CVE

### CVEFactory 架构
```
Orchestrator（编排器）
  ├── Agent-1 → CVE-001（容器1）
  ├── Agent-2 → CVE-002（容器2）
  └── Agent-3 → CVE-003（容器3）
```
- 核心技术：asyncio.gather 并发调度

### 单个 CVE Agent 工作流程
1. 创建 Docker 容器
2. 挂载漏洞代码
3. LLM 分析补丁
4. 写 PoC 代码
5. 在容器里运行测试
6. 判断结果，不对就修改重试
7. 成功或超时后收集结果
8. 销毁容器

### 技术栈总对应
| 技术 | CVEFactory 角色 |
|------|----------------|
| Python | 编程语言 |
| subprocess | 调用 Docker 命令 |
| asyncio.gather | 并发处理多个 CVE |
| Docker run/-v/--rm | 创建/挂载/销毁环境 |
| Dockerfile | 构建基础镜像 |
| DinD | 主容器创建子容器 |
| LLM API | Agent 的大脑 |
| Tool Use | 调用各种工具 |
| System Prompt | 定义 Agent 角色 |

---

## 神经网络基础（3b1b 视频笔记）

### 核心概念
- **bias（偏置）**：神经元的激活门槛，训练后固定
- **weights（权重）**：连接强度，决定上一层对下一层的影响
- **全连接层**：下一层每个神经元连接上一层所有神经元（连接结构固定，权重训练出来）
- **激活**：加权求和 + bias 超过阈值才激活，未激活的神经元输出 ≈ 0

### 训练过程
1. **前向传播**：输入数据，算出预测
2. **Loss（损失函数）**：和正确答案对比，算误差
3. **反向传播（Backpropagation）**：链式求导，算每个参数的梯度 ∂Loss/∂w
4. **梯度下降**：`w_new = w_old - 学习率 × 梯度`，重复百万次

### 关键理解
- 梯度 = 把总误差分配到每个参数上，告诉你每个参数该怎么调
- 同一个网络处理所有输入，不同输入产生不同激活模式
- 训练需要大量标注数据 + 大量算力

---

## 真实 Agent 轨迹

### 数据来源
- HuggingFace 上有公开的 Agent 轨迹数据集
- 格式就是 messages JSON 数组

### 真实轨迹示例（swe-agent 修 bug）
```
[1] SYSTEM   → 系统设定
[2] USER     → bug 描述
[3] ASSISTANT → 读代码（调用 view 工具）
[4] USER     → 工具返回代码内容（OBSERVATION）
...反复读代码找问题...
[9] ASSISTANT → 写测试脚本复现 bug
[11] ASSISTANT → 运行脚本确认问题
[13] ASSISTANT → 修改代码
[15] ASSISTANT → 再跑测试确认修复
[17] ASSISTANT → 提交
```

**核心模式：读代码 → 思考 → 写测试 → 运行 → 改代码 → 验证**
