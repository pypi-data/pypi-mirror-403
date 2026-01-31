# D-Fetch

**D-Fetch** is a high-speed, multi-connection downloader engine built with Python. Developed by **Dayona** to provide a fast and efficient download experience.

[![CI Status](https://github.com/dayonaa/d-fetch/actions/workflows/ci.yml/badge.svg)](https://github.com/dayonaa/d-fetch/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/dfetch-cli.svg)](https://pypi.org/project/dfetch-cli/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Key Features

- **High Speed**: Uses parallel connections for faster downloads
- **YouTube Support**: Download YouTube videos with various qualities
- **Resume Downloads**: Continue interrupted downloads
- **Universal Downloader**: Supports various file types and URLs
- **Full Control**: Customize number of connections, chunk size, and rate limits
- **Force Mode**: Overwrite existing files
- **Multi-language**: Support for Indonesian and English
- **Progress Bar**: Informative progress display with tqdm

## Installation

### System Requirements

- Python 3.10 or newer
- ffmpeg (for YouTube downloads)

### Installing uv

For the best experience, we recommend using uv, a fast Python package installer powered by Rust. Install uv with:

**Linux/macOS:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Installation from Source

```bash
# Clone repository
git clone https://github.com/dayonaa/d-fetch.git
cd d-fetch

# Install with pip
pip install .

# Or using uv (recommended)
uv pip install .

# To build the package
uv build
```

### Installation from PyPI (if available)

```bash
pip install d-fetch
```

### Installing ffmpeg

For YouTube downloads, you need to install ffmpeg:

**Linux (Ubuntu/Debian):**

```bash
sudo apt install ffmpeg
```

**Linux (Fedora):**

```bash
sudo dnf install ffmpeg
```

**Linux (Arch):**

```bash
sudo pacman -S ffmpeg
```

**Windows:**

1. Download from [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/)
2. Extract and add the `bin` folder to PATH environment variables

## Usage

### Basic Syntax

```bash
d-fetch [OPTIONS] URL
```

### Command Line Options

| Option              | Description                                             | Default               |
| ------------------- | ------------------------------------------------------- | --------------------- |
| `URL`               | URL of the file to download                             | -                     |
| `-c, --connections` | Number of parallel connections                          | 8                     |
| `-o, --output`      | Destination folder                                      | . (current directory) |
| `-f, --force`       | Overwrite file if it already exists                     | False                 |
| `-s, --chunk-size`  | Chunk size in bytes                                     | 65536 (64KB)          |
| `-r, --rate-limit`  | Rate limit per connection (bytes/second, 0 = unlimited) | 0                     |

### Usage Examples

#### Regular File Download

```bash
# Download with default settings
d-fetch https://example.com/file.zip

# Download with 16 parallel connections
d-fetch -c 16 https://example.com/large-file.zip

# Download to specific folder
d-fetch -o /path/to/downloads https://example.com/file.zip

# Overwrite file if it exists
d-fetch -f https://example.com/file.zip

# Limit download speed (100KB/s per connection)
d-fetch -r 102400 https://example.com/file.zip
```

#### YouTube Video Download

```bash
# Download YouTube video (will select best quality)
d-fetch https://www.youtube.com/watch?v=VIDEO_ID

# Download with manual quality selection
d-fetch https://youtu.be/VIDEO_ID
```

### Sample Output

```
D-Fetch v0.0.1 - Universal High-Speed Downloader
URL: https://example.com/file.zip
Output: /home/user/downloads/file.zip
Connections: 8
Size: 1.2 GB

100%|████████████████████████████████████████| 1.23G/1.23G [00:45<00:00, 27.1MB/s]

Transaction successful: File downloaded perfectly.
Location: /home/user/downloads/file.zip
```

## Architecture

```
d_fetch/
├── main.py              # Entry point and CLI
├── messages.py          # Multi-language messages
├── engine/
│   ├── base.py          # Base downloader class
│   ├── regular_downloader.py  # Regular file downloader
│   └── youtube_downloader.py  # YouTube-specific downloader
└── utils/
    └── helpers.py       # Utility functions
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/dayonaa/d-fetch.git
cd d-fetch

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync --dev

# Activate the environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run tests
uv run pytest tests/

# Check code quality
uv run ruff check .

# Format code
uv run ruff format .
```

### Code Quality

This project uses:

- **ruff**: Fast Python linter and formatter (basic E/F/I rules)
- **pytest**: Testing framework
- **pytest-asyncio**: Async testing support

Run quality checks:

```bash
# Lint and format
uv run ruff check . --fix
uv run ruff format .

# Run tests with coverage
uv run pytest tests/ --cov=d_fetch --cov-report=html
```

## CI/CD

This project uses GitHub Actions for continuous integration and deployment. The CI pipeline includes:

- **Testing**: Runs tests on Python 3.10, 3.11, and 3.12
- **Linting**: Basic code quality checks with ruff (E/F rules)
- **Building**: Package building verification

To set up PyPI publishing:

1. Create a PyPI API token at https://pypi.org/manage/account/token/
2. Add `PYPI_API_TOKEN` as a repository secret in GitHub

## Contributing

Contributions are very welcome! Please:

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Create a Pull Request

### Contribution Guidelines

- Follow PEP 8 for Python code style
- Add tests for new features
- Update documentation if needed
- Use descriptive commit messages

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

- **Developer**: Dayona (arifadayona@gmail.com)
- **Dependencies**: httpx, tqdm, yt-dlp
- **Inspiration**: The need for a fast and reliable downloader

## Issues and Support

If you find a bug or have questions:

1. Check existing [Issues](https://github.com/dayonaa/d-fetch/issues)
2. Create a new Issue if none exists
3. Include system information and steps to reproduce the problem

## Roadmap

- [ ] Proxy support
- [ ] GUI interface
- [ ] Torrent support
- [ ] Browser extension integration
- [ ] Batch download from file list

## Project Structure

```
d-fetch/
├── .github/
│   └── workflows/
│       └── ci.yml          # GitHub Actions CI/CD
├── src/d_fetch/
│   ├── main.py             # Entry point and CLI
│   ├── messages.py         # Multi-language messages
│   ├── engine/
│   │   ├── base.py         # Base downloader class
│   │   ├── regular_downloader.py  # Regular file downloader
│   │   └── youtube_downloader.py  # YouTube-specific downloader
│   └── utils/
│       └── helpers.py      # Utility functions
├── tests/                  # Test files
├── pyproject.toml          # Project configuration
├── README.md               # This file
├── LICENSE                 # MIT License
└── .gitignore             # Git ignore rules
```

---
