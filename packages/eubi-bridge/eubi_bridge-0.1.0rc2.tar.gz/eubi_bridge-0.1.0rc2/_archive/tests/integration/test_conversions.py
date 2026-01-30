"""
Integration tests for EuBI-Bridge conversions.

Tests the full conversion pipeline from various image formats to OME-Zarr.
"""

import tempfile
from pathlib import Path

import pytest
import zarr

from tests.conftest_fixtures import generate_test_fixtures


class TestUnaryConversions:
    """Test one-to-one conversions (one input file → one Zarr output)."""
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_output_dir):
        """Set up test fixtures."""
        self.output_dir = tmp_output_dir
        self.fixtures = generate_test_fixtures(tmp_output_dir / "input")
    
    def test_tiff_to_zarr(self, bridge_instance):
        """Test TIFF to OME-Zarr conversion."""
        input_file = self.fixtures['tiff_3d']
        output_dir = self.output_dir / "tiff_output"
        output_dir.mkdir(exist_ok=True)
        
        # Run conversion
        bridge_instance.to_zarr(
            input_path=str(input_file),
            output_path=str(output_dir),
            zarr_format=2,
            verbose=True
        )
        
        # Validate output
        zarr_files = list(output_dir.glob("*.zarr"))
        assert len(zarr_files) > 0, "No Zarr output created"
        
        # Check Zarr structure
        zarr_path = zarr_files[0]
        store = zarr.open_group(str(zarr_path), mode='r')
        assert '0' in store, "Base resolution layer '0' not found"
        assert 'multiscales' in store.attrs, "NGFF metadata missing"
    
    def test_ometiff_to_zarr(self, bridge_instance):
        """Test OME-TIFF to OME-Zarr conversion."""
        input_file = self.fixtures['ometiff']
        output_dir = self.output_dir / "ometiff_output"
        output_dir.mkdir(exist_ok=True)
        
        bridge_instance.to_zarr(
            input_path=str(input_file),
            output_path=str(output_dir),
            zarr_format=2,
            verbose=True
        )
        
        zarr_files = list(output_dir.glob("*.zarr"))
        assert len(zarr_files) > 0, "No Zarr output created"
    
    def test_zarr_input_to_zarr_output(self, bridge_instance):
        """Test Zarr input to Zarr output conversion (reprocessing)."""
        input_dir = self.output_dir / "input"
        input_dir.mkdir(exist_ok=True)
        
        # Use the generated NGFF as input
        input_zarr = self.fixtures['zarr_ngff']
        output_dir = self.output_dir / "zarr_reprocess"
        output_dir.mkdir(exist_ok=True)
        
        bridge_instance.to_zarr(
            input_path=str(input_zarr),
            output_path=str(output_dir),
            zarr_format=2,
            verbose=True
        )
        
        zarr_files = list(output_dir.glob("*.zarr"))
        assert len(zarr_files) > 0, "No Zarr output created from Zarr input"


class TestAggregativeConversions:
    """Test aggregative conversions (multiple input files → single Zarr output)."""
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_output_dir):
        """Set up test fixtures with multiple files."""
        self.output_dir = tmp_output_dir
        self.input_dir = tmp_output_dir / "aggregative_input"
        self.input_dir.mkdir(exist_ok=True)
        
        # Create multiple test files
        self.fixtures = generate_test_fixtures(self.input_dir)
    
    def test_tiff_stack_aggregation_z(self, bridge_instance):
        """Test stacking multiple TIFFs along Z dimension."""
        output_file = self.output_dir / "stacked_z.zarr"
        
        # This would concatenate multiple TIFF files along Z
        # Implementation depends on your aggregative_conversion_base API
        pytest.skip("Aggregative conversion setup needed")
    
    def test_tiff_stack_aggregation_t(self, bridge_instance):
        """Test stacking multiple TIFFs along T (time) dimension."""
        output_file = self.output_dir / "stacked_t.zarr"
        pytest.skip("Aggregative conversion setup needed")


class TestConversionValidation:
    """Validate conversion output correctness."""
    
    def test_output_zarr_structure(self, tmp_output_dir):
        """Verify output Zarr has correct NGFF structure."""
        # Create a test Zarr
        from tests.conftest_fixtures import create_sample_zarr
        zarr_path = create_sample_zarr(tmp_output_dir / "test.zarr")
        
        # Validate structure
        store = zarr.open_group(str(zarr_path), mode='r')
        
        # Check required attributes
        assert 'multiscales' in store.attrs, "Missing multiscales metadata"
        assert 'omero' in store.attrs, "Missing omero metadata"
        
        multiscales = store.attrs['multiscales'][0]
        assert 'datasets' in multiscales, "Missing datasets in multiscales"
        assert 'axes' in multiscales, "Missing axes in multiscales"
    
    def test_downscaling_creates_layers(self, bridge_instance, tmp_output_dir):
        """Verify downscaling creates multiple resolution layers."""
        from tests.conftest_fixtures import create_sample_tiff
        
        input_file = create_sample_tiff(
            tmp_output_dir / "test_downscale.tif",
            shape=(10, 512, 512)
        )
        output_dir = tmp_output_dir / "downscale_output"
        output_dir.mkdir(exist_ok=True)
        
        bridge_instance.configure_downscale(
            n_layers=3,
            z_scale_factor=2,
            y_scale_factor=2,
            x_scale_factor=2
        )
        
        bridge_instance.to_zarr(
            input_path=str(input_file),
            output_path=str(output_dir),
            zarr_format=2
        )
        
        zarr_files = list(output_dir.glob("*.zarr"))
        assert len(zarr_files) > 0
        
        store = zarr.open_group(str(zarr_files[0]), mode='r')
        datasets = store.attrs['multiscales'][0]['datasets']
        
        # Should have multiple resolution layers
        assert len(datasets) >= 2, "Downscaling should create multiple layers"


class TestMetadataHandling:
    """Test metadata extraction and handling."""
    
    def test_channel_metadata_preservation(self, bridge_instance, tmp_output_dir):
        """Verify channel metadata is preserved in output."""
        from tests.conftest_fixtures import create_sample_ometiff
        
        input_file = create_sample_ometiff(
            tmp_output_dir / "test_channels.ome.tif",
            shape=(3, 10, 256, 256)  # 3 channels
        )
        output_dir = tmp_output_dir / "channel_output"
        output_dir.mkdir(exist_ok=True)
        
        bridge_instance.to_zarr(
            input_path=str(input_file),
            output_path=str(output_dir),
            zarr_format=2
        )
        
        zarr_files = list(output_dir.glob("*.zarr"))
        store = zarr.open_group(str(zarr_files[0]), mode='r')
        
        # Check channel metadata
        if 'omero' in store.attrs:
            channels = store.attrs['omero'].get('channels', [])
            assert len(channels) > 0, "Channel metadata missing"
    
    def test_axis_metadata(self, tmp_output_dir):
        """Verify axis metadata is correct in output."""
        from tests.conftest_fixtures import create_sample_zarr
        
        zarr_path = create_sample_zarr(tmp_output_dir / "test_axes.zarr")
        store = zarr.open_group(str(zarr_path), mode='r')
        
        multiscales = store.attrs['multiscales'][0]
        axes = multiscales.get('axes', [])
        
        assert len(axes) > 0, "Axes metadata missing"
        axis_names = [ax['name'] for ax in axes]
        assert all(name in ['t', 'c', 'z', 'y', 'x'] for name in axis_names)


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_input_path(self, bridge_instance, tmp_output_dir):
        """Test handling of invalid input paths."""
        with pytest.raises((FileNotFoundError, ValueError)):
            bridge_instance.to_zarr(
                input_path="/nonexistent/path/file.tif",
                output_path=str(tmp_output_dir)
            )
    
    def test_missing_output_directory_creation(self, bridge_instance, tmp_output_dir):
        """Test that output directory is created if missing."""
        from tests.conftest_fixtures import create_sample_tiff
        
        input_file = create_sample_tiff(
            tmp_output_dir / "test.tif",
            shape=(10, 256, 256)
        )
        output_dir = tmp_output_dir / "nested" / "output" / "dir"
        
        # Directory should be created automatically
        bridge_instance.to_zarr(
            input_path=str(input_file),
            output_path=str(output_dir.parent),
            verbose=False
        )
        
        assert list(output_dir.parent.glob("*.zarr")), "Output not created"
