"""
Files Upload Test Cases

Tests for uploading file content via the Files endpoint client.
Updated to use new FileUploadResponse objects.
"""

import logging
import io
from pathlib import Path
from typing import Dict, Any


async def run_file_upload_tests(client, space_id: str, graph_id: str, file_uri: str, logger=None) -> bool:
    """Run file upload tests."""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    logger.info("🧪 Running File Upload Tests")
    
    try:
        # Test 1: Upload file from bytes
        logger.info("  Test 1: Upload file from bytes (real PDF)")
        # Load real PDF file
        pdf_path = Path("/Users/hadfield/Local/vital-git/vital-graph/test_files/2502.16143v1.pdf")
        test_content = pdf_path.read_bytes()
        
        response = client.files.upload_file_content(
            space_id=space_id,
            graph_id=graph_id,
            file_uri=file_uri,
            source=test_content,
            filename="2502.16143v1.pdf",
            content_type="application/pdf"
        )
        
        if response.is_success:
            logger.info(f"  ✅ File uploaded from bytes successfully ({response.size} bytes)")
        else:
            logger.error(f"  ❌ Failed to upload file from bytes: {response.error_message}")
            return False
        
        # Test 2: Upload file from stream
        logger.info("  Test 2: Upload file from stream (real PNG)")
        # Load real PNG file
        png_path = Path("/Users/hadfield/Local/vital-git/vital-graph/test_files/vampire_queen_baby.png")
        stream_content = png_path.read_bytes()
        stream = io.BytesIO(stream_content)
        
        response = client.files.upload_file_content(
            space_id=space_id,
            graph_id=graph_id,
            file_uri=file_uri,
            source=stream,
            filename="vampire_queen_baby.png",
            content_type="image/png"
        )
        
        if response.is_success:
            logger.info(f"  ✅ File uploaded from stream successfully ({response.size} bytes)")
        else:
            logger.error(f"  ❌ Failed to upload file from stream: {response.error_message}")
            return False
        
        # Test 3: Upload larger file (using real PNG which is 2.5MB)
        logger.info("  Test 3: Upload larger file (2.5MB PNG)")
        large_content = png_path.read_bytes()  # Reuse the PNG file
        
        response = client.files.upload_file_content(
            space_id=space_id,
            graph_id=graph_id,
            file_uri=file_uri,
            source=large_content,
            filename="large_file.bin",
            content_type="application/octet-stream"
        )
        
        if response.is_success:
            logger.info(f"  ✅ Large file uploaded successfully ({response.size} bytes)")
        else:
            logger.error(f"  ❌ Failed to upload large file: {response.error_message}")
            return False
        
        logger.info("✅ All file upload tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ File upload tests failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
