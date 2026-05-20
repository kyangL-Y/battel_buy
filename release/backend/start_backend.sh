#!/usr/bin/env bash

set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${BASE_DIR}"

load_env_file() {
  local env_file="${BASE_DIR}/.env.mysql"
  if [[ -f "${env_file}" ]]; then
    set -a
    # shellcheck disable=SC1090
    . <(tr -d '\r' < "${env_file}")
    set +a
  fi
}

load_env_file

ensure_runtime_env() {
  # 宝塔进程管理常见场景下 HOME 可能仍指向 /root，导致 pip 缓存目录无权限。
  if [[ -z "${HOME:-}" || ! -w "${HOME}" ]]; then
    export HOME="${BASE_DIR}"
  fi

  export PIP_CACHE_DIR="${BASE_DIR}/.cache/pip"
  export PIP_DISABLE_PIP_VERSION_CHECK=1
  export PIP_DEFAULT_TIMEOUT="${PIP_DEFAULT_TIMEOUT:-180}"
  export PIP_RETRIES="${PIP_RETRIES:-6}"
  export PIP_PROGRESS_BAR=off
  mkdir -p "${PIP_CACHE_DIR}"
}

has_required_runtime_deps() {
  "$1" -c "import uvicorn; import jwt; import sqlalchemy; import pymysql; import pandas; import requests" >/dev/null 2>&1
}

pip_install_requirements() {
  local py_bin="$1"
  local requirements_file="$2"
  local -a pip_args=(
    install
    --upgrade
    --default-timeout "${PIP_DEFAULT_TIMEOUT}"
    --retries "${PIP_RETRIES}"
    -r "${requirements_file}"
  )

  if [[ -n "${PIP_INDEX_URL:-}" ]]; then
    pip_args+=(--index-url "${PIP_INDEX_URL}")
  fi
  if [[ -n "${PIP_EXTRA_INDEX_URL:-}" ]]; then
    pip_args+=(--extra-index-url "${PIP_EXTRA_INDEX_URL}")
  fi
  if [[ -n "${PIP_TRUSTED_HOST:-}" ]]; then
    pip_args+=(--trusted-host "${PIP_TRUSTED_HOST}")
  fi

  "${py_bin}" -m pip "${pip_args[@]}" >&2
}

pick_python() {
  if [[ -x "${BASE_DIR}/venv/bin/python" ]] && has_required_runtime_deps "${BASE_DIR}/venv/bin/python"; then
    echo "${BASE_DIR}/venv/bin/python"
    return 0
  fi
  if [[ -x "${BASE_DIR}/.venv/bin/python" ]] && has_required_runtime_deps "${BASE_DIR}/.venv/bin/python"; then
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
  local venv_py="${BASE_DIR}/.venv/bin/python"
  local tmp_venv="${BASE_DIR}/.venv.__tmp.$$"
  local venv_err
  local runtime_requirements="${BASE_DIR}/requirements.runtime.txt"
  if [[ ! -f "${runtime_requirements}" ]]; then
    runtime_requirements="${BASE_DIR}/requirements.txt"
  fi

  if has_required_runtime_deps "${py_bin}"; then
    echo "${py_bin}"
    return 0
  fi

  echo "当前 Python 环境缺少后端运行依赖，开始检查或重建项目虚拟环境..." >&2

  if [[ -x "${venv_py}" ]]; then
    if has_required_runtime_deps "${venv_py}"; then
      echo "${venv_py}"
      return 0
    fi

    if ! "${venv_py}" -m pip --version >/dev/null 2>&1; then
      echo "检测到现有 .venv 已损坏：其中的 pip 不可用，将尝试重建虚拟环境。" >&2
    fi
  fi

  rm -rf "${tmp_venv}"
  if command -v uv >/dev/null 2>&1; then
    local uv_python="${py_bin}"
    if ! "${uv_python}" -c "import ensurepip" >/dev/null 2>&1; then
      uv_python="3.11"
    fi
    if UV_LINK_MODE=copy uv venv --seed --python "${uv_python}" "${tmp_venv}" >&2 && UV_LINK_MODE=copy uv pip install --python "${tmp_venv}/bin/python" --default-timeout "${PIP_DEFAULT_TIMEOUT}" --retries "${PIP_RETRIES}" -r "${runtime_requirements}" >&2; then
      if ! has_required_runtime_deps "${tmp_venv}/bin/python"; then
        echo "依赖安装完成，但仍未找到完整后端运行依赖，请检查 uv 安装日志。" >&2
        rm -rf "${tmp_venv}"
        exit 1
      fi
      rm -rf "${BASE_DIR}/.venv"
      mv "${tmp_venv}" "${BASE_DIR}/.venv"
      echo "${BASE_DIR}/.venv/bin/python"
      return 0
    fi
    echo "uv 创建或安装依赖失败，将回退到 python -m venv。" >&2
    rm -rf "${tmp_venv}"
  fi

  if ! venv_err="$(${py_bin} -m venv "${tmp_venv}" 2>&1)"; then
    if [[ "${venv_err}" == *"ensurepip"* || "${venv_err}" == *"python3-venv"* ]]; then
      echo "当前 Python 无法创建虚拟环境：缺少 ensurepip/python3-venv。请安装 python3-venv（以及需要时 python3-pip），或手动准备带有完整后端运行依赖的 ${BASE_DIR}/.venv 后重试。" >&2
    elif [[ "${venv_err}" == *"No module named venv"* ]]; then
      echo "当前 Python 不包含 venv 模块，无法自动创建后端虚拟环境。" >&2
    else
      echo "创建虚拟环境失败：${venv_err}" >&2
    fi
    rm -rf "${tmp_venv}"
    exit 1
  fi

  if ! "${tmp_venv}/bin/python" -m pip --version >/dev/null 2>&1; then
    echo "虚拟环境已创建，但其中仍然没有 pip，说明当前 Python 的 venv/ensurepip 组件不完整。" >&2
    rm -rf "${tmp_venv}"
    exit 1
  fi

  "${tmp_venv}/bin/python" -m pip install --upgrade --default-timeout "${PIP_DEFAULT_TIMEOUT}" --retries "${PIP_RETRIES}" pip >&2
  pip_install_requirements "${tmp_venv}/bin/python" "${runtime_requirements}"

  if ! has_required_runtime_deps "${tmp_venv}/bin/python"; then
    echo "依赖安装完成，但仍未找到完整后端运行依赖，请检查 pip 安装日志。" >&2
    rm -rf "${tmp_venv}"
    exit 1
  fi

  rm -rf "${BASE_DIR}/.venv"
  mv "${tmp_venv}" "${BASE_DIR}/.venv"
  echo "${BASE_DIR}/.venv/bin/python"
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
