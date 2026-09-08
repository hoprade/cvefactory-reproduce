# Docker 基础：镜像与容器

> 类比：镜像 = C++ 的 .exe 安装包，容器 = 运行起来的进程

## 核心概念

```
Dockerfile  --build-->  Image  --run-->  Container
(源代码)               (可执行文件)        (运行中进程)
```

- **镜像 (Image)**：只读模板，包含OS + 依赖 + 你的代码
- **容器 (Container)**：镜像的运行实例，相互隔离
- **仓库 (Registry)**：存镜像的地方（Docker Hub ≈ GitHub）

## 为什么 CVEFactory 需要 Docker？

CVEFactory 要复现漏洞，每个漏洞需要不同环境（不同版本的 Linux、Python、Java…）。
Docker 让每个漏洞在**独立容器**里运行，互不干扰，用完销毁。

---

## 动手练习

**按顺序在终端执行，观察输出：**

### 练习 1：拉取并运行第一个容器

```bash
# 拉取一个极小的镜像（~5MB）
docker pull alpine:latest

# 运行容器，执行一条命令后退出
docker run alpine echo "Hello from Docker!"

# 在容器里启动交互式 shell（-it = interactive + tty）
# 进去之后试试 ls、cat /etc/os-release，然后 exit 退出
docker run -it alpine sh
```

### 练习 2：查看镜像和容器

```bash
# 列出本地镜像
docker images

# 列出正在运行的容器
docker ps

# 列出所有容器（包括已停止的）
docker ps -a
```

### 练习 3：容器生命周期

```bash
# 后台运行一个容器（-d = detach），命名为 mybox
docker run -d --name mybox alpine sleep 300

# 查看运行中的容器
docker ps

# 在运行中的容器里执行命令
docker exec mybox cat /etc/os-release

# 停止容器
docker stop mybox

# 删除容器
docker rm mybox

# 一次清理所有已停止的容器
docker container prune -f
```

### 练习 4：端口映射和环境变量

```bash
# 运行一个 nginx 服务器
# -p 8080:80 表示：宿主机的 8080 端口 -> 容器的 80 端口
# -d 后台运行
docker run -d --name webserver -p 8080:80 nginx:alpine

# 测试访问
curl http://localhost:8080

# 传环境变量给容器（-e）
docker run --rm alpine sh -c 'echo "My name is $MY_NAME"'
docker run --rm -e MY_NAME=CVEFactory alpine sh -c 'echo "My name is $MY_NAME"'

# 清理
docker stop webserver && docker rm webserver
```

### 练习 5：挂载目录（Volume）

```bash
# 创建一个测试文件
echo "data from host" > /tmp/test_docker.txt

# -v 宿主机路径:容器路径 把文件挂进容器
docker run --rm -v /tmp/test_docker.txt:/data/input.txt alpine cat /data/input.txt

# 双向同步：容器写的文件宿主机也能看到
docker run --rm -v /tmp/docker_share:/output alpine sh -c 'echo "written by container" > /output/result.txt'
cat /tmp/docker_share/result.txt
```

> **CVEFactory 关联**：CVEFactory 把漏洞代码和补丁通过 `-v` 挂载进容器，在容器内编译、运行、测试。

---

## 关键参数速查

| 参数 | 作用 | 例子 |
|------|------|------|
| `-d` | 后台运行 | `docker run -d nginx` |
| `-it` | 交互模式 | `docker run -it alpine sh` |
| `--name` | 给容器命名 | `--name myapp` |
| `-p` | 端口映射 | `-p 8080:80` |
| `-e` | 环境变量 | `-e API_KEY=xxx` |
| `-v` | 挂载目录 | `-v /host/path:/container/path` |
| `--rm` | 退出自动删除 | `docker run --rm alpine echo hi` |

---

## 自测题

完成以上练习后回答：
1. `docker run` vs `docker exec` 的区别是什么？
2. 容器停止后数据还在吗？什么时候会丢？
3. 如果 CVEFactory 要在容器里运行一个有漏洞的 Python 程序，需要用哪些参数？
