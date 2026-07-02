# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Single-script Python project that downloads a YouTube video and generates a PNG "barcode" image where each vertical line is the average colour of one frame per second of video.

## Commands

Install dependencies (no requirements.txt exists):
```
pip install pytubefix opencv-python pillow
```

Run the script (takes the YouTube URL as an argument, or prompts interactively if omitted):
```
python average-colours.py [URL] [-m {classic,strip,multi}] [-r WIDTHxHEIGHT] [-o OUTPUT_FILE] [-n]
```

There is no test framework, linter, or build step. `test/test.py` is a standalone PIL scratch script, not an automated test — run it directly with `python test/test.py` to see a sample gradient image.

## Architecture

Everything lives in `average-colours.py`. The pipeline in `average_colours(video_url)`:

1. Deletes and recreates the `cache/` working directory (gitignored).
2. Downloads the video via pytubefix as `cache/test.mp4` (360p mp4 stream).
3. Frame sampling depends on the mode:
   - `classic`: `get_colour_list()` extracts one frame per second into `cache/frames/` as JPEGs and averages them via `PIL.ImageStat`; drawn as a square image resized to the resolution.
   - `strip`/`multi`: `get_frame_means()` averages every frame in memory with OpenCV (note BGR→RGB swap), `pick_bar_count()` chooses up to 6 bars (`multi` only; `ceil(frames/width)` capped at 6), and `resample_means()` maps frames onto `bars × width` columns — averaging chunks when frames outnumber columns, stretching frames across columns otherwise, always ≥1 frame per column. `render_bars()` stacks the bars with no gaps; `--resolution` means the size of one bar here.
4. Saves to the requested file (default `output.png` in the repo root; extension determines format) and opens it in the default viewer unless `-n`/`--no-show` is given.

Note: the project originally used `pytube`/`pytube3`, but those are unmaintained and fail against current YouTube (HTTP 410). It now uses `pytubefix`, a maintained drop-in fork.
