# Dockerfile：构建自定义镜像

> 类比：Dockerfile = Makefile，docker build = make

## Dockerfile 基本结构

```dockerfile
# 基础镜像（从哪里开始）
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制文件到镜像
COPY requirements.txt .

# 执行命令（安装依赖）
RUN pip install -r requirements.txt

# 复制项目代码
COPY . .

# 容器启动时执行的命令
CMD ["python", "main.py"]
```

每条指令 = 一层（layer），Docker 会缓存不变的层，加速重复构建。

---

## 动手练习

### 练习 1：构建一个 Python 镜像

```bash
# 创建项目目录
mkdir -p /tmp/docker-lab/app1
cd /tmp/docker-lab/app1
```

创建 `vuln_app.py`（模拟一个有漏洞的程序）：

```bash
cat > vuln_app.py << 'EOF'
import sys
import json

def check_vulnerability(version):
    """模拟漏洞检测：版本 < 2.0 有漏洞"""
    major = int(version.split(".")[0])
    result = {
        "version": version,
        "vulnerable": major < 2,
        "severity": "HIGH" if major < 2 else "SAFE"
    }
    return result

if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else "1.5.3"
    result = check_vulnerability(version)
    print(json.dumps(result, indent=2))
EOF
```

创建 `Dockerfile`：

```bash
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY vuln_app.py .

CMD ["python", "vuln_app.py"]
EOF
```

构建和运行：

```bash
# 构建镜像，-t 指定名字:标签
docker build -t vuln-checker:v1 .

# 运行，默认版本
docker run --rm vuln-checker:v1

# 传参覆盖默认命令
docker run --rm vuln-checker:v1 python vuln_app.py 3.0.0
docker run --rm vuln-checker:v1 python vuln_app.py 1.2.0
```

### 练习 2：带依赖的镜像

```bash
mkdir -p /tmp/docker-lab/app2
cd /tmp/docker-lab/app2
```

```bash
cat > requirements.txt << 'EOF'
requests==2.31.0
EOF

cat > fetch_cve.py << 'EOF'
import requests
import json
import sys

def fetch_cve_info(cve_id):
    """从公开 API 查询 CVE 信息"""
    url = f"https://cveawg.mitre.org/api/cve/{cve_id}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            title = data.get("containers", {}).get("cna", {}).get("title", "N/A")
            return {"cve_id": cve_id, "status": "found", "title": title}
        else:
            return {"cve_id": cve_id, "status": "not_found"}
    except Exception as e:
        return {"cve_id": cve_id, "status": "error", "message": str(e)}

if __name__ == "__main__":
    cve_id = sys.argv[1] if len(sys.argv) > 1 else "CVE-2024-0001"
    result = fetch_cve_info(cve_id)
    print(json.dumps(result, indent=2))
EOF

cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# 先复制 requirements.txt 并安装——利用 Docker 缓存
# 只有 requirements.txt 变了才会重新 pip install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY fetch_cve.py .

CMD ["python", "fetch_cve.py"]
EOF
```

```bash
# 构建
docker build -t cve-fetcher:v1 .

# 运行
docker run --rm cve-fetcher:v1
docker run --rm cve-fetcher:v1 python fetch_cve.py CVE-2023-44487
```

### 练习 3：ENTRYPOINT vs CMD

```bash
mkdir -p /tmp/docker-lab/app3
cd /tmp/docker-lab/app3

cat > scanner.py << 'EOF'
import sys
print(f"Scanning target: {' '.join(sys.argv[1:])}")
EOF

# CMD 方式：docker run 的参数会**替换**整个 CMD
cat > Dockerfile.cmd << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY scanner.py .
CMD ["python", "scanner.py", "default-target"]
EOF

# ENTRYPOINT 方式：docker run 的参数会**追加**到 ENTRYPOINT 后面
cat > Dockerfile.entry << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY scanner.py .
ENTRYPOINT ["python", "scanner.py"]
CMD ["default-target"]
EOF
```

```bash
# 对比两种方式
docker build -t scan-cmd -f Dockerfile.cmd .
docker build -t scan-entry -f Dockerfile.entry .

# 不传参——都输出 "Scanning target: default-target"
docker run --rm scan-cmd
docker run --rm scan-entry

# 传参——区别来了
docker run --rm scan-cmd echo "oops"          # CMD 被替换，变成 echo
docker run --rm scan-entry "192.168.1.1"      # 参数追加，python scanner.py 192.168.1.1
```

> **CVEFactory 用 ENTRYPOINT**，这样 Orchestrator 只需传 CVE-ID 作为参数，不用写完整命令。

---

## Dockerfile 指令速查

| 指令 | 作用 | 注意 |
|------|------|------|
| `FROM` | 基础镜像 | 必须是第一条 |
| `WORKDIR` | 设置工作目录 | 不存在会自动创建 |
| `COPY` | 复制文件到镜像 | 支持通配符 |
| `RUN` | 构建时执行命令 | 每条 RUN = 一层 |
| `CMD` | 默认启动命令 | 可被 docker run 参数覆盖 |
| `ENTRYPOINT` | 固定启动命令 | docker run 参数会追加 |
| `ENV` | 设置环境变量 | `ENV KEY=value` |
| `EXPOSE` | 声明端口 | 仅文档作用，实际映射用 -p |

---

## 自测题

1. 为什么先 `COPY requirements.txt` 再 `RUN pip install`，最后才 `COPY . .`？
2. `ENTRYPOINT` + `CMD` 组合使用时，各自的角色是什么？
3. 如何让构建出的镜像尽量小？
