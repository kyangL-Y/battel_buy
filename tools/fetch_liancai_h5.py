from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from crawler.liancai_h5 import LiancaiH5Client


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="抓取莲菜网 H5 分类商品")
    parser.add_argument("--phone", default=os.environ.get("LIANCAI_PHONE", ""), help="登录手机号")
    parser.add_argument("--password", default=os.environ.get("LIANCAI_PASSWORD", ""), help="登录密码")
    parser.add_argument("--list-categories", action="store_true", help="仅输出分类列表")
    parser.add_argument("--category-id", help="指定分类 fid，例如 6=蔬菜类")
    parser.add_argument("--page-from", type=int, default=1, help="起始页码")
    parser.add_argument("--page-to", type=int, default=1, help="结束页码")
    parser.add_argument("--output", help="输出 JSON 文件路径")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.phone or not args.password:
        parser.error("请通过 --phone/--password 或环境变量 LIANCAI_PHONE/LIANCAI_PASSWORD 提供登录账号")

    client = LiancaiH5Client(phone=args.phone, password=args.password)
    login_result = client.login()
    if int(login_result.get("code") or 0) != 200:
        print(json.dumps({"login": login_result}, ensure_ascii=False, indent=2))
        return 1

    categories = client.fetch_categories()
    if args.list_categories:
        top_categories, subcategories = client.fetch_category_tree()
        payload = {
            "login": login_result,
            "categories": [category.__dict__ for category in top_categories],
            "subcategories": [category.__dict__ for category in subcategories],
        }
        _emit(payload, args.output)
        return 0

    if not args.category_id:
        parser.error("抓商品时必须提供 --category-id，或改用 --list-categories 先列出分类")

    pages = range(max(1, args.page_from), max(args.page_from, args.page_to) + 1)
    items: list[dict] = []
    for page in pages:
        page_items = client.fetch_category_page(args.category_id, page=page)
        for item in page_items:
            item["category_page"] = page
            item["category_id"] = item.get("category_id") or args.category_id
        items.extend(page_items)

    payload = {
        "login": login_result,
        "category_id": args.category_id,
        "pages": {"from": args.page_from, "to": args.page_to},
        "count": len(items),
        "items": items,
    }
    _emit(payload, args.output)
    return 0


def _emit(payload: dict, output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if output:
        Path(output).write_text(text, encoding="utf-8")
        print(output)
        return
    print(text)


if __name__ == "__main__":
    raise SystemExit(main())
