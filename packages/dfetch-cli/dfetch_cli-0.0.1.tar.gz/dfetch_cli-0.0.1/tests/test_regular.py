import pytest

from d_fetch.engine.regular_downloader import RegularDownloader


@pytest.mark.asyncio
async def test_regular_download_success(tmp_path):
    # Setup
    test_url = "https://ash-speed.hetzner.com/100MB.bin"
    output_dir = tmp_path / "downloads"

    # Inisialisasi Engine
    downloader = RegularDownloader(connections=4, force=True)

    # Catatan: Test ini butuh koneksi internet
    await downloader.start(test_url, str(output_dir))

    # Verifikasi File Utama Ada
    filename = "100MB.bin"
    full_path = output_dir / filename
    assert full_path.exists()
    assert full_path.stat().st_size > 0

    # Verifikasi Partisi Sudah Dihapus (Cleanup Check)
    part_files = list(output_dir.glob("*.part*"))
    assert len(part_files) == 0


@pytest.mark.asyncio
async def test_force_overwrite(tmp_path):
    output_dir = tmp_path / "force_test"
    output_dir.mkdir()
    test_file = output_dir / "100MB.bin"

    # Buat file sampah seolah-olah file lama
    test_file.write_text("file lama")

    downloader = RegularDownloader(connections=10, force=True)
    await downloader.start("https://ash-speed.hetzner.com/100MB.bin", str(output_dir))

    # Cek apakah file lama sudah ditimpa (ukurannya pasti bukan lagi size "file lama")
    assert test_file.stat().st_size > 9
