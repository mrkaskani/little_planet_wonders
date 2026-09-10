# RTX 4090 Wan 2.2 S2V production commands

This runbook creates the 12-second `A Warm Light in the Garden` candidate on a
single RTX 4090 with 24 GB VRAM and 32 GB system RAM. It uses direct Python and
DiffSynth-Studio, not ComfyUI. The DiT and text encoder use true E4M3 FP8
execution; the audio encoder and VAE use FP16. All large components use
disk-backed layer management to remain within the limited host RAM.

The implementation is pinned to DiffSynth-Studio commit
`4dbf980d4d0eb34eda136300dd0d72014cff8965` because its current S2V multi-clip
path carries 73 motion frames between internal windows.

## 1. Upload the project

Run from the local Mac, replacing the SSH destination:

```bash
rsync -av --progress \
  --exclude '.git/' \
  --exclude '.venv*/' \
  --exclude 'runtime/production/' \
  --exclude 'runtime/video/' \
  --exclude 'runtime/models/' \
  /Users/oldowl/PycharmProjects/little_planet_wonders/ \
  USER@GPU_HOST:/workspace/little_planet_wonders/
```

This upload must include the approved reference image, clean 12-second dialogue,
and approved final audio mix under `runtime/`.

## 2. Connect and inspect the machine

```bash
ssh USER@GPU_HOST
cd /workspace/little_planet_wonders
nvidia-smi
free -h
df -h .
```

The runner intentionally stops unless CUDA identifies an RTX 4090 with compute
capability 8.9 or newer.

## 3. Install the pinned direct-Python runtime

```bash
bash scripts/production/setup_rtx4090_wan22_s2v.sh
```

## 4. Download the official Wan S2V source weights

The downloader uses the project's wget-based resumable download helper. The
official shards are read from disk and prepared as FP8 by the direct runtime;
the ComfyUI-only single-file checkpoint is not used.

```bash
bash scripts/models/download_wan22_s2v_rtx4090_fp8_source.sh
```

Re-running the same command resumes partial files and verifies completed files.

## 5. Run the 12-second episode

```bash
bash scripts/production/run_episode001_wan22_s2v_fp8_480p.sh \
  2>&1 | tee runtime/video/episode-001-fp8-production.log
```

The runner reads prompts and settings from:

```text
src/lpw/context/projects/riri-yoyo/generation-records/video-jobs/episode-001--moonlit-garden-greeting--wan22-s2v-fp8-480p--v002.yaml
```

It generates three internal 80-interval S2V windows, preserves 73 motion frames
between them, saves a motion checkpoint after each window, and retains exactly
192 encoded frames for a 12.000-second CFR video at 16 FPS.

## 6. Inspect the result

```bash
OUTPUT=runtime/video/riri-yoyo/episodes/episode-001/s2v/fp8-480p-v002
ffprobe -v error -count_frames -show_entries \
  stream=index,codec_type,width,height,r_frame_rate,nb_read_frames,duration \
  -of default=noprint_wrappers=1 "$OUTPUT/episode-001--fp8-480p--final-mix.mp4"
```

Expected picture values:

```text
width=832
height=480
r_frame_rate=16/1
nb_read_frames=192
duration=12.000000
```

Create a contact sheet for rapid review:

```bash
ffmpeg -y \
  -i "$OUTPUT/episode-001--fp8-480p--final-mix.mp4" \
  -vf "fps=1,scale=416:240,tile=4x3" \
  -frames:v 1 "$OUTPUT/episode-001--contact-sheet.jpg"
```

Review active-speaker mouth motion, the 5s and 10s boundaries, Yoyo looking
toward the light, Yoyo face emphasis at 8s, Riri face emphasis after 10s, both
Riri front paws grounded after 10s, identity stability, VAE burn, tile seams,
and background geometry.

## 7. Download results and stop billing

Run from the local Mac:

```bash
rsync -av --progress \
  USER@GPU_HOST:/workspace/little_planet_wonders/runtime/video/riri-yoyo/episodes/episode-001/s2v/fp8-480p-v002/ \
  /Users/oldowl/PycharmProjects/little_planet_wonders/runtime/video/riri-yoyo/episodes/episode-001/s2v/fp8-480p-v002/
```

After verifying the local files, stop or delete the paid GPU instance from the
provider dashboard.
