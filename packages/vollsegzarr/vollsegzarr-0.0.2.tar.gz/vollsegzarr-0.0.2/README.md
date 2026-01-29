# VollSegZarr

**Zarr-enabled volume segmentation for extremely large microscopy images**

VollSegZarr is a fork of [VollSeg](https://github.com/Kapoorlabs-CAPED/vollseg) that adds native support for **Zarr** format, enabling efficient processing of multi-terabyte microscopy volumes that don't fit in memory.

## Features

- **Zarr Format Support**: Native support for chunked, compressed Zarr arrays
- **Memory Efficient**: Process images larger than available RAM
- **100% Backward Compatible**: Works with all existing TIFF workflows
- **Automatic Format Detection**: Transparently handles TIFF and Zarr
- **Better Compression**: 60-80% smaller file sizes with Zstd
- **Cloud Ready**: Efficient streaming from cloud storage
- **All VollSeg Modes**: StarDist, UNET, Hybrid, CellPose, etc.

## Installation

```bash
pip install vollsegzarr
```

## Quick Start

```python
from vollsegzarr import VollSeg, StarDist3D
from vollsegzarr.zarr_io import imread, imwrite

# Load model
star_model = StarDist3D.local_from_pretrained("Carcinoma_cells")

# Segment from Zarr (or TIFF - automatic detection)
image = imread("data/volume.zarr")
results = VollSeg(image, star_model=star_model, axes="ZYX", n_tiles=(4, 8, 8))

# Save to Zarr
imwrite("output/labels.zarr", results[1], compression='zstd')
```

See [README_ZARR.md](README_ZARR.md) for full documentation.

## Why Zarr?

For huge images like (201, 5, 7577, 7577) ≈ 114 GB:
- TIFF: 114 GB file, 2-5 min load, 114 GB RAM required
- Zarr: 20-40 GB file, < 1 sec load, on-demand memory

## License

BSD-3-Clause

## Credits

Original VollSeg by Varun Kapoor et al. Zarr integration for large-scale imaging.
