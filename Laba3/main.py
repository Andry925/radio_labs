import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

GPS_RE = re.compile(
    r"(?P<dt>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}),\s*"
    r"Lat:\s*(?P<lat>-?\d+(?:\.\d+)?),\s*"
    r"Lon:\s*(?P<lon>-?\d+(?:\.\d+)?),\s*"
    r"Speed:\s*(?P<speed>-?\d+(?:\.\d+)?)\s*km/h,\s*"
    r"\s*Course:\s*(?P<course>-?\d+)\s*°",
    flags=re.MULTILINE
)


def read_text(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path.resolve()}")
    return path.read_text(encoding="utf-8")


def parse_gps(file_path: str) -> list[dict]:
    text = read_text(file_path)
    gps_logs = []

    for m in GPS_RE.finditer(text):
        gps_logs.append({
            "datetime": m.group("dt"),
            "lat": float(m.group("lat")),
            "lon": float(m.group("lon")),
            "speed_kmh": float(m.group("speed")),
            "course_deg": int(m.group("course")),
        })

    return gps_logs


def build_payload(device_id: str, gps_logs: list[dict]) -> dict:
    return {
        "device_id": device_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gps_logs": gps_logs
    }


def send_x_www_form_urlencoded(url: str, payload: dict) -> requests.Response:
    form = {
        "data": json.dumps(payload, ensure_ascii=False)
    }
    return requests.post(url, data=form, timeout=10)


def send_multipart_form_data(url: str, file_path: str, payload: dict) -> requests.Response:
    with open(file_path, "rb") as f:
        files = {"file": (Path(file_path).name, f, "text/plain")}
        data = {
            "device_id": payload["device_id"],
            "timestamp": payload["timestamp"],
        }
        return requests.post(url, data=data, files=files, timeout=10)


def send_application_json(url: str, payload: dict) -> requests.Response:
    return requests.post(url, json=payload, timeout=10)


def main():
    FILE = "gps_log.txt"
    URL = "http://127.0.0.1:81/post"
    DEVICE_ID = "device_6"

    gps_logs = parse_gps(FILE)

    payload = build_payload(DEVICE_ID, gps_logs)
    send_x_www_form_urlencoded(URL, payload)
    send_multipart_form_data(URL, FILE, payload)
    send_application_json(URL, payload)


if __name__ == "__main__":
    main()
