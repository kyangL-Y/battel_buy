from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from crawler.public_source_crawlers import PublicSourceCrawler


DEFAULT_SALE_CLASS_TREE = Path("tmp/meicai_sale_class_tree.json")
DEFAULT_LOCAL_OUTPUT = Path(".local-secrets/meicai_runtime_class_products.jsonl")
REMOTE_OUTPUT = "/sdcard/Download/meicai_runtime_class_products.jsonl"


def load_sale_class_filters(tree_path: Path, *, limit: int) -> list[dict[str, str]]:
    filters = PublicSourceCrawler.load_meicai_category_filters_from_sale_class_tree(tree_path)
    selected_filters = filters[:limit] if limit > 0 else filters
    return [
        {
            "category": str(item.get("category") or "").strip(),
            "sale_c1_id": str(item.get("sale_c1_id") or item.get("class1_id") or "").strip(),
            "sale_c2_id": str(item.get("sale_c2_id") or item.get("class2_id") or "").strip(),
        }
        for item in selected_filters
        if str(item.get("class1_id") or "").strip()
    ]


def build_runtime_script(category_filters: list[dict[str, str]], *, max_pages: int, page_size: int) -> str:
    category_json = json.dumps(category_filters, ensure_ascii=False)
    return f"""
Java.perform(function () {{
  const Gson = Java.use("com.google.gson.Gson");
  const File = Java.use("java.io.File");
  const FileOutputStream = Java.use("java.io.FileOutputStream");
  const StringCls = Java.use("java.lang.String");
  const dumpPath = "{REMOTE_OUTPUT}";
  const categoryQueue = {category_json};
  const maxPages = {int(max_pages)};
  const pageSize = {int(page_size)};
  const seen = {{}};
  let requestIndex = 0;
  let decodedCount = 0;

  function writeLine(payload) {{
    try {{
      const text = StringCls.$new(JSON.stringify(payload) + "\\n");
      const bytes = text.getBytes("UTF-8");
      const stream = FileOutputStream.$new(File.$new(dumpPath), true);
      stream.write(bytes);
      stream.close();
    }} catch (error) {{
      send({{ type: "meicai_runtime_file_error", payload: String(error) }});
    }}
  }}

  function emit(payload) {{
    send({{ type: "meicai_runtime_class_products", payload: payload }});
    writeLine(payload);
  }}

  function toJson(javaObject) {{
    try {{ return String(Gson.$new().toJson(javaObject)); }} catch (error) {{ return ""; }}
  }}

  function parseJson(text) {{
    try {{ return JSON.parse(text); }} catch (error) {{ return null; }}
  }}

  function arrayAtPath(value, path) {{
    let current = value;
    for (let index = 0; index < path.length; index += 1) {{
      if (!current || typeof current !== "object") return null;
      current = current[path[index]];
    }}
    return Array.isArray(current) ? current : null;
  }}

  function findRows(value) {{
    const paths = [["rows"], ["list"], ["goodsRows"], ["data", "rows"], ["data", "list"], ["data", "refeactorSkus"], ["data", "skus"], ["data", "skuList"], ["pageData", "rows"], ["pageData", "list"], ["skuList"], ["refeactorSkus"], ["skus"]];
    for (let index = 0; index < paths.length; index += 1) {{
      const rows = arrayAtPath(value, paths[index]);
      if (rows) return {{ path: paths[index].join("."), rows: rows }};
    }}
    return {{ path: "", rows: [] }};
  }}

  function goodsIdentity(row) {{
    if (!row || typeof row !== "object") return "";
    const skuBase = row.skuBase && typeof row.skuBase === "object" ? row.skuBase : {{}};
    return String(skuBase.skuId || skuBase.spuId || row.skuId || row.spuId || "");
  }}

  function summarizeRows(rows) {{
    let uniqueInPage = 0;
    rows.forEach(function (row) {{
      const id = goodsIdentity(row);
      if (id && !seen[id]) {{
        seen[id] = true;
        uniqueInPage += 1;
      }}
    }});
    return {{ row_count: rows.length, unique_in_page: uniqueInPage, total_unique: Object.keys(seen).length }};
  }}

  try {{
    const CategoryViewModel = Java.use("com.meicai.mall.category.CategoryViewModel");
    const parseCategoryPage = CategoryViewModel.c.overload("com.meicai.mall.net.result.BaseResult", "java.lang.String", "java.lang.String");
    parseCategoryPage.implementation = function (baseResult, class1Id, class2Id) {{
      const parsedResult = parseCategoryPage.call(this, baseResult, class1Id, class2Id);
      decodedCount += 1;
      const text = toJson(parsedResult);
      const parsedJson = parseJson(text);
      const rowsInfo = findRows(parsedJson);
      const summary = summarizeRows(rowsInfo.rows);
      writeLine({{ event: "decoded_payload", class1_id: String(class1Id || ""), class2_id: String(class2Id || ""), json: parsedJson }});
      emit({{ event: "decoded", decoded_count: decodedCount, class1_id: String(class1Id || ""), class2_id: String(class2Id || ""), row_path: rowsInfo.path, row_count: summary.row_count, unique_in_page: summary.unique_in_page, total_unique: summary.total_unique }});
      return parsedResult;
    }};

    function triggerNext() {{
      if (requestIndex >= categoryQueue.length * maxPages) {{
        emit({{ event: "trigger_complete", requested: requestIndex, decoded_count: decodedCount, total_unique: Object.keys(seen).length }});
        return;
      }}
      const categoryIndex = Math.floor(requestIndex / maxPages);
      const page = (requestIndex % maxPages) + 1;
      const item = categoryQueue[categoryIndex];
      requestIndex += 1;
      let called = false;
      Java.choose("com.meicai.mall.category.CategoryViewModel", {{
        onMatch: function (instance) {{
          if (called) return;
          called = true;
          emit({{ event: "trigger", index: requestIndex, category: item.category, class1_id: item.sale_c1_id, class2_id: item.sale_c2_id, page: page, size: pageSize }});
          Java.scheduleOnMainThread(function () {{
            try {{
              instance.n(item.sale_c1_id, item.sale_c2_id, page, pageSize);
              emit({{ event: "trigger_dispatched", index: requestIndex, class1_id: item.sale_c1_id, class2_id: item.sale_c2_id, page: page }});
            }} catch (error) {{
              emit({{ event: "trigger_error", index: requestIndex, class1_id: item.sale_c1_id, class2_id: item.sale_c2_id, page: page, error: String(error) }});
            }}
          }});
        }},
        onComplete: function () {{
          if (!called) emit({{ event: "trigger_missing_vm", index: requestIndex, class1_id: item.sale_c1_id, class2_id: item.sale_c2_id }});
        }}
      }});
      setTimeout(triggerNext, 1500);
    }}

    emit({{ event: "hooked", dump_path: dumpPath, category_count: categoryQueue.length, max_pages: maxPages, page_size: pageSize }});
    setTimeout(triggerNext, 1000);
  }} catch (error) {{
    emit({{ event: "hook_error", error: String(error) }});
  }}
}});
"""


def run_command(command: list[str], *, timeout: int, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=check, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


def collect_runtime_class_products(
    *,
    sale_class_tree: Path,
    local_output: Path,
    limit_categories: int,
    max_pages: int,
    page_size: int,
    wait_seconds: int,
) -> dict[str, Any]:
    category_filters = load_sale_class_filters(sale_class_tree, limit=limit_categories)
    if not category_filters:
        raise RuntimeError("美菜 saleClass 树没有可用分类")

    script_path = REPO_ROOT / "tmp" / "meicai_runtime_class_products.js"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(build_runtime_script(category_filters, max_pages=max_pages, page_size=page_size), encoding="utf-8")

    run_command(["adb", "shell", "rm", "-f", REMOTE_OUTPUT], timeout=10, check=False)
    pid = run_command(["adb", "shell", "pidof", "com.meicai.mall"], timeout=10).stdout.strip()
    if not pid:
        raise RuntimeError("未找到 com.meicai.mall 进程，请先打开并登录美菜 App")

    frida_process = subprocess.Popen(
        ["frida", "-U", "-p", pid, "-l", str(script_path), "--runtime=v8", "--eternalize", "-q"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        time.sleep(wait_seconds)
    finally:
        frida_process.terminate()
        try:
            frida_stdout, frida_stderr = frida_process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            frida_process.kill()
            frida_stdout, frida_stderr = frida_process.communicate()

    local_output.parent.mkdir(parents=True, exist_ok=True)
    run_command(["adb", "pull", REMOTE_OUTPUT, str(local_output)], timeout=20)
    summary = summarize_runtime_payloads(local_output)
    summary["frida_stdout_tail"] = (frida_stdout or "")[-2000:]
    summary["frida_stderr_tail"] = (frida_stderr or "")[-2000:]
    return summary


def summarize_runtime_payloads(payload_path: Path) -> dict[str, Any]:
    decoded_pages = 0
    trigger_count = 0
    trigger_dispatched_count = 0
    trigger_errors: list[str] = []
    unique_goods: set[str] = set()
    category_keys: set[tuple[str, str]] = set()
    row_count = 0
    last_summary: dict[str, Any] = {}
    with payload_path.open(encoding="utf-8-sig") as payload_file:
        for line in payload_file:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            event_name = str(payload.get("event") or "")
            if event_name == "trigger":
                trigger_count += 1
            if event_name == "trigger_dispatched":
                trigger_dispatched_count += 1
            if event_name == "trigger_error":
                trigger_errors.append(str(payload.get("error") or ""))
            if event_name == "decoded":
                decoded_pages += 1
                row_count += int(payload.get("row_count") or 0)
                last_summary = payload
                category_keys.add((str(payload.get("class1_id") or ""), str(payload.get("class2_id") or "")))
            if event_name != "decoded_payload":
                continue
            decoded_json = payload.get("json")
            for goods_row in PublicSourceCrawler.extract_meicai_goods_rows({"data": decoded_json}):
                goods_identity = PublicSourceCrawler._meicai_goods_identity(goods_row)
                if goods_identity:
                    unique_goods.add(goods_identity)
    return {
        "payload_path": str(payload_path),
        "trigger_count": trigger_count,
        "trigger_dispatched_count": trigger_dispatched_count,
        "trigger_errors": trigger_errors,
        "decoded_pages": decoded_pages,
        "decoded_category_count": len(category_keys),
        "row_count": row_count,
        "unique_goods_count": len(unique_goods),
        "last_summary": last_summary,
    }


def build_runtime_price_rows(payload_path: Path) -> list[dict[str, Any]]:
    crawler = PublicSourceCrawler()
    rows: list[dict[str, Any]] = []
    with payload_path.open(encoding="utf-8-sig") as payload_file:
        for line in payload_file:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if str(payload.get("event") or "") != "decoded_payload":
                continue
            decoded_json = payload.get("json")
            goods_rows = PublicSourceCrawler.extract_meicai_goods_rows({"data": decoded_json})
            rows.extend(
                crawler.build_meicai_app_gateway_rows(
                    goods_rows,
                    {"category": f"{payload.get('class1_id') or ''}/{payload.get('class2_id') or ''}"},
                    page=0,
                    endpoint_name="class_products_runtime",
                    city_id="17",
                    area_id="4402",
                )
            )
    return PublicSourceCrawler._deduplicate_meicai_rows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect Meicai class product payloads from the logged-in App runtime.")
    parser.add_argument("--sale-class-tree", default=str(DEFAULT_SALE_CLASS_TREE))
    parser.add_argument("--output", default=str(DEFAULT_LOCAL_OUTPUT))
    parser.add_argument("--limit-categories", type=int, default=3)
    parser.add_argument("--max-pages", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--wait-seconds", type=int, default=12)
    parser.add_argument("--summarize-only", action="store_true")
    parser.add_argument("--export-rows", default="")
    args = parser.parse_args()

    if args.summarize_only:
        summary = summarize_runtime_payloads(Path(args.output))
    else:
        summary = collect_runtime_class_products(
            sale_class_tree=Path(args.sale_class_tree),
            local_output=Path(args.output),
            limit_categories=max(0, args.limit_categories),
            max_pages=max(1, args.max_pages),
            page_size=max(1, args.page_size),
            wait_seconds=max(3, args.wait_seconds),
        )
    if args.export_rows:
        rows = build_runtime_price_rows(Path(args.output))
        export_path = Path(args.export_rows)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        export_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        summary["export_rows"] = str(export_path)
        summary["export_row_count"] = len(rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
