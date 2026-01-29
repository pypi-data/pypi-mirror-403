"""
Unified I/O module for reading and writing both TIFF and Zarr formats.

This module provides a transparent interface that automatically detects
file format and handles reading/writing appropriately.
"""

import os
import zarr
import numpy as np
from pathlib import Path
from typing import Union, Optional, Tuple, Dict, Any
from tifffile import imread as tiff_imread, imwrite as tiff_imwrite


def is_zarr(path: Union[str, Path]) -> bool:
    """
    Check if a path points to a Zarr array.

    Parameters
    ----------
    path : str or Path
        Path to check

    Returns
    -------
    bool
        True if path is a Zarr array, False otherwise
    """
    path = Path(path)

    # Check for .zarr extension or .zarray file
    if path.suffix == '.zarr':
        return True
    if (path / '.zarray').exists():
        return True
    if path.name.endswith('.zarr'):
        return True

    return False


def is_tiff(path: Union[str, Path]) -> bool:
    """
    Check if a path points to a TIFF file.

    Parameters
    ----------
    path : str or Path
        Path to check

    Returns
    -------
    bool
        True if path is a TIFF file, False otherwise
    """
    path = Path(path)
    tiff_extensions = {'.tif', '.tiff', '.TIF', '.TIFF'}
    return path.suffix in tiff_extensions


def imread(
    path: Union[str, Path],
    **kwargs
) -> np.ndarray:
    """
    Read image from TIFF or Zarr format.

    Automatically detects format based on file extension/structure.

    Parameters
    ----------
    path : str or Path
        Path to image file (TIFF or Zarr)
    **kwargs
        Additional arguments passed to format-specific reader

    Returns
    -------
    np.ndarray
        Loaded image array

    Examples
    --------
    >>> img = imread('data/image.tif')
    >>> img = imread('data/image.zarr')
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if is_zarr(path):
        # Read from Zarr
        z = zarr.open(str(path), mode='r')
        return np.array(z)
    elif is_tiff(path):
        # Read from TIFF
        return tiff_imread(str(path), **kwargs)
    else:
        # Try TIFF as fallback (for backwards compatibility)
        try:
            return tiff_imread(str(path), **kwargs)
        except Exception as e:
            raise ValueError(
                f"Unsupported file format: {path.suffix}. "
                f"Supported formats: .tif, .tiff, .zarr. Error: {e}"
            )


def imwrite(
    path: Union[str, Path],
    data: np.ndarray,
    compression: Optional[str] = 'zlib',
    chunks: Optional[Tuple[int, ...]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """
    Write image to TIFF or Zarr format.

    Format is determined by file extension.

    Parameters
    ----------
    path : str or Path
        Output path (.tif/.tiff for TIFF, .zarr for Zarr)
    data : np.ndarray
        Image data to write
    compression : str, optional
        Compression method:
        - For TIFF: 'zlib', 'lzw', 'jpeg', etc.
        - For Zarr: 'blosc', 'zstd', 'lz4', 'gzip', etc.
        Default: 'zlib'
    chunks : tuple of int, optional
        Chunk shape for Zarr arrays. If None, auto-determined.
        Ignored for TIFF.
    metadata : dict, optional
        Metadata to store with the image
    **kwargs
        Additional arguments passed to format-specific writer

    Examples
    --------
    >>> imwrite('output/result.tif', labels)
    >>> imwrite('output/result.zarr', labels, chunks=(64, 256, 256))
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.suffix == '.zarr' or path.name.endswith('.zarr'):
        # Write to Zarr
        _write_zarr(path, data, compression, chunks, metadata, **kwargs)
    else:
        # Write to TIFF
        _write_tiff(path, data, compression, metadata, **kwargs)


def _write_zarr(
    path: Path,
    data: np.ndarray,
    compression: Optional[str],
    chunks: Optional[Tuple[int, ...]],
    metadata: Optional[Dict[str, Any]],
    **kwargs
) -> None:
    """Write data to Zarr format."""

    # Auto-determine chunks if not provided
    if chunks is None:
        chunks = _auto_chunks(data.shape)

    # Map compression names
    if compression == 'zlib':
        compressor = zarr.Blosc(cname='zlib', clevel=5, shuffle=zarr.Blosc.SHUFFLE)
    elif compression == 'blosc':
        compressor = zarr.Blosc(cname='zstd', clevel=5, shuffle=zarr.Blosc.SHUFFLE)
    elif compression == 'zstd':
        compressor = zarr.Blosc(cname='zstd', clevel=5, shuffle=zarr.Blosc.SHUFFLE)
    elif compression == 'lz4':
        compressor = zarr.Blosc(cname='lz4', clevel=5, shuffle=zarr.Blosc.SHUFFLE)
    elif compression == 'gzip':
        compressor = zarr.Blosc(cname='zlib', clevel=5, shuffle=zarr.Blosc.SHUFFLE)
    elif compression is None:
        compressor = None
    else:
        compressor = zarr.Blosc(cname='zstd', clevel=5, shuffle=zarr.Blosc.SHUFFLE)

    # Create Zarr array
    z = zarr.open(
        str(path),
        mode='w',
        shape=data.shape,
        chunks=chunks,
        dtype=data.dtype,
        compressor=compressor,
        **kwargs
    )

    # Write data
    z[:] = data

    # Write metadata
    if metadata:
        z.attrs.update(metadata)


def _write_tiff(
    path: Path,
    data: np.ndarray,
    compression: Optional[str],
    metadata: Optional[Dict[str, Any]],
    **kwargs
) -> None:
    """Write data to TIFF format."""

    # Prepare TIFF metadata
    tiff_kwargs = {}
    if compression:
        tiff_kwargs['compression'] = compression

    # Merge with additional kwargs
    tiff_kwargs.update(kwargs)

    # Write TIFF
    tiff_imwrite(str(path), data, **tiff_kwargs)


def _auto_chunks(shape: Tuple[int, ...]) -> Tuple[int, ...]:
    """
    Automatically determine optimal chunk sizes for Zarr arrays.

    Strategy:
    - Target chunk size: ~64-256 MB
    - Prefer full slices in leading dimensions
    - Tile spatial dimensions

    Parameters
    ----------
    shape : tuple of int
        Array shape

    Returns
    -------
    tuple of int
        Chunk sizes
    """
    ndim = len(shape)

    if ndim == 2:
        # 2D: tile both dimensions
        return (min(1024, shape[0]), min(1024, shape[1]))

    elif ndim == 3:
        # 3D (Z, Y, X): small Z chunks, tile YX
        z_chunk = min(64, shape[0])
        y_chunk = min(512, shape[1])
        x_chunk = min(512, shape[2])
        return (z_chunk, y_chunk, x_chunk)

    elif ndim == 4:
        # 4D (T, Z, Y, X) or (C, Z, Y, X): one frame/channel at a time
        return (1, min(64, shape[1]), min(512, shape[2]), min(512, shape[3]))

    elif ndim == 5:
        # 5D (T, C, Z, Y, X): one frame, one channel
        return (1, 1, min(64, shape[2]), min(512, shape[3]), min(512, shape[4]))

    else:
        # Default: chunk all dimensions to reasonable sizes
        return tuple(min(256, s) for s in shape)


def get_acceptable_formats() -> list:
    """
    Get list of acceptable file format extensions.

    Returns
    -------
    list of str
        List of supported file extensions
    """
    return ['.tif', '.tiff', '.TIF', '.TIFF', '.zarr', '.png']


def convert_tiff_to_zarr(
    tiff_path: Union[str, Path],
    zarr_path: Union[str, Path],
    chunks: Optional[Tuple[int, ...]] = None,
    compression: str = 'zstd'
) -> None:
    """
    Convert a TIFF file to Zarr format.

    Parameters
    ----------
    tiff_path : str or Path
        Input TIFF file path
    zarr_path : str or Path
        Output Zarr path
    chunks : tuple of int, optional
        Chunk sizes. Auto-determined if None.
    compression : str, optional
        Compression algorithm. Default: 'zstd'

    Examples
    --------
    >>> convert_tiff_to_zarr('data/image.tif', 'data/image.zarr')
    """
    # Read TIFF
    data = tiff_imread(str(tiff_path))

    # Write Zarr
    imwrite(zarr_path, data, compression=compression, chunks=chunks)

    print(f"Converted {tiff_path} -> {zarr_path}")
    print(f"  Shape: {data.shape}, Dtype: {data.dtype}")
    if chunks is None:
        chunks = _auto_chunks(data.shape)
    print(f"  Chunks: {chunks}")


def convert_zarr_to_tiff(
    zarr_path: Union[str, Path],
    tiff_path: Union[str, Path],
    compression: str = 'zlib'
) -> None:
    """
    Convert a Zarr array to TIFF format.

    Parameters
    ----------
    zarr_path : str or Path
        Input Zarr path
    tiff_path : str or Path
        Output TIFF file path
    compression : str, optional
        TIFF compression. Default: 'zlib'

    Examples
    --------
    >>> convert_zarr_to_tiff('data/image.zarr', 'data/image.tif')
    """
    # Read Zarr
    data = imread(zarr_path)

    # Write TIFF
    tiff_imwrite(str(tiff_path), data, compression=compression)

    print(f"Converted {zarr_path} -> {tiff_path}")
    print(f"  Shape: {data.shape}, Dtype: {data.dtype}")
