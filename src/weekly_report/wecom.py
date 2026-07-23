from __future__ import annotations

import json
import urllib.request


def send_markdown(webhook_url: str, report_date: str, site_url: str, repositories: list[dict], summary: str) -> None:
    if not webhook_url:
        print("未配置 WECOM_WEBHOOK_URL，跳过企业微信推送。")
        return
    top = repositories[:3]
    ranking = "\n".join(
        f"> {repo['rank']}. [{repo['full_name']}]({repo['html_url']}) · 本周 +{repo['weekly_stars']:,} Stars"
        for repo in top
    )
    report_url = f"{site_url.rstrip('/')}/reports/{report_date}.html"
    content = (
        f"## GitHub 热门项目周报 · {report_date}\n"
        f"{summary[:450]}\n\n"
        f"**本周前三**\n{ranking}\n\n"
        f"[查看前十项目完整分析]({report_url})"
    )
    payload = json.dumps({"msgtype": "markdown", "markdown": {"content": content}}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(webhook_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))
    if result.get("errcode") != 0:
        raise RuntimeError(f"企业微信推送失败：{result}")
    print("企业微信推送成功。")

