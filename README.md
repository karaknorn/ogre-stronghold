# The Ogre Stronghold — static archive

A fast, searchable, un-killable static tribute to a dead Warhammer Ogre
Kingdoms forum. No database, no server, no running forum software — just
HTML hosted on GitHub Pages.

```
archive.json + pages.json ──▶ build.py ──▶ site/ ──▶ pagefind ──▶ deploy
      (the collected data)     (generator)  (static)   (search)
```

`archive.json` is the canonical dataset — see `SCHEMA.md` for its shape.
The tooling that produced it is not part of this repo.

## Why this shape
- **Minimalist forum layout, not chat.** Threads → posts in order, with author +
  date. That structure *is* the knowledge ("which thread is this Gutstar tip in").
- **Text-first.** Images are long gone, which makes the archive tiny and perfect for
  static generation + client-side search.
- **Pagefind for search.** Indexes the built HTML, runs entirely in the browser,
  scales to thousands of threads without loading a giant index up front.

## Run it

```bash
pip install jinja2 beautifulsoup4 lxml

# Generate the static site from the collected data.
python3 scripts/build.py archive.json pages.json

# Add search (downloads a small binary via npx, indexes ./site).
npx -y pagefind --site site

# Preview locally.
python3 -m http.server -d site 8000   # → http://localhost:8000
```

## Deploy to GitHub Pages
1. **`archive.json` is large (100MB+) — over GitHub's 100MB hard per-file
   limit for a normal commit.** Install [Git LFS](https://git-lfs.com) once
   (`git lfs install`) before your *first* commit that adds this file —
   `.gitattributes` already marks it for LFS tracking.
2. `git init`, commit, push to a GitHub repo.
3. Repo → Settings → Pages → source: **GitHub Actions**. `.github/workflows/deploy.yml`
   already runs build → pagefind → deploy on every push to `main` (its checkout
   step pulls LFS content automatically).
4. Optionally set `forum.github_repo` in `archive.json` to `"owner/repo"` to turn
   on the "Continue this conversation on GitHub" button on every thread — see
   SCHEMA.md for how that layer works (no bulk issue creation, no tokens).
5. `.github/ISSUE_TEMPLATE/` gives Issues real forum-like structure for *new*
   topics — a curated set of templates (Introductions, Army Lists, Painting
   Showcase, Battle Reports, etc.) mirroring the original board categories,
   each auto-labeled so Issues stay filterable/browsable like boards did.
6. Done — a permanent, forkable, searchable memorial. Because it's a repo, the
   *archive itself* can be forked and mirrored, so it can't die either.

## The one rule that keeps this clean
The posts belong to the people who wrote them. Keep usernames and dates intact
(the generator already does), keep it non-commercial and clearly a memorial,
and honour any "please remove my posts" request without fuss. See the note
baked into every page footer.

## Files
- `scripts/build.py` — `archive.json` + `pages.json` → `site/` via Jinja2
- `.github/workflows/deploy.yml` — build + pagefind + deploy to Pages on push
- `templates/` — base / index / board / thread / page / pages_index (edit these to reskin)
- `static/style.css` — the mountain-hold theme; all personality lives here
- `static/images/header.jpg` — the site's own original banner
- `SCHEMA.md` — the `archive.json` contract
- `archive.json` / `pages.json` — the collected data
