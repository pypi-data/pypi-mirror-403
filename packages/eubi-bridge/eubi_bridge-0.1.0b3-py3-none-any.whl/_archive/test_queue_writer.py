#!/usr/bin/env python3
"""
Test script to compare old batch writer vs new queue-based writer.

This script:
1. Creates a synthetic 5D array (TCZYX)
2. Writes it using the new queue-based writer (via store_multiscale_async)
3. Validates NGFF compliance
4. Measures write time and memory usage
5. Optionally compares with old writer (if available)

Usage:
    python test_queue_writer.py [--size SIZE] [--verbose]
"""

import argparse
import asyncio
import os
import shutil
import time
from pathlib import Path

import dask.array as da
import numpy as np
import psutil
import zarr

# Add project to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from eubi_bridge.core.writers import store_multiscale_async
from eubi_bridge.ngff.multiscales import Pyramid
from eubi_bridge.utils.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def create_test_array(shape=(10, 3, 50, 512, 512), dtype=np.uint16, chunks='auto'):
    """Create a synthetic 5D test array with dask."""
    logger.info(f"Creating test array with shape={shape}, dtype={dtype}")
    
    # Create dask array filled with random data
    if chunks == 'auto':
        # Auto-chunk: 1 for T, all for C, reasonable chunks for spatial
        chunks = (1, shape[1], min(50, shape[2]), min(256, shape[3]), min(256, shape[4]))
    
    arr = da.random.randint(0, np.iinfo(dtype).max, size=shape, chunks=chunks, dtype=dtype)
    
    logger.info(f"Created array with chunks={arr.chunks}")
    return arr


def get_memory_usage():
    """Get current memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


def validate_ngff(output_path):
    """Validate that output is NGFF-compliant."""
    logger.info(f"Validating NGFF compliance for {output_path}")
    
    try:
        # Open as pyramid
        pyr = Pyramid(output_path)
        
        # Check multiscales metadata
        assert pyr.meta.metadata is not None, "No metadata found"
        assert 'multiscales' in pyr.meta.metadata, "No multiscales metadata"
        
        # Check base layer exists
        assert '0' in pyr.meta.resolution_paths, "Base layer '0' not found in resolution paths"
        
        # Get base array using dask_arrays property
        base = pyr.dask_arrays['0']
        logger.info(f"Base layer shape: {base.shape}, chunks: {base.chunks}")
        
        # Check data integrity (read a slice)
        test_slice = tuple(slice(0, min(2, s)) for s in base.shape)
        data = base[test_slice].compute() if hasattr(base[test_slice], 'compute') else base[test_slice]
        assert data is not None, "Failed to read data"
        
        logger.info(f"✓ NGFF validation passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ NGFF validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_queue_writer(output_path, arr, axes, scales, units, **kwargs):
    """Test the new queue-based writer."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing NEW QUEUE-BASED WRITER")
    logger.info(f"{'='*60}")
    
    # Clean output
    if os.path.exists(output_path):
        shutil.rmtree(output_path)
    
    mem_before = get_memory_usage()
    start_time = time.time()
    
    try:
        # Write with new queue-based writer
        ts_store = await store_multiscale_async(
            arr=arr,
            output_path=output_path,
            axes=axes,
            scales=[scales],  # List of scales for each resolution
            units=units,
            zarr_format=2,
            auto_chunk=True,
            target_chunk_mb=128,
            overwrite=True,
            channel_meta='auto',
            # New queue-based parameters
            num_readers=8,
            max_workers=4,
            region_size_mb=8.0,
            queue_size=None,  # Auto
            gc_interval=15.0,
            **kwargs
        )
        
        elapsed = time.time() - start_time
        mem_after = get_memory_usage()
        mem_peak = mem_after - mem_before
        
        logger.info(f"✓ Write completed successfully")
        logger.info(f"  Time: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")
        logger.info(f"  Memory delta: {mem_peak:.1f} MB")
        logger.info(f"  Output: {output_path}")
        
        # Validate
        valid = validate_ngff(output_path)
        
        return {
            'success': True,
            'elapsed': elapsed,
            'memory_delta': mem_peak,
            'valid': valid
        }
        
    except Exception as e:
        logger.error(f"✗ Write failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def compare_outputs(path1, path2):
    """Compare two zarr outputs for consistency."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Comparing outputs")
    logger.info(f"{'='*60}")
    
    try:
        pyr1 = Pyramid(path1)
        pyr2 = Pyramid(path2)
        
        # Compare shapes
        shape1 = pyr1.base_array.shape
        shape2 = pyr2.base_array.shape
        assert shape1 == shape2, f"Shape mismatch: {shape1} vs {shape2}"
        logger.info(f"✓ Shapes match: {shape1}")
        
        # Compare metadata
        assert pyr1.meta.axis_order == pyr2.meta.axis_order, "Axis order mismatch"
        logger.info(f"✓ Axes match: {pyr1.meta.axis_order}")
        
        # Compare data (sample random slices)
        n_samples = 5
        for _ in range(n_samples):
            # Random slice
            slices = tuple(
                slice(np.random.randint(0, max(1, s//2)), np.random.randint(max(1, s//2), s))
                for s in shape1
            )
            data1 = pyr1.base_array[slices]
            data2 = pyr2.base_array[slices]
            
            if hasattr(data1, 'compute'):
                data1 = data1.compute()
            if hasattr(data2, 'compute'):
                data2 = data2.compute()
            
            assert np.array_equal(data1, data2), f"Data mismatch at {slices}"
        
        logger.info(f"✓ Data matches (sampled {n_samples} regions)")
        return True
        
    except Exception as e:
        logger.error(f"✗ Comparison failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    parser = argparse.ArgumentParser(description="Test queue-based writer")
    parser.add_argument('--size', type=str, default='small', 
                       choices=['tiny', 'small', 'medium', 'large'],
                       help='Test array size')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--output-dir', type=str, default='./test_output',
                       help='Output directory for test files')
    
    args = parser.parse_args()
    
    # Define test sizes
    sizes = {
        'tiny': (5, 2, 20, 256, 256),      # ~80 MB
        'small': (10, 3, 50, 512, 512),    # ~1.5 GB
        'medium': (20, 4, 100, 1024, 1024), # ~16 GB
        'large': (50, 5, 200, 2048, 2048),  # ~400 GB
    }
    
    shape = sizes[args.size]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    logger.info(f"\n{'#'*60}")
    logger.info(f"Queue-Based Writer Test")
    logger.info(f"{'#'*60}")
    logger.info(f"Array size: {args.size} → shape={shape}")
    logger.info(f"Expected memory: ~{np.prod(shape) * 2 / (1024**3):.2f} GB")
    
    # Create test array
    arr = create_test_array(shape=shape, dtype=np.uint16)
    
    # Test parameters
    axes = ['t', 'c', 'z', 'y', 'x']
    scales = [1.0, 1.0, 0.5, 0.108, 0.108]  # seconds, N/A, microns
    units = ['second', None, 'micrometer', 'micrometer', 'micrometer']
    
    # Test new queue-based writer
    new_output = output_dir / 'output_queue_writer.zarr'
    result_new = await test_queue_writer(
        output_path=str(new_output),
        arr=arr,
        axes=axes,
        scales=scales,
        units=units,
        verbose=args.verbose
    )
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info(f"TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    if result_new['success']:
        logger.info(f"✓ Queue-based writer: {result_new['elapsed']:.2f}s, "
                   f"{result_new['memory_delta']:.1f} MB, "
                   f"valid={result_new['valid']}")
    else:
        logger.error(f"✗ Queue-based writer failed: {result_new.get('error', 'Unknown')}")
    
    logger.info(f"\nOutput files:")
    logger.info(f"  Queue-based: {new_output}")
    
    # Cleanup option
    if input("\nDelete test outputs? (y/n): ").lower() == 'y':
        if new_output.exists():
            shutil.rmtree(new_output)
        logger.info("✓ Cleaned up test outputs")


if __name__ == '__main__':
    asyncio.run(main())
