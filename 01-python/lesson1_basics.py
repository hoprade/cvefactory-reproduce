"""
Lesson 1: C++ 选手快速上手 Python
跑一遍，看输出，改改玩
"""

# === 1. 变量和类型：没有声明，直接用 ===
# C++: int x = 10; string s = "hello";
x = 10
s = "hello"
nums = [1, 2, 3, 4, 5]  # C++ 的 vector<int>
d = {"name": "张三", "age": 20}  # C++ 的 unordered_map

print(f"x={x}, s={s}, nums={nums}")
print(f"字典取值: {d['name']}, 年龄: {d['age']}")


# === 2. 列表推导式：Python 最常用的写法 ===
# C++: for(int i=0;i<10;i++) if(i%2==0) v.push_back(i*i);
squares = [i * i for i in range(10) if i % 2 == 0]
print(f"偶数的平方: {squares}")


# === 3. 函数：带类型提示（不强制，但好项目都写） ===
def two_sum(nums: list[int], target: int) -> list[int]:
    """你熟悉的两数之和，Python 写法"""
    seen: dict[int, int] = {}
    for i, n in enumerate(nums):
        comp = target - n
        if comp in seen:
            return [seen[comp], i]
        seen[n] = i
    return []

print(f"two_sum([2,7,11,15], 9) = {two_sum([2, 7, 11, 15], 9)}")


# === 4. 字符串处理：比 C++ 方便太多 ===
path = "/home/user/CVE-2025-1234.md"
filename = path.split("/")[-1]          # 取最后一段
cve_id = filename.replace(".md", "")    # 去掉后缀
year = cve_id.split("-")[1]             # 取年份
print(f"文件名: {filename}, CVE ID: {cve_id}, 年份: {year}")


# === 5. 文件读写：CVEFactory 大量使用 ===
import json

data = {"cve_id": "CVE-2025-1234", "severity": "high", "stages_completed": [1, 2, 3]}

with open("example.json", "w") as f:
    json.dump(data, f, indent=2)

with open("example.json", "r") as f:
    loaded = json.load(f)
    print(f"读回来: {loaded}")


# === 6. 异常处理：Python 的 try/catch ===
# C++: try { } catch(exception& e) { }
try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"捕获异常: {e}")


# === 练习题（写在下面，跑通为止）===
# 
# 题目：给你一个 CVE 列表文件（每行一个 CVE-ID），
#       统计每个年份有多少个 CVE，输出 JSON
#
# 输入示例（cve_list.txt）:
#   CVE-2024-1001
#   CVE-2024-1002  
#   CVE-2025-2001
#   CVE-2025-2002
#   CVE-2025-2003
#
# 期望输出: {"2024": 2, "2025": 3}
#
# 提示: 用 split("-") 取年份，用 dict 计数
# 你的代码写在这里 ↓

with open("cve_list.txt", "r") as f:
    lines = f.readlines()
count = {}
for line in lines:
    line = line.strip()
    year = line.split("-")[1]
    if year in count:
        count[year] += 1
    else:
        count[year] = 1

print(json.dumps(count))
