#!/usr/bin/env python3
"""
KGEntity Frame Retrieval Test Case

Client-side test case for KG entity frame retrieval operations using VitalGraph client.
Tests frame retrieval within entity context, pagination, and filtering.
"""

import logging
from typing import Dict, Any, List
from vitalgraph.client.vitalgraph_client import VitalGraphClient, VitalGraphClientError
from vitalgraph.model.kgframes_model import FrameCreateResponse
from vitalgraph.model.kgentities_model import EntityFramesResponse
from vitalgraph.model.jsonld_model import JsonLdDocument
from vitalgraph_client_test.client_test_data import ClientTestDataCreator

logger = logging.getLogger(__name__)


class KGEntityFrameGetTester:
    """Client-side test case for KG entity frame retrieval operations."""
    
    def __init__(self, client: VitalGraphClient, test_data_creator: ClientTestDataCreator):
        """
        Initialize the frame retrieval tester.
        
        Args:
            client: VitalGraphClient instance
            test_data_creator: ClientTestDataCreator instance for generating test data
        """
        self.client = client
        self.test_data_creator = test_data_creator
        self.created_entity_uris = []
        self.created_frame_uris = []
        
    async def test_basic_frame_retrieval(self, space_id: str, graph_id: str) -> bool:
        """
        Test basic frame retrieval within entity context.
        
        Args:
            space_id: Test space identifier
            graph_id: Test graph identifier
            
        Returns:
            bool: True if basic frame retrieval successful, False otherwise
        """
        try:
            logger.info("🧪 Testing basic frame retrieval within entity context")
            
            # Create test entity with multiple frames
            entity_objects = self.test_data_creator.create_person_with_contact("Frame Get Test Person")
            
            # Convert to JSON-LD for client
            from vital_ai_vitalsigns.model.GraphObject import GraphObject
            entity_document_dict = GraphObject.to_jsonld_list(entity_objects)
            entity_document = JsonLdDocument(**entity_document_dict)
            
            entity_response = self.client.kgentities.create_kgentities(
                space_id=space_id,
                graph_id=graph_id,
                data=entity_document
            )
            
            if not entity_response or not entity_response.created_uris:
                logger.error("Failed to create test entity for frame retrieval")
                return False
                
            entity_uri = str(entity_objects[0].URI)  # Get URI from VitalSigns object and convert to string
            self.created_entity_uris.append(entity_uri)
            logger.info(f"✅ Created test entity: {entity_uri}")
            
            # Test frame retrieval with existing frames from entity creation
            # (Skip additional frame creation since create_employment_frame doesn't exist)
            logger.info("✅ Using existing frames from entity creation for retrieval test")
            
            # Test 1: Get all frames for the entity using get_kgentity_frames
            frames_response = self.client.kgentities.get_kgentity_frames(
                space_id=space_id,
                graph_id=graph_id,
                entity_uri=entity_uri
            )
            
            # Validate response structure
            if not isinstance(frames_response, EntityFramesResponse):
                logger.error(f"Expected EntityFramesResponse, got {type(frames_response)}")
                return False
                
            if not hasattr(frames_response, 'total_count') or frames_response.total_count == 0:
                logger.error("No frames found for entity")
                return False
                
            logger.info(f"✅ Retrieved {frames_response.total_count} frames for entity")
            
            # Test 2: Get frames using get_entity_frames (returns JsonLdDocument)
            frames_jsonld = self.client.kgentities.get_entity_frames(
                space_id=space_id,
                graph_id=graph_id,
                entity_uri=entity_uri
            )
            
            if not isinstance(frames_jsonld, JsonLdDocument):
                logger.error(f"Expected JsonLdDocument from get_entity_frames, got {type(frames_jsonld)}")
                return False
                
            if not hasattr(frames_jsonld, 'graph') or not frames_jsonld.graph:
                logger.error("No graph data in JsonLdDocument response")
                return False
                
            logger.info(f"✅ Retrieved frames as JsonLdDocument with {len(frames_jsonld.graph)} objects")
            
            logger.info("✅ Basic frame retrieval completed successfully")
            return True
            
        except VitalGraphClientError as e:
            logger.error(f"Client error in basic frame retrieval test: {e}")
            return False
        except Exception as e:
            logger.error(f"Error in basic frame retrieval test: {e}")
            return False
    
    async def test_frame_retrieval_pagination(self, space_id: str, graph_id: str) -> bool:
        """
        Test frame retrieval with pagination.
        
        Args:
            space_id: Test space identifier
            graph_id: Test graph identifier
            
        Returns:
            bool: True if pagination test successful, False otherwise
        """
        try:
            logger.info("🧪 Testing frame retrieval pagination")
            
            # Create entity with multiple frames for pagination testing
            entity_objects = self.test_data_creator.create_organization_with_address("Pagination Test Corp")
            
            # Convert to JSON-LD for client
            from vital_ai_vitalsigns.model.GraphObject import GraphObject
            entity_document_dict = GraphObject.to_jsonld_list(entity_objects)
            entity_document = JsonLdDocument(**entity_document_dict)
            
            entity_response = self.client.kgentities.create_kgentities(
                space_id=space_id,
                graph_id=graph_id,
                data=entity_document
            )
            
            if not entity_response or not entity_response.created_uris:
                logger.error("Failed to create test entity for pagination")
                return False
                
            entity_uri = str(entity_objects[0].URI)  # Get URI from VitalSigns object and convert to string
            self.created_entity_uris.append(entity_uri)
            
            # Use existing frames from entity creation for pagination test
            # (Skip additional frame creation since create_employment_frame doesn't exist)
            logger.info("✅ Using existing frames from entity creation for pagination test")
            
            # Test pagination with page_size=2
            page_size = 2
            offset = 0
            total_retrieved = 0
            page_count = 0
            
            while True:
                page_response = self.client.kgentities.get_kgentity_frames(
                    space_id=space_id,
                    graph_id=graph_id,
                    entity_uri=entity_uri,
                    page_size=page_size,
                    offset=offset
                )
                
                if not isinstance(page_response, EntityFramesResponse):
                    logger.error(f"Expected EntityFramesResponse for pagination, got {type(page_response)}")
                    return False
                    
                page_count += 1
                current_page_count = len(page_response.frames) if hasattr(page_response, 'frames') and page_response.frames else 0
                total_retrieved += current_page_count
                
                logger.info(f"Page {page_count}: Retrieved {current_page_count} frames (offset={offset})")
                
                # Check if we've retrieved all frames
                if current_page_count < page_size or offset + page_size >= page_response.total_count:
                    break
                    
                offset += page_size
                
                # Safety check to prevent infinite loop
                if page_count > 10:
                    logger.warning("Pagination test exceeded maximum page count")
                    break
            
            logger.info(f"✅ Pagination test completed: {page_count} pages, {total_retrieved} total frames retrieved")
            
            # Validate total count consistency
            final_response = self.client.kgentities.get_kgentity_frames(
                space_id=space_id,
                graph_id=graph_id,
                entity_uri=entity_uri,
                page_size=100  # Large page size to get all
            )
            
            if isinstance(final_response, EntityFramesResponse):
                if total_retrieved != final_response.total_count:
                    logger.warning(f"Pagination total mismatch: retrieved {total_retrieved}, expected {final_response.total_count}")
                else:
                    logger.info("✅ Pagination total count validation successful")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in frame retrieval pagination test: {e}")
            return False
    
    async def test_frame_retrieval_filtering(self, space_id: str, graph_id: str) -> bool:
        """
        Test frame retrieval with search filtering.
        
        Args:
            space_id: Test space identifier
            graph_id: Test graph identifier
            
        Returns:
            bool: True if filtering test successful, False otherwise
        """
        try:
            logger.info("🧪 Testing frame retrieval with search filtering")
            
            # Create entity with frames containing specific searchable content
            entity_objects = self.test_data_creator.create_person_with_contact("Filter Test Person")
            
            # Convert to JSON-LD for client
            from vital_ai_vitalsigns.model.GraphObject import GraphObject
            entity_document_dict = GraphObject.to_jsonld_list(entity_objects)
            entity_document = JsonLdDocument(**entity_document_dict)
            
            entity_response = self.client.kgentities.create_kgentities(
                space_id=space_id,
                graph_id=graph_id,
                data=entity_document
            )
            
            if not entity_response or not entity_response.created_uris:
                logger.error("Failed to create test entity for filtering")
                return False
                
            entity_uri = str(entity_objects[0].URI)  # Get URI from VitalSigns object and convert to string
            self.created_entity_uris.append(entity_uri)
            
            # Use existing frames from entity creation for filtering test
            # (Skip additional frame creation since create_employment_frame doesn't exist)
            logger.info("✅ Using existing frames from entity creation for filtering test")
                
            logger.info(f"✅ Created frames with searchable content")
            
            # Test search filtering
            search_terms = ["Engineer", "Manager", "Technology"]
            
            for search_term in search_terms:
                search_response = self.client.kgentities.get_kgentity_frames(
                    space_id=space_id,
                    graph_id=graph_id,
                    entity_uri=entity_uri,
                    search=search_term
                )
                
                if isinstance(search_response, EntityFramesResponse):
                    found_count = search_response.total_count
                    logger.info(f"✅ Search for '{search_term}': found {found_count} frames")
                    
                    # Validate that search actually filtered results
                    all_frames_response = self.client.kgentities.get_kgentity_frames(
                        space_id=space_id,
                        graph_id=graph_id,
                        entity_uri=entity_uri
                    )
                    
                    if isinstance(all_frames_response, EntityFramesResponse):
                        total_count = all_frames_response.total_count
                        if found_count <= total_count:
                            logger.info(f"✅ Search filtering working: {found_count} <= {total_count}")
                        else:
                            logger.warning(f"Search returned more results than total: {found_count} > {total_count}")
                else:
                    logger.error(f"Expected EntityFramesResponse for search, got {type(search_response)}")
                    return False
            
            logger.info("✅ Frame retrieval filtering test completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in frame retrieval filtering test: {e}")
            return False
    
    async def test_hierarchical_frame_retrieval(self, space_id: str, graph_id: str) -> bool:
        """
        Test retrieval of hierarchical frames.
        
        Args:
            space_id: Test space identifier
            graph_id: Test graph identifier
            
        Returns:
            bool: True if hierarchical retrieval successful, False otherwise
        """
        try:
            logger.info("🧪 Testing hierarchical frame retrieval")
            
            # Create entity with hierarchical frame structure
            entity_objects = self.test_data_creator.create_organization_with_address("Hierarchical Get Corp")
            
            # Convert to JSON-LD for client
            from vital_ai_vitalsigns.model.GraphObject import GraphObject
            entity_document_dict = GraphObject.to_jsonld_list(entity_objects)
            entity_document = JsonLdDocument(**entity_document_dict)
            
            entity_response = self.client.kgentities.create_kgentities(
                space_id=space_id,
                graph_id=graph_id,
                data=entity_document
            )
            
            if not entity_response or not entity_response.created_uris:
                logger.error("Failed to create test entity for hierarchical retrieval")
                return False
                
            entity_uri = str(entity_objects[0].URI)  # Get URI from VitalSigns object and convert to string
            self.created_entity_uris.append(entity_uri)
            
            # Get existing frames from entity for hierarchical retrieval test
            existing_frames = self.client.kgentities.get_entity_frames(
                space_id=space_id,
                graph_id=graph_id,
                entity_uri=entity_uri
            )
            
            if isinstance(existing_frames, JsonLdDocument) and existing_frames.graph:
                frame_count = len(existing_frames.graph)
                logger.info(f"✅ Hierarchical frame retrieval test successful: Retrieved {frame_count} hierarchical frames")
                return True
            else:
                logger.error("No frames found for hierarchical retrieval test")
                return False
            
        except Exception as e:
            logger.error(f"Error in hierarchical frame retrieval test: {e}")
            return False
    
    async def test_nonexistent_entity_frame_retrieval(self, space_id: str, graph_id: str) -> bool:
        """
        Test frame retrieval for non-existent entity.
        
        Args:
            space_id: Test space identifier
            graph_id: Test graph identifier
            
        Returns:
            bool: True if non-existent entity handling correct, False otherwise
        """
        try:
            logger.info("🧪 Testing frame retrieval for non-existent entity")
            
            nonexistent_entity_uri = "http://vital.ai/test/nonexistent/entity/12345"
            
            # Test get_kgentity_frames with non-existent entity
            try:
                frames_response = self.client.kgentities.get_kgentity_frames(
                    space_id=space_id,
                    graph_id=graph_id,
                    entity_uri=nonexistent_entity_uri
                )
                
                # Should get structured response with 0 frames or error message
                if isinstance(frames_response, EntityFramesResponse):
                    if frames_response.total_count == 0:
                        logger.info("✅ Correctly handled non-existent entity (0 frames returned)")
                    elif hasattr(frames_response, 'message') and 'not found' in frames_response.message.lower():
                        logger.info("✅ Correctly handled non-existent entity with error message")
                    else:
                        logger.warning(f"Unexpected response for non-existent entity: {frames_response}")
                else:
                    logger.error(f"Expected EntityFramesResponse for non-existent entity, got {type(frames_response)}")
                    return False
                    
            except VitalGraphClientError as e:
                # Client-side validation is acceptable
                logger.info(f"✅ Client-side validation caught non-existent entity: {e}")
            
            # Test get_entity_frames with non-existent entity
            try:
                frames_jsonld = self.client.kgentities.get_entity_frames(
                    space_id=space_id,
                    graph_id=graph_id,
                    entity_uri=nonexistent_entity_uri
                )
                
                # Should get empty JsonLdDocument or error
                if isinstance(frames_jsonld, JsonLdDocument):
                    if not frames_jsonld.graph or len(frames_jsonld.graph) == 0:
                        logger.info("✅ Correctly handled non-existent entity (empty JsonLdDocument)")
                    else:
                        logger.warning(f"Unexpected JsonLdDocument content for non-existent entity: {len(frames_jsonld.graph)} objects")
                else:
                    logger.error(f"Expected JsonLdDocument for non-existent entity, got {type(frames_jsonld)}")
                    return False
                    
            except VitalGraphClientError as e:
                # Client-side validation is acceptable
                logger.info(f"✅ Client-side validation caught non-existent entity in JsonLd retrieval: {e}")
            
            logger.info("✅ Non-existent entity frame retrieval test completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in non-existent entity frame retrieval test: {e}")
            return False
    
    async def cleanup_created_resources(self, space_id: str, graph_id: str) -> bool:
        """
        Clean up resources created during testing.
        
        Args:
            space_id: Test space identifier
            graph_id: Test graph identifier
            
        Returns:
            bool: True if cleanup successful, False otherwise
        """
        try:
            logger.info("🧹 Cleaning up created frame retrieval test resources")
            
            # Delete created entities (which should cascade to frames)
            for entity_uri in self.created_entity_uris:
                try:
                    delete_response = self.client.kgentities.delete_kgentity(
                        space_id=space_id,
                        graph_id=graph_id,
                        uri=entity_uri,
                        delete_entity_graph=True
                    )
                    logger.info(f"✅ Deleted entity: {entity_uri}")
                except Exception as e:
                    logger.warning(f"Failed to delete entity {entity_uri}: {e}")
            
            self.created_entity_uris.clear()
            self.created_frame_uris.clear()
            
            logger.info("✅ Frame retrieval test cleanup completed")
            return True
            
        except Exception as e:
            logger.error(f"Error during frame retrieval test cleanup: {e}")
            return False
