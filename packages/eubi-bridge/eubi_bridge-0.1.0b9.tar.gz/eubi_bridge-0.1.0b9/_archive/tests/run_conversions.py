#!/usr/bin/env python
"""
Standalone test runner for EuBI-Bridge conversions.

This script can be run without pytest to perform manual conversion testing
and validation of the conversion pipeline.

Usage:
    python tests/run_conversions.py
    python tests/run_conversions.py --input /path/to/images --output /path/to/output
    python tests/run_conversions.py --formats tiff,ometiff --verbose
"""

import argparse
import sys
import tempfile
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from eubi_bridge.ebridge import EuBIBridge
from tests.conftest_fixtures import generate_test_fixtures


def run_conversion_test(input_file: Path,
                        output_dir: Path,
                        config: dict,
                        verbose: bool = False) -> dict:
    """
    Run a single conversion test.
    
    Returns
    -------
    dict
        Results dictionary with timing and status information.
    """
    result = {
        'input': str(input_file),
        'output': str(output_dir),
        'format': input_file.suffix.lower(),
        'status': 'pending',
        'error': None,
        'time_seconds': 0.0
    }
    
    try:
        start_time = time.time()
        
        bridge = EuBIBridge()
        
        # Apply configuration
        if config.get('zarr_format'):
            bridge.configure_conversion(zarr_format=config['zarr_format'])
        
        if verbose:
            bridge.configure_conversion(verbose=True)
        
        # Run conversion
        bridge.to_zarr(
            input_path=str(input_file),
            output_path=str(output_dir),
            verbose=verbose
        )
        
        elapsed = time.time() - start_time
        result['status'] = 'success'
        result['time_seconds'] = elapsed
        
        # Check output
        zarr_files = list(output_dir.glob("*.zarr"))
        result['output_files'] = len(zarr_files)
        result['output_path'] = str(zarr_files[0]) if zarr_files else None
        
    except Exception as e:
        elapsed = time.time() - start_time
        result['status'] = 'failed'
        result['error'] = str(e)
        result['time_seconds'] = elapsed
    
    return result


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(
        description="Run EuBI-Bridge conversion tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_conversions.py                                    # Test with generated fixtures
  python tests/run_conversions.py --input /path/to/images           # Test with real images
  python tests/run_conversions.py --formats tiff,ometiff --verbose  # Specific formats
  python tests/run_conversions.py --zarr-format 3                   # Use Zarr v3
        """
    )
    
    parser.add_argument(
        '--input',
        type=Path,
        default=None,
        help='Directory with input images (uses generated fixtures if not provided)'
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        default=None,
        help='Output directory (uses temp dir if not provided)'
    )
    
    parser.add_argument(
        '--formats',
        type=str,
        default='tiff,ometiff,zarr',
        help='Comma-separated list of formats to test (tiff, ometiff, zarr, ometiff)'
    )
    
    parser.add_argument(
        '--zarr-format',
        type=int,
        choices=[2, 3],
        default=2,
        help='Zarr format version (2 or 3)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--keep-output',
        action='store_true',
        help='Keep output directory (default: use temp dir)'
    )
    
    args = parser.parse_args()
    
    # Set up directories
    if args.input is None:
        input_dir = Path(tempfile.mkdtemp(prefix='eubi_test_input_'))
        print(f"Generating test fixtures in: {input_dir}")
        fixtures = generate_test_fixtures(input_dir)
        print(f"Generated {len(fixtures)} test files")
    else:
        input_dir = Path(args.input)
        assert input_dir.exists(), f"Input directory not found: {input_dir}"
    
    if args.output is None:
        output_dir = Path(tempfile.mkdtemp(prefix='eubi_test_output_'))
        print(f"Output directory: {output_dir}")
    else:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine which formats to test
    test_formats = {
        'tiff': '*.tif',
        'ometiff': '*.ome.tif',
        'zarr': '*.zarr'
    }
    
    formats_to_test = [f for f in args.formats.split(',') if f in test_formats]
    
    # Find input files
    input_files = []
    for fmt in formats_to_test:
        input_files.extend(input_dir.glob(test_formats[fmt]))
    
    if not input_files:
        print(f"ERROR: No input files found matching formats: {formats_to_test}")
        return 1
    
    # Run tests
    print(f"\n{'=' * 80}")
    print(f"EuBI-Bridge Conversion Tests")
    print(f"{'=' * 80}")
    print(f"Input directory:  {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Zarr format:      {args.zarr_format}")
    print(f"Test files:       {len(input_files)}")
    print(f"{'=' * 80}\n")
    
    config = {
        'zarr_format': args.zarr_format
    }
    
    results = []
    for i, input_file in enumerate(sorted(input_files), 1):
        # Create per-file output directory
        file_output = output_dir / input_file.stem
        file_output.mkdir(exist_ok=True)
        
        print(f"[{i}/{len(input_files)}] Testing: {input_file.name}")
        result = run_conversion_test(input_file, file_output, config, args.verbose)
        results.append(result)
        
        if result['status'] == 'success':
            print(f"  ✓ OK ({result['time_seconds']:.2f}s, {result['output_files']} output files)")
        else:
            print(f"  ✗ FAILED: {result['error']}")
    
    # Summary
    print(f"\n{'=' * 80}")
    print(f"Test Summary")
    print(f"{'=' * 80}")
    
    passed = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'failed')
    total_time = sum(r['time_seconds'] for r in results)
    
    print(f"Total tests:     {len(results)}")
    print(f"Passed:          {passed}")
    print(f"Failed:          {failed}")
    print(f"Total time:      {total_time:.2f}s")
    
    if failed > 0:
        print(f"\nFailed conversions:")
        for r in results:
            if r['status'] == 'failed':
                print(f"  - {r['input']}: {r['error']}")
    
    print(f"\nOutput directory: {output_dir}")
    if args.keep_output:
        print("(output kept)")
    else:
        print("(output directory will be cleaned up if using temp dir)")
    
    print(f"{'=' * 80}\n")
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
