from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path


CSS = """
:root{--bg:#f6f7fb;--card:#fff;--text:#172033;--muted:#667085;--line:#e4e7ec;--brand:#2563eb;--accent:#eef4ff}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.72 system-ui,-apple-system,"Segoe UI","PingFang SC",sans-serif}a{color:var(--brand);text-decoration:none}a:hover{text-decoration:underline}.wrap{max-width:1080px;margin:auto;padding:28px 20px 70px}.hero{padding:42px;border-radius:22px;background:linear-gradient(135deg,#111827,#1d4ed8);color:white;margin-bottom:24px}.hero h1{font-size:clamp(30px,6vw,54px);line-height:1.12;margin:0 0 14px}.hero p{max-width:780px;color:#dbeafe}.meta{display:flex;gap:12px;flex-wrap:wrap;color:#dbeafe}.pill{padding:5px 11px;border-radius:999px;background:#ffffff1a}.panel,.project{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:28px;margin:18px 0;box-shadow:0 8px 24px #1018280a}.project h2{line-height:1.25;margin:0}.rank{display:inline-grid;place-items:center;width:38px;height:38px;border-radius:11px;background:var(--accent);color:var(--brand);margin-right:10px}.stats{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0}.stat{padding:6px 10px;border-radius:8px;background:#f2f4f7;color:#344054}.tagline{font-size:19px;color:#344054}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.section{border-top:1px solid var(--line);padding-top:14px}.section h3{font-size:16px;margin:0 0 6px;color:#344054}.section ul{margin:0;padding-left:21px}.archive{display:grid;gap:10px}.archive a{display:flex;justify-content:space-between;padding:14px 16px;border:1px solid var(--line);border-radius:12px;background:white}.notice{color:var(--muted);font-size:14px}footer{color:var(--muted);text-align:center;margin-top:36px}@media(max-width:720px){.hero{padding:28px}.panel,.project{padding:20px}.grid{grid-template-columns:1fr}}
"""


def esc(value: object) -> str:
    return html.escape(str(value or ""))


def list_html(items: object) -> str:
    if not isinstance(items, list):
        items = [items] if items else []
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def page(title: str, body: str) -> str:
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="每周 GitHub 热门项目中文深度分析"><title>{esc(title)}</title><style>{CSS}</style></head><body><main class="wrap">{body}</main></body></html>"""


def render_report(report_date: str, repositories: list[dict], analysis: dict) -> str:
    analyses = {item["full_name"]: item for item in analysis["projects"]}
    cards = []
    fields = [
        ("核心功能", "core_features"), ("解决的问题", "problems"), ("典型应用", "use_cases"),
        ("适合谁", "audience"), ("差异化特点", "differentiators"), ("限制与风险", "limitations"),
        ("应用潜力", "potential"),
    ]
    for repo in repositories:
        item = analyses[repo["full_name"]]
        sections = "".join(f'<section class="section"><h3>{label}</h3>{list_html(item.get(key))}</section>' for label, key in fields)
        cards.append(f"""<article class="project"><h2><span class="rank">{repo['rank']}</span><a href="{esc(repo['html_url'])}">{esc(repo['full_name'])}</a></h2><p class="tagline">{esc(item.get('tagline'))}</p><div class="stats"><span class="stat">本周 +{repo['weekly_stars']:,} ★</span><span class="stat">总计 {repo['stars']:,} ★</span><span class="stat">{esc(repo['language'])}</span><span class="stat">{esc(repo['license'])}</span></div><p>{esc(item.get('overview'))}</p><div class="grid">{sections}<section class="section"><h3>快速开始</h3><p>{esc(item.get('quick_start'))}</p></section><section class="section"><h3>成熟度判断</h3><p>{esc(item.get('maturity'))}</p></section></div></article>""")
    top_picks = "、".join(esc(name) for name in analysis.get("top_picks", []))
    body = f"""<header class="hero"><h1>GitHub 热门项目周报</h1><p>{esc(analysis.get('trend_summary'))}</p><div class="meta"><span class="pill">{esc(report_date)}</span><span class="pill">过去一周热度增长前 10</span><span class="pill">每周六更新</span></div></header><section class="panel"><h2>本周观察</h2><p>{esc(analysis.get('trend_summary'))}</p><p><strong>编辑推荐：</strong>{top_picks}</p><p class="notice">排名采用 GitHub Trending 周榜；“本周新增 Star”为榜单页面在生成时显示的近一周数据。分析基于仓库公开信息和 README，使用前请自行核验安全性、许可证及生产适用性。</p></section>{''.join(cards)}<footer><a href="../index.html">返回历史归档</a> · 自动生成于 {esc(datetime.now().astimezone().isoformat(timespec='minutes'))}</footer>"""
    return page(f"GitHub 热门项目周报 · {report_date}", body)


def render_archive(docs_dir: Path, latest_date: str, summary: str) -> None:
    report_dir = docs_dir / "reports"
    reports = sorted(report_dir.glob("*.html"), reverse=True)
    links = "".join(f'<a href="reports/{esc(item.name)}"><strong>{esc(item.stem)}</strong><span>查看周报 →</span></a>' for item in reports)
    body = f"""<header class="hero"><h1>GitHub 热门项目周报</h1><p>每周追踪过去七天热度增长最快的开源项目，提供中文应用分析、痛点拆解和潜力判断。</p><div class="meta"><span class="pill">每周六 09:17（北京时间）</span><span class="pill">历史永久归档</span></div></header><section class="panel"><h2>最新一期 · {esc(latest_date)}</h2><p>{esc(summary)}</p><p><a href="reports/{esc(latest_date)}.html">阅读本期完整分析 →</a></p></section><section><h2>历史周报</h2><div class="archive">{links}</div></section><footer>数据来自 GitHub 公开页面与 API · 内容由 AI 辅助生成</footer>"""
    (docs_dir / "index.html").write_text(page("GitHub 热门项目周报", body), encoding="utf-8")
    (docs_dir / ".nojekyll").touch()


def write_outputs(root: Path, report_date: str, repositories: list[dict], analysis: dict) -> Path:
    docs = root / "docs"
    report_dir = docs / "reports"
    data_dir = root / "data"
    report_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{report_date}.html"
    report_path.write_text(render_report(report_date, repositories, analysis), encoding="utf-8")
    snapshot = {"date": report_date, "repositories": repositories, "analysis": analysis}
    (data_dir / f"{report_date}.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    render_archive(docs, report_date, str(analysis.get("trend_summary", "")))
    return report_path

