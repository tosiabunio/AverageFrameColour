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
python average-colours.py [URL] [-r WIDTHxHEIGHT] [-o OUTPUT_FILE]
```

There is no test framework, linter, or build step. `test/test.py` is a standalone PIL scratch script, not an automated test — run it directly with `python test/test.py` to see a sample gradient image.

## Architecture

Everything lives in `average-colours.py`. The pipeline in `average_colours(video_url)`:

1. Deletes and recreates the `cache/` working directory (gitignored).
2. Downloads the video via pytubefix as `cache/test.mp4` (360p mp4 stream).
3. `get_colour_list()` uses OpenCV to extract one frame per second (based on FPS) into `cache/frames/`, and `get_average_colour()` computes each frame's mean RGB via `PIL.ImageStat`.
4. Draws one vertical line per frame colour, resizes to the requested resolution (default 1920x1080), saves to the requested file (default `output.png` in the repo root; extension determines format), and opens it in the default viewer.

Note: the project originally used `pytube`/`pytube3`, but those are unmaintained and fail against current YouTube (HTTP 410). It now uses `pytubefix`, a maintained drop-in fork.
