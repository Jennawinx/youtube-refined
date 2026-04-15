# YouTube Refined - Architecture

## Project Overview

A personal YouTube dashboard with a custom recommendation algorithm that shapes the feed around daily lifestyle rhythms rather than engagement-driven algorithms. Single-user, local-first, desktop-friendly.

---

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Backend | Django (Python) | Standard project, Django templates |
| Frontend | Django templates + Tailwind CSS | No separate JS framework |
| Database | SQLite | Single file, portable, desktop-friendly |
| Data Collection | YouTube RSS feeds | Free, no auth, ToS-compliant |
| Desktop packaging | Tauri (future) | Wrap Django app when feature-complete |

---

## Data Collection Strategy

**Primary: YouTube RSS Feeds**
- Endpoint: `https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID`
- Free, no API key required, ToS-compliant
- Returns: title, description, publish date, video URL, thumbnail
- Limitation: ~15 most recent videos per channel, no stats (views/likes)

**Future enrichment: YouTube Data API v3**
- Optional — used only to fill in `duration_seconds` and other metadata
- Free tier: 10,000 quota units/day
- Use `playlistItems.list` (1 unit) over `search.list` (100 units)

**Ruled out: Web scraping**
- Violates YouTube ToS, fragile, legal risk

---

## Database Schema

### `channels`
```sql
CREATE TABLE channels (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id       TEXT UNIQUE NOT NULL,         -- YouTube channel ID
    name             TEXT NOT NULL,
    upload_frequency TEXT DEFAULT 'biweekly',      -- biweekly | weekly | daily
    last_updated     DATETIME,                     -- NULL = never fetched
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### `videos`
```sql
CREATE TABLE videos (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id         TEXT UNIQUE NOT NULL,         -- YouTube video ID
    channel_id       INTEGER NOT NULL,             -- FK → channels.id
    title            TEXT NOT NULL,
    description      TEXT,
    url              TEXT NOT NULL,
    thumbnail_url    TEXT,
    publish_date     DATETIME NOT NULL,            -- primary sort key
    category_tags    TEXT,                         -- JSON array e.g. ["motivation", "morning-routine"]
    duration_seconds INTEGER,                      -- future: populated via YouTube API
    is_watched       BOOLEAN DEFAULT FALSE,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(channel_id) REFERENCES channels(id)
);
```

### `feed_rules`
```sql
CREATE TABLE feed_rules (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,                   -- e.g. "weekday lunch learning"
    monday       BOOLEAN DEFAULT FALSE,
    tuesday      BOOLEAN DEFAULT FALSE,
    wednesday    BOOLEAN DEFAULT FALSE,
    thursday     BOOLEAN DEFAULT FALSE,
    friday       BOOLEAN DEFAULT FALSE,
    saturday     BOOLEAN DEFAULT FALSE,
    sunday       BOOLEAN DEFAULT FALSE,
    start_time   TIME NOT NULL,
    end_time     TIME NOT NULL,
    category_tag TEXT NOT NULL,                   -- matched against videos.category_tags
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Schema Diagram
```
┌──────────────────────────┐
│         channels         │
├──────────────────────────┤
│ id (PK)                  │
│ channel_id (UNIQUE)      │
│ name                     │
│ upload_frequency         │
│ last_updated             │
│ created_at               │
│ updated_at               │
└────────────┬─────────────┘
             │ 1:N
┌────────────▼─────────────┐
│          videos          │
├──────────────────────────┤
│ id (PK)                  │
│ video_id (UNIQUE)        │
│ channel_id (FK)          │
│ title                    │
│ description              │
│ url                      │
│ thumbnail_url            │
│ publish_date ← sort key  │
│ category_tags (JSON)     │
│ duration_seconds         │
│ is_watched               │
│ created_at               │
│ updated_at               │
└──────────────────────────┘

┌──────────────────────────┐
│        feed_rules        │
├──────────────────────────┤
│ id (PK)                  │
│ name                     │
│ monday … sunday          │
│ start_time               │
│ end_time                 │
│ category_tag             │
│ created_at               │
│ updated_at               │
└──────────────────────────┘
```

---

## Key Design Decisions

### `category_tags` — JSON Array in SQLite
Stored as `TEXT` containing a JSON array (e.g. `["motivation", "morning-routine"]`).

SQLite supports this via built-in JSON functions (available since SQLite 3.38.0):

```sql
-- Find videos matching a tag
SELECT * FROM videos
WHERE EXISTS (
    SELECT 1 FROM json_each(videos.category_tags)
    WHERE json_each.value = 'motivation'
);
```

**Tradeoff:** Fine for hundreds–low thousands of videos. If tag-filtering at scale becomes a bottleneck, normalize into a `video_tags` join table later.

### Channel Management
- Channels pre-populated via Django data migration
- UI to add/remove channels (MVP)
- No CSV upload in MVP

### Refresh Strategy
- Manual refresh button only (no background scheduler for MVP)
- Per-channel `last_updated` tracks fetch history
- Duplicate videos skipped via `video_id` uniqueness check

### Default Feed Sorting
- `publish_date DESC` as base ordering
- Boosted/filtered by active `feed_rules` match at request time

---

## Recommendation Algorithm

### Phase 1 — Rule-based (MVP)
Match the current day + time against `feed_rules`. Score and sort videos:

$$
score = recency + rule\_match - mismatch\_penalty
$$

- `recency` — reward recent uploads
- `rule_match` — boost videos whose `category_tags` include the active rule's `category_tag`
- `mismatch_penalty` — down-rank content mismatched for the current time window

### Phase 2 — Better Classification (Future)
Introduce content buckets: `motivation`, `news`, `tutorial`, `work/tech`, `vlog`, `music`, `calm`, etc. Initially via manual `category_tags`, later via inference.

### Phase 3 — Healthier Viewing Controls (Future)
- Cap stimulating content late at night
- Limit binge patterns from a single channel
- Surface intentional "next watch" options

---

## RSS Fetch Flow

```
User clicks "Refresh"
    ↓
For each channel in DB:
    Fetch https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}
    ↓
    Parse XML → extract video items
    ↓
    For each video:
        if video_id not in DB → INSERT
        else → SKIP
    ↓
    UPDATE channels.last_updated = NOW()
    ↓
Redirect to updated feed
```

---

## Desktop Packaging Plan

Build order:
1. Finish Django web app (SQLite + templates + Tailwind)
2. Ensure app is fully local — no remote hosting dependency
3. Package with Tauri (recommended) or Electron

**Options:**
| Option | Pros | Cons |
|---|---|---|
| Tauri | Lightweight, modern | Requires Rust toolchain |
| Electron | Mature, many examples | Heavy footprint |
| pywebview | Pure Python, simple | Fewer production patterns |

**Desktop-readiness constraints to maintain throughout development:**
- Use portable SQLite file paths (no hardcoded absolute paths)
- No assumptions that the app runs in a browser tab
- Avoid hard dependency on remote hosting for core flows
- Keep refresh jobs tied to explicit user actions (no background daemons in MVP)
