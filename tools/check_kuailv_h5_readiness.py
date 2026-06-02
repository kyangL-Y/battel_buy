from __future__ import annotations

import argparse
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

import requests


KUAILV_H5_BASE_URL = "https://klmall.meituan.com/wxmall"
KUAILV_REGISTER_OPEN_URL = f"{KUAILV_H5_BASE_URL}/api/register/check/open"
KUAILV_CATEGORY_FIRST_URL = f"{KUAILV_H5_BASE_URL}/api/goods/category/first/list"
KUAILV_CATEGORY_SECOND_URL = f"{KUAILV_H5_BASE_URL}/api/goods/category/second/list"
KUAILV_GOODS_LIST_URL = f"{KUAILV_H5_BASE_URL}/api/goods/list"
KUAILV_DEFAULT_CITY_ID = "320100"
KUAILV_DEFAULT_PAGE_SIZE = 20
KUAILV_H5_UA_WEB = 44500


def load_env_file_without_override(path: Path) -> list[str]:
    loaded_names: list[str] = []
    if not path.exists():
        return loaded_names
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        clean_name = name.strip()
        if not clean_name or clean_name in os.environ:
            continue
        os.environ[clean_name] = value.strip().strip("'").strip('"')
        loaded_names.append(clean_name)
    return loaded_names


def parse_json_env(name: str, *, required: bool) -> dict[str, Any]:
    raw_value = os.environ.get(name)
    if not raw_value:
        if required:
            raise RuntimeError(f"missing {name}")
        return {}
    try:
        parsed_value = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{name} is not valid JSON") from exc
    if not isinstance(parsed_value, dict):
        raise RuntimeError(f"{name} must be a JSON object")
    return parsed_value


def summarize_json_object(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "present": bool(value),
        "top_level_keys": sorted(str(key) for key in value.keys()),
    }


def build_session(headers: dict[str, Any], cookies: dict[str, Any]) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Safari/604.1"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://klmall.meituan.com/m/category",
            "Origin": "https://klmall.meituan.com",
        }
    )
    session.headers.update({str(key): str(value) for key, value in headers.items() if value is not None})
    for name, value in cookies.items():
        session.cookies.set(str(name), str(value), domain=".meituan.com")
    return session


def build_common_params(city_id: str, address_context: dict[str, Any]) -> dict[str, Any]:
    selected_poi_address_id = str(
        address_context.get("selectedPoiAddressId")
        or address_context.get("poiAddressId")
        or address_context.get("selected_poi_address_id")
        or ""
    ).strip()
    selected_sales_grid_id = str(
        address_context.get("selectedSalesGridId") or address_context.get("salesGridId") or ""
    ).strip()
    request_uuid = str(address_context.get("uuid") or uuid.uuid4().hex).strip()

    params: dict[str, Any] = {
        "gtCityId": city_id,
        "uaWeb": KUAILV_H5_UA_WEB,
        "uaEnv": str(address_context.get("uaEnv") or "other"),
        "loginAcctType": str(address_context.get("loginAcctType") or "99"),
        "uuid": request_uuid,
        "riskLevel": 71,
        "optimusCode": 10,
        "_": int(time.time() * 1000),
    }
    if selected_poi_address_id:
        params["selectedPoiAddressId"] = selected_poi_address_id
    if selected_sales_grid_id:
        params["selectedSalesGridId"] = selected_sales_grid_id
    return params


def safe_response_summary(response: requests.Response) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "http_status": response.status_code,
        "content_type": response.headers.get("content-type"),
    }
    try:
        payload = response.json()
    except ValueError:
        summary["json"] = False
        summary["text_prefix"] = response.text[:80]
        return summary
    summary.update(
        {
            "json": True,
            "code": payload.get("code"),
            "status": payload.get("status"),
            "success": payload.get("success"),
            "message": payload.get("message") or payload.get("msg"),
            "data_keys": sorted(str(key) for key in (payload.get("data") or {}).keys())
            if isinstance(payload.get("data"), dict)
            else [],
        }
    )
    return summary


def probe_kuailv_h5(
    *,
    session: requests.Session,
    city_id: str,
    address_context: dict[str, Any],
    cat1_id: str | None,
    cat2_id: str | None,
    page_size: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    common_params = build_common_params(city_id, address_context)
    open_response = session.get(
        KUAILV_REGISTER_OPEN_URL,
        params={"cityId": city_id, "uaWeb": KUAILV_H5_UA_WEB},
        timeout=timeout_seconds,
    )
    first_response = session.get(
        KUAILV_CATEGORY_FIRST_URL,
        params=common_params,
        timeout=timeout_seconds,
    )

    first_payload: dict[str, Any] = {}
    try:
        first_payload = first_response.json()
    except ValueError:
        first_payload = {}
    category_rows = []
    if isinstance(first_payload.get("data"), dict):
        category_rows = first_payload["data"].get("categoryList") or []
    resolved_cat1_id = cat1_id or (
        str(category_rows[0].get("id")) if category_rows and isinstance(category_rows[0], dict) else None
    )

    second_summary: dict[str, Any] | None = None
    goods_summary: dict[str, Any] | None = None
    resolved_cat2_id = cat2_id
    if resolved_cat1_id:
        second_response = session.get(
            KUAILV_CATEGORY_SECOND_URL,
            params={**common_params, "cat1Id": resolved_cat1_id},
            timeout=timeout_seconds,
        )
        second_summary = safe_response_summary(second_response)
        try:
            second_payload = second_response.json()
        except ValueError:
            second_payload = {}
        second_rows = []
        if isinstance(second_payload.get("data"), dict):
            second_rows = second_payload["data"].get("categoryList") or []
        if not resolved_cat2_id and second_rows and isinstance(second_rows[0], dict):
            resolved_cat2_id = str(second_rows[0].get("id"))

    if resolved_cat1_id and resolved_cat2_id:
        goods_body = {
            "cat1Id": resolved_cat1_id,
            "cat2Id": resolved_cat2_id,
            "foodTagIds": None,
            "sortIds": None,
            "pageSize": page_size,
            "data": {
                "common": {
                    "uuid": str(common_params.get("uuid") or ""),
                    "timestamp": int(time.time() * 1000),
                },
                "context": {
                    "recent_click_goods": [],
                    "recent_add_cart_goods": [],
                },
            },
            "taken": None,
        }
        goods_response = session.post(
            KUAILV_GOODS_LIST_URL,
            params=common_params,
            json=goods_body,
            timeout=timeout_seconds,
        )
        goods_summary = safe_response_summary(goods_response)
        try:
            goods_payload = goods_response.json()
        except ValueError:
            goods_payload = {}
        goods_data = goods_payload.get("data") if isinstance(goods_payload, dict) else {}
        goods_rows = goods_data.get("goodsList") if isinstance(goods_data, dict) else None
        if isinstance(goods_rows, list):
            goods_summary["goods_count"] = len(goods_rows)
            goods_summary["has_next_page"] = (goods_data.get("page") or {}).get("hasNextPage")
            goods_summary["taken_present"] = bool((goods_data.get("page") or {}).get("taken"))

    return {
        "register_open": safe_response_summary(open_response),
        "category_first": safe_response_summary(first_response),
        "category_first_count": len(category_rows),
        "resolved_cat1_id": resolved_cat1_id,
        "category_second": second_summary,
        "resolved_cat2_id": resolved_cat2_id,
        "goods_list": goods_summary,
    }


def build_readiness_report(
    *,
    secret_env_file: Path | None,
    city_id: str,
    cat1_id: str | None,
    cat2_id: str | None,
    page_size: int,
    timeout_seconds: int,
    skip_network: bool,
) -> dict[str, Any]:
    loaded_env_names = load_env_file_without_override(secret_env_file) if secret_env_file else []
    headers_env_name = "KUAILV_REQUEST_HEADERS"
    cookies_env_name = "KUAILV_COOKIES"
    address_context_env_name = "KUAILV_ADDRESS_CONTEXT"
    request_headers = parse_json_env(headers_env_name, required=False)
    cookies = parse_json_env(cookies_env_name, required=False)
    address_context = parse_json_env(address_context_env_name, required=False)

    report: dict[str, Any] = {
        "ready": False,
        "base_url": KUAILV_H5_BASE_URL,
        "city_id": city_id,
        "required_account": "快驴商城采购/商家账号",
        "required_context": [
            "valid KUAILV_COOKIES or equivalent login headers",
            "南京可服务地址",
            "selectedPoiAddressId",
            "selectedSalesGridId when account uses sales grid routing",
        ],
        "env": {
            headers_env_name: summarize_json_object(request_headers),
            cookies_env_name: summarize_json_object(cookies),
            address_context_env_name: summarize_json_object(address_context),
        },
        "loaded_env_names": loaded_env_names,
        "secret_env_file": str(secret_env_file) if secret_env_file else None,
    }
    if skip_network:
        report["error"] = "network probe skipped"
        return report

    session = build_session(request_headers, cookies)
    probe = probe_kuailv_h5(
        session=session,
        city_id=city_id,
        address_context=address_context,
        cat1_id=cat1_id,
        cat2_id=cat2_id,
        page_size=page_size,
        timeout_seconds=timeout_seconds,
    )
    report["probe"] = probe
    goods_list = probe.get("goods_list") or {}
    report["ready"] = (
        goods_list.get("http_status") == 200
        and goods_list.get("status") == 1
        and int(goods_list.get("goods_count") or 0) > 0
    )
    if not report["ready"]:
        report["error"] = "快驴 H5 商品接口未返回可用 goodsList；请补充快驴商家登录态和南京地址上下文"
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check Kuailv H5 crawl readiness without printing cookie or token values."
    )
    parser.add_argument("--secret-env-file", default=os.environ.get("KUAILV_SECRET_ENV_FILE"))
    parser.add_argument("--city-id", default=os.environ.get("KUAILV_CITY_ID", KUAILV_DEFAULT_CITY_ID))
    parser.add_argument("--cat1-id", default=os.environ.get("KUAILV_CAT1_ID"))
    parser.add_argument("--cat2-id", default=os.environ.get("KUAILV_CAT2_ID"))
    parser.add_argument("--page-size", type=int, default=KUAILV_DEFAULT_PAGE_SIZE)
    parser.add_argument("--timeout-seconds", type=int, default=15)
    parser.add_argument("--skip-network", action="store_true")
    parsed_args = parser.parse_args()

    try:
        report = build_readiness_report(
            secret_env_file=Path(parsed_args.secret_env_file) if parsed_args.secret_env_file else None,
            city_id=str(parsed_args.city_id),
            cat1_id=str(parsed_args.cat1_id) if parsed_args.cat1_id else None,
            cat2_id=str(parsed_args.cat2_id) if parsed_args.cat2_id else None,
            page_size=parsed_args.page_size,
            timeout_seconds=parsed_args.timeout_seconds,
            skip_network=parsed_args.skip_network,
        )
    except (RuntimeError, requests.RequestException) as exc:
        report = {
            "ready": False,
            "error": str(exc),
            "secret_env_file": str(parsed_args.secret_env_file) if parsed_args.secret_env_file else None,
        }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
