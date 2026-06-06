import pytest



pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from fastapi import HTTPException

import pandas as pd



import analysis.metrics as metrics_module

import api.app as api_app_module

import api.deps as api_deps_module

from api.app import create_app

from storage.database import Database

from utils.auth import hash_password





def _create_authenticated_client(

    monkeypatch,

    *,

    role: str = "admin",

    supplier_id: int | None = 5,

    procurement_supplier_ids: list[int] | None = None,

    username: str = "tester",

    display_name: str = "测试账号",

    db=None,

):

    user = {

        "id": 1,

        "username": username,

        "role": role,

        "display_name": display_name,

        "is_active": True,

        "supplier_id": supplier_id,

        "procurement_supplier_ids": list(procurement_supplier_ids or []),

        "supplier_profile": {

            "supplier_id": supplier_id,

            "supplier_name": "测试供应商",

            "market_category": "干调类",

            "channel": "微信小程序",

            "market_scope": "本地市场",

            "is_active": True,

        } if supplier_id is not None else None,

    }



    def _require_authenticated_user():

        return user



    def _require_admin_user():

        if role != "admin":

            raise HTTPException(status_code=403, detail="当前账号没有管理员权限")

        return user

    def _require_procurement_or_admin_user():

        if role not in {"admin", "procurement"}:

            raise HTTPException(status_code=403, detail="当前账号没有采购端权限")

        return user



    monkeypatch.setattr(api_app_module, "require_authenticated_user", _require_authenticated_user)

    monkeypatch.setattr(api_app_module, "require_admin_user", _require_admin_user)

    monkeypatch.setattr(api_app_module, "require_procurement_or_admin_user", _require_procurement_or_admin_user)

    if db is not None:

        db_getter = lambda: db

        monkeypatch.setattr(api_app_module, "get_db", db_getter)

        monkeypatch.setattr(api_deps_module, "get_db", db_getter)

    else:

        monkeypatch.setattr(api_deps_module, "get_db", api_app_module.get_db)

    return TestClient(create_app())





def test_api_health():

    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200

    assert response.json()["status"] == "ok"





def test_auth_login_and_me_endpoint_with_seeded_admin(tmp_path, monkeypatch):

    db = Database(tmp_path / "auth_test.db")

    db.init_db()

    admin_row = db.get_auth_user_by_username("admin")
    assert len(admin_row) == 1
    admin_record = admin_row.iloc[0].to_dict()
    db.upsert_auth_user(
        user_id=int(admin_record["id"]),
        username=str(admin_record["username"]),
        password_hash=str(admin_record["password_hash"]),
        role="admin",
        display_name=str(admin_record.get("display_name") or ""),
        market_scope="河南本地市场",
        is_active=True,
    )



    monkeypatch.setattr(api_deps_module, "get_db", lambda: db)

    monkeypatch.setattr(api_app_module, "get_db", lambda: db)

    client = TestClient(create_app())



    login_response = client.post(

        "/api/auth/login",

        json={"username": "admin", "password": "admin123"},

    )



    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    assert token

    assert login_response.json()["user"]["role"] == "admin"
    assert login_response.json()["user"]["market_scope"] == "河南本地市场"
    assert login_response.json()["user"]["default_province"] == "河南省"
    assert login_response.json()["user"]["default_city"] is None



    me_response = client.get(

        "/api/auth/me",

        headers={"Authorization": f"Bearer {token}"},

    )



    assert me_response.status_code == 200

    assert me_response.json()["user"]["username"] == "admin"

    assert me_response.json()["user"]["role"] == "admin"
    assert me_response.json()["user"]["market_scope"] == "河南本地市场"
    assert me_response.json()["user"]["default_province"] == "河南省"





def test_procurement_direct_register_endpoint_is_not_available(tmp_path, monkeypatch):

    db = Database(tmp_path / "procurement_direct_register.db")

    db.init_db()

    monkeypatch.setattr(api_deps_module, "get_db", lambda: db)

    monkeypatch.setattr(api_app_module, "get_db", lambda: db)

    client = TestClient(create_app())

    response = client.post(
        "/api/auth/procurement/register",
        json={
            "company_name": "南京采购组",
            "contact_name": "采购小李",
            "contact_phone": "13800138000",
            "username": "buyer-nj-direct",
            "password": "buyer123456",
            "market_scope": "南京市场",
            "requested_supplier_names": "莲菜档口, 冻品档口",
        },
    )

    assert response.status_code == 404



def test_inactive_supplier_account_cannot_login(tmp_path, monkeypatch):

    db = Database(tmp_path / "auth_inactive_supplier.db")

    db.init_db()



    supplier_id = db.upsert_supplier(

        supplier_name="莲菜档口A",

        contact_name="老王",

        market_scope="本地市场",

        market_category="干调类",

        channel="微信小程序",

        is_active=True,

    )

    db.upsert_auth_user(

        username="supplier-disabled",

        password_hash=hash_password("demo123456"),

        role="supplier",

        supplier_id=supplier_id,

        display_name="停用供应商账号",

        is_active=False,

    )



    monkeypatch.setattr(api_deps_module, "get_db", lambda: db)

    monkeypatch.setattr(api_app_module, "get_db", lambda: db)

    client = TestClient(create_app())



    response = client.post(

        "/api/auth/login",

        json={"username": "supplier-disabled", "password": "demo123456"},

    )



    assert response.status_code == 403

    assert response.json()["detail"] == "当前账号已停用"





def test_inactive_supplier_token_cannot_access_protected_endpoint(tmp_path, monkeypatch):

    db = Database(tmp_path / "auth_inactive_supplier_access.db")

    db.init_db()



    supplier_id = db.upsert_supplier(

        supplier_name="莲菜档口B",

        contact_name="小李",

        market_scope="本地市场",

        market_category="蔬菜类",

        channel="门店直报",

        is_active=True,

    )

    user_id = db.upsert_auth_user(

        username="supplier-access",

        password_hash=hash_password("demo123456"),

        role="supplier",

        supplier_id=supplier_id,

        display_name="供应商账号B",

        is_active=True,

    )



    monkeypatch.setattr(api_deps_module, "get_db", lambda: db)

    monkeypatch.setattr(api_app_module, "get_db", lambda: db)

    client = TestClient(create_app())



    login_response = client.post(

        "/api/auth/login",

        json={"username": "supplier-access", "password": "demo123456"},

    )



    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    existing_rows = db.get_auth_user_by_id(user_id)

    assert len(existing_rows) == 1

    existing_row = existing_rows.iloc[0].to_dict()

    db.upsert_auth_user(

        user_id=user_id,

        username=str(existing_row["username"]),

        password_hash=str(existing_row["password_hash"]),

        role="supplier",

        supplier_id=supplier_id,

        display_name=str(existing_row.get("display_name") or ""),

        is_active=False,

    )



    response = client.get(

        f"/api/suppliers/{supplier_id}/quotes",

        headers={"Authorization": f"Bearer {token}"},

    )



    assert response.status_code == 403

    assert response.json()["detail"] == "当前账号已停用"





def test_auth_user_management_endpoints_cover_create_update_and_self_guard(tmp_path, monkeypatch):

    db = Database(tmp_path / "auth_user_management.db")

    db.init_db()

    supplier_id = db.upsert_supplier(

        supplier_name="莲菜档口A",

        contact_name="老王",

        market_scope="本地市场",

        market_category="蔬菜类",

        channel="门店直报",

    )

    second_supplier_id = db.upsert_supplier(

        supplier_name="蔬菜档口B",

        contact_name="小李",

        market_scope="南京市场",

        market_category="蔬菜类",

        channel="门店直报",

    )

    client = _create_authenticated_client(monkeypatch, db=db, username="admin", display_name="系统管理员")



    list_response = client.get("/api/auth/users")



    assert list_response.status_code == 200

    assert list_response.json()["items"][0]["username"] == "admin"

    assert "password_hash" not in list_response.json()["items"][0]



    create_response = client.post(

        "/api/auth/users",

        json={

            "username": "lencai-a",

            "password": "supplier123",

            "role": "supplier",

            "supplier_id": supplier_id,

            "display_name": "莲菜档口A",

            "market_scope": "南京市场",

            "is_active": True,

        },

    )



    assert create_response.status_code == 200

    created_payload = create_response.json()

    assert created_payload["role"] == "supplier"

    assert created_payload["supplier_profile"]["supplier_name"] == "莲菜档口A"
    assert created_payload["market_scope"] == "南京市场"
    assert created_payload["default_province"] == "江苏省"
    assert created_payload["default_city"] == "南京"



    update_response = client.put(

        f"/api/auth/users/{created_payload['id']}",

        json={

            "username": "lencai-a",

            "role": "supplier",

            "supplier_id": supplier_id,

            "display_name": "莲菜档口A-停用",

            "market_scope": "河南本地市场",

            "is_active": False,

        },

    )



    assert update_response.status_code == 200

    assert update_response.json()["display_name"] == "莲菜档口A-停用"

    assert update_response.json()["is_active"] is False
    assert update_response.json()["market_scope"] == "河南本地市场"
    assert update_response.json()["default_province"] == "河南省"
    assert update_response.json()["default_city"] is None

    procurement_create_response = client.post(

        "/api/auth/users",

        json={

            "username": "buyer-nj",

            "password": "buyer123456",

            "role": "procurement",

            "procurement_supplier_ids": [supplier_id, second_supplier_id],

            "display_name": "南京采购",

            "market_scope": "南京市场",

            "is_active": True,

        },

    )

    assert procurement_create_response.status_code == 200

    procurement_payload = procurement_create_response.json()

    assert procurement_payload["role"] == "procurement"

    assert procurement_payload["market_scope"] == "南京市场"

    assert procurement_payload["default_province"] == "江苏省"

    assert procurement_payload["default_city"] == "南京"

    assert procurement_payload["procurement_supplier_ids"] == [supplier_id, second_supplier_id]



    self_disable_response = client.put(

        "/api/auth/users/1",

        json={

            "username": "admin",

            "role": "admin",

            "display_name": "系统管理员",

            "is_active": False,

        },

    )



    assert self_disable_response.status_code == 400

    assert self_disable_response.json()["detail"] == "不能删除或停用当前登录账号"



    self_delete_response = client.delete("/api/auth/users/1")



    assert self_delete_response.status_code == 400

    assert self_delete_response.json()["detail"] == "不能删除或停用当前登录账号"



    delete_response = client.delete(f"/api/auth/users/{created_payload['id']}")



    assert delete_response.status_code == 200

    assert delete_response.json() == {"deleted": True, "user_id": created_payload["id"]}

    assert db.get_auth_user_by_id(created_payload["id"]).empty

    archived_rows = db.get_auth_user_by_id(created_payload["id"], include_deleted=True)

    assert len(archived_rows) == 1

    archived_row = archived_rows.iloc[0]

    assert bool(archived_row["is_deleted"]) is True

    assert bool(archived_row["is_active"]) is False

    assert archived_row["deleted_username"] == "lencai-a"

    assert archived_row["deleted_by"] == "系统管理员"




def test_supplier_role_cannot_access_other_supplier_quotes(monkeypatch):

    client = _create_authenticated_client(monkeypatch, role="supplier", supplier_id=5)



    response = client.get("/api/suppliers/9/quotes")



    assert response.status_code == 403





class _FakeCrawlManager:

    def __init__(self) -> None:

        self.schedule_enabled = False



    def start(self) -> None:

        return None



    def shutdown(self) -> None:

        return None



    def get_status(self) -> dict:

        return {

            "is_running": False,

            "last_run_source": "manual",

            "last_started_at": None,

            "last_finished_at": "2026-04-11T09:00:00+08:00",

            "last_success_at": "2026-04-11T09:00:00+08:00",

            "last_error": None,

            "current_source_name": None,

            "current_source_index": 0,

            "current_source_progress": 0.0,

            "current_source_detail": None,

            "completed_sources": 3,

            "progress_percent": 100,

            "last_total_sources": 3,

            "last_total_results": 120,

            "last_success_count": 120,

            "last_failed_count": 0,

            "next_run_at": None,

            "schedule_enabled": self.schedule_enabled,

            "schedule_mode": "interval",

            "schedule_daily_run_time": "03:30",

            "schedule_interval_seconds": 86400,

            "schedule_fetch_mode": "requests",

            "schedule_target_scope": "all_saved",

            "schedule_target_province": None,

            "schedule_target_city": None,

            "target_scope": "all_saved",

            "target_province": None,

            "target_city": None,

        }



    def trigger_run(self, source: str = "manual", *, target_scope: str | None = None, target_province: str | None = None, target_city: str | None = None, source_url: str | None = None, source_name: str | None = None) -> tuple[bool, dict]:

        item = self.get_status()

        item["is_running"] = True

        item["last_run_source"] = source

        item["target_scope"] = target_scope or "all_saved"

        item["target_province"] = target_province

        item["target_city"] = target_city

        item["source_url"] = source_url

        item["source_name"] = source_name

        return True, item



    def update_schedule(self, *, enabled: bool | None = None, mode: str | None = None, daily_run_time: str | None = None, interval_seconds: int | None = None, fetch_mode: str | None = None, target_scope: str | None = None, target_province: str | None = None, target_city: str | None = None) -> dict:

        self.schedule_enabled = bool(enabled)

        item = self.get_status()

        item["schedule_enabled"] = self.schedule_enabled

        if interval_seconds is not None:

            item["schedule_interval_seconds"] = interval_seconds

        if mode is not None:

            item["schedule_mode"] = mode

        if daily_run_time is not None:

            item["schedule_daily_run_time"] = daily_run_time

        if fetch_mode is not None:

            item["schedule_fetch_mode"] = fetch_mode

        if target_scope is not None:

            item["schedule_target_scope"] = target_scope

        if target_province is not None:

            item["schedule_target_province"] = target_province

        if target_city is not None:

            item["schedule_target_city"] = target_city

        return item





def test_crawl_status_endpoint(monkeypatch):

    monkeypatch.setattr(api_app_module, "get_crawl_manager", lambda: _FakeCrawlManager())

    client = _create_authenticated_client(monkeypatch)



    response = client.get("/api/crawl/status")



    assert response.status_code == 200

    assert response.json()["item"]["last_total_sources"] == 3

    assert response.json()["item"]["progress_percent"] == 100

    assert "current_source_progress" in response.json()["item"]

    assert "current_source_detail" in response.json()["item"]





def test_crawl_run_endpoint(monkeypatch):

    monkeypatch.setattr(api_app_module, "get_crawl_manager", lambda: _FakeCrawlManager())

    client = _create_authenticated_client(monkeypatch)



    response = client.post("/api/crawl/run")



    assert response.status_code == 200

    assert response.json()["accepted"] is True

    assert response.json()["item"]["is_running"] is True

    assert response.json()["item"]["progress_percent"] == 100


def test_crawl_run_endpoint_accepts_region_scope(monkeypatch):

    monkeypatch.setattr(api_app_module, "get_crawl_manager", lambda: _FakeCrawlManager())

    client = _create_authenticated_client(monkeypatch)

    response = client.post(
        "/api/crawl/run",
        json={"target_scope": "city", "target_province": "河南省", "target_city": "郑州"},
    )

    assert response.status_code == 200

    assert response.json()["item"]["target_scope"] == "city"

    assert response.json()["item"]["target_province"] == "河南省"

    assert response.json()["item"]["target_city"] == "郑州"





def test_crawl_schedule_endpoint(monkeypatch):

    fake_manager = _FakeCrawlManager()

    monkeypatch.setattr(api_app_module, "get_crawl_manager", lambda: fake_manager)

    client = _create_authenticated_client(monkeypatch)



    response = client.post(

        "/api/crawl/schedule",

        json={"enabled": True, "mode": "daily_time", "daily_run_time": "03:30", "interval_seconds": 86400, "fetch_mode": "requests"},

    )



    assert response.status_code == 200

    assert response.json()["item"]["schedule_enabled"] is True

    assert response.json()["item"]["schedule_interval_seconds"] == 86400

    assert response.json()["item"]["schedule_mode"] == "daily_time"

    assert response.json()["item"]["schedule_daily_run_time"] == "03:30"


def test_crawl_schedule_endpoint_persists_region_scope(monkeypatch):

    monkeypatch.setattr(api_app_module, "get_crawl_manager", lambda: _FakeCrawlManager())

    client = _create_authenticated_client(monkeypatch)

    response = client.post(
        "/api/crawl/schedule",
        json={
            "enabled": True,
            "interval_seconds": 86400,
            "fetch_mode": "requests",
            "target_scope": "province",
            "target_province": "河南省",
        },
    )

    assert response.status_code == 200

    assert response.json()["item"]["schedule_target_scope"] == "province"

    assert response.json()["item"]["schedule_target_province"] == "河南省"





def test_source_coverage_endpoint_includes_local_source_metadata(monkeypatch):

    class _FakeDb:

        def get_source_coverage_summary(self):

            return pd.DataFrame(

                [

                    {

                        "source_url": "https://www.wbncp.com/?m=home&c=Lists&a=index&tid=69",

                        "product_key_count": 120,

                        "comparable_item_count": 80,

                        "source_item_count": 80,

                        "market_count": 12,

                        "price_record_count": 500,

                        "latest_capture": "2026-04-18T12:00:00",

                        "failed_count": 0,

                        "last_failure": None,

                    }

                ]

            )



    def fake_load_json_config(path):

        text = str(path)

        if text.endswith("products.json"):

            return [

                {

                    "product_name": "万邦国际行情",

                    "source_name": "万邦国际",

                    "url": "https://www.wbncp.com/?m=home&c=Lists&a=index&tid=69",

                    "enabled": True,

                    "market_scope": "全国公开市场",

                    "market_category": "综合行情",

                    "channel": "公开接口",

                    "notes": "已接入",

                },

                {

                    "product_name": "莲菜网小程序·干调类",

                    "source_name": "莲菜网",

                    "url": "http://m.liancaiwang.cn",

                    "enabled": False,

                    "market_scope": "本地市场",

                    "market_category": "莲菜网",

                    "category": "干调类",

                    "channel": "微信H5",

                    "strategy": "liancai_h5_batch",

                    "notes": "需设置环境变量后启用",

                },

            ]

        return []



    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())

    monkeypatch.setattr(api_app_module, "load_json_config", fake_load_json_config)

    client = _create_authenticated_client(monkeypatch)



    response = client.get("/api/source/coverage")



    assert response.status_code == 200

    rows = response.json()["items"]

    local_row = next(item for item in rows if item["configured_name"] == "莲菜网小程序·干调类")

    assert local_row["status"] == "待接入"

    assert local_row["market_scope"] == "本地市场"

    assert local_row["market_category"] == "莲菜网"

    assert local_row["market_subcategory"] == "干调类"

    assert local_row["channel"] == "微信H5"





def test_menu_plan_endpoint_accepts_preferred_location(monkeypatch):

    monkeypatch.setattr(api_app_module, "get_latest_df", lambda: pd.DataFrame())

    monkeypatch.setattr(api_app_module, "get_runtime_settings", lambda: {"ai": {"enabled": False}})

    captured_kwargs: dict[str, object] = {}



    def fake_build_procurement_plan(menu_items, latest_df, **kwargs):

        captured_kwargs.update(kwargs)

        return pd.DataFrame(), pd.DataFrame()



    monkeypatch.setattr(api_app_module, "build_procurement_plan", fake_build_procurement_plan)

    client = _create_authenticated_client(monkeypatch)



    response = client.post(

        "/api/menu/plan",

        json={

            "menu_text": "蒜蓉西兰花",

            "diners": 100,

            "tables": 10,

            "preferred_location": "当前位置",

        },

    )



    assert response.status_code == 200

    assert captured_kwargs["preferred_location"] == "当前位置"





def test_liancai_category_summary_endpoint_returns_rows(monkeypatch):

    class _FakeDb:

        def get_liancai_category_summary(self):

            import pandas as pd



            return pd.DataFrame(

                [

                    {

                        "liancai_top_category": "蔬菜类",

                        "liancai_subcategory": "叶菜类",

                        "product_count": 93,

                    },

                    {

                        "liancai_top_category": "干调类",

                        "liancai_subcategory": "香辛料",

                        "product_count": 162,

                    },

                ]

            )



    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())

    client = _create_authenticated_client(monkeypatch)



    response = client.get("/api/liancai/category-summary")



    assert response.status_code == 200

    rows = response.json()["items"]

    assert rows[0]["liancai_top_category"] == "蔬菜类"

    assert rows[1]["liancai_subcategory"] == "香辛料"





def test_ai_search_endpoint_returns_answer(monkeypatch):

    monkeypatch.setattr(api_app_module, "get_runtime_settings", lambda: {"ai": {"enabled": True}})

    monkeypatch.setattr(api_app_module, "run_search_query", lambda query, runtime_config=None: f"搜索结果: {query}")

    client = _create_authenticated_client(monkeypatch)



    response = client.post("/api/ai/search", json={"query": "今天的新闻"})



    assert response.status_code == 200

    assert response.json() == {"answer": "搜索结果: 今天的新闻"}





def test_ai_search_endpoint_requires_procurement_or_admin(monkeypatch):

    monkeypatch.setattr(api_app_module, "get_runtime_settings", lambda: {"ai": {"enabled": True}})

    monkeypatch.setattr(api_app_module, "run_search_query", lambda query, runtime_config=None: f"搜索结果: {query}")

    unauthenticated_client = TestClient(create_app())
    unauthenticated_response = unauthenticated_client.post("/api/ai/search", json={"query": "今天的新闻"})

    supplier_client = _create_authenticated_client(monkeypatch, role="supplier", supplier_id=5)
    supplier_response = supplier_client.post("/api/ai/search", json={"query": "今天的新闻"})

    procurement_client = _create_authenticated_client(
        monkeypatch,
        role="procurement",
        supplier_id=None,
        procurement_supplier_ids=[5],
    )
    procurement_response = procurement_client.post("/api/ai/search", json={"query": "今天的新闻"})

    assert unauthenticated_response.status_code == 401
    assert supplier_response.status_code == 403
    assert procurement_response.status_code == 200



def test_product_endpoints_forward_city_and_province(monkeypatch):

    monkeypatch.setattr(api_app_module, "get_product_history_identity_df", lambda _: pd.DataFrame())

    monkeypatch.setattr(api_app_module, "get_latest_df", lambda: pd.DataFrame())

    captured: dict[str, dict] = {}



    def fake_selector(df, selected_province=None, selected_city=None):

        captured["selector"] = {"province": selected_province, "city": selected_city}

        return pd.DataFrame()



    def fake_summary(df, identity_key, selected_province=None, selected_city=None):

        captured["summary"] = {"province": selected_province, "city": selected_city, "identity_key": identity_key}

        return {}



    def fake_cross_trend(df, identity_key, selected_province=None, selected_city=None):

        captured["cross_trend"] = {"province": selected_province, "city": selected_city, "identity_key": identity_key}

        return pd.DataFrame()



    monkeypatch.setattr(api_app_module, "build_single_product_selector_options", fake_selector)

    monkeypatch.setattr(api_app_module, "compute_single_product_summary", fake_summary)

    monkeypatch.setattr(api_app_module, "build_cross_market_product_trend", fake_cross_trend)

    client = _create_authenticated_client(monkeypatch)



    options_response = client.get("/api/product/options?province=北京市&city=北京市")

    summary_response = client.get("/api/product/test-key/summary?province=北京市&city=北京市")

    trend_response = client.get("/api/product/test-key/trend?mode=cross_market&province=北京市&city=北京市")



    assert options_response.status_code == 200

    assert summary_response.status_code == 200

    assert trend_response.status_code == 200

    assert captured["selector"] == {"province": "北京市", "city": "北京市"}

    assert captured["summary"]["province"] == "北京市"

    assert captured["summary"]["city"] == "北京市"

    assert captured["cross_trend"]["province"] == "北京市"

    assert captured["cross_trend"]["city"] == "北京市"





def test_market_summary_endpoint_limits_and_caches_payload(monkeypatch):

    api_app_module._cached_market_summary_payload.cache_clear()

    api_app_module._clear_market_summary_disk_cache()

    calls = {"summary": 0}

    monkeypatch.setattr(api_app_module, "get_latest_df", lambda: pd.DataFrame({"product_name": ["白菜"]}))



    def fake_summary(df, selected_province=None, selected_city=None):

        calls["summary"] += 1

        assert selected_province == "北京市"

        assert selected_city == "北京市"

        return pd.DataFrame(

            [

                {"product_name": "白菜", "lowest_price": 1.2},

                {"product_name": "萝卜", "lowest_price": 1.5},

            ]

        )



    monkeypatch.setattr(api_app_module, "compute_cross_site_price_summary", fake_summary)

    client = _create_authenticated_client(monkeypatch)



    first_response = client.get("/api/market/summary?province=北京市&city=北京市&limit=1")

    second_response = client.get("/api/market/summary?province=北京市&city=北京市&limit=1")



    assert first_response.status_code == 200

    assert second_response.status_code == 200

    assert first_response.json()["total"] == 2

    assert first_response.json()["limit"] == 1

    assert first_response.json()["items"] == [{"product_name": "白菜", "lowest_price": 1.2}]

    assert calls["summary"] == 1

    api_app_module._cached_market_summary_payload.cache_clear()





def test_market_summary_endpoint_requires_procurement_or_admin(monkeypatch):

    api_app_module._cached_market_summary_payload.cache_clear()

    api_app_module._clear_market_summary_disk_cache()

    monkeypatch.setattr(api_app_module, "get_latest_df", lambda: pd.DataFrame({"product_name": ["白菜"]}))

    monkeypatch.setattr(
        api_app_module,
        "compute_cross_site_price_summary",
        lambda *args, **kwargs: pd.DataFrame([{"product_name": "白菜", "lowest_price": 1.2}]),
    )

    unauthenticated_client = TestClient(create_app())
    unauthenticated_response = unauthenticated_client.get("/api/market/summary")

    supplier_client = _create_authenticated_client(monkeypatch, role="supplier", supplier_id=5)
    supplier_response = supplier_client.get("/api/market/summary")

    procurement_client = _create_authenticated_client(
        monkeypatch,
        role="procurement",
        supplier_id=None,
        procurement_supplier_ids=[5],
    )
    procurement_response = procurement_client.get("/api/market/summary")

    admin_client = _create_authenticated_client(monkeypatch, role="admin", supplier_id=None)
    admin_response = admin_client.get("/api/market/summary")

    assert unauthenticated_response.status_code == 401
    assert supplier_response.status_code == 403
    assert procurement_response.status_code == 200
    assert admin_response.status_code == 200

    api_app_module._cached_market_summary_payload.cache_clear()


def test_procurement_market_price_reads_only_include_bound_suppliers(monkeypatch):
    api_app_module._cached_market_summary_payload.cache_clear()
    api_app_module._clear_market_summary_disk_cache()
    monkeypatch.setattr(api_app_module, "get_latest_df", lambda: pd.DataFrame())
    monkeypatch.setattr(api_app_module, "get_product_history_identity_df", lambda _: pd.DataFrame())
    monkeypatch.setattr(api_app_module, "get_identity_aliases", lambda identity_key: [identity_key])

    class _FakeDb:
        def get_latest_supplier_quotes(self, price_identity_keys=None):
            return pd.DataFrame(
                [
                    {
                        "record_id": 10,
                        "supplier_id": 1,
                        "supplier_name": "鲜蔬档口A",
                        "price_identity_key": "白菜",
                        "price_identity_label": "白菜",
                        "product_name": "白菜",
                        "market_category": "蔬菜类",
                        "quote_price": 2.5,
                        "quote_unit": "斤",
                        "quoted_at": "2026-06-01T09:00:00",
                    },
                    {
                        "record_id": 11,
                        "supplier_id": 2,
                        "supplier_name": "鲜蔬档口B",
                        "price_identity_key": "白菜",
                        "price_identity_label": "白菜",
                        "product_name": "白菜",
                        "market_category": "蔬菜类",
                        "quote_price": 1.8,
                        "quote_unit": "斤",
                        "quoted_at": "2026-06-01T09:10:00",
                    },
                ]
            )

    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())
    monkeypatch.setattr(api_deps_module, "get_db", lambda: _FakeDb())
    client = _create_authenticated_client(
        monkeypatch,
        role="procurement",
        supplier_id=None,
        procurement_supplier_ids=[1],
    )

    summary_response = client.get("/api/market/summary?keyword=白菜")
    trend_response = client.get("/api/product/%E7%99%BD%E8%8F%9C/trend")
    quotes_response = client.get("/api/product/%E7%99%BD%E8%8F%9C/supplier-quotes")

    assert summary_response.status_code == 200
    assert trend_response.status_code == 200
    assert quotes_response.status_code == 200
    assert summary_response.json()["items"][0]["source_names"] == "鲜蔬档口A"
    assert {item["site_name"] for item in trend_response.json()["items"]} == {"鲜蔬档口A"}
    assert [item["supplier_name"] for item in quotes_response.json()["items"]] == ["鲜蔬档口A"]

    api_app_module._cached_market_summary_payload.cache_clear()



def test_liancai_keyword_filter_falls_back_to_product_name_when_keyword_column_empty():

    source_df = pd.DataFrame(

        [

            {

                "product_name": "脱皮白芝麻48斤-佐味",

                "liancai_top_category": "干调类",

                "liancai_subcategory": "南北干货",

                "liancai_keyword": None,

            },

            {

                "product_name": "东北木耳",

                "liancai_top_category": "干调类",

                "liancai_subcategory": "南北干货",

                "liancai_keyword": None,

            },

        ]

    )



    filtered = api_app_module._filter_by_liancai_category(

        source_df,

        liancai_top_category="干调类",

        liancai_subcategory="南北干货",

        liancai_keyword="白芝麻",

    )



    assert filtered["product_name"].tolist() == ["脱皮白芝麻48斤-佐味"]





def test_liancai_top_category_filter_matches_common_aliases():

    source_df = pd.DataFrame(

        [

            {

                "product_name": "雪天牌加碘精纯盐400g",

                "liancai_top_category": "调味品",

                "liancai_subcategory": "调味料",

            },

            {

                "product_name": "小白菜",

                "liancai_top_category": "蔬菜类",

                "liancai_subcategory": "叶菜类",

            },

        ]

    )



    filtered = api_app_module._filter_by_liancai_category(

        source_df,

        liancai_top_category="干调类",

    )



    assert filtered["product_name"].tolist() == ["雪天牌加碘精纯盐400g"]





def test_market_summary_endpoint_filters_source_and_liancai_alias(monkeypatch):

    api_app_module._cached_market_summary_payload.cache_clear()

    api_app_module._clear_market_summary_disk_cache()

    captured: dict[str, list[str]] = {}

    source_df = pd.DataFrame(

        [

            {

                "product_name": "雪天牌加碘精纯盐400g",

                "site_name": "莲菜网App | 干调类",

                "source_url": "https://example.test/liancai",

                "liancai_top_category": "调味品",

                "liancai_subcategory": "调味料",

            },

            {

                "product_name": "小白菜",

                "site_name": "其他市场",

                "source_url": "https://example.test/other",

                "liancai_top_category": "蔬菜类",

                "liancai_subcategory": "叶菜类",

            },

        ]

    )

    monkeypatch.setattr(api_app_module, "get_latest_df", lambda: source_df)



    def fake_summary(df, selected_province=None, selected_city=None):

        captured["products"] = df["product_name"].tolist()

        return pd.DataFrame(

            [

                {

                    "product_name": value,

                    "source_names": "莲菜网",

                    "liancai_top_category": "调味品",

                    "lowest_price": 1.2,

                }

                for value in captured["products"]

            ]

        )



    monkeypatch.setattr(api_app_module, "compute_cross_site_price_summary", fake_summary)

    client = _create_authenticated_client(monkeypatch)



    response = client.get("/api/market/summary?source_name=莲菜网&liancai_top_category=干调类&limit=500&offset=0")



    assert response.status_code == 200

    assert captured["products"] == ["雪天牌加碘精纯盐400g"]

    assert response.json()["total"] == 1

    assert response.json()["items"][0]["product_name"] == "雪天牌加碘精纯盐400g"

    api_app_module._cached_market_summary_payload.cache_clear()





def test_product_endpoints_use_identity_scoped_history_lookup(monkeypatch):

    captured: dict[str, str] = {}



    def fake_history(identity_key: str) -> pd.DataFrame:

        captured["identity_key"] = identity_key

        return pd.DataFrame()



    monkeypatch.setattr(api_app_module, "get_product_history_identity_df", fake_history)

    monkeypatch.setattr(api_app_module, "compute_single_product_summary", lambda *args, **kwargs: {})

    monkeypatch.setattr(api_app_module, "build_cross_market_product_trend", lambda *args, **kwargs: pd.DataFrame())

    client = _create_authenticated_client(monkeypatch)



    summary_response = client.get("/api/product/%E5%9C%9F%E8%B1%86%7C%E8%94%AC%E8%8F%9C%E7%B1%BB/summary")

    trend_response = client.get("/api/product/%E5%9C%9F%E8%B1%86%7C%E8%94%AC%E8%8F%9C%E7%B1%BB/trend")



    assert summary_response.status_code == 200

    assert trend_response.status_code == 200

    assert captured["identity_key"] == "土豆|蔬菜类"





def test_location_options_endpoint_returns_province_city_map(monkeypatch):

    latest_df = pd.DataFrame(

        [

            {"product_name": "白菜", "province": "北京市", "city": "北京市"},

            {"product_name": "萝卜", "province": "河南省", "city": "郑州市"},

            {"product_name": "蒜薹", "province": "河南省", "city": "洛阳市"},

        ]

    )

    monkeypatch.setattr(api_app_module, "get_latest_df", lambda: latest_df)

    monkeypatch.setattr(api_app_module, "_fetch_latest_product_rows", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("use fixture df")))

    client = _create_authenticated_client(monkeypatch)



    response = client.get("/api/location/options")



    assert response.status_code == 200

    assert response.json() == {

        "provinces": ["北京市", "河南省"],

        "cities": ["北京市", "洛阳", "郑州"],

        "province_city_map": {

            "北京市": ["北京市"],

            "河南省": ["洛阳", "郑州"],

        },

    }


def test_location_suggestion_prefers_browser_coordinates(monkeypatch):
    def fake_browser_suggestion(latitude, longitude):
        assert latitude == 32.06
        assert longitude == 118.79
        return {
            "matched": True,
            "province": "江苏省",
            "city": "南京",
            "label": "南京",
            "source": "browser_geolocation",
            "source_label": "浏览器定位",
            "confidence": 0.86,
            "raw_location": "江苏省 南京市",
        }

    def fail_ip_suggestion(ip_address_text):
        raise AssertionError("IP fallback should not run when browser location matches")

    monkeypatch.setattr(api_app_module, "_fetch_browser_location_suggestion", fake_browser_suggestion)
    monkeypatch.setattr(api_app_module, "_fetch_ip_location_suggestion", fail_ip_suggestion)

    client = TestClient(create_app())
    response = client.get("/api/location/suggest?latitude=32.06&longitude=118.79")

    assert response.status_code == 200
    assert response.json()["matched"] is True
    assert response.json()["province"] == "江苏省"
    assert response.json()["city"] == "南京"
    assert response.json()["source"] == "browser_geolocation"


def test_location_suggestion_uses_ip_fallback(monkeypatch):
    def fake_browser_suggestion(latitude, longitude):
        return None

    def fake_ip_suggestion(ip_address_text):
        assert ip_address_text == "8.8.8.8"
        return {
            "matched": True,
            "province": "河南省",
            "city": "郑州",
            "label": "郑州",
            "source": "ip_geolocation",
            "source_label": "IP 归属地",
            "confidence": 0.58,
            "raw_location": "河南省 郑州市",
        }

    monkeypatch.setattr(api_app_module, "_fetch_browser_location_suggestion", fake_browser_suggestion)
    monkeypatch.setattr(api_app_module, "_fetch_ip_location_suggestion", fake_ip_suggestion)

    client = TestClient(create_app())
    response = client.get(
        "/api/location/suggest?latitude=0&longitude=0",
        headers={"x-forwarded-for": "8.8.8.8"},
    )

    assert response.status_code == 200
    assert response.json()["matched"] is True
    assert response.json()["province"] == "河南省"
    assert response.json()["city"] == "郑州"
    assert response.json()["source"] == "ip_geolocation"





def test_product_trend_endpoint_returns_source_tier_metadata(monkeypatch):

    def fake_resolve_source_tier(item, fallback=""):

        source_name = str((item or {}).get("source_name") or "").strip()

        if source_name == "PFSC":

            return "主价格源"

        return fallback



    history_df = pd.DataFrame(

        [

            {

                "group_name": "白菜",

                "product_name": "白菜",

                "product_key": "pfsc-a",

                "site_name": "PFSC | 北京新发地",

                "source_url": "https://pfsc.agri.cn/#/priceMarket",

                "market_name": "北京新发地",

                "province": "北京市",

                "city": "北京市",

                "spec_text": "公斤",

                "current_price": 2.6,

                "captured_at": "2026-04-10T08:00:00",

            },

            {

                "group_name": "白菜",

                "product_name": "白菜",

                "product_key": "pfsc-a",

                "site_name": "PFSC | 北京新发地",

                "source_url": "https://pfsc.agri.cn/#/priceMarket",

                "market_name": "北京新发地",

                "province": "北京市",

                "city": "北京市",

                "spec_text": "公斤",

                "current_price": 2.8,

                "captured_at": "2026-04-11T08:00:00",

            },

        ]

    )



    monkeypatch.setattr(metrics_module, "resolve_source_tier", fake_resolve_source_tier)

    monkeypatch.setattr(api_app_module, "get_product_history_identity_df", lambda _: history_df)

    client = _create_authenticated_client(monkeypatch)



    response = client.get("/api/product/%E7%99%BD%E8%8F%9C%7C%E5%85%AC%E6%96%A4/trend")



    assert response.status_code == 200

    assert response.json()["mode"] == "cross_market"

    assert len(response.json()["items"]) == 2

    assert response.json()["items"][0]["source_name"] == "PFSC"

    assert response.json()["items"][0]["source_tier"] == "主价格源"

    assert response.json()["items"][0]["trend_series_name"] == "PFSC · 北京新发地"





def test_signals_overview_endpoint_returns_decision_payload(monkeypatch):

    monkeypatch.setattr(api_app_module, "get_latest_df", lambda: pd.DataFrame())

    monkeypatch.setattr(api_app_module, "get_signal_history_df", lambda: pd.DataFrame())

    monkeypatch.setattr(

        api_app_module,

        "build_signals_overview",

        lambda latest_df, history_df, province=None, city=None, focus=None: {

            "generated_at": "2026-04-18",

            "scope": {"province": province, "city": city, "focus": focus},

            "headline": "北京市 当前适合先讲机会再讲风险",

            "overview_metrics": [{"label": "信号总数", "value": "3", "detail": "mock"}],

            "top_opportunities": [

                {

                    "identity_key": "土豆",

                    "product_name": "土豆",

                    "signal_code": "overview",

                    "signal_level": "high",

                    "timing_score": 81,

                    "risk_score": 38,

                    "confidence": 79,

                    "recommended_action": "立即采购",

                    "reason_summary": "mock opportunity",

                }

            ],

            "top_risks": [],

            "recommended_actions": [{"title": "优先锁定土豆", "description": "mock", "action": "立即采购"}],

            "source_health": {"status": "healthy"},

            "alert_count": 1,

            "alert_items": [],

        },

    )

    client = _create_authenticated_client(monkeypatch)



    response = client.get("/api/signals/overview?province=北京市&city=北京市&focus=土豆")



    assert response.status_code == 200

    assert response.json()["scope"] == {"province": "北京市", "city": "北京市", "focus": "土豆"}

    assert response.json()["top_opportunities"][0]["identity_key"] == "土豆"





def test_signal_detail_endpoint_returns_404_when_missing(monkeypatch):

    monkeypatch.setattr(api_app_module, "get_product_history_identity_df", lambda _: pd.DataFrame())

    monkeypatch.setattr(api_app_module, "build_product_signal_detail", lambda *args, **kwargs: {})

    client = _create_authenticated_client(monkeypatch)



    response = client.get("/api/signals/土豆")



    assert response.status_code == 404





def test_procurement_recommend_and_sales_endpoints(monkeypatch):

    monkeypatch.setattr(api_app_module, "get_latest_df", lambda: pd.DataFrame())

    monkeypatch.setattr(api_app_module, "get_runtime_settings", lambda: {"ai": {"enabled": False}})

    monkeypatch.setattr(api_app_module, "get_db", lambda: type("FakeDb", (), {"get_price_record_count": lambda self: 42})())

    monkeypatch.setattr(

        api_app_module,

        "build_procurement_recommendation",

        lambda **kwargs: {

            "summary": {"menu_count": 1, "recommendation_count": 1, "matched_count": 1, "pending_count": 0, "total_cost": 88.0},

            "ingredient_items": [{"menu_name": "蒜蓉西兰花", "ingredient_name": "西兰花"}],

            "items": [

                {

                    "menu_name": "蒜蓉西兰花",

                    "ingredient_name": "西兰花",

                    "identity_key": None,

                    "price_status": "已匹配报价",

                    "estimated_cost": 88.0,

                    "reference_price": 8.8,

                    "recommended_market": "北京新发地",

                    "recommended_site": "北京新发地",

                    "backup_market": None,

                    "backup_site": None,

                    "timing_score": 78,

                    "risk_score": 36,

                    "confidence": 82,

                    "signal_level": "high",

                    "recommended_action": "立即锁价",

                    "reason_summary": "mock recommendation",

                }

            ],

        },

    )

    monkeypatch.setattr(

        api_app_module,

        "build_sales_demo_content",

        lambda latest_df, history_df, scene=None, record_count=None: {

            "scene": scene or "default",

            "hero": {"title": "demo"},

            "proof_points": [{"label": "历史记录", "value": str(record_count or 0)}],

            "scenes": [{"title": "老板驾驶舱", "description": "demo", "highlight": "mock"}],

            "storyline": ["a", "b"],

        },

    )

    monkeypatch.setattr(

        api_app_module,

        "build_pricing_packages",

        lambda: {

            "items": [

                {

                    "name": "经营决策版",

                    "price_band": "主推报价",

                    "target": "采购团队",

                    "recommended": True,

                    "features": ["经营信号"],

                    "cta": "立即报价",

                }

            ]

        },

    )

    client = _create_authenticated_client(monkeypatch)



    recommend_response = client.post("/api/procurement/recommend", json={"menu_text": "蒜蓉西兰花", "diners": 20, "tables": 2})

    demo_response = client.get("/api/sales/demo-content?scene=sales")

    pricing_response = client.get("/api/pricing/packages")



    assert recommend_response.status_code == 200

    assert recommend_response.json()["summary"]["matched_count"] == 1

    assert demo_response.status_code == 200

    assert demo_response.json()["scene"] == "sales"

    assert pricing_response.status_code == 200

    assert pricing_response.json()["items"][0]["recommended"] is True





def test_suppliers_endpoint_returns_supplier_list(monkeypatch):

    class _FakeDb:

        def get_suppliers(self, active_only=True):

            assert active_only is True

            return pd.DataFrame(

                [

                    {

                        "id": 1,

                        "supplier_name": "莲菜档口A",

                        "contact_name": "老王",

                        "contact_phone": "13800000000",

                        "market_scope": "本地市场",

                        "market_category": "干调类",

                        "channel": "微信小程序",

                        "notes": None,

                        "is_active": 1,

                        "created_at": "2026-04-20T09:00:00",

                        "updated_at": "2026-04-20T09:00:00",

                        "quote_count": 3,

                        "latest_quoted_at": "2026-04-20T10:00:00",

                    }

                ]

            )



    db = _FakeDb()

    client = _create_authenticated_client(monkeypatch, db=db)



    response = client.get("/api/suppliers")



    assert response.status_code == 200

    assert response.json()["items"][0]["supplier_name"] == "莲菜档口A"

    assert response.json()["items"][0]["quote_count"] == 3





def test_suppliers_overview_endpoint_returns_category_and_recent_quotes(monkeypatch):

    class _FakeDb:

        def get_suppliers(self, active_only=False):

            assert active_only is False

            return pd.DataFrame(

                [

                    {

                        "id": 1,

                        "supplier_name": "莲菜档口A",

                        "contact_name": "老王",

                        "contact_phone": "13800000000",

                        "market_scope": "本地市场",

                        "market_category": "干调类",

                        "channel": "微信小程序",

                        "notes": None,

                        "is_active": 1,

                        "created_at": "2026-04-20T09:00:00",

                        "updated_at": "2026-04-20T09:00:00",

                        "quote_count": 3,

                        "latest_quoted_at": "2026-04-20T10:00:00",

                    },

                    {

                        "id": 2,

                        "supplier_name": "蔬菜档口B",

                        "contact_name": "小李",

                        "contact_phone": "13900000000",

                        "market_scope": "本地市场",

                        "market_category": "蔬菜类",

                        "channel": "门店直报",

                        "notes": None,

                        "is_active": 0,

                        "created_at": "2026-04-20T09:10:00",

                        "updated_at": "2026-04-20T09:10:00",

                        "quote_count": 1,

                        "latest_quoted_at": "2026-04-20T09:30:00",

                    },

                ]

            )



        def get_supplier_category_summary(self):

            return pd.DataFrame(

                [

                    {

                        "market_category": "干调类",

                        "supplier_count": 1,

                        "active_supplier_count": 1,

                        "quote_count": 3,

                        "latest_quoted_at": "2026-04-20T10:00:00",

                    },

                    {

                        "market_category": "蔬菜类",

                        "supplier_count": 1,

                        "active_supplier_count": 0,

                        "quote_count": 1,

                        "latest_quoted_at": "2026-04-20T09:30:00",

                    },

                ]

            )



        def get_recent_supplier_quotes(self, limit=12):

            assert limit == 8

            return pd.DataFrame(

                [

                    {

                        "supplier_id": 1,

                        "supplier_name": "莲菜档口A",

                        "contact_name": "老王",

                        "contact_phone": "13800000000",

                        "market_scope": "本地市场",

                        "supplier_market_category": "干调类",

                        "supplier_channel": "微信小程序",

                        "price_identity_key": "香菇|干调类|500g",

                        "price_identity_label": "香菇 | 干调类 | 500g",

                        "product_name": "香菇",

                        "category": "干调类",

                        "spec_text": "500g",

                        "market_category": "干调类",

                        "channel": "微信小程序",

                        "quote_price": 17.9,

                        "quote_unit": "斤",

                        "box_price": 214.8,

                        "tax_price": None,

                        "inventory_status": "现货",

                        "remarks": "上午更新",

                        "quoted_by": "老王",

                        "quoted_at": "2026-04-20T10:00:00",

                    }

                ]

            )



    db = _FakeDb()

    client = _create_authenticated_client(monkeypatch, db=db)



    response = client.get("/api/suppliers/overview?limit=8")



    assert response.status_code == 200

    payload = response.json()

    assert payload["summary"]["supplier_count"] == 2

    assert payload["summary"]["active_supplier_count"] == 1

    assert payload["summary"]["inactive_supplier_count"] == 1

    assert payload["summary"]["category_count"] == 2

    assert payload["summary"]["total_quote_count"] == 4

    assert payload["category_items"][0]["market_category"] == "干调类"

    assert payload["recent_quotes"][0]["supplier_name"] == "莲菜档口A"


def test_procurement_account_scopes_suppliers_and_overview_to_bound_suppliers(monkeypatch):

    class _FakeDb:

        def get_suppliers(self, active_only=False):

            return pd.DataFrame(

                [

                    {"id": 1, "supplier_name": "莲菜档口A", "market_category": "干调类", "channel": "微信小程序", "market_scope": "南京市场", "is_active": 1, "quote_count": 3, "latest_quoted_at": "2026-04-20T10:00:00"},

                    {"id": 2, "supplier_name": "蔬菜档口B", "market_category": "蔬菜类", "channel": "门店直报", "market_scope": "南京市场", "is_active": 1, "quote_count": 1, "latest_quoted_at": "2026-04-20T09:30:00"},

                    {"id": 3, "supplier_name": "冻品档口C", "market_category": "冻品类", "channel": "Excel", "market_scope": "南京市场", "is_active": 0, "quote_count": 2, "latest_quoted_at": "2026-04-20T11:00:00"},

                ]

            )

        def get_supplier_quote_records(self, supplier_id, limit=12, offset=0, **kwargs):

            quote_rows = {

                1: [{"supplier_id": 1, "supplier_name": "莲菜档口A", "supplier_market_category": "干调类", "supplier_channel": "微信小程序", "market_scope": "南京市场", "price_identity_key": "香菇|干调类|500g", "quote_price": 17.9, "quoted_at": "2026-04-20T10:00:00"}],

                3: [{"supplier_id": 3, "supplier_name": "冻品档口C", "supplier_market_category": "冻品类", "supplier_channel": "Excel", "market_scope": "南京市场", "price_identity_key": "虾仁|冻品类|5斤", "quote_price": 118.0, "quoted_at": "2026-04-20T11:00:00"}],

            }

            return pd.DataFrame(quote_rows.get(int(supplier_id), []))


    db = _FakeDb()

    client = _create_authenticated_client(
        monkeypatch,
        db=db,
        role="procurement",
        supplier_id=None,
        procurement_supplier_ids=[1, 3],
        username="buyer-nj",
        display_name="南京采购",
    )

    suppliers_response = client.get("/api/suppliers")

    assert suppliers_response.status_code == 200
    assert [item["id"] for item in suppliers_response.json()["items"]] == [1, 3]

    overview_response = client.get("/api/suppliers/overview?limit=8")

    assert overview_response.status_code == 200
    payload = overview_response.json()
    assert payload["summary"]["supplier_count"] == 2
    assert payload["summary"]["total_quote_count"] == 5
    assert [item["market_category"] for item in payload["category_items"]] == ["干调类", "冻品类"]
    assert [item["supplier_name"] for item in payload["recent_quotes"]] == ["冻品档口C", "莲菜档口A"]


def test_procurement_account_binding_rejects_supplier_owned_by_other_procurement_user(tmp_path, monkeypatch):
    db = Database(tmp_path / "procurement_scope_conflict.db")
    db.init_db()

    supplier_a = db.upsert_supplier(
        supplier_name="莲菜档口A",
        contact_name="老王",
        market_scope="南京市场",
        market_category="干调类",
        channel="微信小程序",
    )
    supplier_b = db.upsert_supplier(
        supplier_name="冻品档口B",
        contact_name="小李",
        market_scope="南京市场",
        market_category="冻品类",
        channel="门店直报",
    )

    admin_client = _create_authenticated_client(monkeypatch, db=db)

    create_first_response = admin_client.post(
        "/api/auth/users",
        json={
            "username": "buyer-a",
            "password": "buyer123456",
            "role": "procurement",
            "procurement_supplier_ids": [supplier_a],
            "display_name": "采购A",
            "market_scope": "南京市场",
            "is_active": True,
        },
    )

    assert create_first_response.status_code == 200

    conflict_response = admin_client.post(
        "/api/auth/users",
        json={
            "username": "buyer-b",
            "password": "buyer123456",
            "role": "procurement",
            "procurement_supplier_ids": [supplier_a, supplier_b],
            "display_name": "采购B",
            "market_scope": "南京市场",
            "is_active": True,
        },
    )

    assert conflict_response.status_code == 400
    assert "已绑定其他采购账号" in conflict_response.json()["detail"]


def test_procurement_supplier_creation_rejects_existing_supplier_name(tmp_path, monkeypatch):
    db = Database(tmp_path / "procurement_supplier_duplicate.db")
    db.init_db()

    owned_supplier_id = db.upsert_supplier(
        supplier_name="自有档口",
        contact_name="王哥",
        market_scope="南京市场",
        market_category="蔬菜类",
        channel="门店直报",
    )
    existing_supplier_id = db.upsert_supplier(
        supplier_name="莲菜档口A",
        contact_name="老王",
        market_scope="南京市场",
        market_category="干调类",
        channel="微信小程序",
    )

    procurement_user_id = db.upsert_auth_user(
        username="buyer-owned",
        password_hash=hash_password("buyer123456"),
        role="procurement",
        display_name="采购A",
        is_active=True,
    )
    db.replace_procurement_user_suppliers(procurement_user_id, [owned_supplier_id])
    other_procurement_user_id = db.upsert_auth_user(
        username="buyer-other",
        password_hash=hash_password("buyer123456"),
        role="procurement",
        display_name="采购B",
        is_active=True,
    )
    db.replace_procurement_user_suppliers(other_procurement_user_id, [existing_supplier_id])

    client = _create_authenticated_client(
        monkeypatch,
        db=db,
        role="procurement",
        supplier_id=None,
        procurement_supplier_ids=[owned_supplier_id],
        username="buyer-owned",
        display_name="采购A",
    )

    response = client.post(
        "/api/suppliers",
        json={
            "supplier_name": "莲菜档口A",
            "contact_name": "老王",
            "contact_phone": "13800000000",
            "market_scope": "南京市场",
            "market_category": "干调类",
            "channel": "微信小程序",
            "notes": "应被拦截",
            "is_active": True,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "供应商已存在，请直接编辑现有档案"





def test_auth_password_reset_updates_password_and_returns_session(tmp_path, monkeypatch):

    db = Database(tmp_path / "auth_password_reset.db")

    db.init_db()

    supplier_id = db.upsert_supplier(
        supplier_name="莲菜档口A",
        contact_name="老王",
        market_scope="南京市场",
        market_category="蔬菜类",
        channel="微信小程序",
    )
    db.upsert_auth_user(
        username="supplier-reset",
        password_hash=hash_password("oldpass123"),
        role="supplier",
        supplier_id=supplier_id,
        display_name="莲菜档口A",
        is_active=True,
    )

    monkeypatch.setattr(api_deps_module, "get_db", lambda: db)
    monkeypatch.setattr(api_app_module, "get_db", lambda: db)

    client = TestClient(create_app())

    reset_response = client.post(
        "/api/auth/password/reset",
        json={
            "username": "supplier-reset",
            "current_password": "oldpass123",
            "new_password": "newpass123",
        },
    )

    assert reset_response.status_code == 200
    reset_payload = reset_response.json()
    assert reset_payload["access_token"]
    assert reset_payload["user"]["username"] == "supplier-reset"
    assert reset_payload["user"]["supplier_id"] == supplier_id

    old_login_response = client.post(
        "/api/auth/login",
        json={"username": "supplier-reset", "password": "oldpass123"},
    )
    assert old_login_response.status_code == 401

    new_login_response = client.post(
        "/api/auth/login",
        json={"username": "supplier-reset", "password": "newpass123"},
    )
    assert new_login_response.status_code == 200


def test_registration_request_endpoints_are_not_available(tmp_path, monkeypatch):

    db = Database(tmp_path / "removed_registration_request_endpoints.db")

    db.init_db()

    monkeypatch.setattr(api_deps_module, "get_db", lambda: db)
    monkeypatch.setattr(api_app_module, "get_db", lambda: db)

    public_client = TestClient(create_app())
    admin_client = _create_authenticated_client(monkeypatch, db=db)

    supplier_create_response = public_client.post(
        "/api/supplier-registration-requests",
        json={
            "company_name": "郑州鲜采档口",
            "contact_name": "老刘",
            "contact_phone": "13900139000",
            "username": "fresh-liu",
        },
    )
    procurement_create_response = public_client.post(
        "/api/procurement-registration-requests",
        json={
            "company_name": "Nanjing Buyer Team",
            "contact_name": "Buyer Lead",
            "contact_phone": "13800138000",
            "username": "buyer-nj-apply",
            "market_scope": "南京市场",
        },
    )
    supplier_list_response = admin_client.get("/api/supplier-registration-requests?status=pending")
    procurement_list_response = admin_client.get("/api/procurement-registration-requests?status=pending")

    assert supplier_create_response.status_code == 404
    assert procurement_create_response.status_code == 404
    assert supplier_list_response.status_code == 404
    assert procurement_list_response.status_code == 404


@pytest.mark.skip(reason="public supplier registration request flow removed")
def test_supplier_registration_request_endpoints_cover_submit_and_review(tmp_path, monkeypatch):

    db = Database(tmp_path / "registration_requests.db")

    db.init_db()



    monkeypatch.setattr(api_deps_module, "get_db", lambda: db)

    monkeypatch.setattr(api_app_module, "get_db", lambda: db)



    public_client = TestClient(create_app())

    create_response = public_client.post(

        "/api/supplier-registration-requests",

        json={

            "company_name": "郑州鲜采档口",

            "contact_name": "老刘",

            "contact_phone": "13900139000",

            "username": "fresh-liu",

        },

    )



    assert create_response.status_code == 200

    request_id = create_response.json()["id"]

    assert create_response.json()["status"] == "pending"



    admin_client = _create_authenticated_client(monkeypatch, db=db)

    list_response = admin_client.get("/api/supplier-registration-requests?status=pending")



    assert list_response.status_code == 200

    assert list_response.json()["items"][0]["company_name"] == "郑州鲜采档口"



    approve_response = admin_client.post(

        f"/api/supplier-registration-requests/{request_id}/approve",

        json={

            "supplier_name": "郑州鲜采档口",

            "market_scope": "本地市场",

            "market_category": "蔬菜类",

            "channel": "门店直报",

            "account_password": "fresh123456",

            "review_notes": "资料完整，允许开通",

        },

    )



    assert approve_response.status_code == 200

    assert approve_response.json()["status"] == "approved"

    assert approve_response.json()["supplier_id"] is not None



    supplier_rows = db.get_suppliers(active_only=False)

    assert len(supplier_rows) == 1

    assert supplier_rows.iloc[0]["supplier_name"] == "郑州鲜采档口"





@pytest.mark.skip(reason="public procurement registration request flow removed")
def test_procurement_registration_request_endpoints_cover_submit_review_and_reject(tmp_path, monkeypatch):

    db = Database(tmp_path / "procurement_registration_requests.db")

    db.init_db()

    first_supplier_id = db.upsert_supplier(
        supplier_name="Nanjing Greens",
        contact_name="Alice",
        market_scope="Nanjing Market",
        market_category="Vegetable",
        channel="Mini Program",
    )
    second_supplier_id = db.upsert_supplier(
        supplier_name="Nanjing Frozen",
        contact_name="Bob",
        market_scope="Nanjing Market",
        market_category="Frozen",
        channel="Phone",
    )

    monkeypatch.setattr(api_deps_module, "get_db", lambda: db)

    monkeypatch.setattr(api_app_module, "get_db", lambda: db)

    public_client = TestClient(create_app())

    create_response = public_client.post(
        "/api/procurement-registration-requests",
        json={
            "company_name": "Nanjing Buyer Team",
            "contact_name": "Buyer Lead",
            "contact_phone": "13800138000",
            "username": "buyer-nj-apply",
            "market_scope": "南京市场",
            "requested_supplier_names": "Nanjing Greens, Nanjing Frozen",
        },
    )

    assert create_response.status_code == 200
    request_id = create_response.json()["id"]
    assert create_response.json()["status"] == "pending"
    assert create_response.json()["market_scope"] == "南京市场"

    admin_client = _create_authenticated_client(monkeypatch, db=db)

    list_response = admin_client.get("/api/procurement-registration-requests?status=pending")

    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["username"] == "buyer-nj-apply"

    approve_response = admin_client.post(
        f"/api/procurement-registration-requests/{request_id}/approve",
        json={
            "display_name": "南京采购",
            "market_scope": "南京市场",
            "procurement_supplier_ids": [first_supplier_id, second_supplier_id],
            "account_password": "buyer123456",
            "review_notes": "scope approved",
        },
    )

    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"
    assert approve_response.json()["auth_user_id"] is not None
    assert approve_response.json()["display_name"] == "南京采购"

    auth_rows = db.get_auth_user_by_username("buyer-nj-apply")
    assert len(auth_rows) == 1
    auth_row = auth_rows.iloc[0]
    assert auth_row["role"] == "procurement"
    assert auth_row["market_scope"] == "南京市场"
    assert db.get_procurement_user_supplier_ids(int(auth_row["id"])) == [first_supplier_id, second_supplier_id]

    rejected_create_response = public_client.post(
        "/api/procurement-registration-requests",
        json={
            "company_name": "Henan Buyer Team",
            "contact_name": "Reject Me",
            "contact_phone": "13900139000",
            "username": "buyer-hn-apply",
        },
    )

    assert rejected_create_response.status_code == 200
    rejected_request_id = rejected_create_response.json()["id"]

    reject_response = admin_client.post(
        f"/api/procurement-registration-requests/{rejected_request_id}/reject",
        json={
            "procurement_supplier_ids": [],
            "account_is_active": True,
            "review_notes": "missing supplier scope",
        },
    )

    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "rejected"
    assert reject_response.json()["review_notes"] == "missing supplier scope"


def test_create_supplier_rejects_duplicate_account_username(tmp_path, monkeypatch):

    db = Database(tmp_path / "duplicate_supplier_account.db")

    db.init_db()

    existing_supplier_id = db.upsert_supplier(supplier_name="莲菜档口A")

    existing_user_id = db.upsert_auth_user(

        username="lencai-a",

        password_hash=hash_password("supplier123"),

        role="supplier",

        supplier_id=existing_supplier_id,

        display_name="莲菜档口A",

        is_active=True,

    )

    client = _create_authenticated_client(monkeypatch, db=db)



    response = client.post(

        "/api/suppliers",

        json={

            "supplier_name": "莲菜档口B",

            "is_active": True,

            "account_username": "lencai-a",

            "account_password": "newpass123",

        },

    )



    assert response.status_code == 400

    assert response.json()["detail"] == "登录账号已被其他供应商使用"

    first_auth_rows = db.get_auth_user_by_supplier_id(existing_supplier_id)

    assert first_auth_rows.iloc[0]["id"] == existing_user_id

    assert int(first_auth_rows.iloc[0]["supplier_id"]) == existing_supplier_id




def test_create_supplier_price_endpoint_accepts_supplier_name(monkeypatch):

    captured: dict[str, object] = {}



    class _FakeDb:

        def upsert_supplier(self, **kwargs):

            captured["supplier"] = kwargs

            return 9



        def insert_supplier_price_record(self, **kwargs):

            captured["quote"] = kwargs

            return 12



        def get_supplier_price_record(self, record_id):

            assert record_id == 12

            return pd.DataFrame(

                [

                    {

                        "supplier_id": 9,

                        "supplier_name": "莲菜档口A",

                        "contact_name": "老王",

                        "contact_phone": None,

                        "market_scope": "本地市场",

                        "supplier_market_category": "干调类",

                        "supplier_channel": "微信小程序",

                        "price_identity_key": "香菇|干调类|500g",

                        "price_identity_label": "香菇 | 干调类 | 500g",

                        "product_name": "香菇",

                        "category": "干调类",

                        "spec_text": "500g",

                        "market_category": "干调类",

                        "channel": "微信小程序",

                        "quote_price": 17.9,

                        "quote_unit": "斤",

                        "box_price": 214.8,

                        "tax_price": None,

                        "inventory_status": "现货",

                        "remarks": "上午更新",

                        "quoted_by": "老王",

                        "quoted_at": "2026-04-20T10:00:00",

                    }

                ]

            )



        def get_latest_supplier_quotes(self, identity_key):

            assert identity_key == "香菇|干调类|500g"

            return pd.DataFrame(

                [

                    {

                        "supplier_id": 9,

                        "supplier_name": "莲菜档口A",

                        "contact_name": "老王",

                        "contact_phone": None,

                        "market_scope": "本地市场",

                        "supplier_market_category": "干调类",

                        "supplier_channel": "微信小程序",

                        "price_identity_label": "香菇 | 干调类 | 500g",

                        "product_name": "香菇",

                        "category": "干调类",

                        "spec_text": "500g",

                        "market_category": "干调类",

                        "channel": "微信小程序",

                        "quote_price": 17.9,

                        "quote_unit": "斤",

                        "box_price": 214.8,

                        "tax_price": None,

                        "inventory_status": "现货",

                        "remarks": "上午更新",

                        "quoted_by": "老王",

                        "quoted_at": "2026-04-20T10:00:00",

                    }

                ]

            )



    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())

    monkeypatch.setattr(api_app_module, "get_product_keys_for_identity", lambda _: ["mock-key"])

    monkeypatch.setattr(api_app_module, "get_product_history_identity_df", lambda _: pd.DataFrame())

    client = _create_authenticated_client(monkeypatch)



    response = client.post(

        "/api/supplier-prices",

        json={

            "price_identity_key": "香菇|干调类|500g",

            "supplier_name": "莲菜档口A",

            "contact_name": "老王",

            "market_scope": "本地市场",

            "market_category": "干调类",

            "channel": "微信小程序",

            "product_name": "香菇",

            "price_identity_label": "香菇 | 干调类 | 500g",

            "quote_price": 17.9,

            "quote_unit": "斤",

            "box_price": 214.8,

            "inventory_status": "现货",

            "remarks": "上午更新",

            "quoted_by": "老王",

            "quoted_at": "2026-04-20T10:00:00",

        },

    )



    assert response.status_code == 200

    assert captured["supplier"]["supplier_name"] == "莲菜档口A"

    assert captured["quote"]["quote_price"] == 17.9

    assert response.json()["item"]["comparison_label"] == "待补公开行情"


def test_procurement_account_can_create_quote_for_bound_supplier(monkeypatch):
    captured_quote: dict[str, object] = {}

    class _FakeDb:
        def insert_supplier_price_record(self, **kwargs):
            captured_quote.update(kwargs)
            return 21

        def get_supplier_price_record(self, record_id):
            assert record_id == 21
            return pd.DataFrame([
                {
                    "record_id": 21,
                    "supplier_id": 9,
                    "supplier_name": "莲菜档口A",
                    "price_identity_key": "香菇|干调类|500g",
                    "price_identity_label": "香菇 | 干调类 | 500g",
                    "product_name": "香菇",
                    "category": "干调类",
                    "market_category": "干调类",
                    "quote_price": 17.9,
                    "quote_unit": "斤",
                    "quoted_by": "南京采购",
                    "quoted_at": "2026-04-20T10:00:00",
                }
            ])

        def get_latest_supplier_quotes(self, *args, **kwargs):
            return pd.DataFrame([
                {
                    "record_id": 21,
                    "supplier_id": 9,
                    "supplier_name": "莲菜档口A",
                    "price_identity_key": "香菇|干调类|500g",
                    "price_identity_label": "香菇 | 干调类 | 500g",
                    "product_name": "香菇",
                    "category": "干调类",
                    "market_category": "干调类",
                    "quote_price": 17.9,
                    "quote_unit": "斤",
                    "quoted_by": "南京采购",
                    "quoted_at": "2026-04-20T10:00:00",
                }
            ])

    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())
    monkeypatch.setattr(api_app_module, "get_product_keys_for_identity", lambda _: ["mock-key"])
    monkeypatch.setattr(api_app_module, "get_product_history_identity_df", lambda _: pd.DataFrame())
    client = _create_authenticated_client(
        monkeypatch,
        role="procurement",
        supplier_id=None,
        procurement_supplier_ids=[9],
        display_name="南京采购",
    )

    response = client.post(
        "/api/supplier-prices",
        json={
            "supplier_id": 9,
            "price_identity_key": "香菇|干调类|500g",
            "price_identity_label": "香菇 | 干调类 | 500g",
            "product_name": "香菇",
            "market_category": "干调类",
            "quote_price": 17.9,
            "quote_unit": "斤",
        },
    )

    assert response.status_code == 200
    assert captured_quote["supplier_id"] == 9
    assert captured_quote["quoted_by"] == "南京采购"
    assert response.json()["item"]["supplier_id"] == 9





def test_invalidate_supplier_price_endpoint_returns_updated_quote(monkeypatch):

    captured: dict[str, object] = {}

    read_count = {"value": 0}



    class _FakeDb:

        def invalidate_supplier_price_record(self, record_id, reason=None):

            captured["record_id"] = record_id

            captured["reason"] = reason

            return 12



        def insert_supplier_quote_action(self, **kwargs):

            captured["action"] = kwargs

            return 100



        def get_supplier_price_record(self, record_id):

            assert record_id == 12

            read_count["value"] += 1

            return pd.DataFrame(

                [

                    {

                        "id": 12,

                        "supplier_id": 9,

                        "supplier_name": "莲菜档口A",

                        "contact_name": "老王",

                        "contact_phone": None,

                        "market_scope": "本地市场",

                        "supplier_market_category": "干调类",

                        "supplier_channel": "微信小程序",

                        "price_identity_key": "香菇|干调类|500g",

                        "price_identity_label": "香菇 | 干调类 | 500g",

                        "product_name": "香菇",

                        "category": "干调类",

                        "spec_text": "500g",

                        "market_category": "干调类",

                        "channel": "微信小程序",

                        "quote_price": 17.9,

                        "quote_unit": "斤",

                        "box_price": 214.8,

                        "tax_price": None,

                        "inventory_status": "现货",

                        "remarks": "上午更新",

                        "quoted_by": "老王",

                        "status": "active" if read_count["value"] <= 2 else "invalidated",

                        "invalidated_at": None if read_count["value"] <= 2 else "2026-04-21T10:30:00",

                        "invalidated_reason": None if read_count["value"] <= 2 else "录错价格",

                        "quoted_at": "2026-04-20T10:00:00",

                    }

                ]

            )



    db = _FakeDb()

    monkeypatch.setattr(api_app_module, "get_db", lambda: db)

    client = _create_authenticated_client(monkeypatch, db=db)



    response = client.post("/api/supplier-prices/12/invalidate", json={"reason": "录错价格"})



    assert response.status_code == 200

    assert captured["record_id"] == 12

    assert captured["reason"] == "录错价格"

    assert captured["action"]["action_type"] == "invalidate"

    assert captured["action"]["operator_name"] == "测试账号"

    assert captured["action"]["action_payload"]["previous_status"] == "active"

    assert captured["action"]["action_payload"]["next_invalidated_reason"] == "录错价格"

    assert response.json()["item"]["status"] == "invalidated"

    assert response.json()["item"]["invalidated_reason"] == "录错价格"





def test_invalidate_supplier_price_endpoint_allows_updating_reason_for_invalidated_quote(monkeypatch):

    captured: dict[str, object] = {}



    class _FakeDb:

        def invalidate_supplier_price_record(self, record_id, reason=None):

            captured["record_id"] = record_id

            captured["reason"] = reason

            return 12



        def insert_supplier_quote_action(self, **kwargs):

            captured["action"] = kwargs

            return 101



        def get_supplier_price_record(self, record_id):

            assert record_id == 12

            return pd.DataFrame(

                [

                    {

                        "id": 12,

                        "supplier_id": 9,

                        "supplier_name": "莲菜档口A",

                        "contact_name": "老王",

                        "contact_phone": None,

                        "market_scope": "本地市场",

                        "supplier_market_category": "干调类",

                        "supplier_channel": "微信小程序",

                        "price_identity_key": "香菇|干调类|500g",

                        "price_identity_label": "香菇 | 干调类 | 500g",

                        "product_name": "香菇",

                        "category": "干调类",

                        "spec_text": "500g",

                        "market_category": "干调类",

                        "channel": "微信小程序",

                        "quote_price": 17.9,

                        "quote_unit": "斤",

                        "box_price": 214.8,

                        "tax_price": None,

                        "inventory_status": "现货",

                        "remarks": "上午更新",

                        "quoted_by": "老王",

                        "status": "invalidated",

                        "invalidated_at": "2026-04-21T10:30:00",

                        "invalidated_reason": "规格填错",

                        "quoted_at": "2026-04-20T10:00:00",

                    }

                ]

            )



    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())

    client = _create_authenticated_client(monkeypatch)



    response = client.post("/api/supplier-prices/12/invalidate", json={"reason": "规格填错", "operator_name": "刘洋"})



    assert response.status_code == 200

    assert captured["record_id"] == 12

    assert captured["reason"] == "规格填错"

    assert captured["action"]["action_type"] == "update_invalidation_reason"

    assert captured["action"]["operator_name"] == "测试账号"

    assert captured["action"]["action_payload"]["previous_status"] == "invalidated"

    assert captured["action"]["action_payload"]["previous_invalidated_reason"] == "规格填错"

    assert captured["action"]["action_payload"]["next_invalidated_reason"] == "规格填错"

    assert response.json()["item"]["status"] == "invalidated"

    assert response.json()["item"]["invalidated_reason"] == "规格填错"





def test_create_supplier_price_endpoint_logs_copy_action_when_source_record_is_provided(monkeypatch):

    captured: dict[str, object] = {}



    class _FakeDb:

        def insert_supplier_price_record(self, **kwargs):

            captured["quote"] = kwargs

            return 18



        def insert_supplier_quote_action(self, **kwargs):

            captured["action"] = kwargs

            return 88



        def get_supplier_price_record(self, record_id):

            assert record_id == 18

            return pd.DataFrame(

                [

                    {

                        "id": 18,

                        "supplier_id": 9,

                        "supplier_name": "莲菜档口A",

                        "contact_name": "老王",

                        "contact_phone": None,

                        "market_scope": "本地市场",

                        "supplier_market_category": "干调类",

                        "supplier_channel": "微信小程序",

                        "price_identity_key": "香菇|干调类|500g",

                        "price_identity_label": "香菇 | 干调类 | 500g",

                        "product_name": "香菇",

                        "category": "干调类",

                        "spec_text": "500g",

                        "market_category": "干调类",

                        "channel": "微信小程序",

                        "quote_price": 17.9,

                        "quote_unit": "斤",

                        "box_price": 214.8,

                        "tax_price": None,

                        "inventory_status": "现货",

                        "remarks": "复制自历史报价",

                        "quoted_by": "老王",

                        "status": "active",

                        "invalidated_at": None,

                        "invalidated_reason": None,

                        "quoted_at": "2026-04-20T10:00:00",

                    }

                ]

            )



        def get_latest_supplier_quotes(self, identity_key):

            assert identity_key == "香菇|干调类|500g"

            return pd.DataFrame()



    db = _FakeDb()

    monkeypatch.setattr(api_app_module, "get_db", lambda: db)

    monkeypatch.setattr(api_app_module, "get_product_keys_for_identity", lambda _: ["mock-key"])

    monkeypatch.setattr(api_app_module, "get_product_history_identity_df", lambda _: pd.DataFrame())

    client = _create_authenticated_client(monkeypatch, db=db)



    response = client.post(

        "/api/supplier-prices",

        json={

            "price_identity_key": "香菇|干调类|500g",

            "source_record_id": 12,

            "supplier_id": 9,

            "supplier_name": "莲菜档口A",

            "contact_name": "老王",

            "market_scope": "本地市场",

            "market_category": "干调类",

            "channel": "微信小程序",

            "product_name": "香菇",

            "price_identity_label": "香菇 | 干调类 | 500g",

            "quote_price": 17.9,

            "quote_unit": "斤",

            "box_price": 214.8,

            "inventory_status": "现货",

            "remarks": "复制自历史报价",

            "quoted_by": "老王",

            "quoted_at": "2026-04-20T10:00:00",

        },

    )



    assert response.status_code == 200

    assert captured["quote"]["supplier_id"] == 9

    assert captured["action"]["action_type"] == "copy_as_new"

    assert captured["action"]["record_id"] == 12

    assert captured["action"]["target_record_id"] == 18

    assert captured["action"]["operator_name"] == "测试账号"





def test_import_supplier_prices_endpoint_returns_summary_and_logs_action(monkeypatch):

    captured: dict[str, object] = {"quotes": []}



    class _FakeDb:

        def insert_supplier_price_record(self, **kwargs):

            captured["quotes"].append(kwargs)

            return 100 + len(captured["quotes"])



        def get_supplier_price_record(self, record_id):

            quote = captured["quotes"][record_id - 101]

            return pd.DataFrame(

                [

                    {

                        "id": record_id,

                        "supplier_id": quote["supplier_id"],

                        "supplier_name": "莲菜档口A",

                        "contact_name": "老王",

                        "contact_phone": None,

                        "market_scope": "本地市场",

                        "supplier_market_category": quote["market_category"],

                        "supplier_channel": quote["channel"],

                        "price_identity_key": quote["price_identity_key"],

                        "price_identity_label": quote["price_identity_label"],

                        "product_name": quote["product_name"],

                        "category": quote["category"],

                        "spec_text": quote["spec_text"],

                        "market_category": quote["market_category"],

                        "channel": quote["channel"],

                        "quote_price": quote["quote_price"],

                        "quote_unit": quote["quote_unit"],

                        "box_price": quote["box_price"],

                        "tax_price": quote["tax_price"],

                        "inventory_status": quote["inventory_status"],

                        "remarks": quote["remarks"],

                        "quoted_by": quote["quoted_by"],

                        "status": "active",

                        "invalidated_at": None,

                        "invalidated_reason": None,

                        "quoted_at": quote["quoted_at"],

                    }

                ]

            )



        def insert_supplier_quote_action(self, **kwargs):

            captured["action"] = kwargs

            return 301



    db = _FakeDb()

    monkeypatch.setattr(api_app_module, "get_db", lambda: db)

    monkeypatch.setattr(api_app_module, "get_product_keys_for_identity", lambda _: ["mock-key"])

    client = _create_authenticated_client(monkeypatch, db=db)



    response = client.post(

        "/api/supplier-prices/import",

        json={

            "supplier_id": 9,

            "operator_name": "导入专员",

            "file_name": "报价导入.xlsx",

            "items": [

                {

                    "row_number": 2,

                    "price_identity_key": "香菇|干调类|500g",

                    "price_identity_label": "香菇 | 干调类 | 500g",

                    "product_name": "香菇",

                    "category": "干调类",

                    "spec_text": "500g",

                    "quote_price": 17.9,

                    "quote_unit": "斤",

                    "box_price": 214.8,

                    "tax_price": 18.3,

                    "inventory_status": "现货",

                    "remarks": "上午更新",

                    "quoted_at": "2026-04-20T10:00:00",

                    "channel": "微信小程序",

                    "market_category": "干调类",

                },

                {

                    "price_identity_key": "木耳|干调类|250g",

                    "price_identity_label": "木耳 | 干调类 | 250g",

                    "product_name": "木耳",

                    "quote_price": 22.5,

                    "quote_unit": "袋",

                    "remarks": "下午更新",

                    "quoted_by": "老王",

                    "quoted_at": "2026-04-20T11:00:00",

                    "channel": "微信小程序",

                    "market_category": "干调类",

                },

            ],

        },

    )



    assert response.status_code == 200

    assert response.json()["total_count"] == 2

    assert response.json()["success_count"] == 2

    assert response.json()["failed_count"] == 0

    assert response.json()["skipped_count"] == 0

    assert response.json()["items"][0]["row_number"] == 2

    assert response.json()["items"][0]["status"] == "success"

    assert response.json()["items"][0]["record_id"] == 101

    assert captured["quotes"][0]["quoted_by"] == "测试账号"

    assert captured["quotes"][1]["quoted_by"] == "测试账号"

    assert captured["action"]["action_type"] == "import_quotes"

    assert captured["action"]["record_id"] == 101

    assert captured["action"]["operator_name"] == "测试账号"

    assert captured["action"]["action_payload"]["file_name"] == "报价导入.xlsx"

    assert captured["action"]["action_payload"]["import_mode"] == "append"

    assert captured["action"]["action_payload"]["success_count"] == 2

    assert captured["action"]["action_payload"]["failed_count"] == 0

    assert captured["action"]["action_payload"]["skipped_count"] == 0





def test_import_supplier_prices_endpoint_supports_partial_failures(monkeypatch):

    captured: dict[str, object] = {"quotes": []}



    class _FakeDb:

        def insert_supplier_price_record(self, **kwargs):

            captured["quotes"].append(kwargs)

            return 200 + len(captured["quotes"])



        def get_supplier_price_record(self, record_id):

            quote = captured["quotes"][record_id - 201]

            return pd.DataFrame(

                [

                    {

                        "id": record_id,

                        "supplier_id": quote["supplier_id"],

                        "supplier_name": "莲菜档口A",

                        "contact_name": "老王",

                        "contact_phone": None,

                        "market_scope": "本地市场",

                        "supplier_market_category": quote["market_category"],

                        "supplier_channel": quote["channel"],

                        "price_identity_key": quote["price_identity_key"],

                        "price_identity_label": quote["price_identity_label"],

                        "product_name": quote["product_name"],

                        "category": quote["category"],

                        "spec_text": quote["spec_text"],

                        "market_category": quote["market_category"],

                        "channel": quote["channel"],

                        "quote_price": quote["quote_price"],

                        "quote_unit": quote["quote_unit"],

                        "box_price": quote["box_price"],

                        "tax_price": quote["tax_price"],

                        "inventory_status": quote["inventory_status"],

                        "remarks": quote["remarks"],

                        "quoted_by": quote["quoted_by"],

                        "status": "active",

                        "invalidated_at": None,

                        "invalidated_reason": None,

                        "quoted_at": quote["quoted_at"],

                    }

                ]

            )



        def insert_supplier_quote_action(self, **kwargs):

            captured["action"] = kwargs

            return 401



    db = _FakeDb()

    monkeypatch.setattr(api_app_module, "get_db", lambda: db)

    monkeypatch.setattr(api_app_module, "get_product_keys_for_identity", lambda _: ["mock-key"])

    client = _create_authenticated_client(monkeypatch, db=db)



    response = client.post(

        "/api/supplier-prices/import",

        json={

            "supplier_id": 9,

            "operator_name": "导入专员",

            "file_name": "报价导入.csv",

            "items": [

                {

                    "row_number": 7,

                    "price_identity_label": "缺失主键的行",

                    "product_name": "异常行",

                    "quote_price": 10.5,

                },

                {

                    "price_identity_key": "白芷|干调类|500g",

                    "price_identity_label": "白芷 | 干调类 | 500g",

                    "product_name": "白芷",

                    "category": "干调类",

                    "quote_price": 31.2,

                    "quote_unit": "斤",

                    "quoted_at": "2026-04-20T12:00:00",

                    "channel": "微信小程序",

                    "market_category": "干调类",

                },

            ],

        },

    )



    assert response.status_code == 200

    assert response.json()["total_count"] == 2

    assert response.json()["success_count"] == 1

    assert response.json()["failed_count"] == 1

    assert response.json()["skipped_count"] == 0

    assert response.json()["items"][0]["row_number"] == 7

    assert response.json()["items"][0]["status"] == "failed"

    assert response.json()["items"][0]["failure_reason"] == "缺少 price_identity_key"

    assert response.json()["items"][1]["status"] == "success"

    assert len(captured["quotes"]) == 1

    assert captured["action"]["action_payload"]["import_mode"] == "append"

    assert captured["action"]["action_payload"]["failed_count"] == 1

    assert captured["action"]["action_payload"]["failure_examples"][0]["row_number"] == 7





def test_import_supplier_prices_endpoint_skips_duplicates_when_requested(monkeypatch):

    captured: dict[str, object] = {}



    class _FakeDb:

        def get_latest_supplier_quote_for_supplier(self, supplier_id, price_identity_key):

            captured["latest_lookup"] = {

                "supplier_id": supplier_id,

                "price_identity_key": price_identity_key,

            }

            return pd.DataFrame(

                [

                    {

                        "id": 88,

                        "supplier_id": supplier_id,

                        "supplier_name": "莲菜档口A",

                        "contact_name": "老王",

                        "contact_phone": None,

                        "market_scope": "本地市场",

                        "supplier_market_category": "干调类",

                        "supplier_channel": "微信小程序",

                        "price_identity_key": price_identity_key,

                        "price_identity_label": "香菇 | 干调类 | 500g",

                        "product_name": "香菇",

                        "category": "干调类",

                        "spec_text": "500g",

                        "market_category": "干调类",

                        "channel": "微信小程序",

                        "quote_price": 17.9,

                        "quote_unit": "斤",

                        "box_price": 214.8,

                        "tax_price": None,

                        "inventory_status": "现货",

                        "remarks": "已存在有效报价",

                        "quoted_by": "老王",

                        "status": "active",

                        "invalidated_at": None,

                        "invalidated_reason": None,

                        "quoted_at": "2026-04-20T10:00:00",

                    }

                ]

            )



        def insert_supplier_price_record(self, **kwargs):

            raise AssertionError("skip_duplicate 不应写入新报价")



        def insert_supplier_quote_action(self, **kwargs):

            captured["action"] = kwargs

            return 501



    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())

    client = _create_authenticated_client(monkeypatch)



    response = client.post(

        "/api/supplier-prices/import",

        json={

            "supplier_id": 9,

            "operator_name": "导入专员",

            "file_name": "报价导入.xlsx",

            "import_mode": "skip_duplicate",

            "items": [

                {

                    "row_number": 3,

                    "price_identity_key": "香菇|干调类|500g",

                    "price_identity_label": "香菇 | 干调类 | 500g",

                    "product_name": "香菇",

                    "quote_price": 17.9,

                    "quote_unit": "斤",

                    "box_price": 214.8,

                    "inventory_status": "现货",

                    "remarks": "已存在有效报价",

                    "channel": "微信小程序",

                    "market_category": "干调类",

                    "market_scope": "本地市场",

                }

            ],

        },

    )



    assert response.status_code == 200

    assert response.json()["total_count"] == 1

    assert response.json()["success_count"] == 0

    assert response.json()["failed_count"] == 0

    assert response.json()["skipped_count"] == 1

    assert response.json()["items"][0]["status"] == "skipped"

    assert response.json()["items"][0]["record_id"] == 88

    assert captured["latest_lookup"] == {

        "supplier_id": 9,

        "price_identity_key": "香菇|干调类|500g",

    }

    assert captured["action"]["record_id"] is None

    assert captured["action"]["action_payload"]["import_mode"] == "skip_duplicate"

    assert captured["action"]["action_payload"]["skipped_count"] == 1

    assert captured["action"]["action_payload"]["skipped_examples"][0]["existing_record_id"] == 88





def test_import_supplier_prices_endpoint_supports_configurable_duplicate_match_fields(monkeypatch):

    captured: dict[str, object] = {}



    class _FakeDb:

        def get_latest_supplier_quote_for_supplier(self, supplier_id, price_identity_key):

            return pd.DataFrame(

                [

                    {

                        "id": 98,

                        "supplier_id": supplier_id,

                        "supplier_name": "莲菜档口A",

                        "contact_name": "老王",

                        "contact_phone": None,

                        "market_scope": "本地市场",

                        "supplier_market_category": "干调类",

                        "supplier_channel": "微信小程序",

                        "price_identity_key": price_identity_key,

                        "price_identity_label": "香菇 | 干调类 | 500g",

                        "product_name": "香菇",

                        "category": "干调类",

                        "spec_text": "500g",

                        "market_category": "干调类",

                        "channel": "微信小程序",

                        "quote_price": 17.9,

                        "quote_unit": "斤",

                        "box_price": 214.8,

                        "tax_price": None,

                        "inventory_status": "现货",

                        "remarks": "旧备注",

                        "quoted_by": "老王",

                        "status": "active",

                        "invalidated_at": None,

                        "invalidated_reason": None,

                        "quoted_at": "2026-04-20T10:00:00",

                    }

                ]

            )



        def insert_supplier_price_record(self, **kwargs):

            raise AssertionError("配置化重复判定命中后不应写入新报价")



        def insert_supplier_quote_action(self, **kwargs):

            captured["action"] = kwargs

            return 701



    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())

    client = _create_authenticated_client(monkeypatch)



    response = client.post(

        "/api/supplier-prices/import",

        json={

            "supplier_id": 9,

            "operator_name": "导入专员",

            "file_name": "规则导入.xlsx",

            "import_mode": "skip_duplicate",

            "duplicate_match_fields": ["quote_price", "quote_unit", "channel", "market_category", "market_scope"],

            "items": [

                {

                    "row_number": 6,

                    "price_identity_key": "香菇|干调类|500g",

                    "price_identity_label": "香菇 | 干调类 | 500g",

                    "product_name": "香菇",

                    "quote_price": 17.9,

                    "quote_unit": "斤",

                    "box_price": 214.8,

                    "inventory_status": "现货",

                    "remarks": "新备注",

                    "channel": "微信小程序",

                    "market_category": "干调类",

                    "market_scope": "本地市场",

                }

            ],

        },

    )



    assert response.status_code == 200

    assert response.json()["items"][0]["status"] == "skipped"

    assert response.json()["items"][0]["record_id"] == 98

    assert response.json()["items"][0]["duplicate_match_fields"] == [

        "quote_price",

        "quote_unit",

        "channel",

        "market_category",

        "market_scope",

    ]

    assert captured["action"]["action_payload"]["duplicate_match_fields"] == [

        "quote_price",

        "quote_unit",

        "channel",

        "market_category",

        "market_scope",

    ]





def test_preview_import_supplier_prices_endpoint_returns_duplicate_and_invalid_rows(monkeypatch):

    captured: dict[str, object] = {}



    class _FakeDb:

        def get_latest_supplier_quote_for_supplier(self, supplier_id, price_identity_key):

            captured.setdefault("lookups", []).append(

                {

                    "supplier_id": supplier_id,

                    "price_identity_key": price_identity_key,

                }

            )

            if price_identity_key != "香菇|干调类|500g":

                return pd.DataFrame()

            return pd.DataFrame(

                [

                    {

                        "id": 88,

                        "supplier_id": supplier_id,

                        "supplier_name": "莲菜档口A",

                        "contact_name": "老王",

                        "contact_phone": None,

                        "market_scope": "本地市场",

                        "supplier_market_category": "干调类",

                        "supplier_channel": "微信小程序",

                        "price_identity_key": price_identity_key,

                        "price_identity_label": "香菇 | 干调类 | 500g",

                        "product_name": "香菇",

                        "category": "干调类",

                        "spec_text": "500g",

                        "market_category": "干调类",

                        "channel": "微信小程序",

                        "quote_price": 17.9,

                        "quote_unit": "斤",

                        "box_price": 214.8,

                        "tax_price": None,

                        "inventory_status": "现货",

                        "remarks": "已存在有效报价",

                        "quoted_by": "老王",

                        "status": "active",

                        "invalidated_at": None,

                        "invalidated_reason": None,

                        "quoted_at": "2026-04-20T10:00:00",

                    }

                ]

            )



    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())

    client = _create_authenticated_client(monkeypatch)



    response = client.post(

        "/api/supplier-prices/import-preview",

        json={

            "supplier_id": 9,

            "import_mode": "skip_duplicate",

            "items": [

                {

                    "row_number": 3,

                    "price_identity_key": "香菇|干调类|500g",

                    "quote_price": 17.9,

                    "quote_unit": "斤",

                    "box_price": 214.8,

                    "inventory_status": "现货",

                    "remarks": "已存在有效报价",

                    "channel": "微信小程序",

                    "market_category": "干调类",

                    "market_scope": "本地市场",

                },

                {

                    "row_number": 4,

                    "price_identity_label": "缺少主键",

                    "quote_price": 20.0,

                },

            ],

        },

    )



    assert response.status_code == 200

    assert response.json()["items"][0]["preview_status"] == "skip_duplicate"

    assert response.json()["items"][0]["existing_record_id"] == 88

    assert response.json()["items"][1]["preview_status"] == "invalid"

    assert response.json()["items"][1]["preview_reason"] == "缺少 price_identity_key"





def test_preview_import_supplier_prices_endpoint_supports_configurable_duplicate_fields(monkeypatch):

    class _FakeDb:

        def get_latest_supplier_quote_for_supplier(self, supplier_id, price_identity_key):

            return pd.DataFrame(

                [

                    {

                        "id": 99,

                        "supplier_id": supplier_id,

                        "supplier_name": "莲菜档口A",

                        "contact_name": "老王",

                        "contact_phone": None,

                        "market_scope": "本地市场",

                        "supplier_market_category": "干调类",

                        "supplier_channel": "微信小程序",

                        "price_identity_key": price_identity_key,

                        "price_identity_label": "香菇 | 干调类 | 500g",

                        "product_name": "香菇",

                        "category": "干调类",

                        "spec_text": "500g",

                        "market_category": "干调类",

                        "channel": "微信小程序",

                        "quote_price": 17.9,

                        "quote_unit": "斤",

                        "box_price": 214.8,

                        "tax_price": None,

                        "inventory_status": "现货",

                        "remarks": "旧备注",

                        "quoted_by": "老王",

                        "status": "active",

                        "invalidated_at": None,

                        "invalidated_reason": None,

                        "quoted_at": "2026-04-20T10:00:00",

                    }

                ]

            )



    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())

    client = _create_authenticated_client(monkeypatch)



    response = client.post(

        "/api/supplier-prices/import-preview",

        json={

            "supplier_id": 9,

            "import_mode": "skip_duplicate",

            "duplicate_match_fields": ["quote_price", "quote_unit", "channel", "market_category", "market_scope"],

            "items": [

                {

                    "row_number": 8,

                    "price_identity_key": "香菇|干调类|500g",

                    "quote_price": 17.9,

                    "quote_unit": "斤",

                    "box_price": 214.8,

                    "inventory_status": "现货",

                    "remarks": "新备注",

                    "channel": "微信小程序",

                    "market_category": "干调类",

                    "market_scope": "本地市场",

                }

            ],

        },

    )



    assert response.status_code == 200

    assert response.json()["items"][0]["preview_status"] == "skip_duplicate"

    assert response.json()["items"][0]["existing_record_id"] == 99

    assert response.json()["items"][0]["duplicate_match_fields"] == [

        "quote_price",

        "quote_unit",

        "channel",

        "market_category",

        "market_scope",

    ]





def test_preview_import_supplier_prices_endpoint_returns_abnormal_hint(monkeypatch):

    class _FakeDb:

        def get_latest_supplier_quote_for_supplier(self, supplier_id, price_identity_key):

            return pd.DataFrame(

                [

                    {

                        "id": 108,

                        "supplier_id": supplier_id,

                        "supplier_name": "蔬菜档口B",

                        "contact_name": "小李",

                        "contact_phone": None,

                        "market_scope": "本地市场",

                        "supplier_market_category": "蔬菜类",

                        "supplier_channel": "门店直报",

                        "price_identity_key": price_identity_key,

                        "price_identity_label": "菠菜 | 蔬菜类 | 斤",

                        "product_name": "菠菜",

                        "category": "蔬菜类",

                        "spec_text": "斤",

                        "market_category": "蔬菜类",

                        "channel": "门店直报",

                        "quote_price": 10.0,

                        "quote_unit": "斤",

                        "box_price": None,

                        "tax_price": None,

                        "inventory_status": "现货",

                        "remarks": "旧报价",

                        "quoted_by": "小李",

                        "status": "active",

                        "invalidated_at": None,

                        "invalidated_reason": None,

                        "quoted_at": "2026-04-20T09:00:00",

                    }

                ]

            )



    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())

    client = _create_authenticated_client(monkeypatch)



    response = client.post(

        "/api/supplier-prices/import-preview",

        json={

            "supplier_id": 5,

            "import_mode": "append",

            "abnormal_change_ratio_threshold": 0.2,

            "items": [

                {

                    "row_number": 2,

                    "price_identity_key": "菠菜|蔬菜类|斤",

                    "quote_price": 13.0,

                    "quote_unit": "斤",

                }

            ],

        },

    )



    assert response.status_code == 200

    assert response.json()["items"][0]["preview_status"] == "append"

    assert response.json()["items"][0]["abnormal_change_ratio"] == 0.3

    assert "30.00%" in response.json()["items"][0]["abnormal_change_hint"]





def test_preview_import_supplier_prices_endpoint_marks_override_rows(monkeypatch):

    class _FakeDb:

        def get_latest_supplier_quote_for_supplier(self, supplier_id, price_identity_key):

            return pd.DataFrame(

                [

                    {

                        "id": 77,

                        "supplier_id": supplier_id,

                        "supplier_name": "莲菜档口A",

                        "contact_name": "老王",

                        "contact_phone": None,

                        "market_scope": "本地市场",

                        "supplier_market_category": "干调类",

                        "supplier_channel": "微信小程序",

                        "price_identity_key": price_identity_key,

                        "price_identity_label": "香菇 | 干调类 | 500g",

                        "product_name": "香菇",

                        "category": "干调类",

                        "spec_text": "500g",

                        "market_category": "干调类",

                        "channel": "微信小程序",

                        "quote_price": 18.6,

                        "quote_unit": "斤",

                        "box_price": None,

                        "tax_price": None,

                        "inventory_status": "现货",

                        "remarks": "旧报价",

                        "quoted_by": "老王",

                        "status": "active",

                        "invalidated_at": None,

                        "invalidated_reason": None,

                        "quoted_at": "2026-04-20T09:00:00",

                    }

                ]

            )



    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())

    client = _create_authenticated_client(monkeypatch)



    response = client.post(

        "/api/supplier-prices/import-preview",

        json={

            "supplier_id": 9,

            "import_mode": "override_latest",

            "items": [

                {

                    "row_number": 5,

                    "price_identity_key": "香菇|干调类|500g",

                    "quote_price": 16.9,

                    "quote_unit": "斤",

                }

            ],

        },

    )



    assert response.status_code == 200

    assert response.json()["items"][0]["preview_status"] == "override_latest"

    assert response.json()["items"][0]["existing_record_id"] == 77





def test_import_supplier_prices_endpoint_overrides_latest_when_requested(monkeypatch):

    captured: dict[str, object] = {"quotes": [], "invalidations": []}



    class _FakeDb:

        def get_latest_supplier_quote_for_supplier(self, supplier_id, price_identity_key):

            captured["latest_lookup"] = {

                "supplier_id": supplier_id,

                "price_identity_key": price_identity_key,

            }

            return pd.DataFrame(

                [

                    {

                        "id": 77,

                        "supplier_id": supplier_id,

                        "supplier_name": "莲菜档口A",

                        "contact_name": "老王",

                        "contact_phone": None,

                        "market_scope": "本地市场",

                        "supplier_market_category": "干调类",

                        "supplier_channel": "微信小程序",

                        "price_identity_key": price_identity_key,

                        "price_identity_label": "香菇 | 干调类 | 500g",

                        "product_name": "香菇",

                        "category": "干调类",

                        "spec_text": "500g",

                        "market_category": "干调类",

                        "channel": "微信小程序",

                        "quote_price": 18.6,

                        "quote_unit": "斤",

                        "box_price": None,

                        "tax_price": None,

                        "inventory_status": "现货",

                        "remarks": "旧报价",

                        "quoted_by": "老王",

                        "status": "active",

                        "invalidated_at": None,

                        "invalidated_reason": None,

                        "quoted_at": "2026-04-20T09:00:00",

                    }

                ]

            )



        def invalidate_supplier_quotes_by_identity(self, supplier_id, price_identity_key, reason=None):

            captured["invalidations"].append(

                {

                    "supplier_id": supplier_id,

                    "price_identity_key": price_identity_key,

                    "reason": reason,

                }

            )

            return [77, 66]



        def insert_supplier_price_record(self, **kwargs):

            captured["quotes"].append(kwargs)

            return 301



        def get_supplier_price_record(self, record_id):

            assert record_id == 301

            quote = captured["quotes"][0]

            return pd.DataFrame(

                [

                    {

                        "id": record_id,

                        "supplier_id": quote["supplier_id"],

                        "supplier_name": "莲菜档口A",

                        "contact_name": "老王",

                        "contact_phone": None,

                        "market_scope": "本地市场",

                        "supplier_market_category": quote["market_category"],

                        "supplier_channel": quote["channel"],

                        "price_identity_key": quote["price_identity_key"],

                        "price_identity_label": quote["price_identity_label"],

                        "product_name": quote["product_name"],

                        "category": quote["category"],

                        "spec_text": quote["spec_text"],

                        "market_category": quote["market_category"],

                        "channel": quote["channel"],

                        "quote_price": quote["quote_price"],

                        "quote_unit": quote["quote_unit"],

                        "box_price": quote["box_price"],

                        "tax_price": quote["tax_price"],

                        "inventory_status": quote["inventory_status"],

                        "remarks": quote["remarks"],

                        "quoted_by": quote["quoted_by"],

                        "status": "active",

                        "invalidated_at": None,

                        "invalidated_reason": None,

                        "quoted_at": quote["quoted_at"],

                    }

                ]

            )



        def insert_supplier_quote_action(self, **kwargs):

            captured["action"] = kwargs

            return 601



    db = _FakeDb()

    monkeypatch.setattr(api_app_module, "get_db", lambda: db)

    monkeypatch.setattr(api_app_module, "get_product_keys_for_identity", lambda _: ["mock-key"])

    client = _create_authenticated_client(monkeypatch, db=db)



    response = client.post(

        "/api/supplier-prices/import",

        json={

            "supplier_id": 9,

            "operator_name": "导入专员",

            "file_name": "覆盖导入.xlsx",

            "import_mode": "override_latest",

            "items": [

                {

                    "row_number": 5,

                    "price_identity_key": "香菇|干调类|500g",

                    "price_identity_label": "香菇 | 干调类 | 500g",

                    "product_name": "香菇",

                    "category": "干调类",

                    "spec_text": "500g",

                    "quote_price": 16.9,

                    "quote_unit": "斤",

                    "quoted_at": "2026-04-21T10:00:00",

                    "channel": "微信小程序",

                    "market_category": "干调类",

                }

            ],

        },

    )



    assert response.status_code == 200

    assert response.json()["total_count"] == 1

    assert response.json()["success_count"] == 1

    assert response.json()["failed_count"] == 0

    assert response.json()["skipped_count"] == 0

    assert response.json()["items"][0]["status"] == "success"

    assert response.json()["items"][0]["record_id"] == 301

    assert captured["invalidations"] == [

        {

            "supplier_id": 9,

            "price_identity_key": "香菇|干调类|500g",

            "reason": "导入覆盖：测试账号",

        }

    ]

    assert captured["quotes"][0]["quote_price"] == 16.9

    assert captured["action"]["action_payload"]["import_mode"] == "override_latest"

    assert captured["action"]["action_payload"]["override_count"] == 2

    assert captured["action"]["action_payload"]["override_record_ids"] == [77, 66]

    assert captured["action"]["action_payload"]["override_examples"][0]["row_number"] == 5





def test_import_supplier_prices_endpoint_returns_abnormal_hint_on_success(monkeypatch):

    captured: dict[str, object] = {"quotes": []}



    class _FakeDb:

        def get_latest_supplier_quote_for_supplier(self, supplier_id, price_identity_key):

            return pd.DataFrame(

                [

                    {

                        "id": 120,

                        "supplier_id": supplier_id,

                        "supplier_name": "蔬菜档口B",

                        "contact_name": "小李",

                        "contact_phone": None,

                        "market_scope": "本地市场",

                        "supplier_market_category": "蔬菜类",

                        "supplier_channel": "门店直报",

                        "price_identity_key": price_identity_key,

                        "price_identity_label": "菠菜 | 蔬菜类 | 斤",

                        "product_name": "菠菜",

                        "category": "蔬菜类",

                        "spec_text": "斤",

                        "market_category": "蔬菜类",

                        "channel": "门店直报",

                        "quote_price": 10.0,

                        "quote_unit": "斤",

                        "box_price": None,

                        "tax_price": None,

                        "inventory_status": "现货",

                        "remarks": "旧报价",

                        "quoted_by": "小李",

                        "status": "active",

                        "invalidated_at": None,

                        "invalidated_reason": None,

                        "quoted_at": "2026-04-20T09:00:00",

                    }

                ]

            )



        def insert_supplier_price_record(self, **kwargs):

            captured["quotes"].append(kwargs)

            return 321



        def get_supplier_price_record(self, record_id):

            quote = captured["quotes"][0]

            return pd.DataFrame(

                [

                    {

                        "id": record_id,

                        "supplier_id": quote["supplier_id"],

                        "supplier_name": "蔬菜档口B",

                        "contact_name": "小李",

                        "contact_phone": None,

                        "market_scope": "本地市场",

                        "supplier_market_category": quote["market_category"],

                        "supplier_channel": quote["channel"],

                        "price_identity_key": quote["price_identity_key"],

                        "price_identity_label": quote["price_identity_label"],

                        "product_name": quote["product_name"],

                        "category": quote["category"],

                        "spec_text": quote["spec_text"],

                        "market_category": quote["market_category"],

                        "channel": quote["channel"],

                        "quote_price": quote["quote_price"],

                        "quote_unit": quote["quote_unit"],

                        "box_price": quote["box_price"],

                        "tax_price": quote["tax_price"],

                        "inventory_status": quote["inventory_status"],

                        "remarks": quote["remarks"],

                        "quoted_by": quote["quoted_by"],

                        "status": "active",

                        "invalidated_at": None,

                        "invalidated_reason": None,

                        "quoted_at": quote["quoted_at"],

                    }

                ]

            )



        def insert_supplier_quote_action(self, **kwargs):

            captured["action"] = kwargs

            return 801



    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())

    monkeypatch.setattr(api_app_module, "get_product_keys_for_identity", lambda _: ["mock-key"])

    client = _create_authenticated_client(monkeypatch)



    response = client.post(

        "/api/supplier-prices/import",

        json={

            "supplier_id": 5,

            "operator_name": "录价专员",

            "file_name": "波动导入.xlsx",

            "import_mode": "append",

            "abnormal_change_ratio_threshold": 0.2,

            "items": [

                {

                    "row_number": 2,

                    "price_identity_key": "菠菜|蔬菜类|斤",

                    "price_identity_label": "菠菜 | 蔬菜类 | 斤",

                    "product_name": "菠菜",

                    "category": "蔬菜类",

                    "spec_text": "斤",

                    "quote_price": 13.0,

                    "quote_unit": "斤",

                    "quoted_at": "2026-04-21T10:00:00",

                    "channel": "门店直报",

                    "market_category": "蔬菜类",

                }

            ],

        },

    )



    assert response.status_code == 200

    assert response.json()["items"][0]["status"] == "success"

    assert response.json()["items"][0]["record_id"] == 321

    assert response.json()["items"][0]["abnormal_change_ratio"] == 0.3

    assert "30.00%" in response.json()["items"][0]["abnormal_change_hint"]

    assert captured["action"]["action_payload"]["abnormal_change_ratio_threshold"] == 0.2





def test_supplier_quote_actions_endpoints_return_logged_actions(monkeypatch):

    captured: dict[str, object] = {}



    class _FakeDb:

        def insert_supplier_quote_action(self, **kwargs):

            captured["create_payload"] = kwargs

            return 61



        def get_supplier_quote_actions(

            self,

            supplier_id,

            limit=20,

            offset=0,

            action_type=None,

            operator_name=None,

            keyword=None,

            start_created_at=None,

            end_created_at=None,

        ):

            captured["supplier_id"] = supplier_id

            captured["limit"] = limit

            captured["offset"] = offset

            captured["action_type"] = action_type

            captured["operator_name"] = operator_name

            captured["keyword"] = keyword

            captured["start_created_at"] = start_created_at

            captured["end_created_at"] = end_created_at

            return pd.DataFrame(

                [

                    {

                        "id": 61,

                        "supplier_id": supplier_id,

                        "supplier_name": "莲菜档口A",

                        "record_id": 12,

                        "target_record_id": None,

                        "action_type": "export_quotes",

                        "action_reason": "导出 5 条历史报价",

                        "operator_name": "供应商管理台",

                        "action_payload": "{\"format\":\"xlsx\"}",

                        "created_at": "2026-04-21T16:30:00",

                        "price_identity_key": "香菇|干调类|500g",

                        "price_identity_label": "香菇 | 干调类 | 500g",

                        "product_name": "香菇",

                        "quote_price": 17.9,

                        "quote_unit": "斤",

                        "quoted_at": "2026-04-20T10:00:00",

                        "target_price_identity_label": None,

                        "target_product_name": None,

                        "target_quote_price": None,

                        "target_quoted_at": None,

                    }

                ]

            )



        def count_supplier_quote_actions(

            self,

            supplier_id,

            action_type=None,

            operator_name=None,

            keyword=None,

            start_created_at=None,

            end_created_at=None,

        ):

            captured["count_supplier_id"] = supplier_id

            captured["count_action_type"] = action_type

            captured["count_operator_name"] = operator_name

            captured["count_keyword"] = keyword

            captured["count_start_created_at"] = start_created_at

            captured["count_end_created_at"] = end_created_at

            return 1



    db = _FakeDb()

    client = _create_authenticated_client(monkeypatch, db=db)



    create_response = client.post(

        "/api/suppliers/5/quote-actions",

        json={

            "action_type": "export_quotes",

            "record_id": 12,

            "action_reason": "导出 5 条历史报价",

            "operator_name": "供应商管理台",

            "action_payload": {"format": "xlsx"},

        },

    )

    list_response = client.get(

        "/api/suppliers/5/quote-actions"

        "?limit=8&offset=4&action_type=export_quotes&operator_name=%E4%BE%9B%E5%BA%94%E5%95%86"

        "&keyword=%E9%A6%99%E8%8F%87&start_created_at=2026-04-21&end_created_at=2026-04-21"

    )



    assert create_response.status_code == 200

    assert captured["create_payload"]["action_type"] == "export_quotes"

    assert list_response.status_code == 200

    assert captured["supplier_id"] == 5

    assert captured["limit"] == 8

    assert captured["offset"] == 4

    assert captured["action_type"] == "export_quotes"

    assert captured["operator_name"] == "供应商"

    assert captured["keyword"] == "香菇"

    assert captured["start_created_at"] == "2026-04-21"

    assert captured["end_created_at"] == "2026-04-21T23:59:59"

    assert captured["count_supplier_id"] == 5

    assert captured["count_action_type"] == "export_quotes"

    assert captured["count_operator_name"] == "供应商"

    assert captured["count_keyword"] == "香菇"

    assert captured["count_start_created_at"] == "2026-04-21"

    assert captured["count_end_created_at"] == "2026-04-21T23:59:59"

    assert list_response.json()["items"][0]["action_type"] == "export_quotes"

    assert list_response.json()["total"] == 1

    assert list_response.json()["limit"] == 8

    assert list_response.json()["offset"] == 4

    assert list_response.json()["has_more"] is False





def test_supplier_settlement_endpoints_cover_list_create_update_and_build(monkeypatch):

    captured: dict[str, object] = {"actions": []}



    class _FakeDb:

        def get_supplier_settlement_records(

            self,

            supplier_id,

            limit=20,

            offset=0,

            status=None,

            keyword=None,

            start_period_start=None,

            end_period_end=None,

        ):

            captured["list_supplier_id"] = supplier_id

            captured["list_limit"] = limit

            captured["list_offset"] = offset

            captured["list_status"] = status

            captured["list_keyword"] = keyword

            captured["list_start_period_start"] = start_period_start

            captured["list_end_period_end"] = end_period_end

            return pd.DataFrame(

                [

                    {

                        "id": 91,

                        "supplier_id": supplier_id,

                        "supplier_name": "莲菜档口A",

                        "contact_name": "老王",

                        "contact_phone": "13800000000",

                        "market_scope": "本地市场",

                        "market_category": "干调类",

                        "channel": "微信小程序",

                        "settlement_title": "4月干调月结单",

                        "period_start": "2026-04-20T09:00:00",

                        "period_end": "2026-04-21T11:00:00",

                        "quote_record_ids": "[12, 13]",

                        "record_count": 2,

                        "total_amount": 41.1,

                        "paid_amount": 20.0,

                        "pending_amount": 21.1,

                        "status": "partial",

                        "payment_due_date": "2026-04-30",

                        "payment_date": "2026-04-22",

                        "remarks": "先付一部分",

                        "created_by": "采购部小李",

                        "created_at": "2026-04-21T12:00:00",

                        "updated_at": "2026-04-22T09:00:00",

                    }

                ]

            )



        def count_supplier_settlement_records(

            self,

            supplier_id,

            status=None,

            keyword=None,

            start_period_start=None,

            end_period_end=None,

        ):

            captured["count_supplier_id"] = supplier_id

            captured["count_status"] = status

            captured["count_keyword"] = keyword

            captured["count_start_period_start"] = start_period_start

            captured["count_end_period_end"] = end_period_end

            return 1



        def insert_supplier_settlement_record(self, **kwargs):

            captured["create_payload"] = kwargs

            return 91



        def get_supplier_settlement_record(self, record_id):

            captured["get_record_id"] = record_id

            if record_id == 92:

                return pd.DataFrame(

                    [

                        {

                            "id": 92,

                            "supplier_id": 5,

                            "supplier_name": "莲菜档口A",

                            "contact_name": "老王",

                            "contact_phone": "13800000000",

                            "market_scope": "本地市场",

                            "market_category": "干调类",

                            "channel": "微信小程序",

                            "settlement_title": "已选报价结算单",

                            "period_start": "2026-04-20T09:00:00",

                            "period_end": "2026-04-21T11:00:00",

                            "quote_record_ids": "[12, 13]",

                            "record_count": 2,

                            "total_amount": 41.1,

                            "paid_amount": 0,

                            "pending_amount": 41.1,

                            "status": "pending",

                            "payment_due_date": "2026-04-30",

                            "payment_date": None,

                            "remarks": "从已选报价生成",

                            "created_by": "供应商管理台",

                            "created_at": "2026-04-21T12:10:00",

                            "updated_at": "2026-04-21T12:10:00",

                        }

                    ]

                )

            if record_id == 91 and captured.get("settlement_cancelled"):

                return pd.DataFrame(

                    [

                        {

                            "id": 91,

                            "supplier_id": 5,

                            "supplier_name": "莲菜档口A",

                            "contact_name": "老王",

                            "contact_phone": "13800000000",

                            "market_scope": "本地市场",

                            "market_category": "干调类",

                            "channel": "微信小程序",

                            "settlement_title": "4月干调月结单",

                            "period_start": "2026-04-20T09:00:00",

                            "period_end": "2026-04-21T11:00:00",

                            "quote_record_ids": "[12, 13]",

                            "record_count": 2,

                            "total_amount": 41.1,

                            "paid_amount": 20.0,

                            "pending_amount": 21.1,

                            "status": "cancelled",

                            "payment_due_date": "2026-04-30",

                            "payment_date": "2026-04-22",

                            "remarks": "先付一部分",

                            "created_by": "采购部小李",

                            "created_at": "2026-04-21T12:00:00",

                            "updated_at": "2026-04-22T09:30:00",

                        }

                    ]

                )

            return pd.DataFrame(

                [

                    {

                        "id": 91,

                        "supplier_id": 5,

                        "supplier_name": "莲菜档口A",

                        "contact_name": "老王",

                        "contact_phone": "13800000000",

                        "market_scope": "本地市场",

                        "market_category": "干调类",

                        "channel": "微信小程序",

                        "settlement_title": "4月干调月结单",

                        "period_start": "2026-04-20T09:00:00",

                        "period_end": "2026-04-21T11:00:00",

                        "quote_record_ids": "[12, 13]",

                        "record_count": 2,

                        "total_amount": 41.1,

                        "paid_amount": 20.0,

                        "pending_amount": 21.1,

                        "status": "partial",

                        "payment_due_date": "2026-04-30",

                        "payment_date": "2026-04-22",

                        "remarks": "先付一部分",

                        "created_by": "采购部小李",

                        "created_at": "2026-04-21T12:00:00",

                        "updated_at": "2026-04-22T09:00:00",

                    }

                ]

            )



        def get_supplier_price_records_by_ids(self, supplier_id, record_ids):

            captured["detail_supplier_id"] = supplier_id

            captured["detail_record_ids"] = record_ids

            return pd.DataFrame(

                [

                    {

                        "id": 12,

                        "supplier_id": supplier_id,

                        "supplier_name": "莲菜档口A",

                        "contact_name": "老王",

                        "contact_phone": "13800000000",

                        "market_scope": "本地市场",

                        "supplier_market_category": "干调类",

                        "supplier_channel": "微信小程序",

                        "price_identity_key": "香菇|干调类|500g",

                        "price_identity_label": "香菇 | 干调类 | 500g",

                        "product_name": "香菇",

                        "category": "干调类",

                        "spec_text": "500g",

                        "market_category": "干调类",

                        "channel": "微信小程序",

                        "quote_price": 18.6,

                        "quote_unit": "斤",

                        "box_price": None,

                        "tax_price": None,

                        "inventory_status": "现货",

                        "remarks": "早市报价",

                        "quoted_by": "老王",

                        "status": "active",

                        "invalidated_at": None,

                        "invalidated_reason": None,

                        "quoted_at": "2026-04-20T09:00:00",

                    }

                ]

            )



        def update_supplier_settlement_record(self, record_id, **kwargs):

            captured["update_record_id"] = record_id

            captured["update_payload"] = kwargs

            if kwargs.get("status") == "cancelled":

                captured["settlement_cancelled"] = True

                captured["cancel_record_id"] = record_id

                captured["cancel_payload"] = kwargs

            else:

                captured["payment_update_record_id"] = record_id

                captured["payment_update_payload"] = kwargs

            return 91



        def build_supplier_settlement_from_quotes(self, **kwargs):

            captured["build_payload"] = kwargs

            return 92



        def insert_supplier_quote_action(self, **kwargs):

            captured["actions"].append(kwargs)

            return 801



    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())

    client = _create_authenticated_client(monkeypatch)



    list_response = client.get(

        "/api/suppliers/5/settlements?limit=8&offset=2&status=partial&keyword=%E6%9C%88%E7%BB%93&start_period_start=2026-04-20&end_period_end=2026-04-21"

    )

    detail_response = client.get("/api/supplier-settlements/91")

    create_response = client.post(

        "/api/suppliers/5/settlements",

        json={

            "settlement_title": "4月干调月结单",

            "period_start": "2026-04-20T09:00:00",

            "period_end": "2026-04-21T11:00:00",

            "quote_record_ids": [12, 13],

            "total_amount": 41.1,

            "paid_amount": 0,

            "payment_due_date": "2026-04-30",

            "remarks": "手工创建",

            "created_by": "采购部小李",

        },

    )

    update_response = client.put(

        "/api/supplier-settlements/91",

        json={

            "paid_amount": 20.0,

            "payment_date": "2026-04-22",

            "remarks": "先付一部分",

            "operator_name": "财务小张",

        },

    )

    cancel_response = client.post(

        "/api/supplier-settlements/91/cancel",

        json={

            "operator_name": "财务小张",

            "cancel_reason": "重复生成，改走另一张结算单",

        },

    )

    build_response = client.post(

        "/api/suppliers/5/settlements/build-from-quotes",

        json={

            "settlement_title": "已选报价结算单",

            "quote_record_ids": [12, 13],

            "payment_due_date": "2026-04-30",

            "remarks": "从已选报价生成",

            "created_by": "供应商管理台",

        },

    )



    assert list_response.status_code == 200

    assert detail_response.status_code == 200

    assert create_response.status_code == 200

    assert update_response.status_code == 200

    assert cancel_response.status_code == 200

    assert build_response.status_code == 200



    assert captured["list_supplier_id"] == 5

    assert captured["list_limit"] == 8

    assert captured["list_offset"] == 2

    assert captured["list_status"] == "partial"

    assert captured["list_keyword"] == "月结"

    assert captured["list_start_period_start"] == "2026-04-20"

    assert captured["list_end_period_end"] == "2026-04-21"

    assert captured["count_supplier_id"] == 5

    assert captured["count_status"] == "partial"

    assert captured["count_keyword"] == "月结"

    assert captured["count_start_period_start"] == "2026-04-20"

    assert captured["count_end_period_end"] == "2026-04-21"



    assert captured["create_payload"]["settlement_title"] == "4月干调月结单"

    assert captured["detail_supplier_id"] == 5

    assert captured["detail_record_ids"] == [12, 13]

    assert captured["create_payload"]["quote_record_ids"] == [12, 13]

    assert captured["payment_update_record_id"] == 91

    assert captured["payment_update_payload"]["paid_amount"] == 20.0

    assert captured["cancel_record_id"] == 91

    assert captured["cancel_payload"]["status"] == "cancelled"

    assert captured["build_payload"]["quote_record_ids"] == [12, 13]



    assert list_response.json()["items"][0]["status"] == "partial"

    assert list_response.json()["items"][0]["quote_record_ids"] == [12, 13]

    assert detail_response.json()["item"]["settlement_title"] == "4月干调月结单"

    assert detail_response.json()["quote_items"][0]["product_name"] == "香菇"

    assert create_response.json()["settlement_title"] == "4月干调月结单"

    assert update_response.json()["paid_amount"] == 20.0

    assert cancel_response.json()["status"] == "cancelled"

    assert build_response.json()["settlement_title"] == "已选报价结算单"

    assert len(captured["actions"]) == 4

    assert captured["actions"][2]["action_type"] == "cancel_settlement"

    assert captured["actions"][2]["action_payload"]["cancel_reason"] == "重复生成，改走另一张结算单"





def test_product_supplier_quotes_endpoint_returns_comparison_payload(monkeypatch):

    class _FakeDb:

        def get_latest_supplier_quotes(self, price_identity_key=None, price_identity_keys=None):

            assert price_identity_key is None

            assert price_identity_keys == ["香菇|干调类|500g", "香菇"]

            return pd.DataFrame(

                [

                    {

                        "supplier_id": 9,

                        "supplier_name": "莲菜档口A",

                        "contact_name": "老王",

                        "contact_phone": None,

                        "market_scope": "本地市场",

                        "supplier_market_category": "干调类",

                        "supplier_channel": "微信小程序",

                        "price_identity_label": "香菇 | 干调类 | 500g",

                        "product_name": "香菇",

                        "category": "干调类",

                        "spec_text": "500g",

                        "market_category": "干调类",

                        "channel": "微信小程序",

                        "quote_price": 17.9,

                        "quote_unit": "斤",

                        "box_price": 214.8,

                        "tax_price": 18.3,

                        "inventory_status": "现货",

                        "remarks": "上午更新",

                        "quoted_by": "老王",

                        "quoted_at": "2026-04-20T10:00:00",

                    }

                ]

            )



    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())

    monkeypatch.setattr(api_app_module, "get_product_history_identity_df", lambda _: pd.DataFrame([{"demo": True}]))

    monkeypatch.setattr(api_app_module, "get_identity_aliases", lambda identity_key: ["香菇|干调类|500g", "香菇"])

    monkeypatch.setattr(

        api_app_module,

        "compute_single_product_summary",

        lambda df, identity_key, selected_province=None, selected_city=None: {

            "product_name": "香菇 | 干调类 | 500g",

            "current_lowest_price": 18.5,

            "current_lowest_site": "PFSC · 北京新发地",

            "current_lowest_source_name": "PFSC",

            "current_lowest_source_tier": "主价格源",

            "average_price": 19.2,

        },

    )

    client = _create_authenticated_client(monkeypatch)



    response = client.get("/api/product/%E9%A6%99%E8%8F%87%7C%E5%B9%B2%E8%B0%83%E7%B1%BB%7C500g/supplier-quotes")



    assert response.status_code == 200

    assert response.json()["summary"]["supplier_count"] == 1

    assert response.json()["summary"]["market_lowest_price"] == 18.5

    assert response.json()["summary"]["market_lowest_site"] == "PFSC · 北京新发地"

    assert response.json()["summary"]["market_lowest_source_name"] == "PFSC"

    assert response.json()["summary"]["market_lowest_source_tier"] == "主价格源"

    assert response.json()["items"][0]["comparison_label"] == "低于公开最低价 0.60"





def test_update_supplier_endpoint_returns_latest_supplier_payload(monkeypatch):

    captured: dict[str, object] = {}



    class _FakeDb:

        def upsert_supplier(self, **kwargs):

            captured["payload"] = kwargs

            return 5



        def get_auth_user_by_supplier_id(self, supplier_id):

            assert supplier_id == 5

            return pd.DataFrame()



        def get_suppliers(self, active_only=False):

            assert active_only is False

            return pd.DataFrame(

                [

                    {

                        "id": 5,

                        "supplier_name": "莲菜档口B",

                        "contact_name": "小李",

                        "contact_phone": "13900000000",

                        "market_scope": "本地市场",

                        "market_category": "蔬菜类",

                        "channel": "门店直报",

                        "notes": "上午更新",

                        "is_active": 0,

                        "created_at": "2026-04-20T09:00:00",

                        "updated_at": "2026-04-20T10:00:00",

                        "quote_count": 4,

                        "latest_quoted_at": "2026-04-20T10:00:00",

                    }

                ]

            )



    db = _FakeDb()

    client = _create_authenticated_client(monkeypatch, db=db)



    response = client.put(

        "/api/suppliers/5",

        json={

            "supplier_name": "莲菜档口B",

            "contact_name": "小李",

            "contact_phone": "13900000000",

            "market_scope": "本地市场",

            "market_category": "蔬菜类",

            "channel": "门店直报",

            "notes": "上午更新",

            "is_active": False,

        },

    )



    assert response.status_code == 200

    assert captured["payload"]["supplier_id"] == 5

    assert response.json()["is_active"] is False

    assert response.json()["supplier_name"] == "莲菜档口B"





def test_update_supplier_endpoint_can_disable_supplier_account(monkeypatch):

    captured: dict[str, object] = {}



    class _FakeDb:

        def upsert_supplier(self, **kwargs):

            captured["supplier_payload"] = kwargs

            return 5



        def get_auth_user_by_supplier_id(self, supplier_id):

            assert supplier_id == 5

            return pd.DataFrame(

                [

                    {

                        "id": 91,

                        "username": "lencai-b",

                        "password_hash": "pbkdf2_sha256$390000$salt$hash",

                        "role": "supplier",

                        "supplier_id": 5,

                        "display_name": "莲菜档口B",

                        "is_active": 1,

                    }

                ]

            )


        def get_auth_user_by_username(self, username):

            assert username == "lencai-b"

            return pd.DataFrame(

                [

                    {

                        "id": 91,

                        "username": "lencai-b",

                        "password_hash": "pbkdf2_sha256$390000$salt$hash",

                        "role": "supplier",

                        "supplier_id": 5,

                        "display_name": "莲菜档口B",

                        "is_active": 1,

                    }

                ]

            )



        def upsert_auth_user(self, **kwargs):

            captured["auth_payload"] = kwargs

            return 91



        def get_suppliers(self, active_only=False):

            assert active_only is False

            return pd.DataFrame(

                [

                    {

                        "id": 5,

                        "supplier_name": "莲菜档口B",

                        "contact_name": "小李",

                        "contact_phone": "13900000000",

                        "market_scope": "本地市场",

                        "market_category": "蔬菜类",

                        "channel": "门店直报",

                        "notes": "上午更新",

                        "is_active": 1,

                        "created_at": "2026-04-20T09:00:00",

                        "updated_at": "2026-04-20T10:00:00",

                        "quote_count": 4,

                        "latest_quoted_at": "2026-04-20T10:00:00",

                        "account_id": 91,

                        "account_username": "lencai-b",

                        "account_display_name": "莲菜档口B",

                        "account_is_active": 0,

                    }

                ]

            )



    db = _FakeDb()

    client = _create_authenticated_client(monkeypatch, db=db)



    response = client.put(

        "/api/suppliers/5",

        json={

            "supplier_name": "莲菜档口B",

            "contact_name": "小李",

            "contact_phone": "13900000000",

            "market_scope": "本地市场",

            "market_category": "蔬菜类",

            "channel": "门店直报",

            "notes": "上午更新",

            "is_active": True,

            "account_username": "lencai-b",

            "account_display_name": "莲菜档口B",

            "account_is_active": False,

        },

    )



    assert response.status_code == 200

    assert captured["supplier_payload"]["supplier_id"] == 5

    assert captured["auth_payload"]["user_id"] == 91

    assert captured["auth_payload"]["username"] == "lencai-b"

    assert captured["auth_payload"]["is_active"] is False

    assert response.json()["account_username"] == "lencai-b"

    assert response.json()["account_is_active"] is False





def test_supplier_quotes_endpoint_returns_supplier_history(monkeypatch):

    class _FakeDb:

        def get_supplier_quote_records(self, supplier_id, limit=20, offset=0, status=None, keyword=None, start_quoted_at=None, end_quoted_at=None, price_identity_key=None, price_identity_keys=None):

            assert supplier_id == 5

            assert limit == 10

            assert offset == 2

            assert status == "invalidated"

            assert keyword == "菠菜"

            assert start_quoted_at == "2026-04-20"

            assert end_quoted_at == "2026-04-20T23:59:59"

            assert price_identity_key is None

            assert price_identity_keys == ["菠菜|蔬菜类|斤", "菠菜"]

            return pd.DataFrame(

                [

                    {

                        "supplier_id": 5,

                        "supplier_name": "莲菜档口B",

                        "contact_name": "小李",

                        "contact_phone": "13900000000",

                        "market_scope": "本地市场",

                        "supplier_market_category": "蔬菜类",

                        "supplier_channel": "门店直报",

                        "price_identity_key": "菠菜|蔬菜类|斤",

                        "price_identity_label": "菠菜 | 蔬菜类 | 斤",

                        "product_name": "菠菜",

                        "category": "蔬菜类",

                        "spec_text": "斤",

                        "market_category": "蔬菜类",

                        "channel": "门店直报",

                        "quote_price": 4.8,

                        "quote_unit": "斤",

                        "box_price": None,

                        "tax_price": None,

                        "inventory_status": "现货",

                        "remarks": "上午更新",

                        "quoted_by": "小李",

                        "quoted_at": "2026-04-20T10:00:00",

                    }

                ]

            )



        def count_supplier_quote_records(self, supplier_id, status=None, keyword=None, start_quoted_at=None, end_quoted_at=None, price_identity_key=None, price_identity_keys=None):

            assert supplier_id == 5

            assert status == "invalidated"

            assert keyword == "菠菜"

            assert start_quoted_at == "2026-04-20"

            assert end_quoted_at == "2026-04-20T23:59:59"

            assert price_identity_key is None

            assert price_identity_keys == ["菠菜|蔬菜类|斤", "菠菜"]

            return 7



    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())

    monkeypatch.setattr(api_app_module, "get_identity_aliases", lambda identity_key: ["菠菜|蔬菜类|斤", "菠菜"])

    client = _create_authenticated_client(monkeypatch)



    response = client.get(

        "/api/suppliers/5/quotes?limit=10&offset=2&status=invalidated&keyword=%E8%8F%A0%E8%8F%9C&start_quoted_at=2026-04-20&end_quoted_at=2026-04-20&price_identity_key=%E8%8F%A0%E8%8F%9C%7C%E8%94%AC%E8%8F%9C%E7%B1%BB%7C%E6%96%A4"

    )



    assert response.status_code == 200

    assert response.json()["items"][0]["supplier_name"] == "莲菜档口B"

    assert response.json()["items"][0]["price_identity_key"] == "菠菜|蔬菜类|斤"

    assert response.json()["total"] == 7

    assert response.json()["limit"] == 10

    assert response.json()["offset"] == 2

    assert response.json()["has_more"] is True

