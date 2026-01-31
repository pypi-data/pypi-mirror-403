import asyncio
import os
import shutil
from pathlib import Path

import yt_dlp

from ..messages import get_message


class YouTubeDownloader:
    def __init__(self, connections=8, force=False):
        self.connections = connections
        self.force = force
        self.is_dev = os.getenv("DFETCH_DEV") == "1"

    async def start(self, url, output_path):
        # Check for Windows
        ffmpeg_local = Path("ffmpeg.exe").resolve()
        if not shutil.which("ffmpeg") and not ffmpeg_local.exists():
            if os.name == "nt":  # Windows
                print(
                    f"\n❌ {get_message('TX_FAILED')}: {get_message('FFMPEG_WINDOWS_ERROR')}"
                )
                print(get_message("FFMPEG_TIPS_WINDOWS"))
                print(get_message("FFMPEG_LINK_WINDOWS"))
            else:  # Linux
                print(
                    f"\n❌ {get_message('TX_FAILED')}: {get_message('FFMPEG_NOT_FOUND')}"
                )
                print(get_message("FFMPEG_TIPS_FEDORA"))
                print(get_message("FFMPEG_TIPS_UBUNTU"))
                print(get_message("FFMPEG_TIPS_ARCH"))
                print(get_message("FFMPEG_LINK_LINUX"))
            return

        target_dir = Path(output_path).expanduser().resolve()
        target_dir.mkdir(parents=True, exist_ok=True)

        try:
            print(f"📡 {get_message('URL_PROMPT')} {get_message('YOUTUBE_MODE')}")

            # Take list of available formats
            print(get_message("SEARCHING_QUALITIES"))
            info = await asyncio.to_thread(self._extract_info, url)
            formats = info.get("formats", [])

            # Filter Only video formats with unique resolutions
            available_qualities = self._filter_formats(formats)

            print(f"\n{get_message('SELECT_QUALITY')}")
            for i, q in enumerate(available_qualities, 1):
                print(f"{i}. {q['resolution']} ({q['ext']}) - {q['note']}")

            choice = (
                input(
                    get_message("CHOOSE_NUMBER").format(count=len(available_qualities))
                )
                or "1"
            )
            selected_format = available_qualities[int(choice) - 1]["format_id"]

            # 2. Setup yt-dlp
            ydl_opts = {
                # Choice format: video + best audio
                "format": f"{selected_format}+bestaudio/best",
                "outtmpl": str(target_dir / "%(title)s.%(ext)s"),
                "concurrent_fragment_downloads": self.connections,
                "overwrites": self.force,
                "quiet": not self.is_dev,
                "no_warnings": True,
                "part": True,
                "postprocessors": [
                    {
                        "key": "FFmpegVideoConvertor",
                        "preferedformat": "mp4",
                    }
                ],
            }

            print(f"⚡ Connections: {self.connections}")
            await asyncio.to_thread(self._run_download, url, ydl_opts)

            print(f"\n✔ {get_message('TX_SUCCESS')}")
        except Exception as e:
            print(f"\n❌ {get_message('TX_FAILED')}: {e}")

    def _extract_info(self, url):
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            return ydl.extract_info(url, download=False)

    def _filter_formats(self, formats):
        seen_resolutions = set()
        unique_formats = []

        # Filter unique resolutions only, prefer mp4 over webm
        for f in reversed(formats):
            # Take the resolution label
            res_label = f.get("format_note") or f"{f.get('height')}p"

            if f.get("height") and res_label not in seen_resolutions:
                if f.get("vcodec") != "none":  # Make sure it's a video format
                    # Prefer mp4 if available for same resolution
                    existing = next(
                        (x for x in unique_formats if x["resolution"] == res_label),
                        None,
                    )
                    if existing and existing["ext"] == "webm" and f.get("ext") == "mp4":
                        # Replace webm with mp4
                        existing.update(
                            {
                                "format_id": f["format_id"],
                                "ext": f["ext"],
                                "note": get_message("VIDEO_CODEC").format(
                                    codec=f.get("vcodec")[:4]
                                ),
                            }
                        )
                    elif not existing:
                        unique_formats.append(
                            {
                                "format_id": f["format_id"],
                                "resolution": res_label,
                                "ext": f["ext"],
                                "note": get_message("VIDEO_CODEC").format(
                                    codec=f.get("vcodec")[:4]
                                ),
                            }
                        )
                        seen_resolutions.add(res_label)

        return unique_formats[:5]

    def _run_download(self, url, opts):
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
