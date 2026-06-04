# 部署说明

本文档提供当前项目的推荐部署方式：前端使用 `Vite` 构建静态文件，后端使用 `FastAPI + Uvicorn` 提供 API，最终通过 `Nginx` 统一对外暴露。

## 1. 部署结构

推荐拓扑：

```text
Browser
  -> Nginx :80 / :443
     -> /      -> web/dist
     -> /api/* -> 127.0.0.1:8000
```

这样前端在开发和生产都可以使用 `/api` 作为统一接口前缀。

## 2. 前端部署

### 2.1 环境变量

前端支持以下环境变量：

| 变量 | 默认值 | 说明 |
|------|------|------|
| `VITE_API_BASE_URL` | `/api` | 浏览器实际请求的 API 前缀 |
| `VITE_DEV_API_TARGET` | `http://127.0.0.1:8000` | `npm run dev` 时 Vite 代理转发目标 |

示例见 [web/.env.example](/e:/battel/web/.env.example)。

### 2.2 构建

在项目根目录执行：

```bash
cd web
npm install
npm run build
```

构建完成后，静态文件位于 `web/dist/`。

### 2.3 本地发布包同步

`release/dist/` 是本地发布产物目录，不再作为 Git 跟踪资产。需要打包或上传静态资源时，先构建 `web/dist/`，再把当前构建结果同步到 `release/dist/`。

Windows PowerShell：

```powershell
Remove-Item -Recurse -Force release\dist
Copy-Item -Recurse web\dist release\dist
```

Linux / Bash：

```bash
rm -rf release/dist
cp -a web/dist release/dist
```

## 3. 后端部署

当前运行时只支持 MySQL 云库启动；SQLite 仅保留给测试、数据迁移和显式 `Database(db_path=...)` 的离线工具，不再作为后端服务的回退方案。若你习惯在 Linux / Bash 中加载环境文件，先从 `.env.mysql.example` 复制出真实 `.env.mysql`，再执行 `. ./.env.mysql`，不要直接 `source` 一个不存在的 `.env.mysql`。

### 3.1 安装依赖

在项目根目录执行：

```bash
python -m pip install -r requirements.txt
```

### 3.2 启动命令

开发环境可使用：

```bash
uvicorn main_api:app --reload --port 8000
```

生产环境不要使用 `--reload`：

```bash
uvicorn main_api:app --host 127.0.0.1 --port 8000
```

如果服务器上的 Python 路径不固定，或者你不想把 `venv/bin/python` 写死到部署脚本里，优先使用项目自带的启动脚本：

```bash
chmod +x start_backend.sh
./start_backend.sh
```

这个脚本会按以下顺序自动寻找解释器：

1. `./venv/bin/python`
2. `./.venv/bin/python`
3. 系统 `python3`
4. 系统 `python`

如果当前解释器里还没有安装 `uvicorn`，脚本会自动创建 `./.venv/` 并安装 `requirements.txt`，然后再启动服务。

这样即使服务器上不存在 `/lhcos-data/battel/backend/venv/bin/python` 这种旧路径，或者系统 `python3` 里还没装 `uvicorn`，也不会因为绝对路径失效或缺依赖直接启动失败。

## 4. Nginx 配置

以下示例假设：

- 域名为 `your-domain.com`
- 项目根目录为 `/opt/battel`
- 前端构建产物位于 `/opt/battel/web/dist`
- 后端监听 `127.0.0.1:8000`

```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /opt/battel/web/dist;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

如果启用 HTTPS，可在此基础上追加证书配置，或通过 `certbot` / `acme.sh` 维护证书。

## 5. systemd 托管后端

Linux 服务器推荐使用 `systemd` 托管 FastAPI 进程。示例：

```ini
[Unit]
Description=battel api
After=network.target

[Service]
WorkingDirectory=/opt/battel
ExecStart=/opt/battel/start_backend.sh
Restart=always
RestartSec=3
User=www-data

[Install]
WantedBy=multi-user.target
```

保存为 `/etc/systemd/system/battel-api.service` 后执行：

```bash
sudo systemctl daemon-reload
sudo systemctl enable battel-api
sudo systemctl start battel-api
sudo systemctl status battel-api
```

如果你之前的 `ExecStart` 写成了类似 `/lhcos-data/battel/backend/venv/bin/python ...`，请改成上面的 `start_backend.sh`，否则只要虚拟环境目录变了就会继续报 `No such file or directory`。

## 5.1 宝塔面板部署后端

如果你是通过宝塔面板的 Python 项目管理器、Supervisor 管理器或计划任务启动后端，不要再把启动命令写死成：

```bash
/lhcos-data/battel/backend/venv/bin/python -m uvicorn main_api:app --host 127.0.0.1 --port 8000
```

这类命令只要 `venv` 目录不存在、虚拟环境名称改成 `.venv`，或者你重新解压部署目录，就会继续报：

```text
/bin/bash: line 1: /lhcos-data/battel/backend/venv/bin/python: No such file or directory
```

宝塔里优先改成下面两种方式之一：

方式一：直接把启动命令改成脚本路径

```bash
/bin/bash /lhcos-data/battel/backend/start_backend.sh
```

方式二：如果你想先切目录再启动

```bash
/bin/bash -lc 'cd /lhcos-data/battel/backend && chmod +x start_backend.sh && ./start_backend.sh'
```

脚本会自动优先查找：

1. `/lhcos-data/battel/backend/venv/bin/python`
2. `/lhcos-data/battel/backend/.venv/bin/python`
3. 系统 `python3`
4. 系统 `python`

如果前两者不存在，且系统 Python 里还没装 `uvicorn`，脚本会自动创建 `/lhcos-data/battel/backend/.venv` 并安装依赖。

### 宝塔面板建议检查项

1. 重新上传最新的 `backend.zip`，确认解压后目录中存在 `start_backend.sh`
2. 如果原来配过启动项，先把旧启动命令里的 `/venv/bin/python` 全部删掉
3. 启动目录保持为 `/lhcos-data/battel/backend`
4. 启动命令改成上面的 `start_backend.sh` 方式
5. 第一次启动时允许脚本自动创建 `.venv` 并安装依赖，时间会比平时长
6. 若宝塔配置了旧项目守护进程，修改后需要重启对应服务

## 6. 发布步骤

推荐发布顺序：

1. 在服务器拉取最新代码。
2. 安装或更新 Python 依赖。
3. 在 `web/` 下执行 `npm install && npm run build`。
4. 重启 `battel-api.service`。
5. 重载 Nginx：

```bash
sudo systemctl reload nginx
```

## 7. 验证清单

发布后至少检查：

1. `http://127.0.0.1:8000/api/health` 返回 `{"status":"ok"}`。
2. 站点首页可正常打开。
3. 浏览器访问前端页面时，`/api/*` 请求返回正常且没有跨域错误。
4. Nginx 日志与后端日志中没有持续性 4xx/5xx 异常。
