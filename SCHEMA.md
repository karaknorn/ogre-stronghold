# archive.json — the canonical format

Everything the site renders flows through this one file — `build.py`'s only
job is turning it into static HTML. This doc describes its shape.

```jsonc
{
  "forum": {
    "name": "The Ogre Stronghold",
    "tagline": "The first and largest home of the Ogre Kingdoms — preserved.",
    "source_url": "http://www.ogrestronghold.com/forum/",
    "archived_note": "Community archive of a forum that went offline. Posts remain the property of their authors.",
    "github_repo": "yourname/ogre-stronghold-archive",
    "welcome_html": "<p>Welcome to the Ogre Stronghold...</p>"
  },
  "stats": {
    "members": 7105, "posts": 381371, "topics": 27485,
    "newest_member": "ForsetisMuse", "captured_at": "2015-09-06"
  },
  "hierarchy_captured_at": "2007-12-24",
  "categories": [
    { "id": "c4", "name": "Hobby" }
  ],
  "boards": [
    { "id": "b3", "name": "Ogre Tactics", "category_id": "c4", "parent_id": null,
      "description": "Gutstar, Mournfang, and the art of eating armies.",
      "topics": 1369, "posts": 9940 },
    { "id": "b24", "name": "Halfling Cookbook", "category_id": "c4", "parent_id": "b3",
      "description": "", "topics": 48, "posts": 559 }
  ],
  "threads": [
    {
      "id": "t22628",
      "board_id": "b3",
      "title": "Gutstar list help vs Dwarfs",
      "author": "sgtgotten",
      "created": "2013-02-05T10:38:00",
      "source_url": "http://www.ogrestronghold.com/forum/index.php?topic=22628.0",
      "poll": {
        "question": "Do you like powertracks style rocking?",
        "options": [
          { "label": "Yes", "votes": 4, "percent": 66.7 },
          { "label": "No", "votes": 2, "percent": 33.3 }
        ],
        "total_votes": 6,
        "voting_closed": "2006-01-05T08:19:04"
      },
      "posts": [
        {
          "author": "sgtgotten",
          "date": "2013-02-05T10:38:00",
          "body_html": "<p>Running 2 Ironblasters...</p>",
          "body_text": "Running 2 Ironblasters...",
          "signature": { "body_html": "Painting: 2 Ironblasters, 1 Slaughtermaster", "body_text": "Painting: 2 Ironblasters, 1 Slaughtermaster" }
        }
      ]
    }
  ]
}
```

## The GitHub Issues comment layer
Set `forum.github_repo` (`"owner/repo"`) once the archive's GitHub repo exists and
every thread page grows a "Continue this conversation on GitHub" button. It's a
plain link with no API calls or tokens involved — `https://github.com/<repo>/issues/new?title=...&body=...`,
GitHub's own pre-filled-issue URL scheme. Nothing is created until a real person
clicks it and signs in. This deliberately avoids bulk-creating ~5,000 issues up
front (rate limits, notification spam, and an issue nobody ever replies to is just
noise) — issues appear organically, one per thread someone actually wants to
revive. Leave `github_repo` blank to keep the site read-only with no button.

Each pre-filled issue body includes a hidden `Archived-Thread-Id: tNNNN` line.
A future sync step (not built yet) could scan open issues for that marker and
rebuild a thread-id → issue-number map, so a second visitor lands on the existing
issue instead of opening a duplicate. Until that exists, the footer hint asks
people to check for an existing issue first.

## Signatures
Per-post `signature` is `null` when the poster had none. Text-only by design —
the parser strips images and unwraps links (drops the href, keeps any visible
text), since most signature images point at long-dead third-party hosts and
this project would rather not resurface personal outbound links decades later.

## Polls
`poll` is `null` on threads that never had one. Vote counts and percentages are
frozen at whatever the last archived capture shows — voting is dead along with
the forum, this is just the final tally.

## Categories, boards, and sub-boards
SMF groups boards under categories (e.g. "Hobby" containing "Ogre Tactics",
"Painting", "Conversions") and lets a board itself have child boards (a
"Sub-forum" of another board). Every board has a `category_id`; a board
recovered without one gets the literal `"uncategorized"`. `parent_id` is `null`
for a top-level board, or another board's `id` for a sub-board. The generator
nests sub-boards under their parent on the homepage rather than listing them
flat, and preserves the *order* boards were scraped in (the live site's own
layout) rather than re-sorting by activity.

`topics`/`posts` on a board are a single point-in-time snapshot from its
homepage (see below) — **not** a "total" to compute a recovery percentage
against. The archive's threads span the board's entire lifetime, while the
count is frozen at whatever moment the homepage was scraped, so a
long-lived, still-growing board can easily show *more* recovered threads
than that one snapshot ever recorded. The generator shows the snapshot
count as dated context ("had 1,687 topics as of Dec 2007"), never as
"X of Y recovered" — that framing was tried and quietly produced boards
reading "900% recovered," which is a data-honesty bug, not a good sign.

## Hierarchy and stats are separate snapshots, on purpose
`hierarchy_captured_at` / `stats.captured_at` — the board tree (with its
richer sub-forum structure) and the global stats bar reflect two different
points in the forum's life rather than one merged "current" view, since the
site reorganized its categories/boards at least once and no single snapshot
had both the fullest structure and the final numbers. Same "frozen at
capture time" honesty as poll results, just applied to two dates instead of one.

## Unrecovered cross-links
A post that links to another thread (`topic=NNNN`) gets that link rewritten to
the local copy if it exists in this archive, and replaced with an inert,
struck-through `<span class="dead-link">` if it doesn't — never a live link
out to a dead ogrestronghold.com URL. Done at build time (`build.py`'s
`rewrite_thread_links`), not in `archive.json` itself, since it depends on
which *other* threads ended up in the same build.

## Rules that keep it clean
- **Preserve attribution.** `author` and `date` on every post — you are saving
  people's words *as theirs*. Never strip usernames.
- **Keep `source_url`.** Links back to the original (even if dead, the Wayback copy
  resolves), so the archive is honest about where each thread came from.
- **`body_text` is what search indexes; `body_html` is what renders.** Store both.
- IDs are strings and stable (reuse the original SMF topic id) so URLs never change.

## pages.json — articles and the OgreWiki
A second, much smaller file for the non-forum parts of the site that are
still worth keeping — tactics/painting articles, the OgreWiki. Not part of
`archive.json` because they're not forum threads at all:

```jsonc
[
  { "slug": "article3", "kind": "article", "title": "A rundown of the Ogre character choices",
    "author": "Pepi Harlem (Damoun)", "body_html": "...", "body_text": "..." },
  { "slug": "Ogre_Bulls", "kind": "wiki", "title": "Ogre Bulls",
    "author": "", "body_html": "...", "body_text": "..." }
]
```
