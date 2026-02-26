# Tasks: Wave 1 — Hero Shots

## 1. Setup

- [ ] 1.1 Create `media/hero-shots/` directory
- [ ] 1.2 Create `media/hero-shots/catalog.json` with empty clips array

## 2. Generate Clips (Manual — Human)

- [ ] 2.1 Generate intro clip (10s, dramatic establishing shot) via SeedDance 2.0 / JiMeng
- [ ] 2.2 Generate idle loop clip (15s, calm loopable scene) via SeedDance 2.0 / JiMeng
- [ ] 2.3 Generate transition clip A (3s, fast wipe/zoom) via SeedDance 2.0 / JiMeng
- [ ] 2.4 Generate transition clip B (3s, alternate style) via SeedDance 2.0 / JiMeng
- [ ] 2.5 Generate outro clip (10s, closing shot) via SeedDance 2.0 / JiMeng

## 3. Catalog and Organize

- [ ] 3.1 Download all clips, rename to convention: `{use}-{description}.mp4`
- [ ] 3.2 Add metadata entries to `catalog.json` for each clip
- [ ] 3.3 Add `fallback` tags in `catalog.json` for degraded mode selection
- [ ] 3.4 Verify all clips are 1080p+ and MP4 format

## 4. Verify

- [ ] 4.1 All 5 minimum clips present in `media/hero-shots/`
- [ ] 4.2 `catalog.json` has entries for all clips
- [ ] 4.3 Test clips load in OBS as Media Sources without error
- [ ] 4.4 Idle loop plays seamlessly on repeat
- [ ] 4.5 At least 2 clips validated for fallback scene playback
