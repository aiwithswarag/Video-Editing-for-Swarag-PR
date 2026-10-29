# Swarag Video Director — Production Workflow (all 42 effects)

**Status:** Runnable local rendering pipeline. **Not** a hosted, one-click ChatGPT video editor. Video work requires Python, FFmpeg, local licensed assets/models, and a machine with enough RAM/CPU/GPU time. The 42 effects are available; no automated tool can guarantee that an arbitrary input will look like it was shot on a cinema camera or that the result cannot be recognized as AI-assisted.

## Install / preflight

From the repository root:

```bash
python -m pip install -r requirements.txt
python tools/download_assets.py
python -m unittest discover -s tests -v
python scripts/produce_video.py catalog
```

**Video requirements:** native portrait 9:16 with audio, a decodable frame count, constant frame rate 8–30.5 fps, SDR Rec.709 or known-safe SDR. Input above 30.5 fps must be explicitly converted outside the editing workflow; the original 42-effect engine internally caps higher rates. Do not silently drop 60 fps motion. Preserve original files.

## Step 1 — Choose effects in ordinary language, then make explicit edit cues

The assistant/director should watch the video and listen to the verified voice track, then write an editable plain-text cue sheet. Your prompt and script are *instructions*, not direct executable FFmpeg commands. Timed instructions are the contract between creative planning and the rendering engine.

Cue syntax: one line per effect, with quoted text when appropriate:

```text
# FX name START_SECONDS END_SECONDS [key=value ...]
FX slow-push 1.0 3.2 zoom=1.06
FX backdrop-word 8.0 10.5 text="WORLD MODELS"
FX headline-box 25.5 28.5 text="THE EVIDENCE"
```

Every name printed by `python scripts/produce_video.py catalog` is valid here, including aliases such as `push` and `glitter-spotlight`. To use any of the 42, put that effect in the cue sheet and provide its intended options. The underlying effect engine—not a placeholder implementation—executes each one. The CLI also accepts `--style showcase` for deliberate dense experimental edits, but that is **not** the default premium look.

**Realism policy:** Do not apply all 42 effects at the same time. Select only those motivated by the spoken material. Prefer genuine footage, natural skin, a few consistent typographic treatments, and subtle reframes. Effects that require a photo or graph should use **real, approved user assets**, not fictitious content. Synthetic robot illustrations must be labelled as illustrations, not presented as authentic robotics experiments.

## Step 2 — Create the validated machine-readable plan

```bash
python scripts/produce_video.py plan "PRIVATE/original.mp4" \
  --instructions "PRIVATE/director-cues.txt" \
  --script "PRIVATE/verified-script.txt" \
  --brief "PRIVATE/creative-brief.txt" \
  --transcript-verified \
  --output "PRIVATE/edit-plan.json"
```

Only use `--transcript-verified` after someone checks the actual audio against the written transcript. Without that flag, the exporter refuses speech-derived plans. The CLI will not invent quotations, statistics, or effect timecodes from a raw script. It cannot truthfully decide whether the spoken words are accurate on its own.

## Step 3 — Preview the actual moving effects first

```bash
python scripts/produce_video.py render "PRIVATE/original.mp4" \
  --plan "PRIVATE/edit-plan.json" \
  --output-dir "PRIVATE/preview_01" \
  --look clean-studio --brand executive \
  --width 540 --preview-start 8 --preview-seconds 4
```

Preview is lower resolution, but uses the *same* engine and real source audio. Check face/hand segmentation, depth layering, blend edges, subtitles, bright/dark backgrounds and graphics continuity. The initial script may reject the preview if its cut produces a different number of audio/video frames; adjust clip start/length to exact frame boundaries, or render the full-resolution video first. This is intentional fail-closed QA.

## Step 4 — Full-resolution final production master

```bash
python scripts/produce_video.py render "PRIVATE/original.mp4" \
  --plan "PRIVATE/edit-plan.json" \
  --output-dir "PRIVATE/final_release" \
  --look clean-studio --brand executive \
  --crf 18 --chunk-frames 180
```

Pipeline:
1. Validate all 42-effect names, each time window, source dimensions, native fps and creative-risk rules.
2. Use **resumable grading** on the original camera footage *before* adding text or VFX. Preserve natural skin and avoid over-processing the graphics later.
3. Composite selected original effects using the face-aware 42-effect engine on effect-bearing segments, with untouched areas in between.
4. Preserve the source AAC stream when possible, never add synthetic narration automatically.
5. Verify full original-rate H.264 frame count, duration, audio checksum and complete decode. Fail nonzero on mismatches instead of calling a broken file finished.
6. Create the common 9:16 master `final_master.mp4` and three **bit-identical** copies `final_instagram.mp4`, `final_linkedin.mp4`, `final_youtube-shorts.mp4`. These are *not* separate 16:9/4:5 variants.
7. Save `production_qa.json` with creative approval explicitly marked **REVIEW REQUIRED**.

`--style premium` (default) flags aggressive zoom, missing intentional headline text, and more than two simultaneous effects. `--style showcase` permits intentional experiments, reports issues, and never magically upgrades their creative quality.

## Step 5 — Final human production acceptance

At final native resolution, check **every cut and every effect** on phone and desktop:
- The original speaker's face, hair and moving hands must have stable masks, no halos, no doubled anatomy and no graphics slicing across facial features.
- Watch the entire video in motion, not only screenshots. Check edited sections and every join, script synchronisation, reading time, factual accuracy and evidence attribution.
- Verify exposure, noise, compression, skin detail and highlights against the *source*. No artificial bokeh, invented lens optics, deep-fake frames, fake 4K detail or extreme plastic denoising.
- Listen on headphones and a phone speaker for pops, clipping, breaths and subtitle timing. EBU R128 normalization is **optional**, not proof that audio sounds professional.
- Run `tools/frame_continuity_report.py` **only** for exports directly from the resumable grade engine (whose frame boundaries match the input grade). The final *effects edit* must be inspected separately; source-vs-master PSNR will naturally differ in effect-bearing windows.
- Approve a real final MP4 and record signoff; technical PASS alone never implies creative signoff.

## Copy/paste creative direction to use with an uploaded video + script

> **SWARAG PROFESSIONAL VIDEO DIRECTOR — FINAL PRODUCTION**. Use the original uploaded video, my written script, and my creative instructions. Open my 42-effect Swarag Video Director repository and follow its `docs/PRODUCTION_WORKFLOW.md`. Verify every speech excerpt against the audio before placing text. Choose the most appropriate effects from the actual 42-effect catalog; never force all 42 into one cut. Build an explicit, time-accurate `FX ...` cue sheet and validated JSON edit plan. Grade the *camera footage first* with a natural clean-studio or restrained editorial look, preserve believable skin texture and original voice, composite the effects with accurate face/hand occlusion, and render the complete source-resolution video. Do not create fictitious objects, AI-generated replacement faces, fake data graphics, excessive fake bokeh or oversharpening. Listen, visually review real motion, correct any visible seams, and deliver the actual H.264/AAC MP4 master, Instagram/LinkedIn/YouTube Shorts exports, cue sheet, source references and `production_qa.json`. Never call the result approved until its entire video has been watched, audited and signed off. If any source video or tool cannot be accessed, report the exact blocker rather than substituting images.

This is a **workflow instruction for an agent with video-file and computer access**, not a magic built-in slash command. If you're working only in text chat, the assistant can help write the plan, but cannot claim to have edited private footage it has not received or rendered.

## Known limitations

- Requires CPU-heavy MediaPipe tracking and correct licensed model/font assets. Real face/hair occlusion and cutaway realism require artistic inspection.
- `render_chunks.py` preserves fractional FPS such as 29.5 using `--fps auto`, but its older FFmpeg segment/concat architecture can still encounter frame-boundary drift. The final master checker fails rather than silently ignoring drift.
- A 60.71-second 1080p real footage final has **not** been accepted using this new orchestration. Synthetic end-to-end tests do not certify cinema-level image quality.
- The default creative style is restrained. Some of the original 42 effects are intentionally flashy or UI-like; they may look artificial regardless of correct rendering. Creative judgment matters more than merely enabling an effect.
- Source files, transcripts, edit plans, licensed fonts, personal information and final exports must stay private—never commit them into a public GitHub repository.
