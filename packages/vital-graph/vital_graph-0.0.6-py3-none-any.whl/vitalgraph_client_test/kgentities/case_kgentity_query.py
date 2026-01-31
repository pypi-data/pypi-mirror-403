#!/usr/bin/env python3
"""
KGEntity Query Test Case

Client-based test case for KGEntity query operations using VitalGraph client.
"""

import logging
from typing import Dict, Any
from vitalgraph.model.kgentities_model import (
    EntityQueryRequest, EntityQueryResponse, EntityQueryCriteria, QueryFilter
)

logger = logging.getLogger(__name__)


class KGEntityQueryTester:
    """Test case for KGEntity query operations."""
    
    def __init__(self, client):
        self.client = client
        
    def run_tests(self, space_id: str, graph_id: str) -> Dict[str, Any]:
        """
        Run KGEntity query tests.
        
        Args:
            space_id: Space identifier
            graph_id: Graph identifier
            
        Returns:
            Dict containing test results
        """
        results = {
            "test_name": "KGEntity Query Tests",
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": []
        }
        
        # Test 1: Basic entity query with search string
        logger.info("🔍 Testing basic entity query with search string...")
        try:
            query_criteria = EntityQueryCriteria(
                search_string="test",
                entity_type=None,
                frame_type=None
            )
            
            query_request = EntityQueryRequest(
                criteria=query_criteria,
                page_size=5,
                offset=0
            )
            
            query_response = self.client.kgentities.query_entities(
                space_id=space_id,
                graph_id=graph_id,
                query_request=query_request
            )
            
            results["tests_run"] += 1
            
            if isinstance(query_response, EntityQueryResponse):
                if hasattr(query_response, 'entity_uris'):
                    logger.info(f"✅ Basic query successful - Found {len(query_response.entity_uris)} entities")
                    for i, uri in enumerate(query_response.entity_uris[:3]):
                        logger.info(f"   - Entity {i+1}: {uri}")
                    results["tests_passed"] += 1
                else:
                    logger.error("❌ Query response missing entity_uris field")
                    results["tests_failed"] += 1
                    results["errors"].append("Query response missing entity_uris field")
            else:
                logger.error(f"❌ Unexpected query response type: {type(query_response)}")
                results["tests_failed"] += 1
                results["errors"].append(f"Unexpected query response type: {type(query_response)}")
                
        except Exception as e:
            logger.error(f"❌ Basic entity query failed: {e}")
            results["tests_run"] += 1
            results["tests_failed"] += 1
            results["errors"].append(f"Basic entity query error: {str(e)}")
        
        # Test 2: Query with entity type filter
        logger.info("🔍 Testing entity query with entity type filter...")
        try:
            type_criteria = EntityQueryCriteria(
                search_string=None,
                entity_type="http://vital.ai/ontology/haley-ai-kg#KGEntity",
                frame_type=None
            )
            
            type_request = EntityQueryRequest(
                criteria=type_criteria,
                page_size=10,
                offset=0
            )
            
            type_response = self.client.kgentities.query_entities(
                space_id=space_id,
                graph_id=graph_id,
                query_request=type_request
            )
            
            results["tests_run"] += 1
            
            if isinstance(type_response, EntityQueryResponse) and hasattr(type_response, 'entity_uris'):
                logger.info(f"✅ Entity type query successful - Found {len(type_response.entity_uris)} KGEntities")
                results["tests_passed"] += 1
            else:
                logger.error(f"❌ Entity type query failed - response type: {type(type_response)}")
                results["tests_failed"] += 1
                results["errors"].append(f"Entity type query failed - response type: {type(type_response)}")
                
        except Exception as e:
            logger.error(f"❌ Entity type query failed: {e}")
            results["tests_run"] += 1
            results["tests_failed"] += 1
            results["errors"].append(f"Entity type query error: {str(e)}")
        
        # Test 3: Query with QueryFilter (property-based filtering)
        logger.info("🔍 Testing QueryFilter functionality...")
        try:
            query_filter = QueryFilter(
                property_name="name",
                operator="contains",
                value="test"
            )
            
            filter_criteria = EntityQueryCriteria(
                filters=[query_filter]
            )
            
            filter_request = EntityQueryRequest(
                criteria=filter_criteria,
                page_size=5,
                offset=0
            )
            
            filter_response = self.client.kgentities.query_entities(
                space_id=space_id,
                graph_id=graph_id,
                query_request=filter_request
            )
            
            results["tests_run"] += 1
            
            if isinstance(filter_response, EntityQueryResponse) and hasattr(filter_response, 'entity_uris'):
                logger.info(f"✅ QueryFilter test successful - Found {len(filter_response.entity_uris)} filtered entities")
                results["tests_passed"] += 1
            else:
                logger.error(f"❌ QueryFilter test failed - response type: {type(filter_response)}")
                results["tests_failed"] += 1
                results["errors"].append(f"QueryFilter test failed - response type: {type(filter_response)}")
                
        except Exception as e:
            logger.error(f"❌ QueryFilter test failed: {e}")
            results["tests_run"] += 1
            results["tests_failed"] += 1
            results["errors"].append(f"QueryFilter test error: {str(e)}")
        
        # Test 4: Query with multiple filters
        logger.info("🔍 Testing multiple QueryFilters...")
        try:
            name_filter = QueryFilter(
                property_name="name",
                operator="exists",
                value=None
            )
            
            type_filter = QueryFilter(
                property_name="type",
                operator="equals",
                value="http://vital.ai/ontology/haley-ai-kg#KGEntity"
            )
            
            multi_filter_criteria = EntityQueryCriteria(
                filters=[name_filter, type_filter]
            )
            
            multi_filter_request = EntityQueryRequest(
                criteria=multi_filter_criteria,
                page_size=3,
                offset=0
            )
            
            multi_filter_response = self.client.kgentities.query_entities(
                space_id=space_id,
                graph_id=graph_id,
                query_request=multi_filter_request
            )
            
            results["tests_run"] += 1
            
            if isinstance(multi_filter_response, EntityQueryResponse) and hasattr(multi_filter_response, 'entity_uris'):
                entity_count = len(multi_filter_response.entity_uris)
                if entity_count > 0:
                    logger.info(f"✅ Multiple QueryFilters test successful - Found {entity_count} entities")
                    results["tests_passed"] += 1
                else:
                    logger.error(f"❌ Multiple QueryFilters test failed - Expected to find entities but found {entity_count}")
                    results["tests_failed"] += 1
                    results["errors"].append(f"Multiple QueryFilters test failed - Expected entities but found {entity_count}")
            else:
                logger.error(f"❌ Multiple QueryFilters test failed - response type: {type(multi_filter_response)}")
                results["tests_failed"] += 1
                results["errors"].append(f"Multiple QueryFilters test failed - response type: {type(multi_filter_response)}")
                
        except Exception as e:
            logger.error(f"❌ Multiple QueryFilters test failed: {e}")
            results["tests_run"] += 1
            results["tests_failed"] += 1
            results["errors"].append(f"Multiple QueryFilters test error: {str(e)}")
        
        # Test 5: Query with pagination
        logger.info("🔍 Testing query pagination...")
        try:
            page_criteria = EntityQueryCriteria(
                search_string=None,
                entity_type="http://vital.ai/ontology/haley-ai-kg#KGEntity"
            )
            
            # First page
            page1_request = EntityQueryRequest(
                criteria=page_criteria,
                page_size=2,
                offset=0
            )
            
            page1_response = self.client.kgentities.query_entities(
                space_id=space_id,
                graph_id=graph_id,
                query_request=page1_request
            )
            
            # Second page
            page2_request = EntityQueryRequest(
                criteria=page_criteria,
                page_size=2,
                offset=2
            )
            
            page2_response = self.client.kgentities.query_entities(
                space_id=space_id,
                graph_id=graph_id,
                query_request=page2_request
            )
            
            results["tests_run"] += 1
            
            if (isinstance(page1_response, EntityQueryResponse) and hasattr(page1_response, 'entity_uris') and
                isinstance(page2_response, EntityQueryResponse) and hasattr(page2_response, 'entity_uris')):
                
                page1_count = len(page1_response.entity_uris)
                page2_count = len(page2_response.entity_uris)
                
                logger.info(f"✅ Query pagination successful - Page 1: {page1_count}, Page 2: {page2_count}")
                results["tests_passed"] += 1
            else:
                logger.error("❌ Query pagination failed - invalid response types")
                results["tests_failed"] += 1
                results["errors"].append("Query pagination failed - invalid response types")
                
        except Exception as e:
            logger.error(f"❌ Query pagination failed: {e}")
            results["tests_run"] += 1
            results["tests_failed"] += 1
            results["errors"].append(f"Query pagination error: {str(e)}")
        
        logger.info(f"📊 KGEntity Query Tests Summary: {results['tests_passed']}/{results['tests_run']} passed")
        return results
