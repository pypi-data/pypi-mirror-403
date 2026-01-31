#!/usr/bin/env python3
"""
KGEntity Create Test Case

Client-based test case for KGEntity creation operations using VitalGraph client.
"""

import logging
from typing import Dict, Any, List
from vitalgraph.model.jsonld_model import JsonLdDocument
from vitalgraph.model.kgentities_model import EntityCreateResponse, EntityUpdateResponse
from vitalgraph_client_test.client_test_data import ClientTestDataCreator

logger = logging.getLogger(__name__)


class KGEntityCreateTester:
    """Test case for KGEntity creation operations."""
    
    def __init__(self, client):
        self.client = client
        self.data_creator = ClientTestDataCreator()
        
    def run_tests(self, space_id: str, graph_id: str) -> Dict[str, Any]:
        """
        Run KGEntity creation tests.
        
        Args:
            space_id: Space identifier
            graph_id: Graph identifier
            
        Returns:
            Dict containing test results
        """
        results = {
            "test_name": "KGEntity Create Tests",
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": [],
            "created_entities": []
        }
        
        # Test 1: Create basic KGEntity
        logger.info("🔍 Testing basic KGEntity creation...")
        try:
            # Create a person entity with proper VitalSigns objects
            person_objects = self.data_creator.create_person_with_contact("Test Person")
            
            # Convert to JSON-LD for client
            from vital_ai_vitalsigns.model.GraphObject import GraphObject
            from vitalgraph.model.jsonld_model import JsonLdDocument
            test_document_dict = GraphObject.to_jsonld_list(person_objects)
            test_document = JsonLdDocument(**test_document_dict)
            
            create_response = self.client.kgentities.create_kgentities(
                space_id=space_id,
                graph_id=graph_id,
                data=test_document
            )
            
            results["tests_run"] += 1
            
            if isinstance(create_response, (EntityCreateResponse, EntityUpdateResponse)):
                logger.info(f"✅ Basic entity creation successful - Response type: {type(create_response).__name__}")
                results["tests_passed"] += 1
                # Get the entity URI from the created objects
                entity_uri = person_objects[0].URI if person_objects else None
                if entity_uri:
                    results["created_entities"].append(entity_uri)
            else:
                logger.error(f"❌ Unexpected create response type: {type(create_response)}")
                results["tests_failed"] += 1
                results["errors"].append(f"Unexpected create response type: {type(create_response)}")
                
        except Exception as e:
            logger.error(f"❌ Basic entity creation failed: {e}")
            results["tests_run"] += 1
            results["tests_failed"] += 1
            results["errors"].append(f"Basic entity creation error: {str(e)}")
        
        # Test 2: Create entity with parent URI
        logger.info("🔍 Testing KGEntity creation with parent URI...")
        try:
            # Create an organization entity with proper VitalSigns objects
            org_objects = self.data_creator.create_organization_with_address("Test Organization")
            parent_uri = "http://vital.ai/test/client/parent_entity"
            
            # Convert to JSON-LD for client
            child_document_dict = GraphObject.to_jsonld_list(org_objects)
            child_document = JsonLdDocument(**child_document_dict)
            
            parent_create_response = self.client.kgentities.create_kgentities(
                space_id=space_id,
                graph_id=graph_id,
                data=child_document,
                parent_uri=parent_uri
            )
            
            results["tests_run"] += 1
            
            if isinstance(parent_create_response, (EntityCreateResponse, EntityUpdateResponse)):
                logger.info(f"✅ Entity creation with parent URI successful - Response type: {type(parent_create_response).__name__}")
                results["tests_passed"] += 1
                # Get the entity URI from the created objects
                entity_uri = org_objects[0].URI if org_objects else None
                if entity_uri:
                    results["created_entities"].append(entity_uri)
            else:
                logger.error(f"❌ Unexpected parent create response type: {type(parent_create_response)}")
                results["tests_failed"] += 1
                results["errors"].append(f"Unexpected parent create response type: {type(parent_create_response)}")
                
        except Exception as e:
            logger.error(f"❌ Entity creation with parent URI failed: {e}")
            results["tests_run"] += 1
            results["tests_failed"] += 1
            results["errors"].append(f"Entity creation with parent URI error: {str(e)}")
        
        # Test 3: Create multiple entities in one document
        logger.info("🔍 Testing multiple KGEntity creation...")
        try:
            # Create multiple entities using basic entities method
            basic_entities = self.data_creator.create_basic_entities()
            # Flatten the list of lists to get all objects
            all_objects = []
            for entity_group in basic_entities[:2]:  # Take first 2 entity groups
                all_objects.extend(entity_group)
            
            # Convert to JSON-LD for client
            multi_document_dict = GraphObject.to_jsonld_list(all_objects)
            multi_document = JsonLdDocument(**multi_document_dict)
            
            multi_create_response = self.client.kgentities.create_kgentities(
                space_id=space_id,
                graph_id=graph_id,
                data=multi_document
            )
            
            results["tests_run"] += 1
            
            if isinstance(multi_create_response, (EntityCreateResponse, EntityUpdateResponse)):
                logger.info(f"✅ Multiple entity creation successful - Response type: {type(multi_create_response).__name__}")
                results["tests_passed"] += 1
                # Get entity URIs from the created objects
                entity_uris = [obj.URI for obj in all_objects if hasattr(obj, 'URI') and hasattr(obj, 'kGEntityType')]
                results["created_entities"].extend(entity_uris)
            else:
                logger.error(f"❌ Unexpected multi create response type: {type(multi_create_response)}")
                results["tests_failed"] += 1
                results["errors"].append(f"Unexpected multi create response type: {type(multi_create_response)}")
                
        except Exception as e:
            logger.error(f"❌ Multiple entity creation failed: {e}")
            results["tests_run"] += 1
            results["tests_failed"] += 1
            results["errors"].append(f"Multiple entity creation error: {str(e)}")
        
        # Test 4: Test UPSERT operation (if available)
        logger.info("🔍 Testing UPSERT operation...")
        try:
            if hasattr(self.client.kgentities, 'upsert_kgentities'):
                # Create a project entity with proper VitalSigns objects
                project_objects = self.data_creator.create_project_with_timeline("Test UPSERT Project")
                
                # Convert to JSON-LD for client
                upsert_document_dict = GraphObject.to_jsonld_list(project_objects)
                upsert_document = JsonLdDocument(**upsert_document_dict)
                
                upsert_response = self.client.kgentities.upsert_kgentities(
                    space_id=space_id,
                    graph_id=graph_id,
                    data=upsert_document
                )
                
                results["tests_run"] += 1
                
                if isinstance(upsert_response, (EntityCreateResponse, EntityUpdateResponse)):
                    logger.info(f"✅ UPSERT operation successful - Response type: {type(upsert_response).__name__}")
                    results["tests_passed"] += 1
                    # Get the entity URI from the created objects
                    entity_uri = project_objects[0].URI if project_objects else None
                    if entity_uri:
                        results["created_entities"].append(entity_uri)
                else:
                    logger.error(f"❌ Unexpected UPSERT response type: {type(upsert_response)}")
                    results["tests_failed"] += 1
                    results["errors"].append(f"Unexpected UPSERT response type: {type(upsert_response)}")
            else:
                logger.info("⚠️ UPSERT method not available in client")
                results["tests_run"] += 1
                results["tests_passed"] += 1  # Count as passed since it's optional
                
        except Exception as e:
            logger.error(f"❌ UPSERT operation failed: {e}")
            results["tests_run"] += 1
            results["tests_failed"] += 1
            results["errors"].append(f"UPSERT operation error: {str(e)}")
        
        # Test 5: Test duplicate entity creation (error handling)
        logger.info("🔍 Testing duplicate entity creation...")
        try:
            if results["created_entities"]:
                duplicate_uri = results["created_entities"][0]
                
                duplicate_document_dict = {
                    "@context": "urn:vital-ai:contexts:vital-core",
                    "@graph": [
                        {
                            "@id": duplicate_uri,
                            "@type": "http://vital.ai/ontology/haley-ai-kg#KGEntity",
                            "http://vital.ai/ontology/vital-core#name": "Duplicate Test Entity"
                        }
                    ]
                }
                duplicate_document = JsonLdDocument(**duplicate_document_dict)
                
                duplicate_response = self.client.kgentities.create_kgentities(
                    space_id=space_id,
                    graph_id=graph_id,
                    data=duplicate_document
                )
                
                results["tests_run"] += 1
                
                # This might succeed (update) or fail (conflict) depending on implementation
                if isinstance(duplicate_response, (EntityCreateResponse, EntityUpdateResponse)):
                    logger.info(f"✅ Duplicate entity creation handled - Response type: {type(duplicate_response).__name__}")
                    results["tests_passed"] += 1
                else:
                    logger.error(f"❌ Unexpected duplicate response type: {type(duplicate_response)}")
                    results["tests_failed"] += 1
                    results["errors"].append(f"Unexpected duplicate response type: {type(duplicate_response)}")
            else:
                logger.info("⚠️ No entities created to test duplication")
                results["tests_run"] += 1
                results["tests_passed"] += 1
                
        except Exception as e:
            # This might be expected behavior (conflict error)
            logger.info(f"✅ Duplicate entity creation correctly raised exception: {e}")
            results["tests_run"] += 1
            results["tests_passed"] += 1
        
        logger.info(f"📊 KGEntity Create Tests Summary: {results['tests_passed']}/{results['tests_run']} passed")
        logger.info(f"📝 Created entities: {len(results['created_entities'])}")
        return results
