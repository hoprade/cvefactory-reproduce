# Docker Compose & Docker-in-Docker

> 这课直接对接 CVEFactory 的架构

## Part 1: Docker Compose — 多容器编排

CVEFactory 不是只跑一个容器——它需要同时运行：
- 主控程序（Orchestrator）
- 多个漏洞复现环境（每个 CVE 一个容器）
- 可能还有数据库等辅助服务

**docker-compose** 用一个 YAML 文件定义和管理多个容器。

### 练习 1：基础 compose

```bash
mkdir -p /tmp/docker-lab/compose1
cd /tmp/docker-lab/compose1
```

```bash
# 创建两个简单的服务
cat > worker.py << 'EOF'
import os, time, json

worker_id = os.environ.get("WORKER_ID", "unknown")
task = os.environ.get("TASK", "idle")

print(json.dumps({
    "worker": worker_id,
    "task": task,
    "status": "started"
}))

time.sleep(2)

print(json.dumps({
    "worker": worker_id,
    "task": task,
    "status": "completed"
}))
EOF

cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY worker.py .
CMD ["python", "-u", "worker.py"]
EOF

# -u 让 Python 不缓冲输出，这样 docker logs 能实时看到
```

创建 `docker-compose.yml`：

```bash
cat > docker-compose.yml << 'EOF'
services:
  worker-1:
    build: .
    environment:
      - WORKER_ID=agent-1
      - TASK=analyze_patch

  worker-2:
    build: .
    environment:
      - WORKER_ID=agent-2
      - TASK=build_poc

  worker-3:
    build: .
    environment:
      - WORKER_ID=agent-3
      - TASK=verify_exploit
EOF
```

```bash
# 构建并启动所有服务
docker compose up --build

# 三个 worker 会同时启动、并行执行
# 观察输出：这就是 CVEFactory 的 Agent 并行模式！

# Ctrl+C 停止后，清理
docker compose down
```

### 练习 2：服务间通信

```bash
mkdir -p /tmp/docker-lab/compose2
cd /tmp/docker-lab/compose2
```

```bash
cat > server.py << 'EOF'
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response = {"message": "CVE data ready", "count": 42}
        self.wfile.write(json.dumps(response).encode())

    def log_message(self, format, *args):
        print(f"[server] {args[0]}")

HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
EOF

cat > client.py << 'EOF'
import urllib.request, json, time

time.sleep(2)  # 等 server 启动

# compose 中服务名就是主机名！
url = "http://data-server:8000"
try:
    resp = urllib.request.urlopen(url, timeout=5)
    data = json.loads(resp.read())
    print(f"[client] Got from server: {data}")
except Exception as e:
    print(f"[client] Error: {e}")
EOF

cat > Dockerfile.server << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY server.py .
CMD ["python", "-u", "server.py"]
EOF

cat > Dockerfile.client << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY client.py .
CMD ["python", "-u", "client.py"]
EOF

cat > docker-compose.yml << 'EOF'
services:
  data-server:
    build:
      context: .
      dockerfile: Dockerfile.server

  client:
    build:
      context: .
      dockerfile: Dockerfile.client
    depends_on:
      - data-server
EOF
```

```bash
docker compose up --build
# 观察：client 通过服务名 "data-server" 访问到了 server
# 这就是 Docker 的内部 DNS！
docker compose down
```

---

## Part 2: Docker-in-Docker (DinD) — CVEFactory 的核心

### 什么是 DinD？

```
宿主机
└── Docker daemon
    └── CVEFactory 主容器
        └── Docker daemon (DinD)
            ├── CVE-2024-001 容器
            ├── CVE-2024-002 容器
            └── CVE-2024-003 容器
```

CVEFactory 自己运行在容器里，但它需要**在容器里面再创建容器**来复现漏洞。
这就是 Docker-in-Docker。

### 练习 3：体验 DinD

```bash
# 方法 1：挂载宿主机的 Docker socket（简单，CVEFactory 用这种）
docker run --rm -it \
  -v /var/run/docker.sock:/var/run/docker.sock \
  docker:cli \
  sh

# 进入容器后，你可以在容器里使用 docker 命令！
# 试试：
#   docker ps        （能看到宿主机的容器）
#   docker images    （能看到宿主机的镜像）
#   docker run --rm alpine echo "inception!"
#   exit
```

### 练习 4：Python 控制 Docker（模拟 CVEFactory）

```bash
mkdir -p /tmp/docker-lab/dind-test
cd /tmp/docker-lab/dind-test
```

```bash
cat > orchestrator.py << 'PYEOF'
"""
模拟 CVEFactory 的 Orchestrator：
用 Python subprocess 在容器内控制 Docker，创建子容器
"""
import subprocess
import json
import time

def run_in_container(image, command, name=None):
    """在新容器中运行命令并返回输出"""
    cmd = ["docker", "run", "--rm"]
    if name:
        cmd += ["--name", name]
    cmd += [image] + command

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return {
        "exit_code": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip()
    }

def simulate_cve_reproduction(cve_id):
    """模拟一个 CVE 的复现流程"""
    print(f"\n{'='*50}")
    print(f"Reproducing {cve_id}")
    print(f"{'='*50}")

    # Stage 1: 环境准备（检查系统信息）
    print(f"[{cve_id}] Stage 1: Environment Setup")
    result = run_in_container("alpine", ["cat", "/etc/os-release"])
    os_info = result["stdout"].split("\n")[0]
    print(f"  -> OS: {os_info}")

    # Stage 2: 模拟漏洞代码执行
    print(f"[{cve_id}] Stage 2: Running vulnerable code")
    result = run_in_container("python:3.11-slim",
        ["python", "-c", f"print('Testing {cve_id}: vulnerability triggered')"])
    print(f"  -> {result['stdout']}")

    # Stage 3: 验证
    print(f"[{cve_id}] Stage 3: Verification")
    result = run_in_container("alpine",
        ["sh", "-c", "echo 'exploit_verified=true'"])
    print(f"  -> {result['stdout']}")

    return {"cve_id": cve_id, "status": "reproduced"}

if __name__ == "__main__":
    cves = ["CVE-2024-0001", "CVE-2024-0002"]

    print("CVEFactory Orchestrator (simplified)")
    print("=" * 50)

    results = []
    for cve in cves:
        result = simulate_cve_reproduction(cve)
        results.append(result)

    print(f"\n{'='*50}")
    print("Final Results:")
    print(json.dumps(results, indent=2))
PYEOF

cat > Dockerfile << 'EOF'
FROM python:3.11-slim

# 安装 Docker CLI（让容器内能用 docker 命令）
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    curl -fsSL https://get.docker.com | sh && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY orchestrator.py .

CMD ["python", "-u", "orchestrator.py"]
EOF
```

```bash
# 构建
docker build -t orchestrator:v1 .

# 运行——挂载 docker.sock 让容器能控制 Docker
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  orchestrator:v1

# 观察：Python 程序在容器里创建了新容器来"复现漏洞"
# 这就是 CVEFactory 的核心架构！
```

---

## 关键概念总结

```
CVEFactory 架构映射：

docker-compose.yml          = 定义整个系统的服务
├── orchestrator (主容器)    = Orchestrator Agent
│   ├── -v docker.sock      = DinD 能力
│   ├── subprocess.run()    = 控制子容器
│   └── asyncio.gather()    = 并发调度多个 CVE
└── 子容器 (按需创建)        = 每个 CVE 的复现环境
    ├── -v 挂载漏洞代码
    ├── -e 传入配置
    └── --rm 用完销毁
```

---

## 自测题

1. `docker compose up` 中的服务怎么互相访问？
2. Docker socket 挂载 (`-v /var/run/docker.sock:...`) 的安全风险是什么？
3. CVEFactory 为什么选 DinD 而不是直接在宿主机上跑漏洞代码？
