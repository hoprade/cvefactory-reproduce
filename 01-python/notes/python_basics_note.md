# Python 工程基础笔记（C++ 选手版）

> 学习日期：2026-09-04
> 目标：为复现 CVEFactory 打基础

---

## 一、Python vs C++ 核心差异

| 特性 | C++ | Python |
|------|-----|--------|
| 变量声明 | `int x = 10;` | `x = 10` |
| 数组/列表 | `vector<int> v;` | `nums = [1, 2, 3]` |
| 哈希表 | `unordered_map<string, int>` | `d = {"key": value}` |
| 字符串 | `string s; s.substr(...)` | `s = "hello"; s.split(...)` |
| 类型 | 编译期强制 | 运行时动态，可加类型提示 |

---

## 二、列表推导式

C++ 里需要 for 循环 + push_back，Python 一行搞定：

```python
# 偶数的平方
squares = [i * i for i in range(10) if i % 2 == 0]

# 等价的 C++:
# for(int i=0; i<10; i++) if(i%2==0) v.push_back(i*i);
```

---

## 三、文件 IO + JSON

CVEFactory 大量读写 JSON 配置文件（task.yaml、CVE 元数据等），这套操作必须熟：

```python
import json

# 写
with open("data.json", "w") as f:
    json.dump({"key": "value"}, f, indent=2)

# 读
with open("data.json", "r") as f:
    data = json.load(f)
```

**要点**：`with open(...)` 会自动关闭文件，永远用这个写法。

---

## 四、subprocess —— 用 Python 调外部命令

CVEFactory 用这个来执行 `docker build`、`docker run`、运行测试脚本等。

```python
import subprocess

result = subprocess.run(
    ["docker", "ps"],       # 命令和参数，列表形式
    capture_output=True,    # 捕获 stdout 和 stderr
    text=True,              # 输出为字符串（否则是 bytes）
    timeout=30              # 超时秒数，防卡死
)

print(result.stdout)        # 标准输出
print(result.stderr)        # 错误输出
print(result.returncode)    # 0=成功，非0=失败
```

**带管道的命令**要用 `shell=True`：

```python
result = subprocess.run("ps aux | grep python", shell=True, capture_output=True, text=True)
```

---

## 五、async/await —— 异步并发（最重要）

### 为什么需要异步？

CVEFactory 要同时处理多个 CVE，每个 CVE 都要调 LLM API（等几秒）、跑 Docker（等几十秒）。如果串行，处理 100 个 CVE 要等到天荒地老。异步让**等待的时间可以做别的事**。

### 核心三件套

```python
import asyncio

# 1. 定义异步函数：加 async
async def call_llm(prompt: str) -> str:
    await asyncio.sleep(1)  # 模拟等待 API 响应
    return "LLM 的回答"

# 2. 并发执行多个任务：asyncio.gather
async def main():
    results = await asyncio.gather(
        call_llm("分析 CVE-1"),
        call_llm("分析 CVE-2"),
        call_llm("分析 CVE-3"),
    )
    # 3个任务并发，总耗时≈1秒而不是3秒

# 3. 启动入口
asyncio.run(main())
```

### 串行 vs 并发 对比

```
串行（await 一个接一个）：
  A------>B------>C------> 总共 3 秒

并发（asyncio.gather）：
  A------>
  B------>  总共 1 秒
  C------>
```

### 关键理解

- `async def` 定义协程，**不会自动执行**，要 `await` 它
- `await` = "在这里等结果，等待期间让出控制权给别的协程"
- `asyncio.gather()` = "同时启动多个协程，全部完成后返回结果列表"
- 这不是多线程！是**单线程内的任务切换**，在 IO 等待时切换

---

## 六、和 CVEFactory 的关系

| 你学的 | CVEFactory 怎么用 |
|--------|-------------------|
| JSON 读写 | 读 CVE 元数据、写任务配置 |
| subprocess | 调 `docker build/run`、执行测试脚本 |
| async/await | Orchestrator 并发调度多个 Agent |
| asyncio.gather | 同时处理多个 CVE 的 pipeline |

CVEFactory 的核心模式：**Orchestrator 用 asyncio.gather 并发启动多个 Agent，每个 Agent 通过 subprocess 操作 Docker 环境，中间数据用 JSON 传递。**

---

## 下一步

学 Docker 基础：镜像、容器、Dockerfile、docker-compose。
