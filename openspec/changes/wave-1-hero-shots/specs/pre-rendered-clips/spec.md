# Spec: Pre-Rendered Clips

## ADDED Requirements

### Requirement: Minimum Clip Set

The hero shots collection SHALL include at minimum 5 clips covering key stream moments.

#### Scenario: All required clips present

- **WHEN** the hero shots directory is reviewed
- **THEN** it SHALL contain at least: 1 intro clip, 1 idle loop clip, 2 transition clips, 1 outro clip
- **AND** each clip MUST be in MP4 format
- **AND** each clip MUST be at minimum 1080p resolution

### Requirement: Catalog Metadata

Each clip SHALL have corresponding metadata in the catalog.

#### Scenario: Catalog complete

- **WHEN** `media/hero-shots/catalog.json` is parsed
- **THEN** every MP4 file in `media/hero-shots/` SHALL have a corresponding catalog entry
- **AND** each entry MUST include: filename, prompt, model, resolution, duration_seconds, use, generated_date, fallback
- **AND** at least 2 catalog entries MUST set `fallback=true`

### Requirement: OBS Integration Ready

Clips SHALL be in a format OBS can directly consume.

#### Scenario: OBS compatibility

- **WHEN** a hero shot clip is added as a Media Source in OBS
- **THEN** it SHALL play without transcoding or format errors
- **AND** the idle loop clip MUST loop seamlessly (no visible cut)
