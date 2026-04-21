from __future__ import annotations

from collections import OrderedDict
from threading import RLock

import pandas as pd

from analysis.metrics import _build_price_identity_frame, build_cross_site_identity_frame, prepare_history
from storage.database import Database
from utils.config_loader import BASE_DIR, load_runtime_config


_DB = Database()
_DB.init_db()
_DATAFRAME_CACHE_LOCK = RLock()
_DATAFRAME_CACHE: OrderedDict[str, pd.DataFrame] = OrderedDict()
_DATAFRAME_CACHE_MAX_ITEMS = 48


def get_db() -> Database:
    return _DB


def _get_cached_dataframe(cache_key: str, loader) -> pd.DataFrame:
    with _DATAFRAME_CACHE_LOCK:
        cached_entry = _DATAFRAME_CACHE.get(cache_key)
        if cached_entry is not None:
            _DATAFRAME_CACHE.move_to_end(cache_key)
            return cached_entry

        dataframe = loader()
        _DATAFRAME_CACHE[cache_key] = dataframe
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

    latest_identity_df = get_latest_identity_df()
    latest_cross_site_identity_df = get_latest_cross_site_identity_df()
    matched_product_keys: list[str] = []

    if not latest_identity_df.empty:
        matched_product_keys.extend(
            latest_identity_df.loc[
                latest_identity_df["price_identity_key"] == normalized_identity_key,
                "product_key",
            ]
            .dropna()
            .astype(str)
            .tolist()
        )
    if not latest_cross_site_identity_df.empty:
        matched_product_keys.extend(
            latest_cross_site_identity_df.loc[
                latest_cross_site_identity_df["cross_site_identity_key"] == normalized_identity_key,
                "product_key",
            ]
            .dropna()
            .astype(str)
            .tolist()
        )
    return list(dict.fromkeys(item for item in matched_product_keys if item))


def get_latest_df() -> pd.DataFrame:
    return _get_cached_dataframe("latest_df", get_db().get_latest_records)


def get_runtime_settings() -> dict:
    return load_runtime_config(BASE_DIR / "config" / "runtime.json")
