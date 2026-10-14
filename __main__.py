"""
Usage: python . <youtube_url_or_id> <optional file name>

Saves mp4 and mp3 files from the given YouTube video as
<optional file name> or <youtube_id> to the DIR_DESKTOP directory.

"""

import argparse
import os
import re
import sys
from collections.abc import Sequence
from typing import Optional

YOUTUBE_VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download one YouTube video as MP4 and MP3 files.",
    )
    parser.add_argument("youtube_url", help="URL or ID of the YouTube video")
    parser.add_argument(
        "file_name",
        nargs="?",
        help="output base name; defaults to <youtube_id>",
    )

    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] not in {"-h", "--help"}:
        argv = ["--", *argv]

    return parser.parse_args(argv)


def normalize_youtube_url(youtube_url: str) -> str:
    if YOUTUBE_VIDEO_ID_PATTERN.fullmatch(youtube_url):
        return f"https://www.youtube.com/watch?v={youtube_url}"
    return youtube_url


def get_output_template(desktop_dir: str, file_name: Optional[str]) -> str:
    if file_name is None:
        file_name = "%(id)s"
    else:
        file_name = os.path.basename(file_name)
        if file_name.lower().endswith((".mp4", ".mp3")):
            file_name = file_name[:-4]
        file_name = file_name.replace("%", "%%")

    desktop_dir = desktop_dir.replace("%", "%%")
    return os.path.join(desktop_dir, f"{file_name}.%(ext)s")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    try:
        desktop_dir = os.environ["DIR_DESKTOP"]
    except KeyError:
        print("DIR_DESKTOP environment variable is not set", file=sys.stderr)
        return 2

    try:
        from yt_dlp import YoutubeDL
        from yt_dlp.utils import DownloadError
    except ImportError:
        print(
            "yt-dlp is required; install it with: python -m pip install yt-dlp",
            file=sys.stderr,
        )
        return 2

    options = {
        "format": "bv*+ba/b",
        "keepvideo": True,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "outtmpl": get_output_template(desktop_dir, args.file_name),
        "postprocessors": [
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            },
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
            },
        ],
    }

    try:
        with YoutubeDL(options) as downloader:
            youtube_url = normalize_youtube_url(args.youtube_url)
            error_code = downloader.download([youtube_url])
    except DownloadError as error:
        print(f"Download failed: {error}", file=sys.stderr)
        return 1

    return error_code


if __name__ == "__main__":
    raise SystemExit(main())
