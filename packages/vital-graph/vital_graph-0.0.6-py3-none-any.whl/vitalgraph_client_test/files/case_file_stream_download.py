#!/usr/bin/env python3
"""
File Streaming Download Test Case

Tests streaming file download operations using the new /api/files/stream/download endpoint.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional
from vitalgraph.client.binary.async_streaming import AsyncFilePathConsumer


async def run_file_stream_download_tests(
    client,
    space_id: str,
    graph_id: str,
    file_uri: str,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Run file streaming download tests.
    
    Args:
        client: VitalGraph client instance
        space_id: Space identifier
        graph_id: Graph identifier
        file_uri: File URI to download from
        logger: Optional logger instance
        
    Returns:
        bool: True if all tests passed, False otherwise
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    logger.info("🔧 Testing File Streaming Download operations...")
    
    all_passed = True
    
    # Test 1: Stream download with AsyncFilePathConsumer
    logger.info("  Test 1: Stream download with AsyncFilePathConsumer...")
    try:
        # Use designated download directory
        download_dir = Path("/Users/hadfield/Local/vital-git/vital-graph/test_files_download")
        download_path = download_dir / "stream_download_test_1.bin"
        
        try:
            # Create async consumer for streaming download
            consumer = AsyncFilePathConsumer(download_path, create_dirs=False)
            
            # Download using streaming with consumer (async)
            response = await client.files.download_file_stream_async(
                space_id=space_id,
                graph_id=graph_id,
                file_uri=file_uri,
                destination=consumer,
                chunk_size=8192
            )
            
            if response and hasattr(response, 'message'):
                # Verify file was created and has content
                if download_path.exists() and download_path.stat().st_size > 0:
                    logger.info(f"    ✅ Stream download with consumer successful: {response.file_size} bytes")
                else:
                    logger.error(f"    ❌ Stream download with consumer failed: File empty or not created")
                    all_passed = False
            else:
                logger.error(f"    ❌ Stream download with consumer failed: Invalid response")
                all_passed = False
        finally:
            # Clean up downloaded file
            download_path.unlink(missing_ok=True)
            
    except Exception as e:
        logger.error(f"    ❌ Stream download to file path failed: {e}")
        all_passed = False
    
    # Test 2: Stream download with custom chunk size and consumer
    logger.info("  Test 2: Stream download with custom chunk size and consumer...")
    try:
        # Use designated download directory
        download_dir = Path("/Users/hadfield/Local/vital-git/vital-graph/test_files_download")
        download_path = download_dir / "stream_download_test_2.dat"
        
        try:
            # Create async consumer for streaming download
            consumer = AsyncFilePathConsumer(download_path, create_dirs=False)
            
            # Download using streaming with larger chunk size (async)
            response = await client.files.download_file_stream_async(
                space_id=space_id,
                graph_id=graph_id,
                file_uri=file_uri,
                destination=consumer,
                chunk_size=65536  # 64KB chunks
            )
            
            if response and hasattr(response, 'message'):
                # Verify file was created and has content
                if download_path.exists() and download_path.stat().st_size > 0:
                    logger.info(f"    ✅ Stream download with custom chunk size successful: {response.file_size} bytes")
                else:
                    logger.error(f"    ❌ Stream download with custom chunk size failed: File empty or not created")
                    all_passed = False
            else:
                logger.error(f"    ❌ Stream download with custom chunk size failed: Invalid response")
                all_passed = False
        finally:
            # Clean up downloaded file
            download_path.unlink(missing_ok=True)
            
    except Exception as e:
        logger.error(f"    ❌ Stream download with custom chunk size failed: {e}")
        all_passed = False
    
    # Test 3: Stream download with consumer and verify content integrity
    logger.info("  Test 3: Stream download with consumer and verify content integrity...")
    try:
        # Use designated download directory
        download_dir = Path("/Users/hadfield/Local/vital-git/vital-graph/test_files_download")
        download_path = download_dir / "stream_download_test_3.verify"
        
        try:
            # Create async consumer for streaming download
            consumer = AsyncFilePathConsumer(download_path, create_dirs=False)
            
            # Download using streaming (async)
            response = await client.files.download_file_stream_async(
                space_id=space_id,
                graph_id=graph_id,
                file_uri=file_uri,
                destination=consumer,
                chunk_size=4096
            )
            
            if response and hasattr(response, 'file_size'):
                # Verify file size matches response
                actual_size = download_path.stat().st_size
                reported_size = response.file_size
                
                if actual_size == reported_size:
                    logger.info(f"    ✅ Stream download content integrity verified: {actual_size} bytes")
                else:
                    logger.error(f"    ❌ Stream download content integrity failed: Expected {reported_size}, got {actual_size}")
                    all_passed = False
            else:
                logger.error(f"    ❌ Stream download content integrity failed: Invalid response")
                all_passed = False
        finally:
            # Clean up downloaded file
            download_path.unlink(missing_ok=True)
            
    except Exception as e:
        logger.error(f"    ❌ Stream download content integrity failed: {e}")
        all_passed = False
    
    if all_passed:
        logger.info("✅ All File Streaming Download tests passed")
    else:
        logger.error("❌ Some File Streaming Download tests failed")
    
    return all_passed
