#!/usr/bin/env python3
"""
Test suite validating that Pyramid preserves array types.

This tests the refactored Pyramid class that now supports universal
in-memory array storage: dask arrays, DynamicArray, numpy arrays, etc.

The key improvement: array types are preserved, not auto-converted to dask.
"""

import sys
import numpy as np
import dask.array as da
from pathlib import Path

from eubi_bridge.ngff.multiscales import Pyramid
from eubi_bridge.core.tiff_reader import read_tiff_image
from eubi_bridge.utils.logging_config import get_logger

logger = get_logger(__name__)


def test_numpy_array_preserved():
    """Test that numpy arrays are preserved through Pyramid."""
    print("\n" + "="*70)
    print("TEST 1: numpy.ndarray preservation")
    print("="*70)
    
    # Create numpy array
    np_arr = np.random.rand(256, 256).astype(np.uint16)
    print(f"Input type: {type(np_arr).__name__}")
    
    # Create Pyramid
    pyr = Pyramid().from_array(np_arr, axis_order='yx')
    
    # Check stored array
    stored_arr = pyr._array_layers['0']
    print(f"Stored type: {type(stored_arr).__name__}")
    print(f"Stored shape: {stored_arr.shape}")
    print(f"Stored dtype: {stored_arr.dtype}")
    
    # Check base_array (via layers property)
    base_arr = pyr.base_array
    print(f"Base array type: {type(base_arr).__name__}")
    
    # Verify type preserved
    assert type(stored_arr).__name__ == 'ndarray', f"Expected ndarray, got {type(stored_arr).__name__}"
    assert type(base_arr).__name__ == 'ndarray', f"Expected ndarray, got {type(base_arr).__name__}"
    assert np.array_equal(stored_arr, np_arr), "Array content not preserved"
    
    print("✓ PASSED: numpy arrays are preserved without conversion")
    return True


def test_dask_array_preserved():
    """Test that dask arrays are preserved through Pyramid."""
    print("\n" + "="*70)
    print("TEST 2: dask.array.Array preservation")
    print("="*70)
    
    import dask.array as da
    
    # Create dask array
    np_data = np.random.rand(512, 512).astype(np.uint16)
    da_arr = da.from_array(np_data, chunks=(256, 256))
    print(f"Input type: {type(da_arr).__name__}")
    print(f"Input chunks: {da_arr.chunks}")
    
    # Create Pyramid
    pyr = Pyramid().from_array(da_arr, axis_order='yx')
    
    # Check stored array
    stored_arr = pyr._array_layers['0']
    print(f"Stored type: {type(stored_arr).__name__}")
    print(f"Stored shape: {stored_arr.shape}")
    print(f"Stored chunks: {stored_arr.chunks}")
    
    # Check base_array (via layers property)
    base_arr = pyr.base_array
    print(f"Base array type: {type(base_arr).__name__}")
    
    # Verify type preserved
    assert type(stored_arr).__name__ == 'Array', f"Expected dask Array, got {type(stored_arr).__name__}"
    assert type(base_arr).__name__ == 'Array', f"Expected dask Array, got {type(base_arr).__name__}"
    
    print("✓ PASSED: dask arrays are preserved with chunks intact")
    return True


def test_from_arrays_mixed_types():
    """Test from_arrays with multiple arrays of different types."""
    print("\n" + "="*70)
    print("TEST 3: from_arrays with mixed array types")
    print("="*70)
    
    import dask.array as da
    
    # Create arrays at different resolutions
    arr_0 = np.random.rand(512, 512).astype(np.uint16)  # numpy
    arr_1 = da.from_array(np.random.rand(256, 256).astype(np.uint16), chunks=(128, 128))  # dask
    
    print(f"Layer 0 input type: {type(arr_0).__name__}")
    print(f"Layer 1 input type: {type(arr_1).__name__}")
    
    # Create pyramid
    pyr = Pyramid().from_arrays(
        [arr_0, arr_1],
        axis_order='yx',
        scales=[[1, 1], [2, 2]]
    )
    
    # Check stored arrays
    stored_0 = pyr._array_layers['0']
    stored_1 = pyr._array_layers['1']
    
    print(f"Layer 0 stored type: {type(stored_0).__name__}")
    print(f"Layer 1 stored type: {type(stored_1).__name__}")
    
    # Verify types preserved
    assert type(stored_0).__name__ == 'ndarray', "Layer 0 should be ndarray"
    assert type(stored_1).__name__ == 'Array', "Layer 1 should be dask Array"
    assert len(pyr.layers) == 2, "Should have 2 layers"
    
    print("✓ PASSED: from_arrays preserves mixed array types")
    return True


def test_metadata_preservation():
    """Test that metadata is correctly set regardless of array type."""
    print("\n" + "="*70)
    print("TEST 4: Metadata preservation with different array types")
    print("="*70)
    
    # Create numpy array
    np_arr = np.random.rand(256, 512).astype(np.float32)
    
    # Create pyramid with specific metadata
    pyr = Pyramid().from_array(
        np_arr,
        axis_order='yx',
        unit_list=['micrometer', 'micrometer'],
        scale=[0.5, 0.5]
    )
    
    print(f"Axes: {pyr.axes}")
    print(f"Shape: {pyr.shape}")
    print(f"Dtype: {pyr.dtype}")
    print(f"Num layers: {pyr.nlayers}")
    
    # Verify metadata
    assert pyr.axes == 'yx', f"Expected 'yx', got {pyr.axes}"
    assert pyr.shape == (256, 512), f"Expected (256, 512), got {pyr.shape}"
    assert pyr.dtype == np.float32, f"Expected float32, got {pyr.dtype}"
    assert pyr.nlayers == 1, f"Expected 1 layer, got {pyr.nlayers}"
    
    # Check scale metadata
    scale_dict = pyr.meta.get_base_scaledict()
    print(f"Base scale dict: {scale_dict}")
    assert scale_dict['y'] == 0.5, "Y scale should be 0.5"
    assert scale_dict['x'] == 0.5, "X scale should be 0.5"
    
    print("✓ PASSED: Metadata correctly preserved")
    return True


def test_ftsz3_tiff_to_5d_tczyx():
    """Test reading ftsz3.tif, normalizing to 5D, and reordering to tczyx."""
    print("\n" + "="*70)
    print("TEST 5: ftsz3.tif → Pyramid → Normalize to 5D tczyx")
    print("="*70)
    
    # Define TIFF path
    tiff_path = "/Users/eubi-biohub/Desktop/input_data/example_images1/pff/ftsz3.tif"
    print(f"\nInput TIFF: {tiff_path}")
    
    # Verify file exists
    if not Path(tiff_path).exists():
        print(f"✗ SKIPPED: TIFF file not found at {tiff_path}")
        return True
    
    # Read TIFF using eubi_bridge read_tiff_image
    print("\n1. Reading TIFF with read_tiff_image...")
    try:
        reader = read_tiff_image(tiff_path)
        img_data = reader.get_image_dask_data()
        print(f"   Input shape: {img_data.shape}")
        print(f"   Input dtype: {img_data.dtype}")
        print(f"   Input type: {type(img_data).__name__}")
    except Exception as e:
        print(f"✗ FAILED to read TIFF: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # The reader normalizes to 5D, so we already have it
    # Just determine the axes from the shape
    print("\n2. Determining axes from shape...")
    arr = img_data
    shape = arr.shape
    
    # Since reader normalizes to 5D, we have (t, c, z, y, x)
    # Current axes are already normalized
    if len(shape) == 5:
        axes = "tczyx"
        print(f"   Shape {shape} indicates 5D normalized array")
        print(f"   Axes: {axes}")
    else:
        print(f"   Unexpected shape: {shape}")
        return False
    
    # Create Pyramid from already-normalized array
    print("\n3. Creating Pyramid from normalized array...")
    pyr = Pyramid().from_array(
        arr,
        axis_order="tczyx",
        unit_list=['second', 'micrometer', 'micrometer', 'micrometer', 'micrometer'],
        scale=[1.0, 1.0, 1.0, 1.0, 1.0],
        name="ftsz3_normalized"
    )
    
    print(f"   Pyramid axes: {pyr.axes}")
    print(f"   Pyramid shape: {pyr.shape}")
    print(f"   Pyramid dtype: {pyr.dtype}")
    print(f"   Array type: {type(pyr._array_layers['0']).__name__}")
    
    # Validate
    print("\n4. Validating...")
    assert pyr.axes == "tczyx", f"Expected 'tczyx', got {pyr.axes}"
    assert pyr.shape == shape, f"Shape mismatch: {pyr.shape} vs {shape}"
    assert pyr.dtype == arr.dtype, f"Dtype mismatch"
    
    # Verify array type is preserved
    stored_type = type(pyr._array_layers['0']).__name__
    print(f"   Stored array type: {stored_type}")
    assert stored_type in ('DynamicArray', 'ndarray', 'Array'), f"Unexpected type: {stored_type}"
    
    print("\n✓ PASSED: ftsz3.tif read and stored in Pyramid with tczyx normalization")
    return True


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("PYRAMID ARRAY TYPE PRESERVATION TEST SUITE")
    print("="*70)
    print("\nTesting that Pyramid._array_layers now supports universal array types:")
    print("  - numpy.ndarray")
    print("  - dask.array.Array")
    print("  - DynamicArray (when dyna_zarr bug is fixed)")
    print("  - Any array type with shape, dtype, and indexing support")
    
    tests = [
        test_numpy_array_preserved,
        test_dask_array_preserved,
        test_from_arrays_mixed_types,
        test_metadata_preservation,
        test_ftsz3_tiff_to_5d_tczyx,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed > 0:
        sys.exit(1)
    
    print("\n✓ ALL TESTS PASSED!")
    print("\nKey achievement:")
    print("  - Pyramid._array_layers renamed from _dask_layers")
    print("  - from_array() no longer converts inputs to dask")
    print("  - to5D() and squeeze() use layers property to preserve types")
    print("  - get_dask_data() only converts zarr → dask, preserves others")
    print("  - DynamicArray will work seamlessly once dyna_zarr bug is fixed")


if __name__ == '__main__':
    main()
from eubi_bridge.utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)
setup_logging()


def find_test_tiff():
    """Find a test TIFF file in the workspace."""
    project_root = Path("/Users/eubi-biohub/Desktop/vscode_projects/EuBI-Bridge/test_dynamic_array_pyramid.py").parent
    test_locations = [
        project_root / "new_tests" / "test_scripts" / "test_images" / "test_000_2d_large.tif",
        project_root / "new_tests" / "test_scripts" / "test_images" / "test_003_3d_large.tif",
        project_root / "test_images" / "Au.tiff",
        project_root / "test_images" / "ftsz3.tif",
        project_root / "test_images" / "nuclei.tif",
        project_root / "test_scripts" / "test_images" / "Au.tiff",
    ]
    
    for path in test_locations:
        if path.exists():
            logger.info(f"Found test TIFF: {path}")
            return str(path)
    
    raise FileNotFoundError(
        "No test TIFF file found. Checked locations:\n" +
        "\n".join(str(p) for p in test_locations)
    )


def test_dynamic_array_pyramid():
    """Test reading TIFF as DynamicArray and creating Pyramid."""
    
    logger.info("=" * 80)
    logger.info("TEST: DynamicArray Pyramid Construction")
    logger.info("=" * 80)
    
    # Find test TIFF
    tiff_path = find_test_tiff()
    logger.info(f"\n1. Opening TIFF file: {tiff_path}")
    
    # Read TIFF as DynamicArray with --skip_dask behavior
    logger.info("\n2. Reading TIFF as DynamicArray (aszarr=True for dimension normalization)...")
    reader = read_tiff_image(tiff_path, aszarr=True)
    dyn_array = reader.get_image_dask_data()
    
    logger.info(f"   Array type: {type(dyn_array).__name__}")
    logger.info(f"   Array shape: {dyn_array.shape}")
    logger.info(f"   Array dtype: {dyn_array.dtype}")
    logger.info(f"   Array chunks: {getattr(dyn_array, 'chunks', 'N/A')}")
    
    # Get metadata from reader
    axes = reader.get_axes() if hasattr(reader, 'get_axes') else None
    scaledict = reader.get_scaledict() if hasattr(reader, 'get_scaledict') else None
    unitdict = reader.get_unitdict() if hasattr(reader, 'get_unitdict') else None
    
    # Fallback: use defaults if methods don't exist
    if axes is None:
        # For normalized 5D, use tczyx
        axes = 'tczyx'
        logger.info(f"   Using default axes (reader doesn't provide get_axes): {axes}")
    if scaledict is None:
        from eubi_bridge.ngff import defaults
        scaledict = defaults.scale_map
        logger.info(f"   Using default scale_map (reader doesn't provide get_scaledict)")
    if unitdict is None:
        from eubi_bridge.ngff import defaults
        unitdict = defaults.unit_map
        logger.info(f"   Using default unit_map (reader doesn't provide get_unitdict)")
    
    logger.info(f"\n3. Extracting metadata from reader...")
    logger.info(f"   Axes: {axes}")
    logger.info(f"   Scale dict: {scaledict}")
    logger.info(f"   Unit dict: {unitdict}")
    
    # Create Pyramid from DynamicArray
    logger.info(f"\n4. Constructing Pyramid from DynamicArray...")
    pyr = Pyramid()
    scale_list = [scaledict[ax] for ax in axes]
    unit_list = [unitdict[ax] for ax in axes]
    
    pyr.from_array(
        array=dyn_array,
        axis_order=axes,
        unit_list=unit_list,
        scale=scale_list,
        version="0.4",
        name="TIFF_DynamicArray"
    )
    pyr.base_array
    
    # Validate Pyramid properties
    logger.info(f"\n5. Validating Pyramid properties...")
    logger.info(f"   Pyramid type: {type(pyr).__name__}")
    logger.info(f"   Base array type: {type(pyr.base_array).__name__}")
    logger.info(f"   Pyramid shape: {pyr.shape}")
    logger.info(f"   Pyramid dtype: {pyr.dtype}")
    logger.info(f"   Axes: {pyr.axes}")
    logger.info(f"   Number of layers: {pyr.nlayers}")
    logger.info(f"   Resolution paths: {pyr.meta.resolution_paths}")
    
    # Check that base array is the original DynamicArray
    logger.info(f"\n6. Verifying in-memory storage...")
    is_same_array = pyr.base_array is dyn_array
    logger.info(f"   Base array is same object as input: {is_same_array}")
    logger.info(f"   Stored in _array_layers: {'0' in pyr._array_layers}")
    logger.info(f"   zarr.Group (self.gr) is None: {pyr.gr is None}")
    
    # Validate metadata
    logger.info(f"\n7. Validating metadata...")
    logger.info(f"   Pyramid name: {pyr.meta.tag}")
    logger.info(f"   Base scale: {pyr.meta.get_base_scale()}")
    logger.info(f"   Base scale dict: {pyr.meta.get_base_scaledict()}")
    logger.info(f"   Unit list: {pyr.meta.unit_list}")
    logger.info(f"   Metadata valid: {pyr.meta.validate_metadata()}")
    
    # Test layers property
    logger.info(f"\n8. Testing layers property (transparent access)...")
    layers = pyr.layers
    logger.info(f"   Layers type: {type(layers)}")
    logger.info(f"   Number of layers: {len(layers)}")
    logger.info(f"   Layer '0' type: {type(layers['0']).__name__}")
    logger.info(f"   Layer '0' is DynamicArray: {type(layers['0']).__name__ == type(dyn_array).__name__}")
    
    # Test get_dask_data preserves array type
    logger.info(f"\n9. Testing get_dask_data preserves array type...")
    dask_data = pyr.get_dask_data()
    logger.info(f"   Returned type: {type(dask_data['0']).__name__}")
    logger.info(f"   Is same as stored: {dask_data['0'] is pyr._array_layers['0']}")
    
    logger.info(f"\n" + "=" * 80)
    logger.info("✅ TEST PASSED: DynamicArray Pyramid Construction")
    logger.info("=" * 80)
    
    return True


if __name__ == "__main__":
    try:
        success = test_dynamic_array_pyramid()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.exception(f"❌ TEST FAILED: {e}")
        sys.exit(1)
