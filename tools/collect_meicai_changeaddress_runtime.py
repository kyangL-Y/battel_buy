from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import frida


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CAPTURE_PATH = Path(".local-secrets/meicai_capture/meicai_runtime_changeaddress.jsonl")
DEFAULT_SCRIPT_PATH = Path("tmp/meicai_runtime_changeaddress.js")
CHANGE_ADDRESS_PATH = "/api/auth/changeaddress"
MEICAI_PACKAGE_NAME = "com.meicai.mall"


def build_frida_script() -> str:
    return f"""
Java.perform(function () {{
  const Buffer = Java.use("okio.Buffer");

  function headersObject(headers) {{
    const headerValues = {{}};
    const headerCount = headers.size();
    for (let headerIndex = 0; headerIndex < headerCount; headerIndex += 1) {{
      headerValues[String(headers.name(headerIndex))] = String(headers.value(headerIndex));
    }}
    return headerValues;
  }}

  function bodyText(requestBody) {{
    if (!requestBody) return "";
    try {{
      const bodyBuffer = Buffer.$new();
      requestBody.writeTo(bodyBuffer);
      return String(bodyBuffer.readUtf8());
    }} catch (error) {{
      return "";
    }}
  }}

  function emitChangeAddress(request) {{
    const requestUrl = String(request.url().toString());
    const requestPath = String(request.url().encodedPath());
    if (requestPath !== "{CHANGE_ADDRESS_PATH}") return;
    send({{
      event: "request",
      method: String(request.method()),
      url: requestUrl,
      scheme: String(request.url().scheme()),
      host: String(request.url().host()),
      path: requestPath,
      query: {{}},
      request_headers: headersObject(request.headers()),
      request_text: bodyText(request.body()),
      status_code: null,
      response_headers: {{}},
      response_text: ""
    }});
  }}

  function requestFromCall(callInstance) {{
    try {{
      if (callInstance.request && typeof callInstance.request === "function") {{
        return callInstance.request();
      }}
    }} catch (error) {{}}
    try {{
      if (callInstance.getRequest && typeof callInstance.getRequest === "function") {{
        return callInstance.getRequest();
      }}
    }} catch (error) {{}}
    try {{
      if (callInstance.request && callInstance.request.value) {{
        return callInstance.request.value;
      }}
    }} catch (error) {{}}
    return null;
  }}

  function hookRealCall(className) {{
    try {{
      const RealCall = Java.use(className);
      let hookCount = 0;
      RealCall.execute.overloads.forEach(function (executeCall) {{
        executeCall.implementation = function () {{
          const request = requestFromCall(this);
          if (request) emitChangeAddress(request);
          return executeCall.call(this);
        }};
        hookCount += 1;
      }});
      RealCall.enqueue.overloads.forEach(function (enqueueCall) {{
        enqueueCall.implementation = function () {{
          const request = requestFromCall(this);
          if (request) emitChangeAddress(request);
          return enqueueCall.apply(this, arguments);
        }};
        hookCount += 1;
      }});
      send({{ event: "hooked", class_name: className, hook_count: hookCount, path: "{CHANGE_ADDRESS_PATH}" }});
      return true;
    }} catch (error) {{
      send({{ event: "hook_error", class_name: className, error: String(error) }});
      return false;
    }}
  }}

  const hooked = hookRealCall("okhttp3.RealCall") || hookRealCall("okhttp3.internal.connection.RealCall");
  if (!hooked) {{
    send({{ event: "hook_missing", path: "{CHANGE_ADDRESS_PATH}" }});
  }}
}});
"""


def run_command(command_line: list[str], *, timeout: int, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed_command = subprocess.run(
        command_line,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if check and completed_command.returncode != 0:
        joined_command = " ".join(command_line)
        raise RuntimeError(f"命令失败: {joined_command}\n{completed_command.stderr.strip()}")
    return completed_command


def find_meicai_process_id(adb_path: str, serial: str) -> str:
    adb_command = [adb_path]
    if serial:
        adb_command.extend(["-s", serial])
    adb_command.extend(["shell", "pidof", MEICAI_PACKAGE_NAME])
    completed_command = run_command(adb_command, timeout=10)
    meicai_pid = completed_command.stdout.strip()
    if not meicai_pid:
        raise RuntimeError("未找到 com.meicai.mall 进程，请先打开美菜 App")
    return meicai_pid


def append_capture_record(capture_path: Path, frida_message: dict[str, Any]) -> dict[str, Any] | None:
    if frida_message.get("type") != "send":
        return None
    sent_payload = frida_message.get("payload")
    if not isinstance(sent_payload, dict):
        return None
    if sent_payload.get("path") != CHANGE_ADDRESS_PATH:
        return None

    capture_record = {
        "captured_at": datetime.now().isoformat(timespec="seconds"),
        **sent_payload,
    }
    capture_path.parent.mkdir(parents=True, exist_ok=True)
    with capture_path.open("a", encoding="utf-8") as capture_file:
        capture_file.write(json.dumps(capture_record, ensure_ascii=False) + "\n")
    return capture_record


def summarize_captured_addresses(capture_path: Path) -> dict[str, Any]:
    captured_addresses: list[dict[str, str]] = []
    if not capture_path.exists():
        return {"capture_path": str(capture_path), "captured_count": 0, "addresses": []}
    for raw_line in capture_path.read_text(encoding="utf-8-sig").splitlines():
        if not raw_line.strip():
            continue
        capture_record = json.loads(raw_line)
        request_text = str(capture_record.get("request_text") or "").strip()
        try:
            request_body = json.loads(request_text)
        except json.JSONDecodeError:
            continue
        captured_addresses.append(
            {
                "city_id": str(request_body.get("city_id") or ""),
                "area_id": str(request_body.get("area_id") or ""),
                "captured_at": str(capture_record.get("captured_at") or ""),
            }
        )
    return {
        "capture_path": str(capture_path),
        "captured_count": len(captured_addresses),
        "addresses": captured_addresses,
    }


def collect_changeaddress_runtime(
    *,
    adb_path: str,
    serial: str,
    capture_path: Path,
    script_path: Path,
    wait_seconds: int,
) -> dict[str, Any]:
    meicai_pid = find_meicai_process_id(adb_path, serial)
    script_path.parent.mkdir(parents=True, exist_ok=True)
    frida_script_source = build_frida_script()
    script_path.write_text(frida_script_source, encoding="utf-8")
    capture_path.parent.mkdir(parents=True, exist_ok=True)
    if not capture_path.exists():
        capture_path.write_text("", encoding="utf-8")

    hooked_seen = False
    frida_message_count = 0
    frida_errors: list[str] = []

    def record_frida_message(frida_message: dict[str, Any], _message_payload: Any) -> None:
        nonlocal hooked_seen, frida_message_count
        frida_message_count += 1
        sent_payload = frida_message.get("payload") if isinstance(frida_message.get("payload"), dict) else {}
        if sent_payload.get("event") == "hooked":
            hooked_seen = True
        if frida_message.get("type") == "error":
            frida_errors.append(str(frida_message.get("description") or frida_message.get("stack") or "frida script error"))
        if sent_payload.get("event") in {"hook_error", "hook_missing"}:
            frida_errors.append(json.dumps(sent_payload, ensure_ascii=False))
        append_capture_record(capture_path, frida_message)

    frida_device = frida.get_device(serial) if serial else frida.get_usb_device(timeout=5)
    try:
        frida_session = frida_device.attach(int(meicai_pid))
    except frida.PermissionDeniedError as exc:
        raise RuntimeError(
            "Frida 无法附加美菜进程；当前模拟器需要开启 root 后启动 frida-server，"
            "或改用已有 mitmproxy 私密抓包链路捕获 /api/auth/changeaddress。"
        ) from exc
    frida_script = frida_session.create_script(frida_script_source, runtime="v8")
    frida_script.on("message", record_frida_message)
    try:
        frida_script.load()
        time.sleep(wait_seconds)
    finally:
        try:
            frida_script.unload()
        finally:
            frida_session.detach()

    capture_summary = summarize_captured_addresses(capture_path)
    capture_summary["hooked_seen"] = hooked_seen
    capture_summary["frida_message_count"] = frida_message_count
    capture_summary["frida_errors"] = frida_errors[-5:]
    return capture_summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Capture Meicai /api/auth/changeaddress request from the logged-in App runtime without emulator proxy."
    )
    parser.add_argument("--adb", default="adb")
    parser.add_argument("--serial", default="")
    parser.add_argument("--output", default=str(DEFAULT_CAPTURE_PATH))
    parser.add_argument("--script", default=str(DEFAULT_SCRIPT_PATH))
    parser.add_argument("--wait-seconds", type=int, default=60)
    parsed_arguments = parser.parse_args()

    try:
        capture_summary = collect_changeaddress_runtime(
            adb_path=parsed_arguments.adb,
            serial=parsed_arguments.serial,
            capture_path=Path(parsed_arguments.output),
            script_path=Path(parsed_arguments.script),
            wait_seconds=max(5, parsed_arguments.wait_seconds),
        )
    except RuntimeError as exc:
        capture_summary = {
            "capture_path": parsed_arguments.output,
            "captured_count": 0,
            "error": str(exc),
        }
        print(json.dumps(capture_summary, ensure_ascii=False, indent=2))
        raise SystemExit(1) from exc
    print(json.dumps(capture_summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
