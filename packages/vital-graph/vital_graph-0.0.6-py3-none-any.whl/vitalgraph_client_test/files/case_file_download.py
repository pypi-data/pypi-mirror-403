"""
Files Download Test Cases

Tests for downloading file content via the Files endpoint client.
Updated to use new FileDownloadResponse objects.
"""

import logging
import io
from pathlib import Path
from typing import Dict, Any


async def run_file_download_tests(client, space_id: str, graph_id: str, file_uri: str, logger=None) -> bool:
    """Run file download tests."""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    logger.info("🧪 Running File Download Tests")
    
    try:
        # Test 1: Download file as bytes
        logger.info("  Test 1: Download file as bytes")
        
        content = client.files.download_file_content(
            space_id=space_id,
            graph_id=graph_id,
            file_uri=file_uri,
            destination=None  # Returns bytes
        )
        
        if content and isinstance(content, bytes):
            logger.info(f"  ✅ File downloaded as bytes successfully ({len(content)} bytes)")
        else:
            logger.error("  ❌ Failed to download file as bytes")
            return False
        
        # Test 2: Download file to stream
        logger.info("  Test 2: Download file to stream")
        stream = io.BytesIO()
        
        result = client.files.download_file_content(
            space_id=space_id,
            graph_id=graph_id,
            file_uri=file_uri,
            destination=stream
        )
        
        if result.is_success:
            stream.seek(0)
            downloaded_content = stream.read()
            logger.info(f"  ✅ File downloaded to stream successfully ({result.size} bytes)")
        else:
            logger.error(f"  ❌ Failed to download file to stream: {result.error_message}")
            return False
        
        logger.info("✅ All file download tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ File download tests failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
