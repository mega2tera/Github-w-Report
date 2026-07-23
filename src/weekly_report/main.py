from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .ai import analyze
from .github import collect_weekly_repositories
from .render import write_outputs
from .wecom import send_markdown


def site_url_from_environment() -> str:
    explicit = os.environ.get("SITE_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" not in repository:
        return ""
    owner, name = repository.split("/", 1)
    suffix = "" if name.lower() == f"{owner.lower()}.github.io" else f"/{name}"
    return f"https://{owner}.github.io{suffix}"


def main() -> None:
    parser = argparse.ArgumentParser(description="生成 GitHub 热门项目中文周报")
    parser.add_argument("--date", help="报告日期 YYYY-MM-DD，默认北京时间当天")
    parser.add_argument("--fixture", type=Path, help="使用本地 JSON 测试数据，不请求 GitHub 或模型")
    parser.add_argument("--no-push", action="store_true", help="不推送企业微信")
    parser.add_argument("--push-existing", action="store_true", help="读取当日 data 快照并仅推送企业微信")
    args = parser.parse_args()
    report_date = args.date or datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
    root = Path(__file__).resolve().parents[2]

    if args.push_existing:
        snapshot_path = root / "data" / f"{report_date}.json"
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        site_url = site_url_from_environment()
        if not site_url:
            raise RuntimeError("无法确定 SITE_URL，请配置仓库变量 SITE_URL")
        send_markdown(
            os.environ.get("WECOM_WEBHOOK_URL", ""), report_date, site_url,
            snapshot["repositories"], str(snapshot["analysis"].get("trend_summary", "")),
        )
        return

    if args.fixture:
        fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
        repositories, analysis = fixture["repositories"], fixture["analysis"]
    else:
        repositories = collect_weekly_repositories(os.environ.get("GITHUB_TOKEN", ""), limit=10)
        analysis = analyze(
            repositories,
            token=os.environ.get("GITHUB_TOKEN", ""),
            model=os.environ.get("GITHUB_MODELS_MODEL", "openai/gpt-4.1-mini"),
            endpoint=os.environ.get(
                "GITHUB_MODELS_ENDPOINT",
                "https://models.github.ai/inference/chat/completions",
            ),
        )

    report = write_outputs(root, report_date, repositories, analysis)
    print(f"报告已生成：{report}")
    site_url = site_url_from_environment()
    if not args.no_push:
        if not site_url:
            raise RuntimeError("无法确定 SITE_URL，请配置仓库变量 SITE_URL")
        send_markdown(
            os.environ.get("WECOM_WEBHOOK_URL", ""), report_date, site_url,
            repositories, str(analysis.get("trend_summary", "")),
        )


if __name__ == "__main__":
    main()
