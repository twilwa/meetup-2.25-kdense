# Design: Wave 1 — Hero Shots

## Context

SeedDance 2.0 produces the highest quality anime video but is only accessible via JiMeng web UI. This is a manual workstream — a human generates clips in the browser and downloads them.

## Goals

- 5-10 polished anime clips ready for OBS integration
- Clips cover key stream moments: intro, idle, transitions
- Catalog with prompt/settings for reproducibility

## Non-Goals

- Automating SeedDance 2.0 (API not available)
- Character consistency across hero shots (nice-to-have, not required)
- Audio generation in hero shots (add in Wave 2)

## Decisions

### Decision 1: SeedDance 2.0 via JiMeng

Use JiMeng AI (jimeng.com) web interface. Generate at maximum available resolution (up to 2K). Download MP4 directly.

### Decision 2: Catalog as JSON

Store metadata in `media/hero-shots/catalog.json` rather than markdown. JSON is machine-readable — future automation can use it for gallery rotation, random selection, etc.

```json
{
  "clips": [
    {
      "filename": "intro-sakura-wind.mp4",
      "prompt": "anime cherry blossom petals blowing in wind, cinematic, 4K",
      "model": "seedance-2.0",
      "resolution": "1920x1080",
      "duration_seconds": 10,
      "use": "intro",
      "generated_date": "2026-02-25"
    }
  ]
}
```

### Decision 3: Minimum Set

Prioritize these 5 clips for MVP:
1. **Intro** (10s) — dramatic establishing shot, channel branding
2. **Idle loop** (15s, loopable) — calm scene for between generations
3. **Transition A** (3s) — fast wipe/zoom for scene changes
4. **Transition B** (3s) — different style transition
5. **Outro** (10s) — closing shot

### Decision 4: Fallback Tags in Catalog

Each clip entry includes a `fallback` boolean so OBS degraded mode can select only safe loop/background assets.

## Technical Approach

```
Human workflow:
  1. Open jimeng.com
  2. Enter prompt from catalog template
  3. Select highest resolution
  4. Generate and download
  5. Rename to convention: {use}-{description}.mp4
  6. Add entry to catalog.json
  7. Copy to media/hero-shots/
```
