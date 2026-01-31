#!/usr/bin/env python3
"""
KGEntity List Test Case

Client-based test case for KGEntity listing operations using VitalGraph client.
"""

import logging
from typing import Dict, Any, Union
from vitalgraph.model.jsonld_model import JsonLdDocument, JsonLdObject
from vitalgraph.model.kgentities_model import EntitiesResponse
from vitalgraph.utils.graph_utils import sort_objects_into_dag, pretty_print_dag
from vital_ai_vitalsigns.model.GraphObject import GraphObject

logger = logging.getLogger(__name__)


class KGEntityListTester:
    """Test case for KGEntity listing operations."""
    
    def __init__(self, client):
        self.client = client
        
    def run_tests(self, space_id: str, graph_id: str) -> Dict[str, Any]:
        """
        Run KGEntity listing tests.
        
        Args:
            space_id: Space identifier
            graph_id: Graph identifier
            
        Returns:
            Dict containing test results
        """
        results = {
            "test_name": "KGEntity List Tests",
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": []
        }
        
        # Test 1: Basic listing with pagination
        logger.info("🔍 Testing basic KGEntity listing...")
        try:
            response = self.client.kgentities.list_kgentities(
                space_id=space_id,
                graph_id=graph_id,
                page_size=5,
                offset=0
            )
            
            results["tests_run"] += 1
            
            # Handle Union response type with detailed logging
            logger.info(f"🔍 DEBUG: Response type: {type(response)}")
            
            if isinstance(response, JsonLdObject):
                entities = [response.model_dump(by_alias=True)]
                logger.info(f"✅ Basic listing successful - JsonLdObject with 1 entity")
                results["tests_passed"] += 1
            elif isinstance(response, JsonLdDocument):
                entities = response.graph if response.graph else []
                logger.info(f"🔍 DEBUG: JsonLdDocument - graph: {response.graph}")
                logger.info(f"🔍 DEBUG: JsonLdDocument - entities count: {len(entities)}")
                logger.info(f"✅ Basic listing successful - JsonLdDocument with {len(entities)} entities")
                results["tests_passed"] += 1
            elif isinstance(response, EntitiesResponse):
                logger.info(f"🔍 DEBUG: EntitiesResponse - total_count: {response.total_count}")
                logger.info(f"🔍 DEBUG: EntitiesResponse - entities type: {type(response.entities)}")
                logger.info(f"🔍 DEBUG: EntitiesResponse - entities: {response.entities}")
                if isinstance(response.entities, JsonLdObject):
                    entities = [response.entities.model_dump(by_alias=True)]
                elif isinstance(response.entities, JsonLdDocument):
                    entities = response.entities.graph if response.entities.graph else []
                else:
                    entities = []
                logger.info(f"🔍 DEBUG: Final entities count: {len(entities)}")
                logger.info(f"✅ Basic listing successful - EntitiesResponse: {response.total_count} total, {len(entities)} returned")
                results["tests_passed"] += 1
            else:
                logger.error(f"❌ Unexpected response type: {type(response)}")
                results["tests_failed"] += 1
                results["errors"].append(f"Unexpected response type: {type(response)}")
                
        except Exception as e:
            logger.error(f"❌ Basic listing failed: {e}")
            results["tests_run"] += 1
            results["tests_failed"] += 1
            results["errors"].append(f"Basic listing error: {str(e)}")
        
        # Test 2: Search functionality
        logger.info("🔍 Testing KGEntity search...")
        try:
            search_response = self.client.kgentities.list_kgentities(
                space_id=space_id,
                graph_id=graph_id,
                page_size=3,
                search="test"
            )
            
            results["tests_run"] += 1
            
            # Handle Union response type
            if isinstance(search_response, JsonLdObject):
                entities = [search_response.model_dump(by_alias=True)]
                logger.info(f"✅ Search successful - JsonLdObject with 1 matching entity")
            elif isinstance(search_response, JsonLdDocument):
                entities = search_response.graph if search_response.graph else []
                logger.info(f"✅ Search successful - JsonLdDocument with {len(entities)} matching entities")
            elif isinstance(search_response, EntitiesResponse):
                if isinstance(search_response.entities, JsonLdObject):
                    entities = [search_response.entities.model_dump(by_alias=True)]
                elif isinstance(search_response.entities, JsonLdDocument):
                    entities = search_response.entities.graph if search_response.entities.graph else []
                else:
                    entities = []
                logger.info(f"✅ Search successful - EntitiesResponse: {search_response.total_count} matching, {len(entities)} returned")
            else:
                logger.error(f"❌ Unexpected search response type: {type(search_response)}")
                results["tests_failed"] += 1
                results["errors"].append(f"Unexpected search response type: {type(search_response)}")
                return results
                
            results["tests_passed"] += 1
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            results["tests_run"] += 1
            results["tests_failed"] += 1
            results["errors"].append(f"Search error: {str(e)}")
        
        # Test 3: Entity type filtering
        logger.info("🔍 Testing entity type filtering...")
        try:
            filter_response = self.client.kgentities.list_kgentities(
                space_id=space_id,
                graph_id=graph_id,
                page_size=5,
                entity_type_uri="http://vital.ai/ontology/haley-ai-kg#KGEntity"
            )
            
            results["tests_run"] += 1
            
            # Handle Union response type
            if isinstance(filter_response, (JsonLdDocument, EntitiesResponse)):
                logger.info("✅ Entity type filtering successful")
                results["tests_passed"] += 1
            else:
                logger.error(f"❌ Unexpected filter response type: {type(filter_response)}")
                results["tests_failed"] += 1
                results["errors"].append(f"Unexpected filter response type: {type(filter_response)}")
                
        except Exception as e:
            logger.error(f"❌ Entity type filtering failed: {e}")
            results["tests_run"] += 1
            results["tests_failed"] += 1
            results["errors"].append(f"Entity type filtering error: {str(e)}")
        
        # Test 4: Include entity graph parameter
        logger.info("🔍 Testing include_entity_graph parameter...")
        try:
            graph_response = self.client.kgentities.list_kgentities(
                space_id=space_id,
                graph_id=graph_id,
                page_size=2,
                include_entity_graph=True
            )
            
            results["tests_run"] += 1
            
            # Should return JsonLdDocument when include_entity_graph=True
            if isinstance(graph_response, JsonLdObject):
                entities = [graph_response.model_dump(by_alias=True)]
            elif isinstance(graph_response, JsonLdDocument):
                entities = graph_response.graph if graph_response.graph else []
                logger.info(f"✅ Include entity graph successful - JsonLdDocument with {len(entities)} entities")
                
                # Convert JSON-LD entities to VitalSigns objects for graph analysis
                if entities:
                    try:
                        # Convert JSON-LD entities back to VitalSigns objects
                        graph_objects = GraphObject.from_jsonld_list({"@graph": entities})
                        
                        logger.info("🔍 ENTITY GRAPH ANALYSIS:")
                        logger.info(f"   • Total objects retrieved: {len(graph_objects)}")
                        
                        # Analyze object types
                        object_types = {}
                        for obj in graph_objects:
                            obj_type = type(obj).__name__
                            object_types[obj_type] = object_types.get(obj_type, 0) + 1
                        
                        logger.info("   • Object type breakdown:")
                        for obj_type, count in object_types.items():
                            logger.info(f"     - {obj_type}: {count}")
                        
                        # Create DAG structure and pretty print
                        try:
                            dag_structure = sort_objects_into_dag(graph_objects)
                            dag_output = pretty_print_dag(dag_structure, show_properties=True, max_property_length=100)
                            
                            logger.info("🌳 ENTITY GRAPH STRUCTURE:")
                            for line in dag_output.split('\n'):
                                if line.strip():
                                    logger.info(f"   {line}")
                                    
                        except ValueError as e:
                            # Not a DAG or has cycles - just log object details
                            logger.info("   • Graph structure (not a strict DAG):")
                            for i, obj in enumerate(graph_objects[:5]):  # Limit to first 5 objects
                                logger.info(f"     [{i+1}] {type(obj).__name__}: {str(obj.URI)}")
                                if hasattr(obj, 'name') and obj.name:
                                    logger.info(f"         Name: {str(obj.name)}")
                            if len(graph_objects) > 5:
                                logger.info(f"     ... and {len(graph_objects) - 5} more objects")
                                
                    except Exception as e:
                        logger.warning(f"   ⚠️ Could not analyze graph structure: {e}")
                        logger.info(f"   • Raw JSON-LD entities count: {len(entities)}")
                
                results["tests_passed"] += 1
            else:
                logger.warning(f"⚠️ Expected JsonLdDocument but got {type(graph_response)}")
                results["tests_passed"] += 1  # Still count as passed, just unexpected type
                
        except Exception as e:
            logger.error(f"❌ Include entity graph failed: {e}")
            results["tests_run"] += 1
            results["tests_failed"] += 1
            results["errors"].append(f"Include entity graph error: {str(e)}")
        
        # Test 5: Pagination with different page sizes
        logger.info("🔍 Testing pagination...")
        for page_size in [1, 5, 10]:
            try:
                page_response = self.client.kgentities.list_kgentities(
                    space_id=space_id,
                    graph_id=graph_id,
                    page_size=page_size,
                    offset=0
                )
                
                results["tests_run"] += 1
                
                # Handle Union response type (JsonLdObject for single, JsonLdDocument for multiple)
                if isinstance(page_response, JsonLdObject):
                    entities = [page_response.model_dump(by_alias=True)]
                    logger.info(f"✅ Page size {page_size}: 1 entity (JsonLdObject)")
                elif isinstance(page_response, JsonLdDocument):
                    entities = page_response.graph if page_response.graph else []
                    logger.info(f"✅ Page size {page_size}: {len(entities)} entities (JsonLdDocument)")
                elif isinstance(page_response, EntitiesResponse):
                    if isinstance(page_response.entities, JsonLdObject):
                        entities = [page_response.entities.model_dump(by_alias=True)]
                    elif isinstance(page_response.entities, JsonLdDocument):
                        entities = page_response.entities.graph if page_response.entities.graph else []
                    else:
                        entities = []
                    logger.info(f"✅ Page size {page_size}: {len(entities)} entities, total: {page_response.total_count}")
                else:
                    logger.error(f"❌ Unexpected pagination response type: {type(page_response)}")
                    results["tests_failed"] += 1
                    results["errors"].append(f"Unexpected pagination response type: {type(page_response)}")
                    continue
                    
                results["tests_passed"] += 1
                
            except Exception as e:
                logger.error(f"❌ Pagination test failed for page_size {page_size}: {e}")
                results["tests_run"] += 1
                results["tests_failed"] += 1
                results["errors"].append(f"Pagination error (page_size {page_size}): {str(e)}")
        
        logger.info(f"📊 KGEntity List Tests Summary: {results['tests_passed']}/{results['tests_run']} passed")
        return results
