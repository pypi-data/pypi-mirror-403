# multimedia

This is a thin web client for a directory containing video files.


## Installation

Installation is optional. It's recommended to use multimedia directly either by using uvx or docker (see [running](#running) below).

```shell
pip install multimedia
```

## Requirements

**FFmpeg** is required for video processing (thumbnail generation and metadata extraction).

- **macOS:** `brew install ffmpeg`
- **Ubuntu/Debian:** `sudo apt install ffmpeg`
- **Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html) or use `choco install ffmpeg`

When using Docker, FFmpeg is included in the image.

## Running

### Using Docker

```shell
docker run \
    -p 8028:8028 \
    -v ${PWD}:/media \
    ozkatz/multimedia
```

### Using UV

If you have [uv installed](https://docs.astral.sh/uv/getting-started/installation/), you can call multimedia directly with `uvx`:

```shell
MULTIMEDIA_DIR="${PWD}" uvx multimedia
```

### Using pip

If installed via pip, simply run:

```shell
MULTIMEDIA_DIR="${PWD}" multimedia
```

## Configuration

Configuring Multimedia is done using environment variables. Typically, minimal configuration is required:


| Env var | Default Value | Description |
|---------|---------------|-------------|
| `MULTIMEDIA_DIR` | `.` | Path to the directory to index video files and images from |
| `MULTIMEDIA_PASSPHRASE` | *(none)* | If set, requires this passphrase to access the UI and API |

### Authentication

To protect your multimedia server with a passphrase:

```shell
MULTIMEDIA_DIR="${PWD}" MULTIMEDIA_PASSPHRASE="your-secret-passphrase" uvx multimedia
```

When a passphrase is configured:
- Users must enter the passphrase in the browser before accessing the UI
- API requests require a `Bearer` token in the `Authorization` header
- The passphrase is stored in the browser's session storage (cleared when tab closes)

## Usage

Once you have a multimedia server running, access it in your web browser:

```
http://localhost:8028/
```

## Development

### Prerequisites

- Python 3.10+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)
- FFmpeg (for video processing)

### Setup

Clone the repository and install dependencies:

```shell
git clone https://github.com/ozkatz/multimedia.git
cd multimedia

# Install Python dependencies
uv sync

# Install frontend dependencies
cd frontend
npm install
```

### Building the Frontend

The React frontend must be built before running the server:

```shell
cd frontend
npm run build
```

This outputs the production build to `src/multimedia/static/`.

### Running in Development

Start the backend server:

```shell
MULTIMEDIA_DIR="/path/to/videos" uv run multimedia
```

For frontend development with hot reload, run in a separate terminal:

```shell
cd frontend
npm run dev
```

The Vite dev server proxies API requests to `http://localhost:8028`.

### Building for Distribution

Build the Python package:

```shell
# Ensure frontend is built first
cd frontend && npm run build && cd ..

# Build wheel
uv build
```

The wheel will be in `dist/`.

### Publishing to PyPI

To publish a new version:

```shell
# Build frontend and package
cd frontend && npm run build && cd ..
uv build

# Publish to PyPI (requires PyPI token)
uv publish
```

To publish to TestPyPI first:

```shell
uv publish --publish-url https://test.pypi.org/legacy/
```

Set your PyPI token via environment variable or keyring:

```shell
export UV_PUBLISH_TOKEN=pypi-your-token-here
```

### Building Docker Image

```shell
docker build -t multimedia .
```

## License

This project is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for the full license text.
