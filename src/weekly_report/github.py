from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser


USER_AGENT = "github-weekly-report/1.0"


def _request(url: str, token: str = "") -> bytes:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


class TrendingParser(HTMLParser):
    """只依赖语义结构解析 Trending 页面，尽量不绑定 GitHub 的 CSS 类名。"""

    def __init__(self) -> None:
        super().__init__()
        self.in_article = False
        self.article_depth = 0
        self.current: dict[str, object] = {}
        self.items: list[dict[str, object]] = []
        self.capture_text = False
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "article" and not self.in_article:
            self.in_article = True
            self.article_depth = 1
            self.current = {"full_name": "", "weekly_stars": 0}
            self.text_parts = []
            return
        if not self.in_article:
            return
        if tag == "article":
            self.article_depth += 1
        if tag == "a":
            href = attrs_dict.get("href") or ""
            if re.fullmatch(r"/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", href):
                candidate = href.strip("/")
                owner = candidate.split("/", 1)[0].lower()
                reserved = {"sponsors", "topics", "collections", "trending", "marketplace", "settings"}
                if owner not in reserved and not self.current.get("full_name"):
                    self.current["full_name"] = candidate
        self.capture_text = True

    def handle_data(self, data: str) -> None:
        if self.in_article and self.capture_text:
            self.text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self.in_article:
            return
        if tag == "article":
            self.article_depth -= 1
            if self.article_depth == 0:
                text = " ".join(" ".join(self.text_parts).split())
                match = re.search(r"([\d,]+)\s+stars?\s+this\s+week", text, re.I)
                if match:
                    self.current["weekly_stars"] = int(match.group(1).replace(",", ""))
                if self.current.get("full_name"):
                    self.items.append(self.current)
                self.in_article = False
                self.capture_text = False


def fetch_trending(limit: int = 10) -> list[dict[str, object]]:
    url = "https://github.com/trending?since=weekly"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US"})
    with urllib.request.urlopen(req, timeout=30) as response:
        body = response.read().decode("utf-8", errors="replace")
    parser = TrendingParser()
    parser.feed(body)
    items = [item for item in parser.items if int(item["weekly_stars"]) > 0]
    if len(items) < limit:
        raise RuntimeError(f"GitHub Trending 解析结果不足：需要 {limit}，实际 {len(items)}")
    return items[:limit]


def _api_json(path: str, token: str = "") -> dict:
    url = "https://api.github.com" + path
    return json.loads(_request(url, token).decode("utf-8"))


def fetch_repository(full_name: str, token: str = "") -> dict[str, object]:
    encoded_name = urllib.parse.quote(full_name, safe="/")
    repo = _api_json(f"/repos/{encoded_name}", token)
    readme = ""
    try:
        readme_obj = _api_json(f"/repos/{encoded_name}/readme", token)
        if readme_obj.get("encoding") == "base64":
            readme = base64.b64decode(readme_obj.get("content", "")).decode("utf-8", errors="replace")
    except (urllib.error.HTTPError, ValueError):
        pass
    license_info = repo.get("license") or {}
    return {
        "full_name": repo["full_name"],
        "html_url": repo["html_url"],
        "description": repo.get("description") or "",
        "homepage": repo.get("homepage") or "",
        "language": repo.get("language") or "未知",
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "open_issues": repo.get("open_issues_count", 0),
        "topics": repo.get("topics") or [],
        "license": license_info.get("spdx_id") or license_info.get("name") or "未声明",
        "created_at": repo.get("created_at", ""),
        "updated_at": repo.get("updated_at", ""),
        "pushed_at": repo.get("pushed_at", ""),
        "archived": bool(repo.get("archived")),
        "readme": readme[:10000],
    }


def collect_weekly_repositories(token: str = "", limit: int = 10) -> list[dict[str, object]]:
    trending = fetch_trending(limit)
    results = []
    for rank, item in enumerate(trending, 1):
        repo = fetch_repository(str(item["full_name"]), token)
        repo["rank"] = rank
        repo["weekly_stars"] = item["weekly_stars"]
        results.append(repo)
    return results
