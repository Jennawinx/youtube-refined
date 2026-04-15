# YouTube Refined - Brainstorm

## Project Goal
Create a custom dashboard of YouTube videos that uses a personal algorithm for suggesting videos (subset of YouTube content, not all videos).

## Product Intent
The purpose of this custom youTube feed is to natually change the feed according to ones lifestlye and encourage a healthy viewing behaiour. The dashboard should adapt the feed to the user's daily rhythm instead of a youtube's original algorithm which is an endless dopamine trap.

Example routine:
- Morning: motivating videos, morning routines, energy-setting content
- Lunch: trusted news, explainers, educational videos, how-to content
- Afternoon: work-related content, tech updates, business ideas, professional growth
- Night: calmer videos, vlogs, music, lighter content that helps the user wind down

The purpose is to make video consumption feel intentional and healthy:
- reduce mindless scrolling
- encourage context-appropriate viewing
- shape the feed around lifestyle rather than pure engagement
- make the dashboard feel more like a curated daily companion than a content firehose

---

## Key Challenges to Solve

1. **Data Collection**
   - How to fetch video metadata from YouTube?
   - What data points matter for recommendations? (views, likes, comments, duration, category, upload date, etc.)
   - Rate limiting & API quotas
   - Privacy & ToS compliance

2. **Algorithm Design**
   - What variables influence a "good" recommendation for the user?
   - Personalization: user history, preferences, watch patterns?
   - Content filtering/curation strategy
   - How to rank/score videos?
  - How should ranking change by time of day?
  - How do we avoid showing stimulating or low-value content at the wrong time?

3. **Data Storage**
   - Database schema for videos, user data, interaction history
   - How much data to cache locally vs. fetch dynamically?

4. **Frontend/UI**
   - Dashboard layout & interaction design
   - Video discovery experience
   - Real-time vs. pre-computed recommendations

5. **Backend Architecture**
   - API endpoints needed
   - How to run the recommendation algorithm (on-demand vs. batch jobs)
   - Scaling considerations

---

## Potential Tech Stack (to discuss)

**Frontend Options:**
- React / Vue / Svelte
- TypeScript for type safety
- Tailwind CSS / Material-UI for styling

**Backend Options:**
- Node.js (Express/Next.js)
- Python (Flask/FastAPI) for algorithm work
- Or both?

**Database:**
- PostgreSQL / MongoDB
- Redis for caching

**Infrastructure:**
- Docker for containerization
- GitHub for version control
- Hosting: Vercel, Netlify, AWS, etc.

---

## MVP (Minimum Viable Product) Scope

What's the smallest version we can build to validate the idea?

- [ ] Fetch ~100 videos from YouTube API
- [ ] Store in a database
- [ ] Build a simple ranking algorithm
- [ ] Display videos in a basic dashboard
- [ ] Allow user to rate/interact with videos

---

## Project Decisions

✅ **Single-user project** - for personal use only
✅ **MVP scope: Subscribed channels only** - start with videos from channels you're already subscribed to
✅ **Tech stack: Django + Templating + Tailwind CSS** - keep it simple and lean
✅ **YouTube API: Defer for now** - explore alternatives or manual approaches first
✅ **Approach: Brainstorm architecture first** - design the system before coding

---

---

---

## 🎯 CHOSEN APPROACH: RSS Feeds (with optional YouTube API for stats later)

### MVP Design Decisions

✅ **Database:** SQLite with separate `channels` and `videos` tables
✅ **Channel Management:** Pre-populated via migration, UI button to add, future CSV import/export
✅ **Refresh Strategy:** Manual refresh button (user-triggered)
✅ **Update Tracking:** Track `last_updated` (null if never fetched) per channel
✅ **Upload Frequency:** Store `upload_frequency` per channel (default: biweekly, algo later to auto-detect)
✅ **Sorting:** By publish_date DESC (newest first)
✅ **Recommendation Theme:** Time-of-day feed shaping for healthier viewing behavior

---

## Recommendation Vision

### Feed Philosophy
This is not just a "latest uploads" dashboard.

The long-term goal is to rank videos based on:
- the active feed rule for the current time/day
- desired mindset for that rule window
- user lifestyle goals
- healthy viewing behavior over raw engagement

### Dynamic Feed Windows

Time slots should be user-defined rather than hardcoded.

Examples of possible rule windows:
- weekdays from 6:00 AM to 9:00 AM for motivating or routine content
- weekdays from 12:00 PM to 1:00 PM for news, explainers, or how-to videos
- weekdays from 1:00 PM to 6:00 PM for work, tech, or business content
- evenings from 8:00 PM onward for calmer content, music, or lighter vlogs

### What This Implies for the Product
- the same channel may be useful in one rule window and less useful in another
- recency alone is not enough; videos need a contextual score
- recommendation logic should come from configurable rules, not fixed app logic
- some content may be intentionally down-ranked at certain times of day
- eventually the system should help the user consume less but better

---

## Database Schema

### Tables

#### `channels` table
```sql
CREATE TABLE channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT UNIQUE NOT NULL,      -- YouTube channel ID (e.g., "UC_x5XG1OV2P6uZZ5FSM9Ttw")
    name TEXT NOT NULL,                   -- Channel name
    url TEXT NOT NULL,                    -- YouTube channel URL
    thumbnail_url TEXT,                   -- Channel avatar
    upload_frequency TEXT DEFAULT 'biweekly',  -- Expected upload frequency (biweekly, weekly, daily, etc.)
    last_updated DATETIME,                -- Last time we fetched this channel's feed (NULL = never fetched)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### `videos` table
```sql
CREATE TABLE videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT UNIQUE NOT NULL,        -- YouTube video ID
    channel_id INTEGER NOT NULL,          -- Foreign key to channels.id
    title TEXT NOT NULL,
    description TEXT,
    url TEXT NOT NULL,                    -- Full YouTube URL
    thumbnail_url TEXT,
    publish_date DATETIME NOT NULL,       -- When video was published
    category_tags TEXT,                   -- JSON array of tags, e.g. ["motivation", "morning-routine"]
    duration_seconds INTEGER,             -- Video length in seconds (future: from API)
    view_count INTEGER,                   -- Future: from API
    is_watched BOOLEAN DEFAULT FALSE,     -- User interaction
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(channel_id) REFERENCES channels(id)
);
```

  #### `feed_rules` table
  ```sql
  CREATE TABLE feed_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                   -- Optional label like "weekday lunch learning"
    monday BOOLEAN DEFAULT FALSE,
    tuesday BOOLEAN DEFAULT FALSE,
    wednesday BOOLEAN DEFAULT FALSE,
    thursday BOOLEAN DEFAULT FALSE,
    friday BOOLEAN DEFAULT FALSE,
    saturday BOOLEAN DEFAULT FALSE,
    sunday BOOLEAN DEFAULT FALSE,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    category_tag TEXT NOT NULL,           -- Tag to match against videos.category_tags
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );
  ```

### JSON Array Decision for `category_tags`

Yes, SQLite supports JSON arrays through its JSON functions.

Important detail:
- SQLite does not have a native `JSON` column type
- JSON is typically stored as `TEXT`
- modern SQLite versions include built-in JSON functions by default
- this means `category_tags` can safely be stored as JSON text such as:

```json
["motivation", "morning-routine", "wellness"]
```

Example queries:

```sql
SELECT *
FROM videos
WHERE EXISTS (
    SELECT 1
    FROM json_each(videos.category_tags)
    WHERE json_each.value = 'motivation'
);
```

```sql
SELECT json_array_length(category_tags)
FROM videos;
```

### Performance Implications

For this project, JSON arrays in SQLite are a good fit for MVP scale.

Pros:
- flexible and easy to evolve without schema churn
- natural representation for multiple tags per video
- easy to work with in Django/Python
- good enough for small to moderate datasets

Tradeoffs:
- SQLite still stores JSON as text unless you explicitly use newer JSONB functions internally
- membership checks require parsing JSON during queries
- indexing inside JSON arrays is limited compared to a normalized join table
- filtering by tag across a very large video table will be slower than a dedicated `video_tags` table

Practical guidance:
- for hundreds or low thousands of videos: totally reasonable
- for tens of thousands of videos with lots of tag-based filtering: expect slower queries
- if tag filtering becomes central and the dataset grows, normalize later into `tags` + `video_tags`

Recommendation:
- use JSON arrays now for simplicity
- keep `feed_rules.category_tag` as a single string
- match rules against `videos.category_tags` using `json_each(...)`
- revisit normalization only if real query performance becomes a problem

### Diagram

```
┌─────────────────────────────────────┐
│         channels                    │
├─────────────────────────────────────┤
│ id (PK)                             │
│ channel_id (UNIQUE)                 │
│ name                                │
│ url                                 │
│ thumbnail_url                       │
│ upload_frequency                    │
│ last_updated ← ⭐ TRACKS REFRESH    │
│ created_at                          │
│ updated_at                          │
└────────────┬────────────────────────┘
             │
             │ 1:N
             │
┌────────────▼────────────────────────┐
│         videos                      │
├─────────────────────────────────────┤
│ id (PK)                             │
│ video_id (UNIQUE)                   │
│ channel_id (FK)                     │
│ title                               │
│ description                         │
│ url                                 │
│ thumbnail_url                       │
│ publish_date ← ⭐ SORT BY THIS      │
│ category_tags                       │
│ duration_seconds                    │
│ view_count (future)                 │
│ is_watched                          │
│ created_at                          │
│ updated_at                          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         feed_rules                  │
├─────────────────────────────────────┤
│ id (PK)                             │
│ name                                │
│ monday                              │
│ tuesday                             │
│ wednesday                           │
│ thursday                            │
│ friday                              │
│ saturday                            │
│ sunday                              │
│ start_time                          │
│ end_time                            │
│ category_tag                        │
│ created_at                          │
│ updated_at                          │
└─────────────────────────────────────┘
```

---

## Recommendation Approach (No Coding Yet)

### Phase 1: Simple but Useful
Start with a lightweight rule-based system:
- determine the currently active feed rule based on day + time
- show newest videos first
- prefer videos whose `category_tags` match the active rule's `category_tag`
- optionally de-prioritize mismatched content

Example:
$$
score = recency + rule\_match - mismatch\_penalty
$$

Where:
- `recency` rewards recent uploads
- `rule_match` boosts content matching the currently active feed rule
- `mismatch_penalty` reduces content that feels wrong for the moment

### Phase 2: Add Better Classification
Later, classify each channel or video into buckets such as:
- motivation
- routine
- news
- explainers
- tutorial
- work/tech
- business
- vlog
- music
- calm

This can start with manual tags stored in `videos.category_tags`, then later move to better inference.

### Phase 3: Healthier Viewing Controls
Later the product can actively shape behavior:
- cap highly stimulating content late at night
- prioritize shorter educational videos at lunch
- reduce repetitive binge patterns from the same channel
- surface "good next watch" options instead of infinite scroll

---

## Data Collection & API Details

### 1. YouTube API

#### Core Functionalities Available
**Public Data (No Auth Required):**
- `videos.list()` - Get video metadata (title, description, duration, statistics)
- `channels.list()` - Get channel information
- `search.list()` - Search YouTube content (costs 100 quota units per request!)
- `playlistItems.list()` - Get videos from a playlist (costs 1 unit)
- `subscriptions.list()` - List authenticated user's subscriptions

**Statistics Available:**
- View count, like count, comment count, upload date
- Video duration, category, thumbnails
- Channel subscriber count (if public)

#### Quota & Pricing Model
- **Free Tier:** 10,000 quota units per day
- **Cost Structure:**
  - Read operations (list): 1 unit each
  - Write operations (create/update/delete): 50 units each
  - Search: 100 units each
  - Video upload: 100 units each
- **How to stay within free tier:**
  - 10,000 list operations/day (easily fetch 100+ videos daily)
  - Use `playlistItems.list` instead of search (1 vs 100 units)
  - Cache results, don't re-fetch unnecessarily
- **Paid Beyond:** Can request additional quota by filling out a form

#### Pros & Cons
✅ Official, reliable, complete metadata
✅ Easy to implement (Google client libraries)
✅ No scraping legal risks
❌ Requires API key setup & OAuth for authenticated requests
❌ Rate limits if you exceed quota
❌ 10,000 units/day is tight if you search frequently

---

### 2. RSS Feeds

#### What Are RSS Feeds?
RSS = "Really Simple Syndication" or "RDF Site Summary"
- XML-based format for distributing frequently updated content
- Each YouTube channel has a public RSS feed at: `https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID`
- Feeds contain: title, description, publish date, video URL, thumbnail

#### Example RSS Feed Structure
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Channel Name</title>
    <link>https://www.youtube.com/channel/UC_xxx</link>
    <item>
      <title>Video Title</title>
      <description>Video Description</description>
      <link>https://www.youtube.com/watch?v=VIDEO_ID</link>
      <pubDate>Sun, 15 Apr 2026 12:30:00 +0000</pubDate>
    </item>
  </channel>
</rss>
```

#### How to Use (for your project)
1. Collect list of YouTube channel IDs (from subscriptions list)
2. Construct RSS feed URLs for each channel
3. Fetch RSS feeds daily/weekly
4. Parse XML and extract video metadata
5. Store in database

#### Limitations
- Limited metadata: Title, description, upload date, thumbnail
- **NO statistics:** View count, likes, comments NOT in RSS feed
- Updates are delayed (15-30 minutes after video upload)
- Most recent ~15 videos per channel

#### Pros & Cons
✅ **Free** - no API key needed
✅ Public feeds, no authentication required
✅ Simple HTTP GET requests
✅ Light on bandwidth
✅ Legal & ToS compliant
❌ Limited metadata (no stats)
❌ Delayed updates
❌ Only recent videos (~15 per channel)
❌ Can't get user interaction data (if needed)

---

### 3. Web Scraping

#### What It Is
Writing code to automatically visit YouTube.com, parse HTML, and extract data without using official APIs.

#### Legal & ToS Risks

**ToS Violations:**
- YouTube's ToS explicitly prohibits scraping: "You agree not to... scrape or download (whether through a robot, spider, scraper, script, wget, curl, or any other automated means) any portion of the Services..."
- Could result in: IP ban, account suspension, legal cease & desist

**Technical Risks:**
- YouTube actively detects and blocks bots (changing HTML structure, CAPTCHA challenges)
- Requires maintaining browser-like headers & cookies
- Fragile - breaks when YouTube updates their website

**Legal Risks:**
- Potential copyright/DMCA violation if you republish content
- Depends on jurisdiction, but generally not worth the risk for personal projects
- Could face legal action from Google/YouTube

#### Why Not Recommended
🚫 Violates YouTube ToS
🚫 High maintenance (breaks frequently)
🚫 Legal risk (even for personal use)
🚫 Gets you IP banned quickly

---

## Recommended Approach for MVP

**HYBRID STRATEGY:**
1. **Primary:** Use RSS feeds for video discovery (free, light, legal)
2. **Secondary:** Optional YouTube API for enriching stats (view count, likes, comments)
   - Only call API when needed (not every request)
   - Cache results aggressively
   - Stay within free 10k units/day

**Why this works:**
- No cost for MVP
- Fully legal & ToS compliant
- Simple to implement
- Can upgrade to full API later if needed
---

## RSS Fetch Workflow

### Manual Refresh Flow
```
User clicks "Refresh" button
    ↓
For each channel in database:
    ↓
Fetch RSS feed: https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}
    ↓
Parse XML → Extract video items
    ↓
For each video:
    - Check if video_id already exists in DB
    - If new: INSERT into videos table
    - If exists: SKIP (avoid duplicates)
    ↓
UPDATE channels.last_updated = NOW()
    ↓
Display updated feed to user
```

### What We Extract from RSS
```
From each video item:
- video_id (extract from URL: youtube.com/watch?v=VIDEO_ID)
- title
- description (or summary)
- url (full YouTube link)
- thumbnail_url
- publish_date
- channel_id (from parent channel)
```

### Initial Channel Setup
```
Django migration creates initial channels:
[
    {
        channel_id: "UC_x5XG1OV2P6uZZ5FSM9Ttw",
        name: "Google Developers",
        url: "https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw",
        upload_frequency: "biweekly",
        last_updated: null
    },
    ... (add your real subscribed channels here)
]
```
---

## Architecture Approach: Subscribed Channels MVP

### High-Level System Flow

**Input Layer:**
- User provides list of subscribed YouTube channels (manual input, CSV, or JSON)
- We fetch video data from those channels

**Processing Layer:**
- Store videos in database with metadata
- Apply ranking algorithm to score videos
- Run daily/weekly refresh to get new videos

**Output Layer:**
- Dashboard displays ranked videos
- User can filter, interact, rate videos

### Key Questions for this Architecture

1. **How do we get video data without YouTube API?**
   - Option A: YouTube RSS feeds (public, no auth needed)
   - Option B: Web scraping
   - Option C: User manually uploads video data
   - Option D: Use a third-party service/API (paid or free tier)

2. **What metadata do we store per video?**
   - Title, description, URL, thumbnail
   - Upload date, duration
   - View count, likes, comments (if available)
   - Channel name, channel URL
   - User rating/interaction (1-5 stars, watched, bookmarked, etc.)

3. **Ranking Algorithm - What factors matter?**
   - Recency (newer videos ranked higher?)
   - Engagement (views, likes relative to channel size?)
   - User preferences (tags, categories)?
   - Diversity (don't show 10 videos from same channel?)

4. **User Interaction Model**
   - How does the user rate/interact with videos?
   - Should we learn from their interactions to improve future recommendations?
   - Track watch history?

---

## Proposed Data Flow Diagram

```
┌─────────────────────┐
│  User Input         │
│ (List of channels)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Data Collection (Daily/Weekly)     │
│ • Fetch from RSS/Scraping/API       │
│ • Extract video metadata            │
│ • Store in DB (avoid duplicates)    │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Video Database                     │
│ • videos table                      │
│ • user_interactions table           │
│ • channels table                    │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Ranking Algorithm                  │
│ • Score videos based on criteria    │
│ • Apply sorting/filtering           │
│ • Consider user interactions        │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Django Dashboard                   │
│ • Display ranked videos             │
│ • User interactions (rate, bookmark)│
│ • Filter/search functionality       │
└─────────────────────────────────────┘
```
