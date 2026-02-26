# Proposal: Wave 1 — Hero Shots

## Why

The stream needs high-quality pre-rendered anime clips for intros, transitions, and showcase moments. These are generated ahead of time using SeedDance 2.0 (via JiMeng web UI) for maximum quality, since SD2.0 produces the best anime output but can't be programmatically accessed yet.

Hero shots set the quality bar for the stream and give viewers something polished to see while the live generation pipeline handles interactive requests.

## What Changes

- 5-10 pre-rendered anime clips (5-15 seconds each) generated via SeedDance 2.0
- Organized in `media/hero-shots/` with metadata
- Integrated into OBS scene collection as media sources for intro/transitions
- Prompt catalog documenting what was generated and settings used
- Explicit fallback tagging so OBS degraded mode can select safe looping clips

## Capabilities

### New Capabilities

- `hero-shot-catalog`: Collection of pre-rendered clips with metadata (prompt, model, resolution, duration)

## Impact

- New directory: `media/hero-shots/` — Pre-rendered MP4 clips
- New file: `media/hero-shots/catalog.json` — Metadata for each clip
- OBS Idle and Gallery scenes reference these clips

## Constraints

- Manual generation via JiMeng web UI (not automatable)
- Clips should be 1080p minimum for stream quality
- File size per clip should be reasonable (<50 MB)
- Must include at least: 1 intro clip, 1 idle loop, 3 transition clips
- Must include at least 2 clips tagged for degraded fallback playback
