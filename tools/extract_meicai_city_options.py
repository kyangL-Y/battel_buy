from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any


CLOSED_SUFFIX = " 未开通此城市"
SECTION_LABELS = {
    "美菜",
    "热门城市",
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "J",
    "K",
    "L",
    "M",
    "N",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "W",
    "X",
    "Y",
    "Z",
}
CITY_NAME_PATTERN = re.compile(r"^[\u4e00-\u9fa5]{2,12}(?:市|州|盟|地区)?$")
AREA_OPTION_PATTERN = re.compile(r"^[\u4e00-\u9fa5]{2,12}(?:市|州|盟|地区)-[\u4e00-\u9fa5]{2,16}$")


def parse_meicai_city_options(xml_path: Path) -> dict[str, Any]:
    xml_root = ET.parse(xml_path).getroot()
    opened_cities: list[str] = []
    closed_cities: list[str] = []
    opened_area_options: list[str] = []

    for ui_text in _iter_visible_texts(xml_root):
        if ui_text in SECTION_LABELS:
            continue

        city_text = ui_text.removesuffix(CLOSED_SUFFIX).strip()
        if AREA_OPTION_PATTERN.match(city_text):
            if not ui_text.endswith(CLOSED_SUFFIX):
                opened_area_options.append(city_text)
            continue
        if not CITY_NAME_PATTERN.match(city_text):
            continue

        if ui_text.endswith(CLOSED_SUFFIX):
            closed_cities.append(city_text)
        else:
            opened_cities.append(city_text)

    opened_city_names = _deduplicate_preserving_order(opened_cities)
    closed_city_names = _deduplicate_preserving_order(closed_cities)
    opened_area_names = _deduplicate_preserving_order(opened_area_options)
    return {
        "source_file": str(xml_path),
        "extracted_at": datetime.now().isoformat(timespec="seconds"),
        "counts": {
            "opened_cities": len(opened_city_names),
            "closed_cities": len(closed_city_names),
            "opened_area_options": len(opened_area_names),
        },
        "opened_cities": opened_city_names,
        "closed_cities": closed_city_names,
        "opened_area_options": opened_area_names,
    }


def _iter_visible_texts(xml_root: ET.Element) -> list[str]:
    visible_texts: list[str] = []
    for ui_node in xml_root.iter("node"):
        ui_text = (ui_node.attrib.get("text") or "").strip()
        if ui_text:
            visible_texts.append(ui_text)
    return visible_texts


def _deduplicate_preserving_order(city_names: list[str]) -> list[str]:
    seen_names: set[str] = set()
    ordered_names: list[str] = []
    for city_name in city_names:
        if city_name in seen_names:
            continue
        seen_names.add(city_name)
        ordered_names.append(city_name)
    return ordered_names


def main() -> None:
    argument_parser = argparse.ArgumentParser(
        description="Extract opened/closed Meicai city options from an Android uiautomator XML dump."
    )
    argument_parser.add_argument(
        "xml_path",
        nargs="?",
        default="tmp/meicai_pick_address.xml",
        help="Path to the uiautomator XML dump from Meicai city picker.",
    )
    argument_parser.add_argument(
        "--output",
        "-o",
        default="tmp/meicai_city_options.json",
        help="JSON output path.",
    )
    parsed_arguments = argument_parser.parse_args()

    xml_path = Path(parsed_arguments.xml_path)
    output_path = Path(parsed_arguments.output)
    city_options = parse_meicai_city_options(xml_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(city_options, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    counts = city_options["counts"]
    print(
        "opened_cities={opened_cities} closed_cities={closed_cities} "
        "opened_area_options={opened_area_options} output={output}".format(
            opened_cities=counts["opened_cities"],
            closed_cities=counts["closed_cities"],
            opened_area_options=counts["opened_area_options"],
            output=output_path,
        )
    )


if __name__ == "__main__":
    main()
