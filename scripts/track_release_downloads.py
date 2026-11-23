#!/usr/bin/env python3
"""Record the cumulative download count for one GitHub Release asset."""

import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

OWNER = "work-piece"
REPO = "WorkPiece"
TAG = "v1.0"
ASSET_NAME = "work-piece-company-profile.pdf"
CSV_PATH = Path("data/download_history.csv")
JST = ZoneInfo("Asia/Tokyo")
FIELDS = [
    "date_jst",
    "repository",
    "release_tag",
    "asset_name",
    "download_count",
    "daily_delta",
    "collected_at_utc",
]


def api_get(url: str, token: str) -> dict:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "WorkPiece-Release-Download-Tracker",
        },
    )
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN が設定されていません。", file=sys.stderr)
        return 1

    repo_slug = f"{OWNER}/{REPO}"
    release_url = (
        f"https://api.github.com/repos/{OWNER}/{REPO}/releases/tags/{TAG}"
    )

    try:
        release = api_get(release_url, token)
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"ERROR: Release情報を取得できません: {exc}", file=sys.stderr)
        return 1

    asset = next(
        (item for item in release.get("assets", [])
         if item.get("name") == ASSET_NAME),
        None,
    )
    if asset is None:
        available = [item.get("name") for item in release.get("assets", [])]
        print(
            f"ERROR: 対象ファイル {ASSET_NAME!r} が見つかりません。"
            f" Release内のファイル: {available}",
            file=sys.stderr,
        )
        return 1

    count = int(asset["download_count"])
    now_utc = datetime.now(timezone.utc)
    today_jst = now_utc.astimezone(JST).date().isoformat()
    collected_at = now_utc.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    if CSV_PATH.exists():
        with CSV_PATH.open("r", newline="", encoding="utf-8-sig") as file:
            rows = list(csv.DictReader(file))

    # 同じ日に手動実行・再実行した場合は、その日の行を更新して重複を防ぐ。
    previous_counts = [
        int(row["download_count"])
        for row in rows
        if row.get("date_jst") != today_jst and row.get("download_count", "").isdigit()
    ]
    previous_count = previous_counts[-1] if previous_counts else None
    delta = "" if previous_count is None else str(count - previous_count)

    new_row = {
        "date_jst": today_jst,
        "repository": repo_slug,
        "release_tag": TAG,
        "asset_name": ASSET_NAME,
        "download_count": str(count),
        "daily_delta": delta,
        "collected_at_utc": collected_at,
    }

    replaced = False
    for index, row in enumerate(rows):
        if row.get("date_jst") == today_jst:
            rows[index] = new_row
            replaced = True
            break
    if not replaced:
        rows.append(new_row)

    rows.sort(key=lambda row: row.get("date_jst", ""))

    with CSV_PATH.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(
        f"記録完了: {today_jst} / {ASSET_NAME} / "
        f"累計 {count} 回 / 前回記録との差 {delta if delta else '初回記録'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
