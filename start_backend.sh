#!/usr/bin/env bash

set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${BASE_DIR}"

if [[ -f "${BASE_DIR}/.env.mysql" ]]; then
  set -a
  # shellcheck disable=SC1091
  . "${BASE_DIR}/.env.mysql"
  set +a
fi

ensure_runtime_env() {
  # 宝塔进程管理常见场景下 HOME 可能仍指向 /root，导致 pip 缓存目录无权限。
  if [[ -z "${HOME:-}" || ! -w "${HOME}" ]]; then
    export HOME="${BASE_DIR}"
  fi

  export PIP_CACHE_DIR="${BASE_DIR}/.cache/pip"
  export PIP_DISABLE_PIP_VERSION_CHECK=1
  mkdir -p "${PIP_CACHE_DIR}"
}

pick_python() {
  if [[ -x "${BASE_DIR}/venv/bin/python" ]]; then
    echo "${BASE_DIR}/venv/bin/python"
    return 0
  fi
  if [[ -x "${BASE_DIR}/.venv/bin/python" ]]; then
    echo "${BASE_DIR}/.venv/bin/python"
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    command -v python
    return 0
  fi
  return 1
}

ensure_requirements() {
  local py_bin="$1"

  if "${py_bin}" -c "import uvicorn" >/dev/null 2>&1; then
    echo "${py_bin}"
    return 0
  fi

  echo "当前 Python 环境缺少 uvicorn，开始准备项目虚拟环境..." >&2

  if [[ ! -x "${BASE_DIR}/.venv/bin/python" ]]; then
    "${py_bin}" -m venv "${BASE_DIR}/.venv"
  fi

  py_bin="${BASE_DIR}/.venv/bin/python"
  "${py_bin}" -m ensurepip --upgrade >/dev/null 2>&1 || true
  "${py_bin}" -m pip install --upgrade pip >&2
  "${py_bin}" -m pip install -r "${BASE_DIR}/requirements.txt" >&2

  if ! "${py_bin}" -c "import uvicorn" >/dev/null 2>&1; then
    echo "依赖安装完成，但仍未找到 uvicorn，请检查 pip 安装日志。" >&2
    exit 1
  fi

  echo "${py_bin}"
}

if ! PYTHON_BIN="$(pick_python)"; then
  echo "未找到可用的 Python 解释器。请先安装 python3。" >&2
  exit 1
fi

ensure_runtime_env
PYTHON_BIN="$(ensure_requirements "${PYTHON_BIN}")"

HOST="${BATTEL_HOST:-127.0.0.1}"
PORT="${BATTEL_PORT:-8000}"

exec "${PYTHON_BIN}" -m uvicorn main_api:app --host "${HOST}" --port "${PORT}"
