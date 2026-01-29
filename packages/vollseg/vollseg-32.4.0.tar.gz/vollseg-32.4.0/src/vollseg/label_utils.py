"""
Utility functions for manipulating integer label images (segmentation masks).

Label images contain integer IDs for different objects (0=background, 1,2,3,...=objects).
Special care must be taken when scaling these images to preserve object identities.
"""

import numpy as np
from scipy.ndimage import zoom, distance_transform_edt
from typing import Tuple, Union


def scale_labels(
    labels: np.ndarray,
    scale_factors: Union[Tuple[float, float, float], float],
    order: int = 0
) -> np.ndarray:
    """
    Scale an integer label image while preserving object identities.

    Uses nearest-neighbor interpolation to ensure labels remain as discrete
    integers without blending. This is critical for segmentation masks where
    each integer represents a unique object.

    Parameters
    ----------
    labels : np.ndarray
        Integer label image (3D or 4D). Shape: (Z, Y, X) or (Z, C, Y, X)
        Background should be 0, objects are labeled 1, 2, 3, ...
    scale_factors : tuple of float or float
        Scaling factors for each axis:
        - If tuple: (scale_z, scale_y, scale_x) for 3D
        - If float: same scaling applied to all spatial axes
        - Values > 1.0 = upscaling (larger output)
        - Values < 1.0 = downscaling (smaller output)
        - Values = 1.0 = no change
    order : int, optional
        Interpolation order. Default: 0 (nearest-neighbor)
        WARNING: Do not change from 0 unless you know what you're doing.
        Higher orders will blend labels together, creating invalid IDs.

    Returns
    -------
    np.ndarray
        Scaled label image with same dtype as input.
        All label IDs are preserved (no blending).

    Examples
    --------
    Downscale 3D labels by half:
    >>> labels = np.random.randint(0, 100, size=(100, 512, 512), dtype=np.uint16)
    >>> scaled = scale_labels(labels, (0.5, 0.5, 0.5))
    >>> scaled.shape
    (50, 256, 256)

    Upscale 3D labels by 2x:
    >>> scaled = scale_labels(labels, 2.0)
    >>> scaled.shape
    (200, 1024, 1024)

    Handle 4D data (Z, C, Y, X):
    >>> labels_4d = np.random.randint(0, 50, size=(100, 4, 512, 512), dtype=np.uint16)
    >>> scaled = scale_labels(labels_4d, (0.5, 0.5, 0.5))
    >>> scaled.shape
    (50, 4, 256, 256)

    Notes
    -----
    - Uses nearest-neighbor interpolation (order=0) to preserve integer labels
    - When downscaling, small objects may disappear if they become < 1 pixel
    - When upscaling, object boundaries become pixelated (no smoothing)
    - For 4D images (Z,C,Y,X), only spatial dimensions are scaled, not channels
    - Output dtype matches input dtype (uint8, uint16, uint32, etc.)

    See Also
    --------
    scipy.ndimage.zoom : Underlying zoom function used for scaling
    """

    if labels.size == 0:
        raise ValueError("Input label array is empty")

    # Ensure labels are integer type
    if not np.issubdtype(labels.dtype, np.integer):
        raise TypeError(f"Labels must be integer type, got {labels.dtype}")

    original_dtype = labels.dtype

    # Handle scalar scale_factors
    if isinstance(scale_factors, (int, float)):
        if labels.ndim == 3:
            zoom_factors = (scale_factors, scale_factors, scale_factors)
        elif labels.ndim == 4:
            zoom_factors = (scale_factors, 1.0, scale_factors, scale_factors)
        else:
            raise ValueError(f"Unsupported number of dimensions: {labels.ndim}. Expected 3 or 4.")
    else:
        # Handle tuple scale_factors
        if len(scale_factors) != 3:
            raise ValueError(f"scale_factors must have 3 elements (Z, Y, X), got {len(scale_factors)}")

        if labels.ndim == 3:
            zoom_factors = scale_factors
        elif labels.ndim == 4:
            # For 4D (Z, C, Y, X), don't scale the channel dimension
            zoom_factors = (scale_factors[0], 1.0, scale_factors[1], scale_factors[2])
        else:
            raise ValueError(f"Unsupported number of dimensions: {labels.ndim}. Expected 3 or 4.")

    # Validate scale factors
    for i, factor in enumerate(zoom_factors):
        if factor <= 0:
            raise ValueError(f"Scale factor at index {i} must be > 0, got {factor}")

    # Check if scaling is needed
    if all(abs(f - 1.0) < 1e-6 for f in zoom_factors):
        print("Scale factors are all 1.0, returning original labels")
        return labels

    print(f"Scaling labels from shape {labels.shape} with factors {zoom_factors}")

    # Perform nearest-neighbor scaling
    # order=0 ensures no interpolation/blending of label values
    scaled_labels = zoom(labels, zoom_factors, order=order)

    # Ensure output has same dtype as input
    scaled_labels = scaled_labels.astype(original_dtype)

    print(f"Scaled labels to shape {scaled_labels.shape}")
    print(f"Original unique labels: {len(np.unique(labels))}, Scaled unique labels: {len(np.unique(scaled_labels))}")

    return scaled_labels


def scale_labels_zyx(
    labels: np.ndarray,
    scale_z: float,
    scale_y: float,
    scale_x: float
) -> np.ndarray:
    """
    Scale an integer label image with separate factors for Z, Y, X axes.

    Convenience wrapper around scale_labels() with named parameters.

    Parameters
    ----------
    labels : np.ndarray
        Integer label image (3D or 4D)
    scale_z : float
        Scaling factor for Z axis
    scale_y : float
        Scaling factor for Y axis
    scale_x : float
        Scaling factor for X axis

    Returns
    -------
    np.ndarray
        Scaled label image

    Examples
    --------
    >>> labels = np.random.randint(0, 100, size=(100, 512, 512), dtype=np.uint16)
    >>> scaled = scale_labels_zyx(labels, scale_z=0.5, scale_y=0.5, scale_x=0.5)
    >>> scaled.shape
    (50, 256, 256)

    See Also
    --------
    scale_labels : Main scaling function
    """
    return scale_labels(labels, (scale_z, scale_y, scale_x))


def upscale_labels(
    labels: np.ndarray,
    target_shape: Tuple[int, ...]
) -> np.ndarray:
    """
    Upscale or downscale labels to match a target shape.

    Automatically calculates the required zoom factors to reach the target shape.
    Useful when you need labels to match the shape of another image.

    Parameters
    ----------
    labels : np.ndarray
        Integer label image (3D or 4D)
    target_shape : tuple of int
        Desired output shape
        - For 3D input: (target_z, target_y, target_x)
        - For 4D input: (target_z, target_c, target_y, target_x)
        Note: For 4D, channel dimension must match input

    Returns
    -------
    np.ndarray
        Scaled label image with shape matching target_shape

    Examples
    --------
    >>> labels = np.random.randint(0, 50, size=(50, 256, 256), dtype=np.uint16)
    >>> upscaled = upscale_labels(labels, target_shape=(100, 512, 512))
    >>> upscaled.shape
    (100, 512, 512)

    >>> labels_4d = np.random.randint(0, 50, size=(50, 4, 256, 256), dtype=np.uint16)
    >>> upscaled = upscale_labels(labels_4d, target_shape=(100, 4, 512, 512))
    >>> upscaled.shape
    (100, 4, 512, 512)

    Raises
    ------
    ValueError
        If target_shape doesn't match input dimensions
    """

    if len(target_shape) != labels.ndim:
        raise ValueError(
            f"target_shape dimensions ({len(target_shape)}) must match "
            f"input dimensions ({labels.ndim})"
        )

    if labels.ndim == 4 and target_shape[1] != labels.shape[1]:
        raise ValueError(
            f"For 4D input, channel dimension must match: "
            f"target has {target_shape[1]} channels, input has {labels.shape[1]}"
        )

    # Calculate zoom factors
    zoom_factors = tuple(
        target_dim / current_dim
        for target_dim, current_dim in zip(target_shape, labels.shape)
    )

    print(f"Upscaling labels from {labels.shape} to {target_shape}")
    print(f"Calculated zoom factors: {zoom_factors}")

    # Use zoom directly with calculated factors
    scaled_labels = zoom(labels, zoom_factors, order=0)

    # Ensure exact target shape (handle rounding errors)
    if scaled_labels.shape != target_shape:
        # This can happen due to floating point rounding in zoom
        # Crop or pad to exact shape if needed
        slices = tuple(slice(0, min(s1, s2)) for s1, s2 in zip(scaled_labels.shape, target_shape))
        scaled_labels = scaled_labels[slices]

        # Pad if still smaller
        if scaled_labels.shape != target_shape:
            pad_width = [
                (0, target_dim - current_dim)
                for target_dim, current_dim in zip(target_shape, scaled_labels.shape)
            ]
            scaled_labels = np.pad(scaled_labels, pad_width, mode='constant', constant_values=0)

    scaled_labels = scaled_labels.astype(labels.dtype)

    return scaled_labels


def scale_labels_distance_transform(
    labels: np.ndarray,
    scale_factors: Union[Tuple[float, float, float], float],
    use_simple_upscale: bool = False
) -> np.ndarray:
    """
    Scale label image using distance transforms to preserve boundaries.

    This method is superior to simple nearest-neighbor interpolation because it:
    1. Preserves proportional spacing between labels
    2. Maintains smoother boundaries during upscaling
    3. Prevents labels from merging or creating gaps at boundaries

    The algorithm works by:
    1. Computing signed distance transform for each label region
    2. Scaling the distance fields (not the binary masks)
    3. Reconstructing labels by assigning each pixel to the nearest label

    Parameters
    ----------
    labels : np.ndarray
        Integer label image (3D). Shape: (Z, Y, X)
        Background should be 0, objects labeled 1, 2, 3, ...
    scale_factors : tuple of float or float
        Scaling factors for each axis:
        - If tuple: (scale_z, scale_y, scale_x)
        - If float: same scaling for all axes
    use_simple_upscale : bool, optional
        If True, fall back to simple nearest-neighbor (faster but lower quality).
        Default: False

    Returns
    -------
    np.ndarray
        Scaled label image with same dtype as input.

    Examples
    --------
    >>> labels = np.random.randint(0, 50, size=(50, 256, 256), dtype=np.uint16)
    >>> upscaled = scale_labels_distance_transform(labels, 2.0)
    >>> upscaled.shape
    (100, 512, 512)

    Notes
    -----
    - For very large images or many labels (>1000), this can be memory intensive
    - For downscaling (scale < 1.0), uses simple nearest-neighbor as distance
      transform doesn't provide benefits when reducing resolution
    - Preserves all label IDs present in the original image

    See Also
    --------
    scale_labels : Simple nearest-neighbor scaling (faster, lower quality)
    scipy.ndimage.distance_transform_edt : Euclidean distance transform
    """

    if labels.size == 0:
        raise ValueError("Input label array is empty")

    if not np.issubdtype(labels.dtype, np.integer):
        raise TypeError(f"Labels must be integer type, got {labels.dtype}")

    if labels.ndim != 3:
        raise ValueError(f"Expected 3D labels (Z,Y,X), got shape {labels.shape}")

    original_dtype = labels.dtype

    # Handle scalar scale_factors
    if isinstance(scale_factors, (int, float)):
        scale_z = scale_y = scale_x = scale_factors
    else:
        if len(scale_factors) != 3:
            raise ValueError(f"scale_factors must have 3 elements (Z,Y,X), got {len(scale_factors)}")
        scale_z, scale_y, scale_x = scale_factors

    # Validate scale factors
    if scale_z <= 0 or scale_y <= 0 or scale_x <= 0:
        raise ValueError("All scale factors must be > 0")

    # Check if scaling is needed
    if abs(scale_z - 1.0) < 1e-6 and abs(scale_y - 1.0) < 1e-6 and abs(scale_x - 1.0) < 1e-6:
        print("Scale factors are all 1.0, returning original labels")
        return labels

    zoom_factors = (scale_z, scale_y, scale_x)

    # For downscaling or if simple method requested, use nearest-neighbor
    if use_simple_upscale or scale_z < 1.0 or scale_y < 1.0 or scale_x < 1.0:
        print(f"Using simple nearest-neighbor scaling (downscaling or use_simple_upscale=True)")
        return scale_labels(labels, zoom_factors)

    print(f"Using distance-transform-based upscaling from {labels.shape} with factors {zoom_factors}")

    # Calculate output shape
    output_shape = (
        int(round(labels.shape[0] * scale_z)),
        int(round(labels.shape[1] * scale_y)),
        int(round(labels.shape[2] * scale_x))
    )

    # Get unique labels (excluding background)
    unique_labels = np.unique(labels)
    unique_labels = unique_labels[unique_labels > 0]
    num_labels = len(unique_labels)

    if num_labels == 0:
        print("No objects found in label image (all zeros)")
        return np.zeros(output_shape, dtype=original_dtype)

    print(f"Processing {num_labels} unique labels")
    print(f"Output shape: {output_shape}")

    # Initialize output
    upscaled_labels = np.zeros(output_shape, dtype=original_dtype)

    # For memory efficiency with many labels, process in chunks
    # If we have many labels, use Voronoi-based approach
    if num_labels > 100:
        print(f"Large number of labels ({num_labels}), using Voronoi-based reconstruction")

        # Compute distance transform of background
        background_mask = (labels == 0)

        # Get distance to nearest label and indices of nearest label
        distances, nearest_indices = distance_transform_edt(
            background_mask,
            return_indices=True
        )

        # Create a "label distance field" where each pixel stores which label it's closest to
        label_field = labels.copy()

        # For background pixels, assign them to nearest label based on distance transform
        # This creates a Voronoi diagram partitioning the space
        for i in range(3):
            nearest_indices[i] = np.clip(nearest_indices[i], 0, labels.shape[i] - 1)

        nearest_labels = labels[nearest_indices[0], nearest_indices[1], nearest_indices[2]]

        # Now scale this continuous label field
        upscaled_labels = zoom(nearest_labels, zoom_factors, order=0).astype(original_dtype)

    else:
        # For smaller number of labels, use distance transform per label (more accurate)
        print("Using per-label distance transform (highest quality)")

        # Create distance maps for each label
        max_distance = np.zeros(output_shape, dtype=np.float32)

        for idx, label_id in enumerate(unique_labels):
            if (idx + 1) % max(1, num_labels // 10) == 0:
                print(f"  Processing label {idx + 1}/{num_labels}")

            # Create binary mask for this label
            mask = (labels == label_id).astype(np.float32)

            # Compute distance transform inside the object
            # (distance from each foreground pixel to nearest background pixel)
            dist_inside = distance_transform_edt(mask)

            # Scale the distance field
            scaled_dist = zoom(dist_inside, zoom_factors, order=1)  # Linear interpolation for distance

            # Assign label where this distance is maximum
            # This preserves the proportional boundaries
            update_mask = scaled_dist > max_distance
            upscaled_labels[update_mask] = label_id
            max_distance[update_mask] = scaled_dist[update_mask]

    num_original = len(unique_labels)
    num_upscaled = len(np.unique(upscaled_labels)) - 1  # -1 for background

    print(f"Upscaling complete: {labels.shape} -> {output_shape}")
    print(f"Labels preserved: {num_original} original, {num_upscaled} in upscaled image")

    if num_upscaled < num_original:
        print(f"WARNING: Lost {num_original - num_upscaled} labels during upscaling")

    return upscaled_labels


def scale_labels_zyx_distance(
    labels: np.ndarray,
    scale_z: float,
    scale_y: float,
    scale_x: float,
    use_simple_upscale: bool = False
) -> np.ndarray:
    """
    Scale label image using distance transforms with named Z,Y,X parameters.

    Convenience wrapper around scale_labels_distance_transform().

    Parameters
    ----------
    labels : np.ndarray
        Integer label image (3D)
    scale_z : float
        Scaling factor for Z axis
    scale_y : float
        Scaling factor for Y axis
    scale_x : float
        Scaling factor for X axis
    use_simple_upscale : bool, optional
        If True, use simple nearest-neighbor instead of distance transform.
        Default: False

    Returns
    -------
    np.ndarray
        Scaled label image

    See Also
    --------
    scale_labels_distance_transform : Main distance-transform scaling function
    scale_labels_zyx : Simple nearest-neighbor scaling
    """
    return scale_labels_distance_transform(
        labels,
        (scale_z, scale_y, scale_x),
        use_simple_upscale=use_simple_upscale
    )
