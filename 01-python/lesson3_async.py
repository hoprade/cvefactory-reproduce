"""
Lesson 3: async/await —— Python 异步编程
CVEFactory 的核心：多个 Agent 并发工作，不是一个做完再做下一个

对比 ACM 理解：
- 同步 = 一个线程，做完 A 再做 B
- 异步 = 一个线程，A 在等 IO 时切去做 B（协程）
"""

import asyncio
import time

# === 1. 最基础的 async 函数 ===
async def say_hello(name: str, delay: float):
    """模拟一个耗时操作（比如调用 LLM API）"""
    print(f"[{name}] 开始工作...")
    await asyncio.sleep(delay)  # 模拟等待（不会阻塞其他协程）
    print(f"[{name}] 完成！（等了 {delay} 秒）")
    return f"{name} 的结果"


# === 2. 串行 vs 并发 ===
async def serial():
    """串行：一个做完再做下一个"""
    start = time.time()
    r1 = await say_hello("Agent-A", 1)
    r2 = await say_hello("Agent-B", 1)
    r3 = await say_hello("Agent-C", 1)
    print(f"串行总耗时: {time.time() - start:.1f}s, 结果: {[r1, r2, r3]}\n")


async def concurrent():
    """并发：同时开始，一起等"""
    start = time.time()
    r1, r2, r3 = await asyncio.gather(
        say_hello("Agent-A", 1),
        say_hello("Agent-B", 1),
        say_hello("Agent-C", 1),
    )
    print(f"并发总耗时: {time.time() - start:.1f}s, 结果: {[r1, r2, r3]}\n")


# === 3. 模拟 CVEFactory 的场景 ===
async def process_cve(cve_id: str) -> dict:
    """模拟处理一个 CVE 的 pipeline"""
    print(f"  [{cve_id}] Stage 1: 收集信息...")
    await asyncio.sleep(0.5)

    print(f"  [{cve_id}] Stage 2: 生成测试用例...")
    await asyncio.sleep(0.3)

    print(f"  [{cve_id}] Stage 3: 构建环境...")
    await asyncio.sleep(0.4)

    return {"cve_id": cve_id, "status": "reproduced"}


async def batch_process():
    """批量处理多个 CVE（并发）"""
    cves = ["CVE-2025-001", "CVE-2025-002", "CVE-2025-003"]

    start = time.time()
    print("=== 开始批量处理 CVE ===")
    results = await asyncio.gather(*[process_cve(cve) for cve in cves])
    print(f"\n全部完成！耗时: {time.time() - start:.1f}s")
    for r in results:
        print(f"  {r}")


# === 运行 ===
async def main():
    print("--- 串行执行 ---")
    await serial()

    print("--- 并发执行 ---")
    await concurrent()

    print("--- 模拟 CVEFactory 批量处理 ---")
    await batch_process()

asyncio.run(main())

