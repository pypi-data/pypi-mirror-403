import locale
from typing import Dict

MESSAGES: Dict[str, Dict[str, str]] = {
    "id": {
        "TX_SUCCESS": "Transaksi berhasil: File telah diunduh sempurna.",
        "TX_FAILED": "Transaksi gagal: Masalah jaringan atau akses ditolak.",
        "AUTH_ERR": "Otentikasi gagal: Silakan cek kredensial Anda.",
        "FORCE_MODE": "◈ Mode: Force (File lama dibersihkan)",
        "FILE_EXISTS": "File sudah ada",
        "MERGING": "\n🛠️ Menggabungkan bagian-bagian...",
        "LOCATION": "📂 Lokasi: {full_path}",
        "URL_PROMPT": "URL file yang mau disedot",
        "CONNECTIONS_PROMPT": "Jumlah jalur paralel",
        "OUTPUT_PROMPT": "Folder tujuan",
        "FORCE_PROMPT": "Timpa file jika sudah ada",
        "CHUNK_SIZE_PROMPT": "Ukuran chunk dalam bytes default adalah 65536 (64KB) untuk performa optimal",
        "RATE_LIMIT_PROMPT": "Batas kecepatan per koneksi (bytes/detik, 0 untuk unlimited)",
        "CANCELLED": "\n🛑 Download dibatalkan oleh user.",
        "YOUTUBE_WARNING": "📺 Mesin YouTube segera hadir! Kembali ke Regular...",
        "RESUME_SUPPORTED": "Didukung",
        "RESUME_NOT_SUPPORTED": "Tidak Didukung",
        "DISK_SPACE_LOW": "Disk space hampir penuh!",
        "SEARCHING_QUALITIES": "🔍 Sedang mencari pilihan kualitas...",
        "SELECT_QUALITY": "📺 Pilih Kualitas Video:",
        "CHOOSE_NUMBER": "Pilih nomor (1-{count}) [default 1]: ",
        "VIDEO_CODEC": "Video {codec}",
        "FFMPEG_NOT_FOUND": "ffmpeg tidak ditemukan!",
        "YOUTUBE_MODE": "(Mode YouTube)",
        "FFMPEG_WINDOWS_ERROR": "ffmpeg.exe tidak ditemukan!",
        "FFMPEG_TIPS_WINDOWS": "💡 Tips Windows: Download ffmpeg, and assign the folder 'bin' to Environment Variables (PATH)",
        "FFMPEG_LINK_WINDOWS": "🔗 Link: https://www.gyan.dev/ffmpeg/builds/",
        "FFMPEG_TIPS_FEDORA": "💡 Tips Fedora: 'sudo dnf install ffmpeg'",
        "FFMPEG_TIPS_UBUNTU": "💡 Tips Ubuntu/Debian: 'sudo apt install ffmpeg'",
        "FFMPEG_TIPS_ARCH": "💡 Tips Arch: 'sudo pacman -S ffmpeg'",
        "FFMPEG_LINK_LINUX": "🔗 Link: https://ffmpeg.org/download.html",
    },
    "en": {
        "TX_SUCCESS": "Transaction successful: File downloaded perfectly.",
        "TX_FAILED": "Transaction failed: Network issue or access denied.",
        "AUTH_ERR": "Authentication failed: Please check your credentials.",
        "FORCE_MODE": "◈ Mode: Force (Old file cleared)",
        "FILE_EXISTS": "File already exists",
        "MERGING": "\n🛠️ Merging parts...",
        "LOCATION": "📂 Location: {full_path}",
        "URL_PROMPT": "URL of the file to be fetched",
        "CONNECTIONS_PROMPT": "Number of parallel connections",
        "OUTPUT_PROMPT": "Destination folder",
        "FORCE_PROMPT": "Overwrite file if it already exists",
        "CHUNK_SIZE_PROMPT": "Chunk size in bytes default is 65536 (64KB) for optimal performance",
        "RATE_LIMIT_PROMPT": "Rate limit per connection (bytes/second, 0 for unlimited)",
        "CANCELLED": "\n🛑 Download cancelled by user.",
        "YOUTUBE_WARNING": "📺 YouTube engine coming soon! Falling back to Regular...",
        "RESUME_SUPPORTED": "Supported",
        "RESUME_NOT_SUPPORTED": "Not Supported",
        "DISK_SPACE_LOW": "Disk space running low!",
        "SEARCHING_QUALITIES": "🔍 Searching for quality options...",
        "SELECT_QUALITY": "📺 Select Video Quality:",
        "CHOOSE_NUMBER": "Choose number (1-{count}) [default 1]: ",
        "VIDEO_CODEC": "Video {codec}",
        "FFMPEG_NOT_FOUND": "ffmpeg not found!",
        "YOUTUBE_MODE": "(YouTube Mode)",
        "FFMPEG_WINDOWS_ERROR": "ffmpeg.exe not found!",
        "FFMPEG_TIPS_WINDOWS": "💡 Tips Windows: Download ffmpeg, and assign the folder 'bin' to Environment Variables (PATH)",
        "FFMPEG_LINK_WINDOWS": "🔗 Link: https://www.gyan.dev/ffmpeg/builds/",
        "FFMPEG_TIPS_FEDORA": "💡 Tips Fedora: 'sudo dnf install ffmpeg'",
        "FFMPEG_TIPS_UBUNTU": "💡 Tips Ubuntu/Debian: 'sudo apt install ffmpeg'",
        "FFMPEG_TIPS_ARCH": "💡 Tips Arch: 'sudo pacman -S ffmpeg'",
        "FFMPEG_LINK_LINUX": "🔗 Link: https://ffmpeg.org/download.html",
    },
}


def _detect_language():
    """fallback 'en'."""
    try:
        loc = locale.getdefaultlocale()[0]
        if loc:
            lang = loc.split("_")[0].lower()
            if lang in MESSAGES:
                return lang
    except Exception:
        pass
    return "en"


def get_message(key, lang=None):
    if lang is None:
        lang = _detect_language()
    return MESSAGES.get(lang, MESSAGES["en"]).get(key, "Error")
