#!/usr/bin/env python3
"""
File Streaming Upload Test Case

Tests streaming file upload operations using the new /api/files/stream/upload endpoint.
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional
from vitalgraph.client.binary.async_streaming import AsyncFilePathGenerator, AsyncBytesGenerator


async def run_file_stream_upload_tests(
    client,
    space_id: str,
    graph_id: str,
    file_uri: str,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Run file streaming upload tests.
    
    Args:
        client: VitalGraph client instance
        space_id: Space identifier
        graph_id: Graph identifier
        file_uri: File URI to upload to
        logger: Optional logger instance
        
    Returns:
        bool: True if all tests passed, False otherwise
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    logger.info("🔧 Testing File Streaming Upload operations...")
    
    all_passed = True
    
    # Test 1: Stream upload with AsyncFilePathGenerator
    logger.info("  Test 1: Stream upload with AsyncFilePathGenerator...")
    try:
        # Create a temporary test file with some content
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.bin') as tmp_file:
            # Write 1MB of test data
            test_data = b"Test streaming data chunk " * 40000  # ~1MB
            tmp_file.write(test_data)
            tmp_file_path = tmp_file.name
        
        try:
            # Create async generator for streaming upload
            generator = AsyncFilePathGenerator(
                file_path=tmp_file_path,
                chunk_size=8192,
                content_type="application/octet-stream"
            )
            
            # Upload using streaming with generator (async)
            response = await client.files.upload_file_stream_async(
                space_id=space_id,
                graph_id=graph_id,
                file_uri=file_uri,
                source=generator,
                chunk_size=8192
            )
            
            if response and hasattr(response, 'message'):
                logger.info(f"    ✅ Stream upload with generator successful: {response.message}")
            else:
                logger.error(f"    ❌ Stream upload with generator failed: Invalid response")
                all_passed = False
        finally:
            # Clean up temp file
            Path(tmp_file_path).unlink(missing_ok=True)
            
    except Exception as e:
        logger.error(f"    ❌ Stream upload with generator failed: {e}")
        all_passed = False
    
    # Test 2: Stream upload with AsyncBytesGenerator
    logger.info("  Test 2: Stream upload with AsyncBytesGenerator...")
    try:
        # Create test data
        test_bytes = b"Streaming bytes test data " * 1000  # ~26KB
        
        # Create async generator for streaming upload
        generator = AsyncBytesGenerator(
            data=test_bytes,
            chunk_size=4096,
            filename="test_bytes.bin",
            content_type="application/octet-stream"
        )
        
        # Upload using streaming with generator (async)
        response = await client.files.upload_file_stream_async(
            space_id=space_id,
            graph_id=graph_id,
            file_uri=file_uri,
            source=generator,
            chunk_size=4096
        )
        
        if response and hasattr(response, 'message'):
            logger.info(f"    ✅ Stream upload with bytes generator successful: {response.message}")
        else:
            logger.error(f"    ❌ Stream upload with bytes generator failed: Invalid response")
            all_passed = False
            
    except Exception as e:
        logger.error(f"    ❌ Stream upload with bytes generator failed: {e}")
        all_passed = False
    
    # Test 3: Stream upload with generator and custom chunk size
    logger.info("  Test 3: Stream upload with generator and custom chunk size...")
    try:
        # Create a larger temporary test file
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as tmp_file:
            # Write 5MB of test data
            test_data = b"X" * (5 * 1024 * 1024)  # 5MB
            tmp_file.write(test_data)
            tmp_file_path = tmp_file.name
        
        try:
            # Create async generator for streaming upload with larger chunks
            generator = AsyncFilePathGenerator(
                file_path=tmp_file_path,
                chunk_size=65536,  # 64KB chunks
                content_type="application/octet-stream"
            )
            
            # Upload using streaming with generator (async)
            response = await client.files.upload_file_stream_async(
                space_id=space_id,
                graph_id=graph_id,
                file_uri=file_uri,
                source=generator,
                chunk_size=65536  # 64KB chunks
            )
            
            if response and hasattr(response, 'message'):
                logger.info(f"    ✅ Stream upload with custom chunk size successful: {response.message}")
            else:
                logger.error(f"    ❌ Stream upload with custom chunk size failed: Invalid response")
                all_passed = False
        finally:
            # Clean up temp file
            Path(tmp_file_path).unlink(missing_ok=True)
            
    except Exception as e:
        logger.error(f"    ❌ Stream upload with custom chunk size failed: {e}")
        all_passed = False
    
    if all_passed:
        logger.info("✅ All File Streaming Upload tests passed")
    else:
        logger.error("❌ Some File Streaming Upload tests failed")
    
    return all_passed
