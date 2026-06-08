# -*- coding: utf-8 -*-
"""
유튜브 URL → 자막(.txt) + 메타데이터(.json) 추출 스크립트

사용법:
    python fetch_youtube_subs.py <URL> [--out <output_dir>] [--lang <lang>]

예:
    python fetch_youtube_subs.py "https://www.youtube.com/watch?v=XXXXX"
    python fetch_youtube_subs.py "https://youtu.be/XXXXX" --out ./ --lang ko

출력:
    <영상제목>_스크립트.txt — 자막 본문(타임코드 포함, 클렌징은 video-script-summary 측에서 수행)
    <영상제목>_meta.json   — title, channel, upload_date, duration, url, subtitle_source

자막 우선순위:
    --lang 지정 시 해당 언어 → 한국어(ko) → 영어(en) → 자동 생성된 자막
    모두 실패 시 에러 코드 2로 종료(사용자가 다른 영상을 시도하거나 STT 사용 결정)

의존성:
    pip install yt-dlp
"""
import argparse
import json
import re
import sys
from pathlib import Path


def safe_filename(name: str) -> str:
    """Windows·POSIX 모두에서 사용 가능한 파일명으로 정제."""
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name[:120]  # 너무 긴 제목 자르기


def srt_to_text(srt_content: str) -> str:
    """SRT 자막 → 평문 (타임코드·번호 제거, 줄바꿈은 공백으로)."""
    lines = srt_content.splitlines()
    text_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.isdigit():
            continue
        if re.match(r'^\d{2}:\d{2}:\d{2}[,.]\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}[,.]\d{3}', line):
            continue
        # 인라인 태그 제거 (<c>, <i> 등)
        line = re.sub(r'<[^>]+>', '', line)
        text_lines.append(line)
    return ' '.join(text_lines)


def vtt_to_text(vtt_content: str) -> str:
    """WebVTT 자막 → 평문."""
    lines = vtt_content.splitlines()
    text_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('WEBVTT'):
            continue
        if '-->' in line:
            continue
        if line.startswith('NOTE') or line.startswith('STYLE'):
            continue
        if re.match(r'^[\d:.]+$', line):
            continue
        line = re.sub(r'<[^>]+>', '', line)
        text_lines.append(line)
    # WebVTT는 종종 같은 라인이 cue 경계마다 중복 표시됨 → 연속 중복 제거
    deduped = []
    for line in text_lines:
        if not deduped or deduped[-1] != line:
            deduped.append(line)
    return ' '.join(deduped)


def fetch(url: str, out_dir: Path, preferred_lang: str | None = None) -> dict:
    try:
        import yt_dlp
    except ImportError:
        print("ERROR: yt-dlp 미설치. 다음 명령으로 설치 후 재시도:", file=sys.stderr)
        print("  pip install yt-dlp", file=sys.stderr)
        sys.exit(3)

    out_dir.mkdir(parents=True, exist_ok=True)

    # 자막 언어 우선순위 결정
    lang_priority = []
    if preferred_lang:
        lang_priority.append(preferred_lang)
    for code in ['ko', 'en']:
        if code not in lang_priority:
            lang_priority.append(code)

    # 1) 메타데이터 + 자막 정보 조회 (다운로드 없이)
    info_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'writesubtitles': False,
        'writeautomaticsub': False,
    }
    with yt_dlp.YoutubeDL(info_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    available_subs = list((info.get('subtitles') or {}).keys())
    available_auto = list((info.get('automatic_captions') or {}).keys())

    # 사용할 언어·자막 종류 결정
    chosen_lang = None
    chosen_kind = None  # 'manual' | 'auto'
    for lang in lang_priority:
        if lang in available_subs:
            chosen_lang, chosen_kind = lang, 'manual'
            break
    if not chosen_lang:
        for lang in lang_priority:
            if lang in available_auto:
                chosen_lang, chosen_kind = lang, 'auto'
                break

    if not chosen_lang:
        print("ERROR: 이 영상에는 사용 가능한 자막이 없음.", file=sys.stderr)
        print(f"  수동 자막 가용: {available_subs}", file=sys.stderr)
        print(f"  자동 자막 가용: {available_auto}", file=sys.stderr)
        print("  → 다른 영상을 시도하거나 STT(Whisper 등)를 직접 적용 필요.", file=sys.stderr)
        sys.exit(2)

    title = info.get('title') or 'youtube_video'
    safe_title = safe_filename(title)
    sub_path_stem = out_dir / safe_title

    # 2) 자막 다운로드 (vtt 우선)
    download_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'writesubtitles': chosen_kind == 'manual',
        'writeautomaticsub': chosen_kind == 'auto',
        'subtitleslangs': [chosen_lang],
        'subtitlesformat': 'vtt/srt/best',
        'outtmpl': str(sub_path_stem) + '.%(ext)s',
    }
    with yt_dlp.YoutubeDL(download_opts) as ydl:
        ydl.download([url])

    # 3) 다운받은 자막 파일 찾기 (yt-dlp는 .<lang>.<ext> 형식으로 저장)
    candidates = list(out_dir.glob(f"{safe_title}*.{chosen_lang}.*"))
    if not candidates:
        # 일부 환경에서 lang suffix가 없을 수 있음 — 확장자로 재탐색
        candidates = list(out_dir.glob(f"{safe_title}*.vtt")) + \
                     list(out_dir.glob(f"{safe_title}*.srt"))
    if not candidates:
        print("ERROR: 자막 파일 다운로드 실패 (yt-dlp 출력 없음).", file=sys.stderr)
        sys.exit(4)

    sub_file = candidates[0]
    raw = sub_file.read_text(encoding='utf-8', errors='replace')

    if sub_file.suffix.lower() == '.srt':
        text = srt_to_text(raw)
    else:  # vtt 또는 기타
        text = vtt_to_text(raw)

    # 4) 출력 파일 저장
    txt_path = out_dir / f"{safe_title}_스크립트.txt"
    txt_path.write_text(text, encoding='utf-8')

    meta = {
        'title': title,
        'channel': info.get('uploader') or info.get('channel'),
        'channel_url': info.get('channel_url'),
        'upload_date': info.get('upload_date'),  # YYYYMMDD
        'duration_sec': info.get('duration'),
        'url': info.get('webpage_url') or url,
        'subtitle_lang': chosen_lang,
        'subtitle_source': chosen_kind,  # manual | auto
        'view_count': info.get('view_count'),
        'description_first_300': (info.get('description') or '')[:300],
    }
    meta_path = out_dir / f"{safe_title}_meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                         encoding='utf-8')

    # 원본 자막 파일 정리 (선택)
    try:
        sub_file.unlink()
    except OSError:
        pass

    return {
        'script_path': str(txt_path),
        'meta_path': str(meta_path),
        'subtitle_lang': chosen_lang,
        'subtitle_source': chosen_kind,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url", help="유튜브 URL")
    ap.add_argument("--out", default=".", help="출력 디렉터리 (기본: 현재 디렉터리)")
    ap.add_argument("--lang", default=None,
                    help="우선 자막 언어 코드 (기본: ko → en → auto)")
    args = ap.parse_args()

    result = fetch(args.url, Path(args.out).resolve(), args.lang)
    print("OK")
    print(f"  script: {result['script_path']}")
    print(f"  meta:   {result['meta_path']}")
    print(f"  lang:   {result['subtitle_lang']} ({result['subtitle_source']})")


if __name__ == "__main__":
    main()
