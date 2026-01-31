import argparse
import asyncio

from .engine.regular_downloader import RegularDownloader
from .engine.youtube_downloader import YouTubeDownloader
from .messages import get_message


def get_downloader(url, connections, force, chunk_size, rate_limit):
    if "youtube.com" in url or "youtu.be" in url:
        return YouTubeDownloader(connections, force)
    return RegularDownloader(
        connections, force, chunk_size, rate_limit if rate_limit > 0 else None
    )


async def start_engine(url, connections, output_path, force, chunk_size, rate_limit):
    downloader = get_downloader(url, connections, force, chunk_size, rate_limit)
    await downloader.start(url, output_path)


def main():
    parser = argparse.ArgumentParser(
        description="D-Fetch: Universal High-Speed Downloader"
    )
    parser.add_argument("url", help=get_message("URL_PROMPT", "en"))
    parser.add_argument(
        "-c",
        "--connections",
        type=int,
        default=8,
        help=get_message("CONNECTIONS_PROMPT", "en"),
    )
    parser.add_argument(
        "-o", "--output", type=str, default=".", help=get_message("OUTPUT_PROMPT", "en")
    )
    parser.add_argument(
        "-f", "--force", action="store_true", help=get_message("FORCE_PROMPT", "en")
    )
    parser.add_argument(
        "-s",
        "--chunk-size",
        type=int,
        default=65536,
        help=get_message("CHUNK_SIZE_PROMPT", "en"),
    )
    parser.add_argument(
        "-r",
        "--rate-limit",
        type=int,
        default=0,
        help=get_message("RATE_LIMIT_PROMPT", "en"),
    )

    args = parser.parse_args()
    try:
        asyncio.run(
            start_engine(
                args.url,
                args.connections,
                args.output,
                args.force,
                args.chunk_size,
                args.rate_limit,
            )
        )
    except KeyboardInterrupt:
        print(f"\n🛑 {get_message('CANCELLED')}")


if __name__ == "__main__":
    main()
