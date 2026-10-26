# 42-effect completeness and release acceptance

## Coverage contract
The 42 names are pinned in `skills/video-director/references/effects-manifest.json`, ordered exactly as the original registry. No effect may be silently omitted, renamed, merged or replaced. Aliases and named looks must also resolve.

## Automated evidence
- Unit test reads actual renderer Python AST to verify all 42 effects exist.
- All aliases and named looks are extracted dynamically from the engine.
- 42 independent PNG renders plus 5 named-look renders run across six GitHub Actions jobs.
- Each render writes its own JSON plan, preview and machine-readable success/failure record.
- A failure makes the job red; no suppressed errors.
- Synthetic video rendering detects crashes and missing dependencies, **not** visual correctness.

## Human approval gates
- Inspect each of 47 PNG frames for face clipping, text truncation, missing typography, misplaced layers, invented values, downstream branding, colour consistency and readability.
- Retest with real portrait footage, real landscape footage and occlusions.
- Render short video segments for each effect to check motion, interpolation and synchronisation; still images alone cannot prove animation quality.
- Confirm the final export has video+audio streams, duration, stable frame rate and acceptable A/V sync.
- Test Windows and macOS setup separately; GitHub Actions uses Linux.
- Record accepted effect and approved sample clip version in a test register; no implicit 'perfect' claim.

## Usage
The system makes all 42 effects **available**, not necessarily **simultaneously applied** to every video. Overlapping every effect would ruin executive visual quality. The editor selects appropriate effects per clip, constrained by verified content and the brand profile.

### Run local gallery (after asset/dependency installation)

```bash
python tools/render_effect_gallery.py --video input.mp4 --output-dir gallery --width 540 --include-variants
```

Upload approved examples only with the video owner's permission; **do not put private user videos in this public GitHub repository**.
