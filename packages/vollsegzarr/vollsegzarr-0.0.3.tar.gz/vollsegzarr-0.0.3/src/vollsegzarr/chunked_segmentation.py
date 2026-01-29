"""
Chunked segmentation for extremely large volumes.

Breaks a large 3D volume into overlapping chunks, segments each chunk,
and stitches them back together with proper label handling.
"""

import numpy as np
from typing import Tuple, Optional, List
from tqdm import tqdm
import gc
from .utils import VollSeg

def chunk_volume_3d(
    volume_shape: Tuple[int, int, int],
    chunk_size: Tuple[int, int, int],
    overlap: Tuple[int, int, int]
) -> List[Tuple[slice, slice, slice]]:
    """
    Generate slicing coordinates for chunking a 3D volume with overlap.

    Parameters
    ----------
    volume_shape : tuple of int
        Shape of the volume (Z, Y, X)
    chunk_size : tuple of int
        Size of each chunk (Z, Y, X)
    overlap : tuple of int
        Overlap between chunks (Z, Y, X)

    Returns
    -------
    list of tuples
        List of (z_slice, y_slice, x_slice) for each chunk
    """
    z_size, y_size, x_size = volume_shape
    z_chunk, y_chunk, x_chunk = chunk_size
    z_overlap, y_overlap, x_overlap = overlap

    chunks = []

    # Calculate step sizes (chunk - overlap)
    z_step = z_chunk - z_overlap
    y_step = y_chunk - y_overlap
    x_step = x_chunk - x_overlap

    # Generate chunks
    z_starts = list(range(0, z_size, z_step))
    y_starts = list(range(0, y_size, y_step))
    x_starts = list(range(0, x_size, x_step))

    for z_start in z_starts:
        z_end = min(z_start + z_chunk, z_size)

        for y_start in y_starts:
            y_end = min(y_start + y_chunk, y_size)

            for x_start in x_starts:
                x_end = min(x_start + x_chunk, x_size)

                z_slice = slice(z_start, z_end)
                y_slice = slice(y_start, y_end)
                x_slice = slice(x_start, x_end)

                chunks.append((z_slice, y_slice, x_slice))

    return chunks


def stitch_single_chunk(
    stitched: np.ndarray,
    chunk_labels: np.ndarray,
    z_slice: slice,
    y_slice: slice,
    x_slice: slice,
    overlap: Tuple[int, int, int],
    max_label: int
) -> int:
    """
    Stitch a single segmented chunk into the output volume.

    Parameters
    ----------
    stitched : np.ndarray
        The output volume being built (modified in-place)
    chunk_labels : np.ndarray
        Segmentation labels for the current chunk
    z_slice, y_slice, x_slice : slice
        Position of this chunk in the full volume
    overlap : tuple of int
        Overlap used during chunking (Z, Y, X)
    max_label : int
        Current maximum label value in stitched volume

    Returns
    -------
    int
        Updated maximum label value
    """
    volume_shape = stitched.shape
    z_overlap, y_overlap, x_overlap = overlap

    # Get chunk coordinates
    z_start, z_end = z_slice.start, z_slice.stop
    y_start, y_end = y_slice.start, y_slice.stop
    x_start, x_end = x_slice.start, x_slice.stop

    # Renumber labels to avoid conflicts
    if chunk_labels.max() > 0:
        # Create mask of non-zero labels
        mask = chunk_labels > 0

        # Renumber: add max_label to all non-zero labels
        renumbered = chunk_labels.copy()
        renumbered[mask] = chunk_labels[mask] + max_label

        # Determine crop region to avoid overlap issues
        # For chunks not at boundaries, crop overlap region
        z_crop_start = z_overlap // 2 if z_start > 0 else 0
        z_crop_end = chunk_labels.shape[0] - (z_overlap // 2) if z_end < volume_shape[0] else chunk_labels.shape[0]

        y_crop_start = y_overlap // 2 if y_start > 0 else 0
        y_crop_end = chunk_labels.shape[1] - (y_overlap // 2) if y_end < volume_shape[1] else chunk_labels.shape[1]

        x_crop_start = x_overlap // 2 if x_start > 0 else 0
        x_crop_end = chunk_labels.shape[2] - (x_overlap // 2) if x_end < volume_shape[2] else chunk_labels.shape[2]

        # Crop the renumbered chunk
        cropped_chunk = renumbered[
            z_crop_start:z_crop_end,
            y_crop_start:y_crop_end,
            x_crop_start:x_crop_end
        ]

        # Calculate target coordinates in stitched volume
        target_z_start = z_start + z_crop_start
        target_z_end = z_start + z_crop_end
        target_y_start = y_start + y_crop_start
        target_y_end = y_start + y_crop_end
        target_x_start = x_start + x_crop_start
        target_x_end = x_start + x_crop_end

        # Place in stitched volume (only where stitched is still 0)
        target_region = stitched[
            target_z_start:target_z_end,
            target_y_start:target_y_end,
            target_x_start:target_x_end
        ]

        # Only place labels where target is empty (0)
        placement_mask = (target_region == 0) & (cropped_chunk > 0)
        target_region[placement_mask] = cropped_chunk[placement_mask]

        # Update stitched volume
        stitched[
            target_z_start:target_z_end,
            target_y_start:target_y_end,
            target_x_start:target_x_end
        ] = target_region

        # Update max label
        max_label = stitched.max()

    return max_label


def segment_volume_chunked(
    volume,
    segment_function,
    chunk_size: Tuple[int, int, int] = (64, 512, 512),
    overlap: Tuple[int, int, int] = (16, 128, 128),
    **segment_kwargs
) -> np.ndarray:
    """
    Segment a large 3D volume in chunks with incremental stitching.

    Memory-efficient: processes and stitches chunks one at a time instead of
    accumulating all segmented chunks in memory before stitching.

    Parameters
    ----------
    volume : np.ndarray or zarr.Array
        3D volume to segment (Z, Y, X). Can be numpy array or zarr array.
    segment_function : callable
        Segmentation function that takes (chunk, **kwargs) and returns labels
    chunk_size : tuple of int
        Size of each chunk (Z, Y, X). Default: (64, 512, 512)
    overlap : tuple of int
        Overlap between chunks (Z, Y, X). Default: (16, 128, 128)
    **segment_kwargs
        Additional arguments passed to segment_function

    Returns
    -------
    np.ndarray
        Segmented volume with stitched labels

    Examples
    --------
    >>> from vollsegzarr import StarDist3D
    >>> from vollsegzarr.chunked_segmentation import segment_volume_chunked
    >>> import zarr
    >>>
    >>> star_model = StarDist3D.local_from_pretrained("model")
    >>>
    >>> def seg_func(chunk, **kwargs):
    ...     labels, _ = star_model.predict_instances(chunk, **kwargs)
    ...     return labels
    >>>
    >>> # Can use zarr array (lazy loading)
    >>> z_array = zarr.open('huge_image.zarr', mode='r')
    >>> channel_view = z_array[:, 0, :, :]  # Lazy view, no memory load
    >>>
    >>> labels = segment_volume_chunked(
    ...     channel_view,
    ...     seg_func,
    ...     chunk_size=(50, 2048, 2048),
    ...     overlap=(10, 256, 256),
    ...     axes='ZYX',
    ...     n_tiles=(1, 2, 2)
    ... )
    """
    volume_shape = volume.shape
    print(f"Segmenting volume of shape {volume_shape} in chunks...")
    print(f"  Chunk size: {chunk_size}")
    print(f"  Overlap: {overlap}")

    # Generate chunks
    chunks = chunk_volume_3d(volume_shape, chunk_size, overlap)
    print(f"  Total chunks: {len(chunks)}")

    # Initialize output volume
    # Use uint32 for large datasets that might have >65k objects
    stitched_labels = np.zeros(volume_shape, dtype=np.uint32)
    max_label = 0

    print(f"  Output volume memory: {stitched_labels.nbytes / 1e9:.2f} GB")
    print(f"  Peak memory per chunk: ~{stitched_labels.nbytes / 1e9 + (chunk_size[0]*chunk_size[1]*chunk_size[2]*4)/1e9:.2f} GB")

    # Process and stitch each chunk incrementally
    for i, (z_slice, y_slice, x_slice) in enumerate(tqdm(chunks, desc="Segmenting & stitching chunks")):
        # Extract chunk (this loads only this chunk into memory)
        chunk = np.array(volume[z_slice, y_slice, x_slice])

        # Convert to float16 if needed (for segmentation models)
        if chunk.dtype != np.float16 and chunk.dtype != np.float32:
            chunk = chunk.astype(np.float16)

        print(f"\n  Chunk {i+1}/{len(chunks)}: shape {chunk.shape}, memory: {chunk.nbytes / 1e6:.1f} MB")

        # Segment chunk
        try:
            chunk_labels = segment_function(chunk, **segment_kwargs)

            print(f"    Segmented {chunk_labels.max()} objects")

            # Stitch immediately (incremental stitching)
            max_label = stitch_single_chunk(
                stitched_labels,
                chunk_labels,
                z_slice, y_slice, x_slice,
                overlap,
                max_label
            )

            print(f"    Stitched into volume, total objects so far: {max_label}")

        except Exception as e:
            print(f"    Error segmenting chunk {i+1}: {e}")
            # Skip failed chunk (don't add empty labels)

        # Clean up immediately
        del chunk
        if 'chunk_labels' in locals():
            del chunk_labels
        gc.collect()

    print(f"\nSegmentation complete! Total objects: {stitched_labels.max()}")

    return stitched_labels


def segment_with_vollseg_chunked(
    volume: np.ndarray,
    star_model,
    unet_model=None,
    chunk_size: Tuple[int, int, int] = (64, 512, 512),
    overlap: Tuple[int, int, int] = (16, 128, 128),
    axes: str = 'ZYX',
    n_tiles: Tuple[int, int, int] = (1, 1, 1),
    min_size: int = 100,
    max_size: int = 10000000,
    prob_thresh: float = 0.5,
    nms_thresh: float = 0.3
) -> np.ndarray:
    """
    Segment a large volume using VollSeg in chunks.

    Parameters
    ----------
    volume : np.ndarray
        3D volume to segment (Z, Y, X)
    star_model : StarDist3D
        StarDist model
    unet_model : UNET, optional
        UNET model (if using hybrid VollSeg)
    chunk_size : tuple of int
        Chunk size (Z, Y, X). Default: (64, 512, 512)
    overlap : tuple of int
        Overlap (Z, Y, X). Default: (16, 128, 128)
    axes : str
        Axes specification. Default: 'ZYX'
    n_tiles : tuple of int
        Tiling for each chunk. Default: (1, 1, 1)
    min_size : int
        Minimum object size
    max_size : int
        Maximum object size
    prob_thresh : float
        Probability threshold
    nms_thresh : float
        NMS threshold

    Returns
    -------
    np.ndarray
        Segmented volume

    Examples
    --------
    >>> from vollsegzarr import StarDist3D
    >>> from vollsegzarr.chunked_segmentation import segment_with_vollseg_chunked
    >>>
    >>> star_model = StarDist3D.local_from_pretrained("model")
    >>> labels = segment_with_vollseg_chunked(
    ...     huge_volume,
    ...     star_model,
    ...     chunk_size=(50, 2048, 2048),
    ...     overlap=(10, 256, 256)
    ... )
    """
    

    def vollseg_segment(chunk, **kwargs):
        """Wrapper for VollSeg."""
        results = VollSeg(
            chunk,
            star_model=star_model,
            unet_model=unet_model,
            **kwargs
        )

        if results is not None and len(results) >= 2:
            return results[1]  # instance_labels
        else:
            return np.zeros(chunk.shape, dtype=np.uint16)

    return segment_volume_chunked(
        volume,
        vollseg_segment,
        chunk_size=chunk_size,
        overlap=overlap,
        axes=axes,
        n_tiles=n_tiles,
        min_size=min_size,
        max_size=max_size,
        prob_thresh=prob_thresh,
        nms_thresh=nms_thresh
    )
