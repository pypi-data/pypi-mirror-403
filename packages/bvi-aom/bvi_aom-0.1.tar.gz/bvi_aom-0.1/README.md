# BVI-AOM Dataset Downloader

A Python utility for downloading the [BVI-AOM](https://arxiv.org/abs/2408.03265) (Bristol Vision Institute - Alliance for Open Media) video dataset hosted on Netflix's Open Content platform.

## Installation

```bash
pip install bvi-aom
```

## Usage

### Command Line Interface

Download a single resolution:

```bash
bvi-aom /path/to/storage -r 1920x1088
```

Download multiple resolutions:

```bash
bvi-aom /path/to/storage -r 1920x1088 960x544 480x272
```

Remove tar files after extraction to save disk space:

```bash
bvi-aom /path/to/storage -r 1920x1088 --remove-tar
```

### Python API

```python
from bvi_aom import BVIAOMDataset

# Download a single resolution
dataset = BVIAOMDataset('/path/to/storage', '1920x1088')

# Download multiple resolutions
dataset = BVIAOMDataset('/path/to/storage', ['1920x1088', '960x544'])

# Remove tar files after extraction
dataset = BVIAOMDataset('/path/to/storage', '1920x1088', remove_tar=True)
```

## Available Resolutions

| Resolution | Description |
|------------|-------------|
| `3840x2176` | 4K UHD (split into 6 parts) |
| `1920x1088` | 1080p Full HD |
| `960x544` | 544p |
| `480x272` | 272p |

## Features

- **Automatic download**: Fetches video sequences from S3 bucket
- **Multi-resolution support**: Download one or more resolutions in a single command
- **Cleanup option**: Optionally remove tar files after extraction with `--remove-tar`

## Dataset Information

The BVI-AOM dataset is a collection of high-quality video sequences used for video codec development and evaluation by the Alliance for Open Media (AOM).
The files can be quite large, so ensure you have sufficient storage space.

## License

The BVI-AOM dataset is subject to its own licensing terms. Please refer to [BVI-AOM Paper](https://arxiv.org/abs/2408.03265). 
