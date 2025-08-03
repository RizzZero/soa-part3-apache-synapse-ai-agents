#!/usr/bin/env python3
"""
Basic Usage Example for Apache Synapse MCP Server

This example demonstrates how to use the Apache Synapse MCP server
to create proxy services, transform messages, and manage enterprise integration.
"""

import asyncio
import json
import logging
from pathlib import Path

# Add the src directory to the Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.server import SynapseMCPServer
from src.core.config import SynapseMCPConfig
from src.services.proxy_service import ProxyConfig, ProxyServiceManager
from src.transformers.message_transformer import MessageTransformer, TransformerConfig
from src.security.auth_manager import AuthManager
from src.monitoring.metrics import MetricsCollector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main example function."""
    logger.info("Starting Apache Synapse MCP Server Example")
    
    # Create configuration
    config = SynapseMCPConfig()
    config.security.enabled = False  # Disable security for this example
    config.monitoring.enabled = True
    
    # Initialize components
    auth_manager = AuthManager(config.security)
    metrics = MetricsCollector()
    
    # Create proxy service manager
    proxy_manager = ProxyServiceManager(auth_manager)
    
    # Create transformer registry
    from src.transformers.message_transformer import TransformerRegistry
    transformer_registry = TransformerRegistry()
    
    # Register transformers
    xml_to_json_config = TransformerConfig(
        name="xml-to-json",
        type="xml-to-json",
        config={}
    )
    xml_to_json_transformer = MessageTransformer("xml-to-json", xml_to_json_config)
    transformer_registry.register(xml_to_json_transformer)
    
    json_to_xml_config = TransformerConfig(
        name="json-to-xml",
        type="json-to-xml",
        config={}
    )
    json_to_xml_transformer = MessageTransformer("json-to-xml", json_to_xml_config)
    transformer_registry.register(json_to_xml_transformer)
    
    # Create proxy services
    logger.info("Creating proxy services...")
    
    # User service proxy
    user_service_config = ProxyConfig(
        name="user-service-proxy",
        target="http://user-service:8080",
        transforms=["xml-to-json"],
        security="none",
        rate_limit=100
    )
    user_service = await proxy_manager.add_service(user_service_config)
    
    # Order service proxy
    order_service_config = ProxyConfig(
        name="order-service-proxy",
        target="http://order-service:8080",
        transforms=["json-to-xml"],
        security="none",
        rate_limit=50
    )
    order_service = await proxy_manager.add_service(order_service_config)
    
    # Start all services
    await proxy_manager.start_all()
    
    # Example 1: Transform XML to JSON
    logger.info("\n=== Example 1: XML to JSON Transformation ===")
    xml_message = """
    <user>
        <id>123</id>
        <name>John Doe</name>
        <email>john.doe@example.com</email>
        <roles>
            <role>user</role>
            <role>admin</role>
        </roles>
    </user>
    """
    
    transformer = transformer_registry.get("xml-to-json")
    if transformer:
        result = await transformer.transform(xml_message)
        logger.info("XML Input:")
        logger.info(xml_message)
        logger.info("JSON Output:")
        logger.info(result)
    
    # Example 2: Transform JSON to XML
    logger.info("\n=== Example 2: JSON to XML Transformation ===")
    json_message = """
    {
        "order": {
            "id": "ORD-001",
            "customer": {
                "id": "CUST-123",
                "name": "Jane Smith"
            },
            "items": [
                {
                    "product_id": "PROD-001",
                    "quantity": 2,
                    "price": 29.99
                },
                {
                    "product_id": "PROD-002",
                    "quantity": 1,
                    "price": 49.99
                }
            ],
            "total": 109.97
        }
    }
    """
    
    transformer = transformer_registry.get("json-to-xml")
    if transformer:
        result = await transformer.transform(json_message)
        logger.info("JSON Input:")
        logger.info(json_message)
        logger.info("XML Output:")
        logger.info(result)
    
    # Example 3: Process request through proxy service
    logger.info("\n=== Example 3: Proxy Service Request Processing ===")
    
    # Simulate a request to the user service
    request_data = {
        "method": "POST",
        "path": "/api/users",
        "headers": {
            "Content-Type": "application/xml",
            "Accept": "application/json"
        },
        "body": xml_message,
        "query_params": {}
    }
    
    try:
        # Note: This would normally make an actual HTTP request
        # For this example, we'll just simulate the transformation
        logger.info("Processing request through user-service-proxy...")
        logger.info(f"Request method: {request_data['method']}")
        logger.info(f"Request path: {request_data['path']}")
        logger.info(f"Request headers: {request_data['headers']}")
        
        # Transform the request body
        if request_data['body'] and user_service_config.transforms:
            transformed_body = await transformer_registry.transform_with_chain(
                request_data['body'], 
                user_service_config.transforms, 
                "request"
            )
            logger.info("Transformed request body:")
            logger.info(transformed_body)
        
        # Record metrics
        metrics.record_request("user-service-proxy", "POST", 0.150, "200")
        
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        metrics.record_error("user-service-proxy", "request_error", str(e))
    
    # Example 4: Get service metrics
    logger.info("\n=== Example 4: Service Metrics ===")
    
    # Get metrics for user service
    user_metrics = metrics.get_service_metrics("user-service-proxy")
    logger.info("User Service Metrics:")
    logger.info(json.dumps(user_metrics, indent=2))
    
    # Get global metrics
    global_metrics = metrics.get_global_metrics()
    logger.info("Global Metrics:")
    logger.info(json.dumps(global_metrics, indent=2))
    
    # Example 5: List all services
    logger.info("\n=== Example 5: Service Listing ===")
    
    services = proxy_manager.list_services()
    logger.info("Available Services:")
    for service_info in services:
        logger.info(f"- {service_info['name']}: {service_info['config']['target']}")
    
    # Example 6: Health check
    logger.info("\n=== Example 6: Health Check ===")
    
    health_status = metrics.get_health_status()
    logger.info("Health Status:")
    logger.info(json.dumps(health_status, indent=2))
    
    # Example 7: Export metrics
    logger.info("\n=== Example 7: Export Metrics ===")
    
    # Export as JSON
    json_metrics = metrics.export_metrics("json")
    logger.info("Metrics (JSON):")
    logger.info(json_metrics[:500] + "..." if len(json_metrics) > 500 else json_metrics)
    
    # Export as Prometheus
    prometheus_metrics = metrics.export_metrics("prometheus")
    logger.info("Metrics (Prometheus):")
    logger.info(prometheus_metrics[:500] + "..." if len(prometheus_metrics) > 500 else prometheus_metrics)
    
    # Cleanup
    logger.info("\n=== Cleanup ===")
    await proxy_manager.stop_all()
    metrics.close()
    
    logger.info("Example completed successfully!")


if __name__ == "__main__":
    asyncio.run(main()) 