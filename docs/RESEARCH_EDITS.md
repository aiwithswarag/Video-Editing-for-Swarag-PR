# Source-led editorial research graphics

The original video-effect engine still includes all 42 effects and five variants. For spoken research claims, use **dedicated, citation-bearing graphics** rather than decorative metrics or generic dashboards.

## Generate from sourced numeric data

\`\`\`bash
python tools/download_assets.py
python scripts/research_cards.py examples/world-model-research-cards.json --output-dir PRIVATE/cards --width 1080
\`\`\`

Each card requires a primary arXiv URL, study scope, a citation, a caveat, and validated numbers. A benchmark-percent comparison needs labels for **both** values; a survey count needs explicit compared model families. The renderer rejects impossible percentages, misleading counts and cards without citations. The numerical examples come from two *public* papers; no personal media is stored in the repository.

- Long-WAM (Huang et al.), https://arxiv.org/abs/2610.10528 — **63.3% to 78.7%** on **RoboCasa GR-1**, using 0.0 versus 19.2 seconds of visual history; a specific simulated benchmark, not proof of general real-world success.
- Do World Models Make Better Robots? (Jena et al.), https://arxiv.org/abs/2609.29669 — **11 of 160** benchmarks explicitly make **world-model vs VLA-policy** comparisons. This documents a measurement gap, not a judgment that world models do not work.

Review all source claims against the current paper version before publishing. An arXiv URL alone does **not** automatically verify user-written text.

## Render graphics to matching-framerate MP4s

Use FFmpeg to turn the generated PNGs into video-only H.264 clips. The picture dimensions and frame rate **must match the source**. Choose exact durations and cut points by reviewing the actual transcript, not guessing from time in seconds.

\`\`\`bash
ffmpeg -loop 1 -framerate 30 -i PRIVATE/cards/evidence_01.png -frames:v 45 -c:v libx264 -pix_fmt yuv420p PRIVATE/first.mp4
\`\`\`

Then provide a **private** plan JSON such as:

\`\`\`json
{"windows":[{"start_frame":60,"clip":"first.mp4"},{"start_frame":190,"clip":"second.mp4"}]}
\`\`\`

The video is assumed to have enough total frames for these example positions. Run:

\`\`\`bash
python scripts/insert_cutaways.py PRIVATE/talking-head.mp4 PRIVATE/cutaway-plan.json PRIVATE/draft.mp4
python tools/master_quality_check.py PRIVATE/talking-head.mp4 PRIVATE/draft.mp4 --output PRIVATE/qa.json
\`\`\`

The insertion tool rejects mismatched resolution/rate, overlapping windows, missing voice track and out-of-bounds cutaways; it copies the original audio without modification. Always inspect video joins and research copy manually.

## Creative constraints

Treat this as editorial evidence, not slideware: one clear statistic per card, short exposure, source and scope always visible, no unsupported performance bars, no fake robot experiment footage. Keep original media and private transcripts outside public Git history. Technical media QA is not creative approval.
