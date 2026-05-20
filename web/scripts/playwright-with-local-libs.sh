#!/usr/bin/env bash
set -euo pipefail

# Playwright 需要本地 Chromium 依赖库时，优先挂载 web/.tmp/pw-libs 里的离线解压目录。
# 目录不存在时不阻断执行，只打印提示，方便直接使用系统依赖或已安装环境。
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LIB_DIR="$ROOT/web/.tmp/pw-libs/root/usr/lib/x86_64-linux-gnu"
if [[ -d "$LIB_DIR" ]]; then
  export LD_LIBRARY_PATH="$LIB_DIR${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
else
  cat >&2 <<MSG
未找到本地 Playwright 依赖库目录：$LIB_DIR
如果 Chromium 报缺少 libnspr4/libnss3，可先执行：
  mkdir -p web/.tmp/pw-libs && cd web/.tmp/pw-libs
  apt-get download libnspr4 libnss3
  for d in *.deb; do dpkg-deb -x "$d" root; done
或使用系统方式安装：
  sudo npx playwright install-deps chromium
MSG
fi

exec npx playwright "$@"
