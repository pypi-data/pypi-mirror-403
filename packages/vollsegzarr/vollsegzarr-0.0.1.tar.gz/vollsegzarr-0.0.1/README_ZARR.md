# VollSegZarr - Zarr-Enabled Volume Segmentation

VollSegZarr is a fork of VollSeg that adds native support for **Zarr** format alongside TIFF files, enabling efficient processing of extremely large microscopy volumes.

## What's New

### Zarr Format Support

VollSegZarr can now read and write images in **Zarr** format, which offers:

- **Chunked storage**: Only load the data you need
- **Better compression**: Smaller file sizes (Blosc/Zstd compression)
- **Cloud-ready**: Efficient streaming from cloud storage
- **Parallel I/O**: Faster reading/writing with multi-threading
- **Metadata**: Rich metadata support with `.zattrs`

### Backward Compatibility

- **100% compatible with original VollSeg TIFF workflows**
- Automatically detects file format (TIFF or Zarr)
- No changes needed to existing code - just change file extension!

## Installation

```bash
cd /home/debian/python_workspace/VollSegZarr
pip install -e .
```

**Additional requirement for Zarr:**
```bash
pip install zarr
```

## Usage

### Basic Segmentation

```python
from vollseg import VollSeg, UNET, StarDist3D
from vollseg.zarr_io import imread, imwrite

# Load pretrained models
unet_model = UNET.local_from_pretrained("Embryo Cell Model (3D)")
star_model = StarDist3D.local_from_pretrained("Carcinoma_cells")

# Load image from Zarr (or TIFF - automatic detection)
image = imread("data/volume.zarr")  # Shape: (Z, Y, X)

# Run segmentation
results = VollSeg(
    image,
    unet_model=unet_model,
    star_model=star_model,
    axes="ZYX",
    n_tiles=(1, 4, 4),  # Larger n_tiles for huge images
    min_size=100
)

# Save results to Zarr
smart_seeds, instance_labels, star_labels, prob, markers, skeleton = results[:6]
imwrite("output/instance_labels.zarr", instance_labels, chunks=(64, 512, 512))
imwrite("output/probability.zarr", prob, compression='zstd')
```

### Converting Between Formats

```python
from vollseg.zarr_io import convert_tiff_to_zarr, convert_zarr_to_tiff

# TIFF → Zarr
convert_tiff_to_zarr(
    'data/huge_image.tif',
    'data/huge_image.zarr',
    chunks=(64, 512, 512),
    compression='zstd'
)

# Zarr → TIFF
convert_zarr_to_tiff('data/image.zarr', 'data/image.tif')
```

### Automatic Format Detection

The library automatically detects format based on file extension:

```python
from vollseg.zarr_io import imread, imwrite

# Read TIFF
img_tiff = imread('data/cells.tif')

# Read Zarr
img_zarr = imread('data/cells.zarr')

# Write to Zarr (detected from .zarr extension)
imwrite('output/result.zarr', labels)

# Write to TIFF (detected from .tif extension)
imwrite('output/result.tif', labels, compression='zlib')
```

## Zarr-Specific Features

### Chunking Strategy

VollSegZarr auto-determines optimal chunk sizes, but you can override:

```python
# Auto-chunking (recommended)
imwrite('output/labels.zarr', data)

# Manual chunking
imwrite('output/labels.zarr', data, chunks=(64, 256, 256))

# For 5D data: (T, C, Z, Y, X)
imwrite('output/timeseries.zarr', data, chunks=(1, 1, 64, 512, 512))
```

### Compression Options

```python
# Zstd (recommended for best compression)
imwrite('output/labels.zarr', data, compression='zstd')

# Blosc (fast, good compression)
imwrite('output/labels.zarr', data, compression='blosc')

# LZ4 (fastest)
imwrite('output/labels.zarr', data, compression='lz4')

# No compression
imwrite('output/labels.zarr', data, compression=None)
```

### Metadata Storage

```python
metadata = {
    'voxel_size_um': [2.0, 0.5, 0.5],  # Z, Y, X
    'channels': ['DAPI', 'GFP', 'RFP'],
    'model': 'StarDist3D',
    'timestamp': '2026-01-23'
}

imwrite('output/labels.zarr', data, metadata=metadata)

# Read metadata back
import zarr
z = zarr.open('output/labels.zarr', mode='r')
print(z.attrs.asdict())
```

## Key Modifications

### 1. New `zarr_io.py` Module

Located at `src/vollseg/zarr_io.py`, provides:

- `imread()`: Unified reader for TIFF and Zarr
- `imwrite()`: Unified writer for TIFF and Zarr
- `is_zarr()`, `is_tiff()`: Format detection
- `convert_tiff_to_zarr()`, `convert_zarr_to_tiff()`: Format conversion
- `get_acceptable_formats()`: List of supported formats

### 2. Updated Core Files

- **`utils.py`**: Imports from `zarr_io` instead of `tifffile`
- **`SmartPatches.py`**: Zarr support in patch generation
- **`SmartSeeds2D.py`**: Zarr support in 2D training data
- **`SmartSeeds3D.py`**: Zarr support in 3D training data
- **`CellPose.py`**: Zarr support in CellPose workflows

### 3. Acceptable Formats Extended

All file format checks now include `.zarr`:
```python
['.tif', '.tiff', '.TIF', '.TIFF', '.zarr', '.png']
```

## Performance Benefits

For the example image `(201, 5, 7577, 7577)` (~114 GB):

| Format | File Size | Load Time | Memory Usage | Chunked Access |
|--------|-----------|-----------|--------------|----------------|
| TIFF | ~114 GB | ~2-5 min | 114 GB RAM | ❌ No |
| Zarr (zstd) | ~20-40 GB | < 1 sec* | On-demand | ✅ Yes |

*When using chunked reading (only loads needed chunks)

## Example: Processing Huge Images

```python
from vollseg import VollSeg, StarDist3D
from vollseg.zarr_io import imread, imwrite
import zarr

# For huge image (201, 5, 7577, 7577), convert to Zarr first
from vollseg.zarr_io import convert_tiff_to_zarr

# Convert once
convert_tiff_to_zarr(
    'data/huge_organoid.tif',
    'data/huge_organoid.zarr',
    chunks=(50, 1, 2048, 2048),  # Z, C, Y, X
    compression='zstd'
)

# Now segment each channel efficiently
z_arr = zarr.open('data/huge_organoid.zarr', mode='r')

for ch_idx in range(z_arr.shape[1]):  # Iterate channels
    print(f"Segmenting channel {ch_idx}...")

    # Extract one channel (only loads this channel into RAM)
    channel_data = z_arr[:, ch_idx, :, :]  # (Z, Y, X)

    # Segment with extreme tiling for memory efficiency
    results = VollSeg(
        channel_data,
        star_model=star_model,
        axes="ZYX",
        n_tiles=(4, 16, 16),  # Process in 64 tiles
        min_size=100
    )

    # Save results to Zarr
    labels = results[1]
    imwrite(
        f'output/channel_{ch_idx}_labels.zarr',
        labels,
        chunks=(64, 512, 512),
        compression='zstd'
    )
```

## Migration Guide

### From VollSeg to VollSegZarr

1. **Install VollSegZarr**:
   ```bash
   pip install zarr
   cd /home/debian/python_workspace/VollSegZarr
   pip install -e .
   ```

2. **Update imports** (optional - for explicit Zarr I/O):
   ```python
   # Old
   from tifffile import imread, imwrite

   # New
   from vollseg.zarr_io import imread, imwrite
   ```

3. **Use Zarr files**:
   ```python
   # Change file extensions
   imread('data/image.zarr')  # Instead of .tif
   imwrite('output/labels.zarr', data)  # Instead of .tif
   ```

4. **Or keep using TIFF** - VollSegZarr is fully backward compatible!

## Supported Segmentation Modes (All Zarr-Compatible)

All original VollSeg modes now support Zarr:

- ✅ StarDist 2D/3D
- ✅ UNET semantic segmentation
- ✅ Hybrid VollSeg (UNET + StarDist + Watershed)
- ✅ CARE denoising
- ✅ ROI-based segmentation (MASKUNET)
- ✅ CellPose integration
- ✅ Time-series (4D) segmentation
- ✅ Multi-channel (5D) segmentation

## Limitations

- PNG files still supported for 2D only (Zarr recommended for 3D+)
- Some legacy napari viewers may need updates for Zarr visualization
- First-time Zarr writes are slower (but subsequent reads are much faster)

## Contributing

VollSegZarr maintains the same API as VollSeg. All existing VollSeg code works without modification.

## Credits

- **Original VollSeg**: Varun Kapoor (Kapoorlabs-CAPED)
- **Zarr Integration**: Extended for large-scale organoid imaging workflows

## License

Same as original VollSeg repository.
