"""
Lesson 2: subprocess —— 用 Python 调用外部命令
CVEFactory 用这个来执行 docker 命令、运行测试脚本等
"""

import subprocess

# === 1. 最简单的用法：跑个命令，拿输出 ===
result = subprocess.run(["echo", "hello from subprocess"], capture_output=True, text=True)
print(f"stdout: {result.stdout.strip()}")
print(f"返回码: {result.returncode}")  # 0 表示成功


# === 2. 跑 shell 命令（带管道）===
result = subprocess.run("ls -la /root/mywork/learn/ | head -5", shell=True, capture_output=True, text=True)
print(f"\n目录内容:\n{result.stdout}")


# === 3. 捕获错误 ===
result = subprocess.run(["ls", "/不存在的路径"], capture_output=True, text=True)
print(f"错误输出: {result.stderr.strip()}")
print(f"返回码: {result.returncode}")  # 非0 表示失败


# === 4. 实际场景：检查 docker 是否可用 ===
def check_tool(name: str) -> bool:
    """检查某个命令行工具是否存在"""
    result = subprocess.run(["which", name], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✓ {name} 可用，路径: {result.stdout.strip()}")
        return True
    else:
        print(f"✗ {name} 不可用")
        return False

print()
for tool in ["python3", "docker", "git", "gcc"]:
    check_tool(tool)


# === 5. 设置超时（防止命令卡死）===
try:
    subprocess.run(["sleep", "10"], timeout=2)
except subprocess.TimeoutExpired:
    print("\n命令超时被杀掉了（设了2秒超时）")

