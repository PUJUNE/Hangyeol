#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fetch YouTube metadata and subtitles as UTF-8 text.

Requires yt-dlp:
    pip install yt-dlp
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def safe_filename(name: str, limit: int = 120) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return (name or "youtube_video")[:limit]


def parse_timestamp(value: str) -> float:
    value = value.strip().replace(",", ".")
    parts = value.split(":")
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    if len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    return float(value)


def format_timecode(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def clean_caption_text(line: str) -> str:
    line = re.sub(r"<[^>]+>", "", line)
    line = line.replace("&nbsp;", " ").strip()
    return re.sub(r"\s+", " ", line)


def extract_caption_entries(raw: str) -> list[dict]:
    entries: list[dict] = []
    current_start: float | None = None
    current_end: float | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_start, current_end, current_lines
        if current_start is None:
            current_lines = []
            return
        text = " ".join(line for line in current_lines if line).strip()
        if text and (not entries or entries[-1]["text"] != text):
            entries.append(
                {
                    "timecode": format_timecode(current_start),
                    "start_sec": int(current_start),
                    "end_sec": int(current_end) if current_end is not None else None,
                    "text": text,
                }
            )
        current_start = None
        current_end = None
        current_lines = []

    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if not line:
            flush()
            continue
        if line.startswith("WEBVTT") or line.startswith("Kind:"):
            continue
        if line.startswith(("NOTE", "STYLE")):
            continue
        if line.isdigit() or re.match(r"^[\d:.,]+$", line):
            continue
        if "-->" in line:
            flush()
            start, end = line.split("-->", 1)
            current_start = parse_timestamp(start.split()[0])
            current_end = parse_timestamp(end.split()[0])
            continue
        text = clean_caption_text(line)
        if text:
            current_lines.append(text)
    flush()
    return entries


def strip_caption_lines(raw: str) -> str:
    entries = extract_caption_entries(raw)
    if entries:
        return "\n".join(f"[{entry['timecode']}] {entry['text']}" for entry in entries)

    lines: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("WEBVTT") or line.startswith("Kind:"):
            continue
        if line.startswith(("NOTE", "STYLE")):
            continue
        if "-->" in line:
            continue
        if line.isdigit() or re.match(r"^[\d:.,]+$", line):
            continue
        line = clean_caption_text(line)
        if line and (not lines or lines[-1] != line):
            lines.append(line)
    return " ".join(lines)


def choose_subtitle(info: dict, preferred_lang: str | None) -> tuple[str, str]:
    order: list[str] = []
    if preferred_lang:
        order.append(preferred_lang)
    for code in ("ko", "en"):
        if code not in order:
            order.append(code)

    subtitles = info.get("subtitles") or {}
    automatic = info.get("automatic_captions") or {}

    for lang in order:
        if lang in subtitles:
            return lang, "manual"
    for lang in order:
        if lang in automatic:
            return lang, "auto"

    raise RuntimeError(
        "No usable subtitles found. "
        f"manual={sorted(subtitles.keys())[:20]} auto={sorted(automatic.keys())[:20]}"
    )


def fetch(url: str, out_dir: Path, preferred_lang: str | None = None) -> dict:
    try:
        import yt_dlp
    except ImportError as exc:
        raise RuntimeError("yt-dlp is not installed. Run: pip install yt-dlp") from exc

    out_dir.mkdir(parents=True, exist_ok=True)

    info_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "writesubtitles": False,
        "writeautomaticsub": False,
    }
    with yt_dlp.YoutubeDL(info_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    lang, kind = choose_subtitle(info, preferred_lang)
    title = info.get("title") or "youtube_video"
    safe_title = safe_filename(title)
    stem = out_dir / safe_title

    download_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "writesubtitles": kind == "manual",
        "writeautomaticsub": kind == "auto",
        "subtitleslangs": [lang],
        "subtitlesformat": "vtt/srt/best",
        "outtmpl": str(stem) + ".%(ext)s",
    }
    with yt_dlp.YoutubeDL(download_opts) as ydl:
        ydl.download([url])

    candidates = (
        list(out_dir.glob(f"{safe_title}*.{lang}.*"))
        + list(out_dir.glob(f"{safe_title}*.vtt"))
        + list(out_dir.glob(f"{safe_title}*.srt"))
    )
    if not candidates:
        raise RuntimeError("Subtitle download completed but no subtitle file was found.")

    subtitle_file = candidates[0]
    raw = subtitle_file.read_text(encoding="utf-8", errors="replace")
    segments = extract_caption_entries(raw)
    text = strip_caption_lines(raw)

    script_path = out_dir / f"{safe_title}_스크립트.txt"
    segments_path = out_dir / f"{safe_title}_segments.json"
    meta_path = out_dir / f"{safe_title}_meta.json"

    script_path.write_text(text, encoding="utf-8")
    segments_path.write_text(json.dumps(segments, ensure_ascii=False, indent=2), encoding="utf-8")
    meta = {
        "title": title,
        "channel": info.get("uploader") or info.get("channel"),
        "channel_url": info.get("channel_url"),
        "upload_date": info.get("upload_date"),
        "duration_sec": info.get("duration"),
        "url": info.get("webpage_url") or url,
        "subtitle_lang": lang,
        "subtitle_source": kind,
        "view_count": info.get("view_count"),
        "thumbnail": info.get("thumbnail"),
        "description_first_300": (info.get("description") or "")[:300],
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    try:
        subtitle_file.unlink()
    except OSError:
        pass

    return {
        "script_path": str(script_path),
        "segments_path": str(segments_path),
        "meta_path": str(meta_path),
        "subtitle_lang": lang,
        "subtitle_source": kind,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--out", default=".")
    parser.add_argument("--lang", default=None)
    args = parser.parse_args()

    try:
        result = fetch(args.url, Path(args.out).resolve(), args.lang)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("OK")
    print(f"  script: {result['script_path']}")
    print(f"  segments: {result['segments_path']}")
    print(f"  meta:   {result['meta_path']}")
    print(f"  lang:   {result['subtitle_lang']} ({result['subtitle_source']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
