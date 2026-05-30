from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.extract_meicai_ui_goods import parse_meicai_ui_goods


DEFAULT_REMOTE_XML_PATH = "/sdcard/meicai_ui_scroll.xml"
DEFAULT_SWIPE_ARGUMENTS = ("540", "1600", "540", "620", "650")


def collect_meicai_ui_scroll_goods(
    *,
    output_path: Path,
    dump_directory: Path,
    max_rounds: int,
    stable_round_limit: int,
    sleep_seconds: float,
    device_serial: str,
    swipe_arguments: tuple[str, str, str, str, str],
) -> dict[str, Any]:
    dump_directory.mkdir(parents=True, exist_ok=True)
    discovered_goods: dict[str, dict[str, Any]] = {}
    round_reports: list[dict[str, Any]] = []
    stable_rounds = 0

    for round_index in range(1, max_rounds + 1):
        xml_path = dump_directory / f"round_{round_index:03d}.xml"
        _dump_ui_xml(device_serial=device_serial, local_xml_path=xml_path)
        visible_report = parse_meicai_ui_goods(xml_path)
        previous_count = len(discovered_goods)

        for visible_goods in visible_report["visible_goods"]:
            goods_identity = str(visible_goods.get("identity") or "").strip()
            if not goods_identity or goods_identity in discovered_goods:
                continue
            discovered_goods[goods_identity] = {
                "name": visible_goods.get("name"),
                "spec_text": visible_goods.get("spec_text"),
                "first_seen_round": round_index,
            }

        added_count = len(discovered_goods) - previous_count
        stable_rounds = stable_rounds + 1 if added_count == 0 else 0
        round_reports.append(
            {
                "round": round_index,
                "dump_file": str(xml_path),
                "visible_goods": visible_report["counts"]["visible_goods"],
                "added_unique_goods": added_count,
                "total_unique_goods": len(discovered_goods),
                "price_image_nodes": visible_report["counts"]["price_image_nodes"],
                "visible_categories": visible_report["visible_categories"],
            }
        )
        if stable_rounds >= stable_round_limit:
            break
        if round_index < max_rounds:
            _swipe_goods_list(device_serial=device_serial, swipe_arguments=swipe_arguments)
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

    collection_report = {
        "output_file": str(output_path),
        "dump_directory": str(dump_directory),
        "extracted_at": datetime.now().isoformat(timespec="seconds"),
        "counts": {
            "rounds": len(round_reports),
            "unique_goods": len(discovered_goods),
        },
        "price_text_available": False,
        "price_note": "美菜当前价格控件是 ImageView，uiautomator XML 未暴露价格文本；按约束未使用 OCR。",
        "rounds": round_reports,
        "goods": list(discovered_goods.values()),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(collection_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return collection_report


def _dump_ui_xml(*, device_serial: str, local_xml_path: Path) -> None:
    adb_prefix = _adb_prefix(device_serial)
    _run_command([*adb_prefix, "shell", "uiautomator", "dump", DEFAULT_REMOTE_XML_PATH], timeout_seconds=20)
    _run_command([*adb_prefix, "pull", DEFAULT_REMOTE_XML_PATH, str(local_xml_path)], timeout_seconds=20)


def _swipe_goods_list(*, device_serial: str, swipe_arguments: tuple[str, str, str, str, str]) -> None:
    adb_prefix = _adb_prefix(device_serial)
    _run_command([*adb_prefix, "shell", "input", "swipe", *swipe_arguments], timeout_seconds=10)


def _adb_prefix(device_serial: str) -> list[str]:
    if device_serial:
        return ["adb", "-s", device_serial]
    return ["adb"]


def _run_command(command_arguments: list[str], *, timeout_seconds: int) -> None:
    completed_command = subprocess.run(
        command_arguments,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        check=False,
    )
    if completed_command.returncode != 0:
        command_text = " ".join(command_arguments[:4])
        raise RuntimeError(f"命令失败: {command_text}")


def _parse_swipe_arguments(raw_value: str) -> tuple[str, str, str, str, str]:
    swipe_parts = [part.strip() for part in raw_value.split(",") if part.strip()]
    if len(swipe_parts) != 5 or not all(part.isdigit() for part in swipe_parts):
        raise RuntimeError("--swipe 必须是 x1,y1,x2,y2,duration_ms")
    return tuple(swipe_parts)  # type: ignore[return-value]


def main() -> None:
    argument_parser = argparse.ArgumentParser(
        description="Collect visible Meicai goods by scrolling uiautomator XML without OCR."
    )
    argument_parser.add_argument("--output", "-o", default="tmp/meicai_ui_scroll_goods.json")
    argument_parser.add_argument("--dump-dir", default="tmp/meicai_ui_scroll")
    argument_parser.add_argument("--rounds", type=int, default=20)
    argument_parser.add_argument("--stable-rounds", type=int, default=3)
    argument_parser.add_argument("--sleep-seconds", type=float, default=0.8)
    argument_parser.add_argument("--device-serial", default="")
    argument_parser.add_argument("--swipe", default=",".join(DEFAULT_SWIPE_ARGUMENTS))
    parsed_arguments = argument_parser.parse_args()

    collection_report = collect_meicai_ui_scroll_goods(
        output_path=Path(parsed_arguments.output),
        dump_directory=Path(parsed_arguments.dump_dir),
        max_rounds=max(1, parsed_arguments.rounds),
        stable_round_limit=max(1, parsed_arguments.stable_rounds),
        sleep_seconds=max(0.0, parsed_arguments.sleep_seconds),
        device_serial=str(parsed_arguments.device_serial or "").strip(),
        swipe_arguments=_parse_swipe_arguments(str(parsed_arguments.swipe)),
    )
    print(
        "rounds={rounds} unique_goods={unique_goods} output={output}".format(
            rounds=collection_report["counts"]["rounds"],
            unique_goods=collection_report["counts"]["unique_goods"],
            output=collection_report["output_file"],
        )
    )


if __name__ == "__main__":
    main()
