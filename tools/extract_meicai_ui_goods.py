from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, NamedTuple


GOODS_NAME_RESOURCE_ID = "com.meicai.mall:id/tvGoodsName"
GOODS_UNIT_RESOURCE_ID = "com.meicai.mall:id/ssuFormatUnit"
CATEGORY_TEXT_RESOURCE_IDS = {
    "com.meicai.mall:id/categoryText",
    "com.meicai.mall:id/cate_tv",
    "com.meicai.mall:id/tvTitle",
}
PRICE_IMAGE_RESOURCE_ID = "com.meicai.mall:id/tv_commodity_now_price"
BOUNDS_PATTERN = re.compile(r"^\[(\d+),(\d+)\]\[(\d+),(\d+)\]$")


class UiBounds(NamedTuple):
    left: int
    top: int
    right: int
    bottom: int


class UiTextNode(NamedTuple):
    text: str
    resource_id: str
    class_name: str
    bounds: UiBounds


def parse_meicai_ui_goods(xml_path: Path) -> dict[str, Any]:
    xml_root = ET.parse(xml_path).getroot()
    ui_nodes = _collect_text_nodes(xml_root)
    goods_name_nodes = [node for node in ui_nodes if node.resource_id == GOODS_NAME_RESOURCE_ID]
    unit_nodes = [node for node in ui_nodes if node.resource_id == GOODS_UNIT_RESOURCE_ID]
    category_nodes = [node for node in ui_nodes if node.resource_id in CATEGORY_TEXT_RESOURCE_IDS]
    price_image_count = _count_resource_id(xml_root, PRICE_IMAGE_RESOURCE_ID)

    visible_goods: list[dict[str, Any]] = []
    for index, goods_name_node in enumerate(goods_name_nodes):
        next_goods_top = (
            goods_name_nodes[index + 1].bounds.top
            if index + 1 < len(goods_name_nodes)
            else goods_name_node.bounds.bottom + 420
        )
        unit_text = _nearest_unit_text(goods_name_node, unit_nodes, next_goods_top)
        visible_goods.append(
            {
                "name": goods_name_node.text,
                "spec_text": unit_text or None,
                "bounds": _serialize_bounds(goods_name_node.bounds),
                "identity": _build_visible_goods_identity(goods_name_node.text, unit_text),
            }
        )

    return {
        "source_file": str(xml_path),
        "extracted_at": datetime.now().isoformat(timespec="seconds"),
        "counts": {
            "visible_goods": len(visible_goods),
            "visible_categories": len(category_nodes),
            "price_image_nodes": price_image_count,
        },
        "visible_categories": _deduplicate_preserving_order([node.text for node in category_nodes]),
        "visible_goods": visible_goods,
        "price_text_available": False,
        "price_note": "美菜当前价格控件是 ImageView，uiautomator XML 未暴露价格文本；按约束未使用 OCR。",
    }


def _collect_text_nodes(xml_root: ET.Element) -> list[UiTextNode]:
    text_nodes: list[UiTextNode] = []
    for ui_node in xml_root.iter("node"):
        ui_text = (ui_node.attrib.get("text") or "").strip()
        resource_id = (ui_node.attrib.get("resource-id") or "").strip()
        bounds = _parse_bounds(ui_node.attrib.get("bounds") or "")
        if not bounds:
            continue
        if not ui_text and resource_id not in {GOODS_NAME_RESOURCE_ID, GOODS_UNIT_RESOURCE_ID}:
            continue
        text_nodes.append(
            UiTextNode(
                text=ui_text,
                resource_id=resource_id,
                class_name=(ui_node.attrib.get("class") or "").strip(),
                bounds=bounds,
            )
        )
    return text_nodes


def _parse_bounds(raw_bounds: str) -> UiBounds | None:
    bounds_match = BOUNDS_PATTERN.match(raw_bounds.strip())
    if not bounds_match:
        return None
    left, top, right, bottom = (int(part) for part in bounds_match.groups())
    return UiBounds(left=left, top=top, right=right, bottom=bottom)


def _nearest_unit_text(goods_name_node: UiTextNode, unit_nodes: list[UiTextNode], next_goods_top: int) -> str:
    candidates = [
        node
        for node in unit_nodes
        if goods_name_node.bounds.bottom <= node.bounds.top < next_goods_top
        and abs(node.bounds.left - goods_name_node.bounds.left) <= 110
    ]
    if not candidates:
        return ""
    nearest_node = min(candidates, key=lambda node: node.bounds.top - goods_name_node.bounds.bottom)
    return nearest_node.text


def _count_resource_id(xml_root: ET.Element, resource_id: str) -> int:
    return sum(1 for ui_node in xml_root.iter("node") if (ui_node.attrib.get("resource-id") or "").strip() == resource_id)


def _serialize_bounds(bounds: UiBounds) -> dict[str, int]:
    return {
        "left": bounds.left,
        "top": bounds.top,
        "right": bounds.right,
        "bottom": bounds.bottom,
    }


def _build_visible_goods_identity(goods_name: str, unit_text: str) -> str:
    return f"{goods_name.strip()}|{unit_text.strip()}".strip("|")


def _deduplicate_preserving_order(values: list[str]) -> list[str]:
    seen_values: set[str] = set()
    ordered_values: list[str] = []
    for value in values:
        if not value or value in seen_values:
            continue
        seen_values.add(value)
        ordered_values.append(value)
    return ordered_values


def main() -> None:
    argument_parser = argparse.ArgumentParser(
        description="Extract visible Meicai goods from an Android uiautomator XML dump without OCR."
    )
    argument_parser.add_argument(
        "xml_path",
        nargs="?",
        default="tmp/meicai_live.xml",
        help="Path to the uiautomator XML dump from a Meicai goods list screen.",
    )
    argument_parser.add_argument(
        "--output",
        "-o",
        default="tmp/meicai_ui_goods.json",
        help="JSON output path.",
    )
    parsed_arguments = argument_parser.parse_args()

    xml_path = Path(parsed_arguments.xml_path)
    output_path = Path(parsed_arguments.output)
    ui_goods_report = parse_meicai_ui_goods(xml_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(ui_goods_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    counts = ui_goods_report["counts"]
    print(
        "visible_goods={visible_goods} visible_categories={visible_categories} "
        "price_image_nodes={price_image_nodes} output={output}".format(
            visible_goods=counts["visible_goods"],
            visible_categories=counts["visible_categories"],
            price_image_nodes=counts["price_image_nodes"],
            output=output_path,
        )
    )


if __name__ == "__main__":
    main()
