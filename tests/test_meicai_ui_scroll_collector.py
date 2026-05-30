from __future__ import annotations

from pathlib import Path

from tools import collect_meicai_ui_goods_scroll as collector


def test_collect_meicai_ui_scroll_goods_deduplicates_and_stops(tmp_path, monkeypatch):
    visible_rounds = [
        {
            "counts": {"visible_goods": 2, "price_image_nodes": 2},
            "visible_categories": ["蔬果豆类"],
            "visible_goods": [
                {"identity": "青菜|1斤", "name": "青菜", "spec_text": "1斤"},
                {"identity": "白菜|2斤", "name": "白菜", "spec_text": "2斤"},
            ],
        },
        {
            "counts": {"visible_goods": 2, "price_image_nodes": 2},
            "visible_categories": ["蔬果豆类"],
            "visible_goods": [
                {"identity": "白菜|2斤", "name": "白菜", "spec_text": "2斤"},
                {"identity": "菠菜|1斤", "name": "菠菜", "spec_text": "1斤"},
            ],
        },
        {
            "counts": {"visible_goods": 2, "price_image_nodes": 2},
            "visible_categories": ["蔬果豆类"],
            "visible_goods": [
                {"identity": "白菜|2斤", "name": "白菜", "spec_text": "2斤"},
                {"identity": "菠菜|1斤", "name": "菠菜", "spec_text": "1斤"},
            ],
        },
    ]
    dumped_paths: list[Path] = []
    swipe_count = 0

    def fake_dump_ui_xml(*, device_serial, local_xml_path):
        dumped_paths.append(local_xml_path)

    def fake_parse_meicai_ui_goods(xml_path):
        return visible_rounds[len(dumped_paths) - 1]

    def fake_swipe_goods_list(*, device_serial, swipe_arguments):
        nonlocal swipe_count
        swipe_count += 1

    monkeypatch.setattr(collector, "_dump_ui_xml", fake_dump_ui_xml)
    monkeypatch.setattr(collector, "parse_meicai_ui_goods", fake_parse_meicai_ui_goods)
    monkeypatch.setattr(collector, "_swipe_goods_list", fake_swipe_goods_list)

    report = collector.collect_meicai_ui_scroll_goods(
        output_path=tmp_path / "goods.json",
        dump_directory=tmp_path / "dumps",
        max_rounds=5,
        stable_round_limit=1,
        sleep_seconds=0,
        device_serial="",
        swipe_arguments=("540", "1600", "540", "620", "650"),
    )

    assert report["counts"] == {"rounds": 3, "unique_goods": 3}
    assert [item["name"] for item in report["goods"]] == ["青菜", "白菜", "菠菜"]
    assert swipe_count == 2
    assert (tmp_path / "goods.json").exists()
