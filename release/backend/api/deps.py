from __future__ import annotations

from collections import OrderedDict
import re
from threading import RLock
from time import monotonic

import pandas as pd
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from analysis.metrics import _build_price_identity_frame, build_cross_site_identity_frame, prepare_history
from storage.database import Database
from utils.auth import decode_access_token
from utils.config_loader import BASE_DIR, load_runtime_config
from utils.location_catalog import match_standard_city, match_standard_province


_DB = Database()
_DB.init_db()
_DATAFRAME_CACHE_LOCK = RLock()
_DATAFRAME_CACHE: OrderedDict[str, tuple[float, pd.DataFrame]] = OrderedDict()
_DATAFRAME_CACHE_MAX_ITEMS = 48
_DATAFRAME_CACHE_TTL_SECONDS = 30.0
_http_bearer = HTTPBearer(auto_error=False)


def get_db() -> Database:
    return _DB


def _get_cached_dataframe(cache_key: str, loader) -> pd.DataFrame:
    now = monotonic()
    with _DATAFRAME_CACHE_LOCK:
        cached_entry = _DATAFRAME_CACHE.get(cache_key)
        if cached_entry is not None:
            cached_at, dataframe = cached_entry
            if now - cached_at <= _DATAFRAME_CACHE_TTL_SECONDS:
                _DATAFRAME_CACHE.move_to_end(cache_key)
                return dataframe
            _DATAFRAME_CACHE.pop(cache_key, None)

        # Keep the loader inside the re-entrant lock to prevent cold-start cache
        # stampedes when the page opens several expensive market endpoints at once.
        dataframe = loader()
        _DATAFRAME_CACHE[cache_key] = (monotonic(), dataframe)
        while len(_DATAFRAME_CACHE) > _DATAFRAME_CACHE_MAX_ITEMS:
            _DATAFRAME_CACHE.popitem(last=False)
        return dataframe


def clear_dataframe_cache() -> None:
    with _DATAFRAME_CACHE_LOCK:
        _DATAFRAME_CACHE.clear()


def get_history_df() -> pd.DataFrame:
    return _get_cached_dataframe("history_df", get_db().get_price_history)


def get_signal_history_df() -> pd.DataFrame:
    return _get_cached_dataframe("signal_history_df", get_db().get_trend_history)


def get_history_identity_df() -> pd.DataFrame:
    return _get_cached_dataframe(
        "history_identity_df",
        lambda: _build_price_identity_frame(prepare_history(get_db().get_trend_history())),
    )


def get_latest_identity_df() -> pd.DataFrame:
    return _get_cached_dataframe(
        "latest_identity_df",
        lambda: _build_price_identity_frame(get_latest_df()),
    )


def get_latest_cross_site_identity_df() -> pd.DataFrame:
    return _get_cached_dataframe(
        "latest_cross_site_identity_df",
        lambda: build_cross_site_identity_frame(get_latest_df()),
    )


def get_product_history_identity_df(identity_key: str) -> pd.DataFrame:
    normalized_identity_key = str(identity_key or "").strip()
    if not normalized_identity_key:
        return pd.DataFrame()

    matched_product_keys = get_product_keys_for_identity(normalized_identity_key)
    if not matched_product_keys:
        history_identity_df = get_history_identity_df()
        if history_identity_df.empty:
            return pd.DataFrame()
        normalized_identity_lookup = normalized_identity_key.casefold()
        compact_identity_lookup = re.sub(r"[\s*·•/]+", "", normalized_identity_key).casefold()
        identity_series = history_identity_df["price_identity_key"].fillna("").astype(str).str.strip()
        compact_identity_series = identity_series.str.replace(r"[\s*·•/]+", "", regex=True).str.casefold()
        fallback_matches = history_identity_df.loc[
            (identity_series.str.casefold() == normalized_identity_lookup)
            | (compact_identity_series == compact_identity_lookup)
        ].copy()
        if not fallback_matches.empty:
            return fallback_matches.reset_index(drop=True)
        return pd.DataFrame()

    return _get_cached_dataframe(
        f"history_identity_df:{normalized_identity_key}",
        lambda: _build_price_identity_frame(
            prepare_history(get_db().get_trend_history_for_product_keys(matched_product_keys))
        ),
    )


def get_product_keys_for_identity(identity_key: str) -> list[str]:
    normalized_identity_key = str(identity_key or "").strip()
    if not normalized_identity_key:
        return []
    normalized_identity_lookup = normalized_identity_key.casefold()
    compact_identity_lookup = re.sub(r"[\s*·•/]+", "", normalized_identity_key).casefold()

    latest_identity_df = get_latest_identity_df()
    latest_cross_site_identity_df = get_latest_cross_site_identity_df()
    matched_product_keys: list[str] = []

    if not latest_identity_df.empty:
        identity_series = latest_identity_df["price_identity_key"].fillna("").astype(str).str.strip()
        compact_identity_series = identity_series.str.replace(r"[\s*·•/]+", "", regex=True).str.casefold()
        matched_product_keys.extend(
            latest_identity_df.loc[
                (identity_series.str.casefold() == normalized_identity_lookup)
                | (compact_identity_series == compact_identity_lookup),
                "product_key",
            ]
            .dropna()
            .astype(str)
            .tolist()
        )
    if not latest_cross_site_identity_df.empty:
        cross_identity_series = latest_cross_site_identity_df["cross_site_identity_key"].fillna("").astype(str).str.strip()
        compact_cross_identity_series = cross_identity_series.str.replace(r"[\s*·•/]+", "", regex=True).str.casefold()
        matched_product_keys.extend(
            latest_cross_site_identity_df.loc[
                (cross_identity_series.str.casefold() == normalized_identity_lookup)
                | (compact_cross_identity_series == compact_identity_lookup),
                "product_key",
            ]
            .dropna()
            .astype(str)
            .tolist()
        )
    return list(dict.fromkeys(item for item in matched_product_keys if item))


def get_identity_aliases(identity_key: str) -> list[str]:
    normalized_identity_key = str(identity_key or "").strip()
    if not normalized_identity_key:
        return []

    alias_map: OrderedDict[str, None] = OrderedDict()

    def build_compact_alias(text: str) -> str:
        return re.sub(r"[\s*·•/]+", "", text)

    def add_alias(value: object) -> None:
        text = str(value or "").strip()
        if not text:
            return
        alias_map.setdefault(text, None)
        compact = build_compact_alias(text)
        if compact and compact != text:
            alias_map.setdefault(compact, None)
        if "|" in text:
            prefix = text.split("|", 1)[0].strip()
            if prefix:
                alias_map.setdefault(prefix, None)
                compact_prefix = build_compact_alias(prefix)
                if compact_prefix and compact_prefix != prefix:
                    alias_map.setdefault(compact_prefix, None)

    add_alias(normalized_identity_key)
    try:
        matched_product_keys = get_product_keys_for_identity(normalized_identity_key)
    except Exception:
        return list(alias_map.keys())
    if not matched_product_keys:
        return list(alias_map.keys())

    try:
        latest_identity_df = get_latest_identity_df()
        latest_cross_site_identity_df = get_latest_cross_site_identity_df()
    except Exception:
        return list(alias_map.keys())

    if not latest_identity_df.empty:
        latest_matches = latest_identity_df.loc[latest_identity_df["product_key"].isin(matched_product_keys)].copy()
        for column_name in ["price_identity_key", "price_identity_label", "product_name", "group_name", "spec_text"]:
            if column_name not in latest_matches.columns:
                continue
            for value in latest_matches[column_name].dropna().astype(str).tolist():
                add_alias(value)

    if not latest_cross_site_identity_df.empty:
        cross_site_matches = latest_cross_site_identity_df.loc[
            latest_cross_site_identity_df["product_key"].isin(matched_product_keys)
        ].copy()
        for column_name in ["cross_site_identity_key", "cross_site_identity_label", "product_name", "group_name", "spec_text"]:
            if column_name not in cross_site_matches.columns:
                continue
            for value in cross_site_matches[column_name].dropna().astype(str).tolist():
                add_alias(value)

    return list(alias_map.keys())


def get_latest_df() -> pd.DataFrame:
    return _get_cached_dataframe("latest_df", get_db().get_latest_records)


def get_runtime_settings() -> dict:
    return load_runtime_config(BASE_DIR / "config" / "runtime.json")


def _resolve_auth_market_scope_defaults(scope_text: str | None) -> tuple[str | None, str | None]:
    normalized_scope = str(scope_text or "").strip()
    if not normalized_scope:
        return None, None
    if "全国" in normalized_scope:
        return None, None
    matched_city, province_from_city = match_standard_city(normalized_scope)
    matched_province = match_standard_province(normalized_scope) or province_from_city
    if "河南本地市场" in normalized_scope and not matched_province:
        matched_province = "河南省"
    return matched_province, matched_city


def _normalize_auth_user_row(row: dict | None) -> dict | None:
    if not row:
        return None

    supplier_id = row.get("supplier_id")
    normalized_supplier_id = int(supplier_id) if supplier_id is not None else None
    account_market_scope = str(row.get("market_scope") or "").strip() or None
    supplier_market_scope = str(row.get("supplier_market_scope") or "").strip() or None
    effective_market_scope = account_market_scope or supplier_market_scope
    default_province, default_city = _resolve_auth_market_scope_defaults(effective_market_scope)
    user_id = int(row.get("id") or 0)
    role = str(row.get("role") or "").strip() or "supplier"
    procurement_supplier_ids = (
        get_db().get_procurement_user_supplier_ids(user_id)
        if role == "procurement" and user_id > 0
        else []
    )
    supplier_profile = None
    if normalized_supplier_id is not None and row.get("supplier_name"):
        supplier_profile = {
            "supplier_id": normalized_supplier_id,
            "supplier_name": str(row.get("supplier_name") or "").strip(),
            "market_category": row.get("supplier_market_category"),
            "channel": row.get("supplier_channel"),
            "market_scope": row.get("supplier_market_scope"),
            "is_active": bool(row.get("supplier_is_active")) if row.get("supplier_is_active") is not None else True,
        }

    return {
        "id": user_id,
        "username": str(row.get("username") or "").strip(),
        "password_hash": row.get("password_hash"),
        "role": role,
        "display_name": row.get("display_name"),
        "market_scope": effective_market_scope,
        "default_province": default_province,
        "default_city": default_city,
        "is_active": bool(row.get("is_active")) if row.get("is_active") is not None else True,
        "is_deleted": bool(row.get("is_deleted")) if row.get("is_deleted") is not None else False,
        "supplier_id": normalized_supplier_id,
        "supplier_profile": supplier_profile,
        "procurement_supplier_ids": procurement_supplier_ids,
        "last_login_at": row.get("last_login_at"),
        "deleted_at": row.get("deleted_at"),
        "deleted_by": row.get("deleted_by"),
        "deleted_username": row.get("deleted_username"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


def get_auth_user_by_username(username: str) -> dict | None:
    rows = get_db().get_auth_user_by_username(username)
    if rows.empty:
        return None
    return _normalize_auth_user_row(rows.iloc[0].to_dict())


def get_auth_user_by_id(user_id: int) -> dict | None:
    rows = get_db().get_auth_user_by_id(user_id)
    if rows.empty:
        return None
    return _normalize_auth_user_row(rows.iloc[0].to_dict())


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_http_bearer),
) -> dict:
    if credentials is None or str(credentials.scheme or "").lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")

    token = str(credentials.credentials or "").strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录状态无效")

    try:
        payload = decode_access_token(token)
    except InvalidTokenError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录状态已失效，请重新登录") from error

    user_id = int(payload.get("sub") or 0)
    if user_id <= 0:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录状态无效")

    user = get_auth_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号不存在或已失效")
    if not user.get("is_active"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前账号已停用")
    return user


def require_authenticated_user(current_user: dict = Depends(get_current_user)) -> dict:
    return current_user


def require_admin_user(current_user: dict = Depends(require_authenticated_user)) -> dict:
    if str(current_user.get("role") or "") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前账号没有管理员权限")
    return current_user


def is_admin_user(current_user: dict) -> bool:
    return str(current_user.get("role") or "") == "admin"


def is_supplier_user(current_user: dict) -> bool:
    return str(current_user.get("role") or "") == "supplier"


def is_procurement_user(current_user: dict) -> bool:
    return str(current_user.get("role") or "") == "procurement"


def get_actor_display_name(current_user: dict) -> str:
    return str(current_user.get("display_name") or current_user.get("username") or "").strip() or "系统用户"


def get_procurement_supplier_ids(current_user: dict) -> list[int]:
    if not is_procurement_user(current_user):
        return []
    return sorted({
        int(supplier_id)
        for supplier_id in current_user.get("procurement_supplier_ids") or []
        if supplier_id is not None and int(supplier_id) > 0
    })


def ensure_supplier_access(current_user: dict, supplier_id: int) -> int:
    normalized_supplier_id = int(supplier_id)
    if is_admin_user(current_user):
        return normalized_supplier_id

    current_supplier_id = int(current_user.get("supplier_id") or 0)
    if current_supplier_id <= 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前账号未绑定供应商")
    if current_supplier_id != normalized_supplier_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="不可访问其他供应商数据")
    return current_supplier_id


def resolve_supplier_record_access_supplier_id(current_user: dict, record_id: int) -> int:
    rows = get_db().get_supplier_price_record(int(record_id))
    if rows.empty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到对应报价记录")
    supplier_id = int(rows.iloc[0].to_dict().get("supplier_id") or 0)
    return ensure_supplier_access(current_user, supplier_id)


def resolve_settlement_record_access_supplier_id(current_user: dict, record_id: int) -> int:
    rows = get_db().get_supplier_settlement_record(int(record_id))
    if rows.empty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到对应结算台账")
    supplier_id = int(rows.iloc[0].to_dict().get("supplier_id") or 0)
    return ensure_supplier_access(current_user, supplier_id)
