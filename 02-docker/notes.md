# Docker 学习笔记

## Linux 基础命令
| 命令 | 作用 |
|------|------|
| `echo "xxx"` | 输出文字到屏幕 |
| `>` | 重定向，输出写入文件（覆盖） |
| `>>` | 追加写入文件（不覆盖） |
| `cat file` | 显示文件内容 |
| `ls` | 列出目录里的文件 |
| `cd xxx` | 进入目录 |
| `mkdir -p` | 创建目录（-p 自动创建父目录） |
| `curl url` | 发 HTTP 请求 |
| `sh -c '...'` | 调用 shell 执行命令 |

## Docker 核心概念
- 镜像 (Image) = 只读模板（类似 .exe）
- 容器 (Container) = 镜像的运行实例（类似运行中的进程）
- Dockerfile = 构建镜像的配方（类似 Makefile）
- `name:tag` 格式指定镜像版本，如 `alpine:latest`

## 常用命令
| 命令 | 作用 |
|------|------|
| `docker pull` | 下载镜像（不存在时 run 会自动拉取） |
| `docker build -t 名字 .` | 按 Dockerfile 构建镜像，`.` 指定当前目录 |
| `docker run` | 创建并运行**新容器** |
| `docker exec` | 在**已运行的容器**里执行命令 |
| `docker ps` | 查看运行中的容器（-a 看所有） |
| `docker stop` | 停止容器 |
| `docker rm` | 删除容器 |
| `docker container prune -f` | 删除所有已停止的容器 |
| `docker images` | 查看本地镜像 |

## docker run 参数
| 参数 | 作用 |
|------|------|
| `-d` | 后台运行 |
| `-it` | 交互模式（进入容器终端） |
| `--rm` | 运行完自动删除容器 |
| `--name` | 给**容器**起名 |
| `-t`（build 时） | 给**镜像**起名 |
| `-p 8080:80` | 端口映射（宿主机:容器） |
| `-e KEY=VALUE` | 传环境变量 |
| `-v 宿主机路径:容器路径` | 挂载目录（双向同步） |

## Dockerfile 指令
```dockerfile
FROM python:3.11-slim    # 基础镜像（必须第一行）
WORKDIR /app             # 设置工作目录
COPY file .              # 复制文件到镜像
RUN pip install ...      # 构建时执行命令（每条 = 一层，会缓存）
CMD ["python", "app.py"] # 默认启动命令（可被 docker run 参数替换）
ENTRYPOINT ["python"]    # 固定启动命令（docker run 参数追加到后面）
```

- 先 COPY requirements.txt + RUN pip install，再 COPY 代码 → 利用缓存，改代码不用重装依赖
- CMD = 灵活，用户可完全替换；ENTRYPOINT = 固定程序，用户只能加参数
- CVEFactory 用 ENTRYPOINT，只需传 CVE-ID 即可

## Docker Compose
- `docker-compose.yml` 定义多个容器的清单
- `docker compose up --build` = 构建 + 启动所有服务
- `docker compose down` = 停止 + 删除所有服务
- 服务间通过**服务名**互相访问（Docker 内部 DNS）

## Docker-in-Docker (DinD)
- 挂载 `-v /var/run/docker.sock:/var/run/docker.sock` 让容器能控制 Docker
- 安全风险：等于给容器 root 权限
- CVEFactory 用 DinD 原因：漏洞代码危险，容器隔离保护宿主机

## CVEFactory 架构映射
```
docker-compose.yml           → 定义整个系统
├── orchestrator (主容器)     → 用 subprocess 控制 Docker
│   ├── -v docker.sock       → DinD 能力
│   └── asyncio.gather()     → 并发调度多个 CVE
└── 子容器 (按需创建)         → 每个 CVE 独立环境
    ├── -v 挂载漏洞代码
    ├── -e 传入配置
    └── --rm 用完销毁
```
