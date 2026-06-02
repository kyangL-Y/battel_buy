import json

from tools.check_kuailv_h5_readiness import build_readiness_report


class FakeKuailvResponse:
    def __init__(self, payload, *, http_status=200, content_type="application/json;charset=utf-8"):
        self._payload = payload
        self.status_code = http_status
        self.headers = {"content-type": content_type}
        self.text = json.dumps(payload, ensure_ascii=False)

    def json(self):
        return self._payload


class FakeKuailvSession:
    headers = {}
    cookies = {}

    def get(self, url, **kwargs):
        if url.endswith("/api/register/check/open"):
            return FakeKuailvResponse(
                {"code": 200, "status": 1, "success": True, "message": "请求成功", "data": {"openRegister": True}}
            )
        if url.endswith("/api/goods/category/first/list"):
            return FakeKuailvResponse(
                {
                    "code": 200,
                    "status": 1,
                    "success": True,
                    "message": "请求成功",
                    "data": {"categoryList": [{"id": "9", "name": "蔬菜"}]},
                }
            )
        if url.endswith("/api/goods/category/second/list"):
            return FakeKuailvResponse(
                {
                    "code": 200,
                    "status": 1,
                    "success": True,
                    "message": "请求成功",
                    "data": {"categoryList": [{"id": "91", "name": "叶菜"}]},
                }
            )
        raise AssertionError(f"unexpected GET {url}")

    def post(self, url, **kwargs):
        if url.endswith("/api/goods/list"):
            return FakeKuailvResponse(
                {
                    "code": 200,
                    "status": 1,
                    "success": True,
                    "message": "请求成功",
                    "data": {
                        "goodsList": [{"id": "secret-goods-id", "name": "青菜"}],
                        "page": {"hasNextPage": False, "taken": "secret-taken"},
                    },
                }
            )
        raise AssertionError(f"unexpected POST {url}")


def test_kuailv_readiness_loads_env_without_secret_values(tmp_path, monkeypatch):
    secret_env_path = tmp_path / "kuailv.env"
    secret_env_path.write_text(
        'KUAILV_COOKIES={"token":"secret-cookie"}\n'
        'KUAILV_REQUEST_HEADERS={"x-auth":"secret-header"}\n'
        'KUAILV_ADDRESS_CONTEXT={"selectedPoiAddressId":"secret-address","selectedSalesGridId":"secret-grid"}\n',
        encoding="utf-8",
    )
    monkeypatch.delenv("KUAILV_COOKIES", raising=False)
    monkeypatch.delenv("KUAILV_REQUEST_HEADERS", raising=False)
    monkeypatch.delenv("KUAILV_ADDRESS_CONTEXT", raising=False)

    report = build_readiness_report(
        secret_env_file=secret_env_path,
        city_id="320100",
        cat1_id=None,
        cat2_id=None,
        page_size=20,
        timeout_seconds=1,
        skip_network=True,
    )
    serialized_report = json.dumps(report, ensure_ascii=False)

    assert report["ready"] is False
    assert report["loaded_env_names"] == ["KUAILV_COOKIES", "KUAILV_REQUEST_HEADERS", "KUAILV_ADDRESS_CONTEXT"]
    assert report["env"]["KUAILV_COOKIES"]["top_level_keys"] == ["token"]
    assert report["env"]["KUAILV_REQUEST_HEADERS"]["top_level_keys"] == ["x-auth"]
    assert report["env"]["KUAILV_ADDRESS_CONTEXT"]["top_level_keys"] == ["selectedPoiAddressId", "selectedSalesGridId"]
    assert "secret-cookie" not in serialized_report
    assert "secret-header" not in serialized_report
    assert "secret-address" not in serialized_report
    assert "secret-grid" not in serialized_report


def test_kuailv_readiness_marks_ready_when_goods_list_returns_rows(monkeypatch):
    monkeypatch.setattr("tools.check_kuailv_h5_readiness.build_session", lambda headers, cookies: FakeKuailvSession())
    monkeypatch.setenv("KUAILV_COOKIES", '{"token":"secret-cookie"}')
    monkeypatch.setenv("KUAILV_ADDRESS_CONTEXT", '{"selectedPoiAddressId":"secret-address"}')
    monkeypatch.delenv("KUAILV_REQUEST_HEADERS", raising=False)

    report = build_readiness_report(
        secret_env_file=None,
        city_id="320100",
        cat1_id=None,
        cat2_id=None,
        page_size=20,
        timeout_seconds=1,
        skip_network=False,
    )
    serialized_report = json.dumps(report, ensure_ascii=False)

    assert report["ready"] is True
    assert report["probe"]["category_first_count"] == 1
    assert report["probe"]["resolved_cat1_id"] == "9"
    assert report["probe"]["resolved_cat2_id"] == "91"
    assert report["probe"]["goods_list"]["goods_count"] == 1
    assert report["probe"]["goods_list"]["taken_present"] is True
    assert "secret-cookie" not in serialized_report
    assert "secret-address" not in serialized_report
    assert "secret-goods-id" not in serialized_report
    assert "青菜" not in serialized_report
