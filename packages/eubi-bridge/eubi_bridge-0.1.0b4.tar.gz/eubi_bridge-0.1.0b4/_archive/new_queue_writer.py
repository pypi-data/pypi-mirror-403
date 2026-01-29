"""
New queue-based writer implementation to be added to writers.py.
This file shows the complete implementation before integration.
"""

# ============================================================================
# HELPER FUNCTIONS (add before write_with_tensorstore_async around line 950)
# ============================================================================

def _read_region(arr, region_slice):
    """
    Unified region reader for both dask.array and DynamicArray.
    
    Parameters
    ----------
    arr : Union[da.Array, DynamicArray, zarr.Array, np.ndarray]
        Array to read from.
    region_slice : tuple of slice
        Region to read.
        
    Returns
    -------
    np.ndarray
        Region data as numpy array.
    """
    try:
        from eubi_bridge.external.dyna_zarr.dynamic_array import DynamicArray
        
        if isinstance(arr, DynamicArray):
            # Zero-copy direct read (optimal for zarr/tensorstore backends)
            return arr._read_direct(region_slice)
        elif hasattr(arr, 'compute') and hasattr(arr, '__dask_graph__'):
            # Dask array: slice then compute
            sliced = arr[region_slice]
            return sliced.compute()
        else:
            # Direct array (zarr.Array, np.ndarray, etc.)
            return np.asarray(arr[region_slice])
    except ImportError:
        # DynamicArray not available, fall back to dask/numpy
        if hasattr(arr, 'compute'):
            return arr[region_slice].compute()
        else:
            return np.asarray(arr[region_slice])


def _compute_region_shape(input_shape, final_chunks, region_size_mb, dtype=None, input_chunks=None):
    """
    Compute optimal region shape with deterministic algorithm.
    
    Uses LCM (Least Common Multiple) to maintain alignment with both
    input chunks and output chunks.
    
    Algorithm:
    1. Start with a single output chunk
    2. Expand dimensions in reverse order (last → first) until region_size_mb reached
    3. Use LCM of input_chunks and output_chunks for expansion increments
    4. Stop when budget exhausted or dimension complete
    
    Parameters
    ----------
    input_shape : tuple of int
        Shape of input array.
    final_chunks : tuple of int
        Output chunk shape (zarr chunks).
    region_size_mb : float
        Target size of read regions in MB.
    dtype : numpy.dtype, optional
        Data type for computing element size.
    input_chunks : tuple of int, optional
        Input chunk shape (for alignment).
        
    Returns
    -------
    tuple of int
        Optimal region shape.
        
    Example
    -------
    >>> _compute_region_shape((50, 179, 2, 339, 415), (1, 64, 1, 64, 64), 8.0)
    (1, 128, 2, 339, 415)
    """
    if dtype is None:
        element_size = 2
    else:
        try:
            element_size = int(np.dtype(dtype).itemsize)
        except Exception:
            element_size = 2
    
    target_bytes = region_size_mb * 1024 * 1024
    
    input_arr = np.array(input_shape, dtype=np.int64)
    output_chunk_arr = np.array(final_chunks, dtype=np.int64)
    
    if input_chunks is None:
        input_chunk_arr = output_chunk_arr.copy()
    else:
        input_chunk_arr = np.array(input_chunks, dtype=np.int64)
    
    # STEP 1: Start with one output chunk
    region_arr = output_chunk_arr.copy()
    current_bytes = np.prod(region_arr) * element_size
    
    # If single output chunk exceeds target, use it anyway (can't split chunks)
    if current_bytes >= target_bytes:
        return tuple(region_arr.tolist())
    
    # STEP 2: Compute expansion increments using LCM (maintains both alignments)
    expansion_increments = np.zeros(len(region_arr), dtype=np.int64)
    for i in range(len(region_arr)):
        gcd = np.gcd(input_chunk_arr[i], output_chunk_arr[i])
        lcm = (input_chunk_arr[i] * output_chunk_arr[i]) // gcd
        expansion_increments[i] = lcm
    
    # STEP 3: Expand dimensions in reverse order (last → first)
    for dim in reversed(range(len(region_arr))):
        # Expand this dimension until complete or budget exhausted
        while region_arr[dim] < input_arr[dim]:
            increment = expansion_increments[dim]
            remaining = input_arr[dim] - region_arr[dim]
            
            # Determine new size
            if remaining <= increment:
                # Remainder fits in one increment - complete the dimension
                new_size = input_arr[dim]
            else:
                # Add one increment
                new_size = region_arr[dim] + increment
                
                # Check if we should include the remainder now
                # to avoid creating a small partial region later
                future_remaining = input_arr[dim] - new_size
                if 0 < future_remaining < increment:
                    # Next time would be a small remainder - include it now
                    new_size = input_arr[dim]
            
            # Test if this fits in budget
            test_region = region_arr.copy()
            test_region[dim] = new_size
            new_bytes = np.prod(test_region) * element_size
            
            if new_bytes <= target_bytes:
                # Fits in budget - accept it
                region_arr[dim] = new_size
                current_bytes = new_bytes
            else:
                # Doesn't fit - stop expanding this dimension
                break
        
        # After completing this dimension, check if we should continue
        # to the next dimension or stop
        if current_bytes >= target_bytes:
            break
    
    # STEP 4: Verify output chunk alignment for PARTIAL dimensions only
    # Full dimensions don't need alignment (they include all chunks anyway)
    for i in range(len(region_arr)):
        # Skip if dimension is fully enclosed
        if region_arr[i] >= input_arr[i]:
            continue
        
        # For partial dimensions, ensure output chunk alignment
        if output_chunk_arr[i] > 0 and region_arr[i] % output_chunk_arr[i] != 0:
            # Round down to output chunk boundary to avoid cutting inside chunks
            aligned_size = (region_arr[i] // output_chunk_arr[i]) * output_chunk_arr[i]
            # Ensure at least one output chunk
            region_arr[i] = max(output_chunk_arr[i], aligned_size)
    
    return tuple(region_arr.tolist())


# ============================================================================
# NEW QUEUE-BASED WRITER (add after write_with_tensorstore_async)
# ============================================================================

async def write_with_queue_async(
        arr: Union[da.Array, 'DynamicArray', zarr.Array, ts.TensorStore],
        store_path: Union[str, os.PathLike],
        chunks: Optional[Tuple[int, ...]] = None,
        shards: Optional[Tuple[int, ...]] = None,
        dimension_names: Optional[str] = None,
        dtype: Any = None,
        compressor: str = 'blosc',
        compressor_params: dict = None,
        overwrite: bool = True,
        zarr_format: int = 2,
        pixel_sizes: Optional[Tuple[float, ...]] = None,
        num_readers: Optional[int] = None,
        max_workers: Optional[int] = None,
        region_size_mb: float = 8.0,
        queue_size: Optional[int] = None,
        gc_interval: float = 15.0,
        ts_io_concurrency: Optional[int] = None,
        **kwargs
) -> 'ts.TensorStore':
    """
    Queue-based parallel writer with producer-consumer threading pattern.
    
    Architecture:
    - Reader threads: Read regions from input array and queue them
    - Writer threads: Pop from queue and submit async TensorStore writes
    - TensorStore: Handles actual parallel I/O in C++ backend
    
    This replaces the micro-batching approach with a simpler streaming pattern
    that works efficiently for both dask.array and DynamicArray.
    
    Parameters
    ----------
    arr : Union[da.Array, DynamicArray, zarr.Array, ts.TensorStore]
        Input array to write.
    store_path : Union[str, os.PathLike]
        Path to output Zarr array.
    chunks : Optional[Tuple[int, ...]]
        Output chunk shape (inner chunks for v3 with sharding).
    shards : Optional[Tuple[int, ...]]
        Shard shape for Zarr v3 (must be multiple of chunks).
    dimension_names : Optional[str]
        Dimension names for Zarr v3.
    dtype : Any
        Data type for output array.
    compressor : str
        Compression algorithm ('blosc', 'zstd', etc.).
    compressor_params : dict
        Compression parameters.
    overwrite : bool
        Whether to overwrite existing array.
    zarr_format : int
        Zarr format version (2 or 3).
    pixel_sizes : Optional[Tuple[float, ...]]
        Pixel sizes for NGFF metadata.
    num_readers : Optional[int]
        Number of reader threads. Default: 2 * max_workers.
    max_workers : Optional[int]
        Number of writer threads. Default: 4.
    region_size_mb : float
        Target size of read regions in MB. Default: 8.0.
    queue_size : Optional[int]
        Queue size for buffering. Default: min(128, max(32, num_readers)).
    gc_interval : float
        Seconds between garbage collection runs. Default: 15.0.
    ts_io_concurrency : Optional[int]
        TensorStore file I/O concurrency limit.
    **kwargs
        Additional keyword arguments.
        
    Returns
    -------
    ts.TensorStore
        TensorStore handle to the written array.
    """
    compressor_params = compressor_params or {}
    
    # Set defaults for threading parameters
    if max_workers is None:
        max_workers = 4
    if num_readers is None:
        num_readers = 2 * max_workers
    
    try:
        dtype = np.dtype(dtype.name)
    except Exception:
        dtype = np.dtype(dtype)
    fill_value = kwargs.get('fill_value', get_default_fill_value(dtype))

    if chunks is None:
        chunks = get_chunk_shape(arr)
    chunks = tuple(int(size) for size in chunks)

    if shards is None:
        shards = copy.deepcopy(chunks)
    if not np.allclose(np.mod(shards, chunks), 0):
        multiples = np.floor_divide(shards, chunks)
        shards = np.multiply(multiples, chunks)
    shards = tuple(int(size) for size in np.ravel(shards))

    # Optionally tune TensorStore file I/O concurrency inside kvstore spec
    kvstore = make_kvstore(store_path)
    if ts_io_concurrency:
        kvstore["file_io_concurrency"] = {"limit": int(ts_io_concurrency)}

    # Build TensorStore spec (same as current implementation)
    if zarr_format == 3:
        zarr_metadata = {
            "data_type": np.dtype(dtype).name,
            "shape": arr.shape,
            "chunk_grid": {"name": "regular", "configuration": {"chunk_shape": shards}},
            "dimension_names": list(dimension_names) if dimension_names else [],
            "codecs": [
                {
                    "name": "sharding_indexed",
                    "configuration": {
                        "chunk_shape": chunks,
                        "codecs": [
                            {"name": "bytes", "configuration": {"endian": "little"}},
                            {"name": compressor, "configuration": compressor_params or {}}
                        ],
                        "index_codecs": [
                            {"name": "bytes", "configuration": {"endian": "little"}},
                            {"name": "crc32c"}
                        ],
                        "index_location": "end"
                    }
                }
            ],
            "node_type": "array"
        }
    else:
        zarr_metadata = {
            "compressor": {"id": compressor, **compressor_params},
            "dtype": np.dtype(dtype).str,
            "shape": arr.shape,
            "chunks": chunks,
            "fill_value": fill_value,
            "dimension_separator": '/',
        }

    zarr_spec = {
        "driver": "zarr" if zarr_format == 2 else "zarr3",
        "kvstore": kvstore,
        "metadata": zarr_metadata,
        "create": True,
        "delete_existing": overwrite,
    }

    ctx = ts.Context({
        "cache_pool": {"total_bytes_limit": 1_000_000_000},  # 1 GB local cache
        "data_copy_concurrency": {"limit": 64},
        "s3_request_concurrency": {"limit": 32},
        "s3_request_retries": {"max_retries": 5},
    })

    ts_store = ts.open(zarr_spec, context=ctx).result()

    # Compute region shape using smart algorithm
    input_chunks = getattr(arr, 'chunks', chunks)
    region_shape = _compute_region_shape(
        arr.shape, chunks, region_size_mb, 
        dtype=dtype, input_chunks=input_chunks
    )
    
    logger.info(
        f"Queue-based write starting: shape={arr.shape}, chunks={chunks}, "
        f"region={region_shape}, readers={num_readers}, writers={max_workers}"
    )
    
    # Generate chunk indices (regions to read)
    chunk_indices = list(itertools.product(
        *[range(0, s, rs) for s, rs in zip(arr.shape, region_shape)]
    ))
    total_chunks = len(chunk_indices)
    
    logger.info(f"Total regions to process: {total_chunks}")
    
    # Queue for work distribution
    if queue_size is None:
        queue_size = min(128, max(32, num_readers))
    
    chunk_queue = Queue(maxsize=queue_size)
    sentinel_lock = threading.Lock()
    
    # Shared state
    state = {
        'read_idx': 0,
        'completed_readers': 0,
        'writes_processed': 0,
        'error': None,
        'start_time': time.time(),
    }
    
    read_idx_lock = threading.Lock()
    write_futures = []
    futures_lock = threading.Lock()
    shutdown_flag = threading.Event()
    
    def reader_thread():
        """Producer thread: reads regions and queues them."""
        try:
            while not shutdown_flag.is_set():
                if state.get('error'):
                    logger.debug("[Reader] Exiting due to error")
                    break
                
                # Atomically get next chunk index
                with read_idx_lock:
                    current_read_idx = state['read_idx']
                    if current_read_idx >= len(chunk_indices):
                        logger.debug(f"[Reader] Finished - processed {current_read_idx} regions")
                        break
                    chunk_start = chunk_indices[current_read_idx]
                    current_idx = current_read_idx
                    state['read_idx'] += 1
                
                try:
                    chunk_slice = tuple(
                        slice(start, min(start + rs, dim_size))
                        for start, rs, dim_size in zip(chunk_start, region_shape, arr.shape)
                    )
                    
                    # Read using unified abstraction
                    data = _read_region(arr, chunk_slice)
                    
                    chunk_queue.put((chunk_slice, data))
                    
                except Exception as chunk_error:
                    logger.error(f"[Reader] ERROR at region {current_idx}: {chunk_error}")
                    state['error'] = chunk_error
                    raise
            
            # Sentinel coordination
            with sentinel_lock:
                state['completed_readers'] += 1
                should_send_sentinels = (state['completed_readers'] == num_readers)
                logger.debug(f"[Reader] Exiting - completed {state['completed_readers']}/{num_readers} readers")
            
            if should_send_sentinels:
                for _ in range(max_workers):
                    chunk_queue.put(None)
                    
        except Exception as e:
            logger.error(f"[Reader] FATAL ERROR: {e}")
            state['error'] = e
    
    def writer_thread():
        """Consumer thread: pops from queue and submits async writes."""
        try:
            while not shutdown_flag.is_set():
                if state.get('error'):
                    break
                
                try:
                    item = chunk_queue.get(block=True, timeout=1.0)
                except Exception:
                    continue
                
                if item is None:
                    chunk_queue.task_done()
                    break
                
                try:
                    chunk_slice, data = item
                    
                    # Submit async write to TensorStore
                    write_future = ts_store[chunk_slice].write(data)
                    state['writes_processed'] += 1
                    
                    # Track future
                    with futures_lock:
                        write_futures.append(write_future)
                    
                    chunk_queue.task_done()
                    
                except Exception as e:
                    logger.error(f"[Writer] ERROR: {e}")
                    state['error'] = e
                    chunk_queue.task_done()
                    break
                    
        except Exception as e:
            logger.error(f"[Writer] FATAL ERROR: {e}")
            state['error'] = e

    def monitor_progress():
        """Progress monitoring thread."""
        last_read = 0
        
        while not shutdown_flag.is_set():
            time.sleep(2.0)
            try:
                current_read = state['read_idx']
                with futures_lock:
                    total_futures = len(write_futures)
                    completed_writes = sum(1 for f in write_futures if f.done())
                
                if current_read >= total_chunks:
                    break
                    
                if current_read > last_read:
                    progress_pct = (current_read / total_chunks) * 100
                    q_size = chunk_queue.qsize()
                    elapsed = time.time() - state['start_time']
                    writes_proc = state.get('writes_processed', 0)
                    
                    logger.info(
                        f"Progress: Read {current_read}/{total_chunks} ({progress_pct:.1f}%), "
                        f"Queue: {q_size}, Writes: {writes_proc} submitted, "
                        f"{completed_writes}/{total_futures} done, Time: {elapsed:.1f}s"
                    )
                    last_read = current_read
            except (KeyError, NameError):
                break
    
    # Wrap threading execution in asyncio
    def _run_threaded_write():
        """Synchronous function that runs the threaded write pipeline."""
        logger.info(f"Starting {num_readers} readers and {max_workers} writers")
        
        # Start threads
        readers = [
            threading.Thread(target=reader_thread, daemon=True, name=f"Reader-{i}")
            for i in range(num_readers)
        ]
        for r in readers:
            r.start()
        
        writers = [
            threading.Thread(target=writer_thread, daemon=True, name=f"Writer-{i}")
            for i in range(max_workers)
        ]
        for w in writers:
            w.start()
        
        # Start monitor
        monitor = threading.Thread(target=monitor_progress, daemon=True, name="Monitor")
        monitor.start()
        
        # Wait for readers
        for r in readers:
            r.join()
            if state.get('error'):
                shutdown_flag.set()
                break
        
        # Wait for writers
        for w in writers:
            w.join()
            if state.get('error'):
                shutdown_flag.set()
                break
        
        # Stop monitor
        shutdown_flag.set()
        monitor.join(timeout=2.0)
        
        if state.get('error'):
            raise state['error']
        
        logger.info(f"All reads/writes queued, waiting for {len(write_futures)} async writes to complete...")
        
        # Wait for all async writes
        last_gc_time = time.time()
        max_wait = 300  # 5 minutes timeout
        wait_start = time.time()
        
        while True:
            if state['error']:
                raise state['error']
            
            with futures_lock:
                completed_count = sum(1 for f in write_futures if f.done())
                total_futures = len(write_futures)
            
            if completed_count >= total_futures:
                break
            
            if time.time() - wait_start > max_wait:
                logger.warning(f"Timeout waiting for futures: {completed_count}/{total_futures} done")
                break
            
            # Periodic GC
            now = time.time()
            if now - last_gc_time >= gc_interval:
                gc.collect()
                last_gc_time = now
            
            time.sleep(0.1)
        
        # Verify all writes succeeded
        if not state.get('error'):
            logger.info("Verifying all writes succeeded...")
            for i, future in enumerate(write_futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Write future {i} failed: {e}")
                    raise
        
        elapsed = time.time() - state['start_time']
        throughput = total_chunks / elapsed if elapsed > 0 else 0
        
        if not state.get('error'):
            logger.info(
                f"Write completed: {total_chunks} regions in {elapsed:.1f}s "
                f"({throughput:.2f} regions/s)"
            )
    
    # Run threaded write in asyncio thread pool
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _run_threaded_write)
    
    # Metadata handling (same as current implementation)
    gr_path = os.path.dirname(store_path)
    arrpath = os.path.basename(store_path)
    gr = zarr.group(gr_path)
    handler = NGFFMetadataHandler()
    handler.connect_to_group(gr)
    handler.read_metadata()
    handler.add_dataset(path=arrpath, scale=pixel_sizes, overwrite=True)
    handler.save_changes()

    return ts_store
