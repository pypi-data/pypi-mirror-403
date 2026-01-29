"""
Utilities for creating test fixtures (sample images).

This module provides functions to generate minimal test images in various formats
for conversion testing without requiring large external files.
"""

import tempfile
from pathlib import Path
from typing import Tuple, Union

import numpy as np
import tifffile
import zarr


def create_sample_tiff(output_path: Union[str, Path],
                       shape: Tuple[int, ...] = (10, 256, 256),
                       dtype: np.dtype = np.uint16) -> Path:
    """
    Create a minimal sample TIFF file for testing.
    
    Parameters
    ----------
    output_path : Union[str, Path]
        Path where the TIFF file will be saved.
    shape : Tuple[int, ...]
        Shape of the image array. Default (10, 256, 256) = (Z, Y, X).
    dtype : np.dtype
        Data type of the image. Default is uint16.
    
    Returns
    -------
    Path
        Path to the created TIFF file.
    """
    output_path = Path(output_path)
    
    # Create a small gradient test image
    z, y, x = shape
    data = np.zeros((z, y, x), dtype=dtype)
    
    # Add some test patterns
    for i in range(z):
        # Gradient along X
        data[i, :, :] = np.linspace(0, np.iinfo(dtype).max // 2, x)[np.newaxis, :] + i * 100
    
    # Write as TIFF
    tifffile.imwrite(output_path, data, compression='lz4')
    return output_path


def create_sample_ometiff(output_path: Union[str, Path],
                          shape: Tuple[int, ...] = (2, 10, 256, 256),
                          dtype: np.dtype = np.uint16) -> Path:
    """
    Create a minimal OME-TIFF file for testing.
    
    Parameters
    ----------
    output_path : Union[str, Path]
        Path where the OME-TIFF file will be saved.
    shape : Tuple[int, ...]
        Shape of the image array. Default (2, 10, 256, 256) = (C, Z, Y, X).
    dtype : np.dtype
        Data type of the image. Default is uint16.
    
    Returns
    -------
    Path
        Path to the created OME-TIFF file.
    """
    output_path = Path(output_path)
    
    c, z, y, x = shape
    data = np.zeros((c, z, y, x), dtype=dtype)
    
    # Create different patterns per channel
    for ch in range(c):
        for i in range(z):
            data[ch, i, :, :] = np.linspace(0, np.iinfo(dtype).max // 2, x)[np.newaxis, :] + (ch * 50 + i * 100)
    
    # Reshape to (Z, Y, X) for tifffile (channels as separate images)
    # In OME-TIFF, this will be interpreted as multi-scene with proper metadata
    reshaped = data.reshape(c * z, y, x)
    
    tifffile.imwrite(
        output_path,
        reshaped,
        compression='lz4',
        metadata={'axes': 'CZX'}
    )
    return output_path


def create_sample_zarr(output_path: Union[str, Path],
                       shape: Tuple[int, ...] = (10, 256, 256),
                       dtype: np.dtype = np.uint16,
                       chunks: bool = True) -> Path:
    """
    Create a minimal OME-Zarr/NGFF pyramid for testing.
    
    Parameters
    ----------
    output_path : Union[str, Path]
        Path where the Zarr directory will be created.
    shape : Tuple[int, ...]
        Shape of the base array. Default (10, 256, 256) = (Z, Y, X).
    dtype : np.dtype
        Data type of the image. Default is uint16.
    chunks : bool
        Whether to use chunked storage. Default is True.
    
    Returns
    -------
    Path
        Path to the created Zarr directory.
    """
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    
    z, y, x = shape
    data = np.zeros((z, y, x), dtype=dtype)
    
    # Add test pattern
    for i in range(z):
        data[i, :, :] = np.linspace(0, np.iinfo(dtype).max // 2, x)[np.newaxis, :] + i * 100
    
    # Create Zarr group with NGFF metadata
    store = zarr.open_group(str(output_path), mode='w')
    
    # Add base resolution
    chunk_size = (1, 128, 128) if chunks else None
    arr = store.create_array(
        '0',
        data=data,
        chunks=chunk_size,
        compressor=zarr.Blosc(cname='zstd', clevel=5)
    )
    
    # Add NGFF metadata
    store.attrs['multiscales'] = [{
        'version': '0.4',
        'name': 'Test Image',
        'axes': [
            {'name': 'z', 'type': 'space'},
            {'name': 'y', 'type': 'space'},
            {'name': 'x', 'type': 'space'}
        ],
        'datasets': [
            {
                'path': '0',
                'coordinateTransformations': [
                    {'type': 'scale', 'scale': [1.0, 1.0, 1.0]}
                ]
            }
        ]
    }]
    
    store.attrs['omero'] = {
        'channels': [
            {
                'color': 'FF0000',
                'coefficient': 1,
                'active': True,
                'label': 'Channel 0',
                'window': {'min': 0, 'max': int(np.iinfo(dtype).max), 'start': 0, 'end': int(np.iinfo(dtype).max)},
                'family': 'linear',
                'inverted': False
            }
        ],
        'rdefs': {
            'defaultZ': 0,
            'defaultT': 0,
            'model': 'greyscale'
        }
    }
    
    return output_path


def generate_test_fixtures(fixture_dir: Union[str, Path]) -> dict:
    """
    Generate all test fixtures in the specified directory.
    
    Parameters
    ----------
    fixture_dir : Union[str, Path]
        Directory where fixtures will be created.
    
    Returns
    -------
    dict
        Dictionary mapping fixture names to their paths.
    """
    fixture_dir = Path(fixture_dir)
    fixture_dir.mkdir(parents=True, exist_ok=True)
    
    fixtures = {}
    
    # Create TIFF variants
    fixtures['tiff_2d'] = create_sample_tiff(
        fixture_dir / "test_image_2d.tif",
        shape=(256, 256),
        dtype=np.uint16
    )
    
    fixtures['tiff_3d'] = create_sample_tiff(
        fixture_dir / "test_image_3d.tif",
        shape=(10, 256, 256),
        dtype=np.uint16
    )
    
    fixtures['tiff_3d_8bit'] = create_sample_tiff(
        fixture_dir / "test_image_3d_8bit.tif",
        shape=(10, 256, 256),
        dtype=np.uint8
    )
    
    # Create OME-TIFF
    fixtures['ometiff'] = create_sample_ometiff(
        fixture_dir / "test_image_ometiff.ome.tif",
        shape=(2, 10, 256, 256),
        dtype=np.uint16
    )
    
    # Create Zarr NGFF
    fixtures['zarr_ngff'] = create_sample_zarr(
        fixture_dir / "test_image_ngff.zarr",
        shape=(10, 256, 256),
        dtype=np.uint16
    )
    
    return fixtures


if __name__ == "__main__":
    # Generate test fixtures in /tmp
    with tempfile.TemporaryDirectory() as tmpdir:
        fixtures = generate_test_fixtures(tmpdir)
        print(f"Generated test fixtures in {tmpdir}:")
        for name, path in fixtures.items():
            print(f"  {name}: {path}")
            if path.exists():
                print(f"    ✓ OK")
