#!/usr/bin/env python3
"""
build.py — archive.json  ->  static searchable site in ./site/

Pipeline:
    parse_smf.py  ->  archive.json  ->  build.py  ->  ./site/  ->  pagefind  ->  deploy

After running this, index search with one command (installs nothing global):
    npx -y pagefind --site site

Then open site/index.html, or deploy the whole ./site folder to GitHub Pages.
"""
import sys, json, re, shutil, pathlib, html
from datetime import datetime
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = pathlib.Path(__file__).resolve().parent.parent
TPL  = ROOT / "templates"
OUT  = ROOT / "site"

env = Environment(loader=FileSystemLoader(TPL), autoescape=select_autoescape(["html"]))

TOPIC_LINK_RE = re.compile(r"topic=(\d+)")

# Maps each recovered board to one of the curated .github/ISSUE_TEMPLATE/
# labels, so a thread continued via the "Continue this conversation on
# GitHub" button lands in the same label taxonomy as a freshly-opened Issue.
# Best-effort for boards outside the original hierarchy scrape (guessed from
# name alone) — a mislabel here is cosmetic, not a data-integrity issue.
BOARD_LABEL = {
    "b7": "introductions",
    "b1": "general-discussion", "b15": "general-discussion", "b23": "general-discussion",
    "b10": "army-lists", "b11": "army-lists",
    "b22": "battle-reports", "b26": "general-discussion",
    "b3": "painting-showcase", "b24": "painting-showcase", "b51": "painting-showcase",
    "b2": "army-blog",
    "b4": "fluff-fiction",
    "b13": "house-rules", "b52": "house-rules",
    "b6": "general-discussion", "b19": "general-discussion",
    "b8": "trading-post",
    "b18": "battle-reports", "b21": "battle-reports", "b16": "battle-reports",
    "b53": "general-discussion", "b30": "general-discussion", "b35": "general-discussion",
    "b32": "general-discussion", "b44": "general-discussion", "b48": "general-discussion",
    "b50": "general-discussion", "b56": "general-discussion", "b55": "general-discussion",
}

def rewrite_thread_links(body_html: str, known_thread_ids: set, self_id: str) -> str:
    """Cross-thread links inside a post's own body: point them at our copy
    when we have one, otherwise render them struck-through and inert — never
    send a reader through an internal link to a dead ogrestronghold.com URL."""
    if not body_html or "topic=" not in body_html:
        return body_html
    soup = BeautifulSoup(body_html, "lxml")
    changed = False
    for a in soup.select("a[href]"):
        m = TOPIC_LINK_RE.search(a["href"])
        if not m:
            continue
        target = f"t{m.group(1)}"
        changed = True
        if target in known_thread_ids:
            a["href"] = f"{target}.html" if target != self_id else f"{target}.html#top"
        else:
            span = soup.new_tag("span", **{"class": "dead-link", "title": "Thread not recovered in this archive"})
            span.string = a.get_text()
            a.replace_with(span)
    if not changed:
        return body_html
    body = soup.find("body")
    return body.decode_contents().strip() if body else str(soup)

def pretty_date(iso: str) -> str:
    if not iso:
        return "date unknown"
    try:
        return datetime.fromisoformat(iso).strftime("%d %b %Y")
    except ValueError:
        return iso

env.filters["date"] = pretty_date

def write(path: pathlib.Path, htmltext: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(htmltext, encoding="utf-8")

def main():
    data = json.loads((ROOT / (sys.argv[1] if len(sys.argv) > 1 else "archive.json")).read_text("utf-8"))
    forum      = data["forum"]
    boards     = {b["id"]: b for b in data["boards"]}
    threads    = data["threads"]
    categories = {c["id"]: c for c in data.get("categories", [])}
    stats      = data.get("stats")
    hierarchy_date = data.get("hierarchy_captured_at")

    # group threads by board, newest first
    by_board = {bid: [] for bid in boards}
    for t in threads:
        by_board.setdefault(t["board_id"], []).append(t)
    for bid in by_board:
        by_board[bid].sort(key=lambda t: t.get("created") or "", reverse=True)

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copytree(ROOT / "static", OUT / "static")

    # index: boards grouped by category, sub-boards nested under their parent —
    # order is preserved from the scraped homepage (document order), not
    # re-sorted, so the archive lays out the same way the live site did.
    boards_with_counts = {bid: {**b, "count": len(by_board.get(bid, [])), "children": []} for bid, b in boards.items()}
    top_level = []
    for b in boards_with_counts.values():
        pid = b.get("parent_id")
        if pid and pid in boards_with_counts:
            boards_with_counts[pid]["children"].append(b)
        else:
            top_level.append(b)

    groups = {cid: {"category": cat, "boards": []} for cid, cat in categories.items()}
    for b in top_level:
        cid = b.get("category_id") or "uncategorized"
        groups.setdefault(cid, {"category": {"id": cid, "name": "Other"}, "boards": []})["boards"].append(b)
    category_groups = [g for g in groups.values() if g["boards"]]

    write(OUT / "index.html", env.get_template("index.html").render(
        forum=forum, stats=stats, category_groups=category_groups, hierarchy_date=hierarchy_date,
    ))

    if forum.get("staff"):
        write(OUT / "staff.html", env.get_template("staff.html").render(forum=forum))

    # one page per board
    for bid, board in boards_with_counts.items():
        cat = categories.get(board.get("category_id"), {"name": "Other"})
        parent = boards_with_counts.get(board.get("parent_id"))
        write(OUT / "board" / f"{bid}.html", env.get_template("board.html").render(
            forum=forum, board=board, category=cat, parent=parent, threads=by_board.get(bid, []),
            hierarchy_date=hierarchy_date,
        ))

    # one page per thread
    known_thread_ids = {t["id"] for t in threads}
    for t in threads:
        for p in t["posts"]:
            p["body_html"] = rewrite_thread_links(p["body_html"], known_thread_ids, t["id"])
        write(OUT / "thread" / f"{t['id']}.html", env.get_template("thread.html").render(
            forum=forum, board=boards.get(t["board_id"], {"name": "General", "id": "general"}),
            thread=t, board_label=BOARD_LABEL.get(t["board_id"], "general-discussion"),
        ))

    # standalone pages: articles + wiki, not part of the forum but part of the site
    pages_path = ROOT / (sys.argv[2] if len(sys.argv) > 2 else "pages.json")
    pages = json.loads(pages_path.read_text("utf-8")) if pages_path.exists() else []
    articles = [p for p in pages if p["kind"] == "article"]
    wiki = [p for p in pages if p["kind"] == "wiki"]
    write(OUT / "pages.html", env.get_template("pages_index.html").render(
        forum=forum, articles=articles, wiki=wiki,
    ))
    for p in pages:
        write(OUT / "pages" / f"{p['slug']}.html", env.get_template("page.html").render(
            forum=forum, page=p,
        ))

    print(f"Built {OUT}  —  1 index, {len(boards)} boards, {len(threads)} threads, {len(pages)} articles/wiki pages")
    print("Next:  npx -y pagefind --site site   (adds client-side search)")

if __name__ == "__main__":
    main()
