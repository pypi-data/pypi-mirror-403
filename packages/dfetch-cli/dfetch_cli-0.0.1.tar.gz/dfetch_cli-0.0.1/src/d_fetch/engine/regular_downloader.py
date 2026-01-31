import asyncio
import os
import shutil
import time
from pathlib import Path

import httpx
from tqdm import tqdm

from ..messages import get_message


class RegularDownloader:
    def __init__(self, connections=8, force=False, chunk_size=65536, rate_limit=None):
        self.connections = connections
        self.force = force
        self.chunk_size = chunk_size
        self.rate_limit = (
            rate_limit  # bytes per second per connection, None for no limit
        )
        # Mode Develop: export DFETCH_DEV=1 unhide folder cache
        self.is_dev = os.getenv("DFETCH_DEV") == "1"
        self.cache_prefix = "" if self.is_dev else "."

    async def _download_part(
        self, client, url, start, end, part_num, cache_dir, progress
    ):
        """Fungsi untuk mengunduh satu bagian (part) file."""
        part_name = cache_dir / f"part{part_num}"

        # Resume logic
        downloaded = part_name.stat().st_size if part_name.exists() else 0
        new_start = start + downloaded
        progress.update(downloaded)

        if new_start > end:
            return part_name

        headers = {
            "Range": f"bytes={new_start}-{end}",
            "User-Agent": "Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        try:
            async with client.stream("GET", url, headers=headers, timeout=30.0) as r:
                if r.status_code == 416:
                    return part_name
                r.raise_for_status()

                with open(part_name, "ab") as f:
                    async for chunk in r.aiter_bytes(chunk_size=self.chunk_size):
                        chunk_start = time.time()
                        f.write(chunk)
                        progress.update(len(chunk))
                        if self.rate_limit:
                            chunk_time = time.time() - chunk_start
                            expected_time = len(chunk) / self.rate_limit
                            if chunk_time < expected_time:
                                await asyncio.sleep(expected_time - chunk_time)
        except Exception as e:
            raise e

        return part_name

    async def start(self, url, output_path):
        limits = httpx.Limits(
            max_connections=self.connections, max_keepalive_connections=self.connections
        )

        async with httpx.AsyncClient(
            follow_redirects=True, timeout=None, limits=limits, http2=False
        ) as client:
            try:
                async with client.stream("GET", url) as r:
                    r.raise_for_status()
                    size = int(r.headers.get("content-length", 0))
                    raw_filename = url.split("/")[-1].split("?")[0] or "downloaded_file"
                    is_resume_supported = r.headers.get("accept-ranges") == "bytes"

                target_dir = Path(output_path).expanduser().resolve()
                target_dir.mkdir(parents=True, exist_ok=True)
                full_path = target_dir / raw_filename

                # --- CHECK DISK SPACE ---
                _, _, free = shutil.disk_usage(target_dir)
                if free < (size * 2):
                    print(
                        f"\n❌ {get_message('TX_FAILED')}: {get_message('DISK_SPACE_LOW')}"
                    )
                    print(
                        f"📦 Butuh: {(size * 2) / (1024**3):.2f} GB | Sisa: {free / (1024**3):.2f} GB"
                    )
                    return

                # Folder cache
                cache_dir_name = f"{self.cache_prefix}dfetch_{raw_filename}_cache"
                cache_dir = target_dir / cache_dir_name

                # 3. Handle Flag Force (-f)
                if self.force:
                    if full_path.exists():
                        full_path.unlink()
                    if cache_dir.exists():
                        shutil.rmtree(cache_dir)
                    print(f"◈ {get_message('FORCE_MODE')}")
                elif full_path.exists():
                    print(
                        f"✅ {get_message('TX_SUCCESS')}\n{get_message('FILE_EXISTS')}"
                    )
                    return

                cache_dir.mkdir(parents=True, exist_ok=True)

                print(f"⚡ Connections: {self.connections}")
                print(f"📂 Destination: {full_path}")
                print(f"📦 File Size: {size / (1024 * 1024):.2f} MB")
                print(
                    f"🔄 Resume: {get_message('RESUME_SUPPORTED' if is_resume_supported else 'RESUME_NOT_SUPPORTED')}"
                )

                progress = tqdm(
                    total=size,
                    unit="B",
                    unit_scale=True,
                    desc=" ◈ D-Fetch ",
                    colour="#00ff00",
                    dynamic_ncols=True,
                    bar_format="{desc} {percentage:3.0f}% ▕{bar}▏ {n_fmt}/{total_fmt} ⇁ {rate_fmt} ⏳ {remaining}",
                )

                # 5. Execution Paralel
                chunk_size_per_part = size // self.connections
                tasks = []
                for i in range(self.connections):
                    start_byte = i * chunk_size_per_part
                    end_byte = (
                        size
                        if i == self.connections - 1
                        else (i + 1) * chunk_size_per_part - 1
                    )
                    tasks.append(
                        self._download_part(
                            client, url, start_byte, end_byte, i, cache_dir, progress
                        )
                    )

                # Wait for all parts to complete
                parts = await asyncio.gather(*tasks)
                progress.close()

                # Merging parts
                print(f"\n🛠️ {get_message('MERGING')}...")
                with open(full_path, "wb") as final:
                    # Sort parts to ensure correct order
                    for part_path in sorted(
                        parts, key=lambda p: int(p.name.replace("part", ""))
                    ):
                        with open(part_path, "rb") as p:
                            shutil.copyfileobj(p, final)

                # Cleanup cache
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)

                print(f"\n✔ {get_message('TX_SUCCESS')}")
                print(f"{get_message('LOCATION').format(full_path=full_path)}")

            except Exception as e:
                print(f"\n❌ {get_message('TX_FAILED')}: {e}")
