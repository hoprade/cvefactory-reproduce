#!/usr/bin/env python3
# test_diff.py - 对比修复前后的检测脚本行为

import subprocess

def run_script(script_path):
    """运行指定脚本并返回输出"""
    result = subprocess.run(['python3', script_path], capture_output=True, text=True)
    return result.stdout

def compare_outputs(original_output, patched_output):
    """对比两个版本的输出"""
    if original_output == patched_output:
        return "输出完全一致，未检测到行为差异。"
    else:
        return "输出存在差异：\n\n修复前输出：\n{}\n\n修复后输出：\n{}".format(original_output, patched_output)

if __name__ == "__main__":
    original_output = run_script("detect.py")
    patched_output = run_script("patch.py")
    comparison_result = compare_outputs(original_output, patched_output)
    
    # 将对比结果写入 diff_report.md
    with open("diff_report.md", "w") as f:
        f.write("# 差异测试报告\n\n")
        f.write("## 修复前后脚本行为对比\n\n")
        f.write(comparison_result + "\n")
        
    print("差异测试报告已生成：diff_report.md")