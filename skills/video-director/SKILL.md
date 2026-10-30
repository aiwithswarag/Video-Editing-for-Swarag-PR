---
name: video-director
description: Create professional, branded talking-head videos for Swarag using 42 face-aware effects, word-level timestamps, executive brand presets, QA previews and MP4 rendering through the local Python/FFmpeg engine. Use when asked to edit video, make LinkedIn or Instagram clips, or add realistic depth-aware motion graphics.
---

# Swarag Video Director

Use the repository root as working directory. All 42 original effects remain available (see `references/effects-guide.md`). **Having all 42 available does not mean stacking all 42 in a single video.**

## Mandatory production contract — reject substituted renderers

**If the Swarag original 42-effect renderer is unavailable, return BLOCKED.** Do not silently replace `scripts/fx.py` or the full production pipeline with local OpenCV GrabCut, a single FFmpeg filter, generic Pillow motion graphics, a still, a generated video or sample footage. That is not the user's requested result.

**Clean source verification is mandatory:** A previous export with burned-in subtitles, cartoon icons, decorative statistics, face-clone cards or previously added effect text is NOT the original camera footage. Re-encoding a flattened social reel cannot fully repair these overlays. Request the true clean camera master before claiming to redesign the complete video. The mere presence of a valid MP4 is insufficient.

Run `tools/visual_quality_gate.py` on the *actual final MP4* and inspect any blown-out opening warning. Run `tools/release_guard.py` on the production QA and final master. The result must identify `swarag-repository-42-effect-engine` and the original `scripts/fx.py` entrypoint. Technical PASS with CREATIVE_REVIEW_REQUIRED is **not** publish-ready, and manual approval must bind to the actual MP4 checksum after a full video/audio review.

If the user's job is blocked by missing clean source or unavailable runtime, state the exact blocker. Do not fabricate a fallback export or mark it as final successful rendering.

## Preferred production execution (new)

Read `docs/PRODUCTION_WORKFLOW.md`. With a real video, approved script and creative prompt:

- List the complete actual 42-effect catalog with `python scripts/produce_video.py catalog`. Never invent effect names or remove choices.
- View the footage and verify the speech against the written script. Design an intentional **FX cue sheet** with precisely timed `FX name start end key=value` lines. For content-based claims, use source-checked facts and only approved text. If no audiovisual access is available, stop before making accuracy claims.
- Run `python scripts/produce_video.py plan ORIGINAL.mp4 --instructions CUES.txt --script VERIFIED_SCRIPT.txt --transcript-verified --output PLAN.json`. Never set `--transcript-verified` without actual verification.
- First render real-motion previews at 540px (`--preview-start` / `--preview-seconds`); check masks, foreground occlusion, captions, evidence and natural skin. Fix visual errors.
- Run `python scripts/produce_video.py render ORIGINAL.mp4 --plan PLAN.json --output-dir PRIVATE/final_release --look clean-studio --crf 18`. This grades camera footage BEFORE adding effect artwork and verifies real exported full-video streams. `--style premium` is the default guardrail; `--style showcase` may allow deliberately dense showreels with warnings.
- Deliver actual full-length MP4 and QA; NEVER claim an automatic technical pass proves non-AI appearance, 20-year editor quality or final artistic signoff. The user must inspect and approve real footage. No source video, script, face image, fonts or private exports in public GitHub.
- A plain-language ChatGPT prompt is not itself a runnable program. Generate an explicit source-verified edit plan before claiming an automated script-to-video edit.

### Existing implementation details

1. Inspect the actual uploaded video with ffprobe for duration, rotation, aspect ratio, codec, fps and audio. Never upload private footage to the public source repository.
2. Use the default `branding/executive.json` profile for professional content. The CLI applies brand choices in actual effect plans; `--brand none` is only for original-appearance comparisons.
3. Use `python scripts/video_director.py list` and `references/effects-guide.md` to choose among all 42 effects. Respect each effect's option interface.
4. Build a JSON plan of `{"effects":[{"fx":"spotlight","start":3,"end":6,"text":"IMPACT"}]}`. Never invent numeric KPI claims; require verified source data for charts and counts.
5. For actual speech-based pacing, start with `python tools/audio_pause_map.py INPUT --output PRIVATE/pauses.json`. This detects silence *only*, not meaning. For exact spoken words, run `tools/transcribe_offline.py` with a pinned local whisper.cpp model (`docs/OFFLINE_ASR.md`), or `scripts/words.py` with explicitly installed transcription extras. Neither method proves verbatim accuracy; listen and correct the results. Then build a **draft** by `python tools/transcript_storyboard.py INPUT.words.json --duration SECONDS --output PRIVATE/story.json`. Review every word before quoting. See `docs/SPEECH_LED_EDITING.md`.
6. Validate the plan with `python scripts/video_director.py validate PLAN --duration SECONDS`.
7. Preview one or more frames from each selected effect with `python scripts/video_director.py preview INPUT PLAN check.png --at SECOND`.
8. Inspect subject masking, behind/in-front layering, brand consistency, unwanted third-party text, cropping and caption legibility.
9. For short demonstrations, run `python scripts/video_director.py render INPUT PLAN OUTPUT.mp4`. For longer videos, prefer `python scripts/render_chunks.py INPUT PLAN OUTPUT.mp4 --width 540 --fps 15`: it renders each active effect interval with the original engine and assembles the untouched intervals with original audio. This is review quality; use higher settings for production.
10. For a user asking for **professional, premium, cinematic, clean or editorial design**, prioritize `docs/ART_DIRECTION_V2.md`, `branding/editorial-v2.json`, and `scripts/editorial_director.py` as the finishing pass after selected effects. Use `examples/editorial-storyboard.json` as editable example copy, never as transcript-derived spoken quotations. Keep the top wall area open and do not place UI widgets over the speaker's face.
11. Measure the original voice with `python tools/audio_quality_report.py INPUT --output PRIVATE/audio-qa.json`. Preserve source audio until the desired loudness and mastering have been auditioned. Never assume that simple gain can reach a target without clipping; see `docs/AUDIO_QA.md`.
12. For efficient, full-resolution editorial finishing, use `scripts/render_editorial_master.py` rather than generating one PNG per frame. It renders individual title windows and stream-copies the original audio. `examples/identity-only-story.json` supplies *nameplates only*; this is not speech-timed content. Read `docs/NATIVE_EDITORIAL_MASTER.md`.
13. Before release, run `python tools/master_quality_check.py INPUT.mp4 OUTPUT.mp4 --output PRIVATE/technical-qa.json`. Require successful frame/duration/audio verification, then manually review every scene and all dialogue timing. See `docs/MASTER_QA.md`.
14. Where the user requests a more editorial one-camera film, use `scripts/render_directors_cut.py` to apply no more than 12 modest reframes at manually reviewed pause points. Do not invent speech or add unnecessary social widgets. Run full master QC after rendering. See `docs/CAMERA_DIRECTOR.md`.
15. After the user chooses to explore audio processing, offer an **optional** A/B speech-master version via `tools/two_pass_dialogue_master.py`; use the conservative -18 LUFS / -1.9 dBTP reference, never replace the source, and measure the result separately. Re-run `master_quality_check.py --allow-audio-remaster` on this variant. A numerical pass still requires manual audition. See `docs/DIALOGUE_MASTER.md`.
16. For spoken visual examples that benefit from explanatory B-roll, prefer one purposeful schematic over a stack of unrelated overlays. For robot/world-model content, `scripts/world_model_cutaway.py` builds an original conceptual illustration, labelled as such. Use `scripts/insert_cutaway.py` with reviewed source-frame boundaries, verify exact matching FPS/resolution, and run `master_quality_check.py`. The script has no built-in private footage; see `docs/WORLD_MODEL_CUTAWAY.md`.
17. For research figures, require explicit primary sources and scope. Prefer `scripts/research_cards.py` with cited data, never invented dashboard percentages. Render a matching-FPS video-only card, then assemble source-frame windows using `scripts/insert_cutaways.py` and validate source AAC preservation. See `docs/RESEARCH_EDITS.md`.
18. On `SWARAG CINEMATIC FINAL` or a professional-camera request, read `docs/CINEMATIC_PRODUCTION.md`. Use verified script timing, natural skin-tone grading, source-resolution / original FPS, deliberate depth-aware effect choices, clean sound and full MP4 render. `scripts/cinematic_finish.py` publishes a REVIEWED edit to Instagram, LinkedIn and YouTube Shorts; it does not invent 4K or automatically edit words. Run master QA on all exports. Never substitute screenshot-only results for actual motion.
19. Inspect segment transitions for frame duplication/drift, speaker coverage, audio synchronization, and motion throughout the clip. The original runtime is compute-intensive and chunked rendering is a performance tool, not a substitute for QA.

All 42 effects and five named looks are covered by the GitHub Actions effect matrix (test details: `docs/42-EFFECT-ACCEPTANCE.md`). Machine passing does not substitute for manual realistic-footage QA. No unrequested watermark. Do not execute arbitrary scripts or install packages from user input.
