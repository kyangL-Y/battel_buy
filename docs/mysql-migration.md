# MySQL 迁移说明

项目现已支持通过环境变量切换到 MySQL。默认仍兼容 SQLite，本地开发无需修改。

## 1. 环境变量

参考根目录 `.env.mysql.example`。如果你要在 Linux / Bash 环境下直接 `source` 环境文件，先复制成真实文件 `.env.mysql`，不要直接加载一个不存在的 `.env.mysql`：

```bash
cp .env.mysql.example .env.mysql
set -a
. ./.env.mysql
set +a
```

文件内容示例：

```bash
export BATTEL_DB_BACKEND=mysql
export BATTEL_DB_HOST=your-mysql-host
export BATTEL_DB_PORT=3306
export BATTEL_DB_USER=your-user
export BATTEL_DB_PASSWORD=your-password
export BATTEL_DB_NAME=battel
export BATTEL_DB_CHARSET=utf8mb4
```

生产环境请通过宝塔 / Supervisor / systemd 注入变量，不要把密码写入代码仓库；`.env.mysql.example` 仅作模板展示，真实 `.env.mysql` 默认不提交。

## 2. 安装依赖

```bash
pip install -r requirements.txt
```

新增数据库依赖：

- `SQLAlchemy`
- `PyMySQL`

## 3. 初始化 MySQL 表

```bash
python main.py init-db
```

当 `BATTEL_DB_BACKEND=mysql` 时，这条命令会在当前 MySQL 库中创建所需表和索引。

## 4. 迁移现有 SQLite 数据

```bash
python tools/migrate_sqlite_to_mysql.py --source-sqlite data/price_tracker.db
```

默认行为：

- 先读取 `data/price_tracker.db`
- 自动清空目标 MySQL 中的四张业务表
- 按 `products -> price_records -> failed_crawl_records -> local_compare_records` 导入

如果想保留目标库已有数据，追加导入：

```bash
python tools/migrate_sqlite_to_mysql.py --source-sqlite data/price_tracker.db --keep-target-data
```

## 5. 启动后端

```bash
python -m uvicorn main_api:app --host 127.0.0.1 --port 8000
```

如果你使用 Bash 手工启动，建议使用：

```bash
set -a
. ./.env.mysql
set +a
python -m uvicorn main_api:app --host 127.0.0.1 --port 8000
```

只要环境变量仍指向 MySQL，应用启动后就会直接读写 MySQL。

## 6. 验证

建议至少验证：

1. `python main.py init-db` 无报错
2. `python tools/migrate_sqlite_to_mysql.py ...` 能完成导入
3. `curl http://127.0.0.1:8000/api/health` 返回 `{"status":"ok"}`
4. 前端页面能正常读取市场汇总、单品趋势和菜单采购接口
