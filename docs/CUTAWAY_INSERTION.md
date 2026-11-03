# Cutaways in the professional Swarag edit

The B-roll tool inserts a matching-resolution, matching-frame-rate visual over a **specified integer-frame window**, retaining the original AAC speech stream. No copyrighted stock imagery or personal recordings are included.

Use the human-reviewed transcript to decide when the speaker needs a visual explanation. A frame count is **not** inferred from words without review.

Run the original cutaway generator (see `scripts/world_model_cutaway.py`), then use the frame-exact compositor:

```bash
python scripts/world_model_cutaway.py PRIVATE/diagram.mp4 --width 1080 --fps 30 --frames 60
python scripts/insert_cutaway.py PRIVATE/source_edit.mp4 PRIVATE/diagram.mp4 PRIVATE/directors_cut_03.mp4 --at-frame 120
python tools/master_quality_check.py PRIVATE/source_edit.mp4 PRIVATE/directors_cut_03.mp4 --output PRIVATE/qa.json
```

The example frame values are **synthetic** and assume a 10-second clip at 30 fps. Choose frame boundaries after reviewing your actual narration. The cutaway is an original conceptual vector illustration of the robot and cup—not actual robot benchmark footage. Production acceptance requires identical source/output frame counts, duration and stream-copied audio, plus independent creative review.

Do not commit private footage, audio, transcript JSON, personal timelines or generated media to this public repository.