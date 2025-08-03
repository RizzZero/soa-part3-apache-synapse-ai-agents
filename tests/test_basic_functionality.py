#!/usr/bin/env python3
"""
Basic Functionality Tests for Apache Synapse MCP Server

This module contains basic tests to verify the core functionality
of the Apache Synapse MCP server.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch

# Add the src directory to the Python path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.config import SynapseMCPConfig, SecurityConfig
from src.transformers.message_transformer import MessageTransformer, TransformerConfig
from src.monitoring.metrics import MetricsCollector


class TestConfiguration:
    """Test configuration management."""
    
    def test_default_config(self):
        """Test default configuration creation."""
        config = SynapseMCPConfig()
        
        assert config.host == "localhost"
        assert config.port == 8080
        assert config.debug is False
        assert config.security.enabled is True
        assert config.monitoring.enabled is True
    
    def test_config_from_dict(self):
        """Test configuration creation from dictionary."""
        config_data = {
            "server": {
                "host": "0.0.0.0",
                "port": 9000,
                "debug": True
            },
            "security": {
                "enabled": False,
                "auth_type": "api_key"
            }
        }
        
        config = SynapseMCPConfig.from_dict(config_data)
        
        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.debug is True
        assert config.security.enabled is False
        assert config.security.auth_type == "api_key"
    
    def test_config_validation(self):
        """Test configuration validation."""
        config = SynapseMCPConfig()
        
        # Should not raise an exception for valid config
        assert config.validate() is True
        
        # Test invalid database type
        config.database.type = "invalid"
        with pytest.raises(ValueError, match="Invalid database type"):
            config.validate()


class TestMessageTransformer:
    """Test message transformation functionality."""
    
    @pytest.fixture
    def xml_to_json_transformer(self):
        """Create XML to JSON transformer."""
        config = TransformerConfig(
            name="xml-to-json",
            type="xml-to-json",
            config={}
        )
        return MessageTransformer("xml-to-json", config)
    
    @pytest.fixture
    def json_to_xml_transformer(self):
        """Create JSON to XML transformer."""
        config = TransformerConfig(
            name="json-to-xml",
            type="json-to-xml",
            config={}
        )
        return MessageTransformer("json-to-xml", config)
    
    @pytest.mark.asyncio
    async def test_xml_to_json_transformation(self, xml_to_json_transformer):
        """Test XML to JSON transformation."""
        xml_input = """
        <user>
            <id>123</id>
            <name>John Doe</name>
            <email>john.doe@example.com</email>
        </user>
        """
        
        result = await xml_to_json_transformer.transform(xml_input)
        
        # Parse the result to verify it's valid JSON
        json_data = json.loads(result)
        
        assert "user" in json_data
        assert json_data["user"]["id"] == "123"
        assert json_data["user"]["name"] == "John Doe"
        assert json_data["user"]["email"] == "john.doe@example.com"
    
    @pytest.mark.asyncio
    async def test_json_to_xml_transformation(self, json_to_xml_transformer):
        """Test JSON to XML transformation."""
        json_input = """
        {
            "order": {
                "id": "ORD-001",
                "customer": {
                    "id": "CUST-123",
                    "name": "Jane Smith"
                },
                "total": 100.50
            }
        }
        """
        
        result = await json_to_xml_transformer.transform(json_input)
        
        # Verify the result contains XML structure
        assert "<order>" in result
        assert "<id>ORD-001</id>" in result
        assert "<customer>" in result
        assert "<name>Jane Smith</name>" in result
    
    @pytest.mark.asyncio
    async def test_invalid_xml_input(self, xml_to_json_transformer):
        """Test handling of invalid XML input."""
        invalid_xml = "<user><id>123</id><name>John Doe</name>"
        
        with pytest.raises(ValueError, match="Failed to transform XML to JSON"):
            await xml_to_json_transformer.transform(invalid_xml)
    
    @pytest.mark.asyncio
    async def test_invalid_json_input(self, json_to_xml_transformer):
        """Test handling of invalid JSON input."""
        invalid_json = '{"order": {"id": "ORD-001", "customer": {}}'
        
        with pytest.raises(ValueError, match="Failed to transform JSON to XML"):
            await json_to_xml_transformer.transform(invalid_json)
    
    def test_transformer_stats(self, xml_to_json_transformer):
        """Test transformer statistics collection."""
        stats = xml_to_json_transformer.get_stats()
        
        assert stats["name"] == "xml-to-json"
        assert stats["type"] == "xml-to-json"
        assert "stats" in stats
        assert stats["stats"]["transformations"] == 0
        assert stats["stats"]["errors"] == 0


class TestMetricsCollector:
    """Test metrics collection functionality."""
    
    @pytest.fixture
    def metrics_collector(self):
        """Create metrics collector."""
        return MetricsCollector()
    
    def test_record_request(self, metrics_collector):
        """Test recording request metrics."""
        service_name = "test-service"
        
        metrics_collector.record_request(service_name, "GET", 0.150, "200")
        
        metrics = metrics_collector.get_service_metrics(service_name)
        
        assert metrics["service_name"] == service_name
        assert metrics["request_count"] == 1
        assert metrics["error_count"] == 0
        assert metrics["avg_response_time"] == 0.150
        assert metrics["min_response_time"] == 0.150
        assert metrics["max_response_time"] == 0.150
    
    def test_record_error(self, metrics_collector):
        """Test recording error metrics."""
        service_name = "test-service"
        
        metrics_collector.record_error(service_name, "timeout", "Request timeout")
        
        metrics = metrics_collector.get_service_metrics(service_name)
        
        assert metrics["service_name"] == service_name
        assert metrics["request_count"] == 0
        assert metrics["error_count"] == 1
    
    def test_record_service_creation(self, metrics_collector):
        """Test recording service creation."""
        service_name = "new-service"
        
        metrics_collector.record_service_creation(service_name)
        
        # Verify service exists in metrics
        metrics = metrics_collector.get_service_metrics(service_name)
        assert metrics["service_name"] == service_name
    
    def test_global_metrics(self, metrics_collector):
        """Test global metrics collection."""
        # Record some requests and errors
        metrics_collector.record_request("service1", "GET", 0.100, "200")
        metrics_collector.record_request("service2", "POST", 0.200, "201")
        metrics_collector.record_error("service1", "timeout", "Request timeout")
        
        global_metrics = metrics_collector.get_global_metrics()
        
        assert global_metrics["total_requests"] == 2
        assert global_metrics["total_errors"] == 1
        assert global_metrics["error_rate_percent"] == 50.0
        assert global_metrics["active_services"] == 2
    
    def test_health_status(self, metrics_collector):
        """Test health status generation."""
        # Record some health checks
        metrics_collector.record_health_check("service1", "healthy", {"uptime": 3600})
        metrics_collector.record_health_check("service2", "unhealthy", {"error": "Connection failed"})
        
        health_status = metrics_collector.get_health_status()
        
        assert health_status["status"] == "unhealthy"  # One service is unhealthy
        assert health_status["total_services"] == 2
        assert health_status["healthy_services"] == 1
    
    def test_export_metrics_json(self, metrics_collector):
        """Test metrics export in JSON format."""
        # Record some metrics
        metrics_collector.record_request("test-service", "GET", 0.100, "200")
        
        json_metrics = metrics_collector.export_metrics("json")
        
        # Parse JSON to verify it's valid
        data = json.loads(json_metrics)
        
        assert "global" in data
        assert "services" in data
        assert "health" in data
        assert data["global"]["total_requests"] == 1
    
    def test_export_metrics_prometheus(self, metrics_collector):
        """Test metrics export in Prometheus format."""
        # Record some metrics
        metrics_collector.record_request("test-service", "GET", 0.100, "200")
        
        prometheus_metrics = metrics_collector.export_metrics("prometheus")
        
        # Verify Prometheus format
        assert "synapse_mcp_requests_total" in prometheus_metrics
        assert "synapse_mcp_request_duration_seconds" in prometheus_metrics
    
    def test_reset_metrics(self, metrics_collector):
        """Test metrics reset functionality."""
        # Record some metrics
        metrics_collector.record_request("test-service", "GET", 0.100, "200")
        
        # Reset metrics for specific service
        metrics_collector.reset_metrics("test-service")
        
        metrics = metrics_collector.get_service_metrics("test-service")
        assert "error" in metrics  # Service should not exist after reset
        
        # Reset all metrics
        metrics_collector.reset_metrics()
        
        global_metrics = metrics_collector.get_global_metrics()
        assert global_metrics["total_requests"] == 0
        assert global_metrics["total_errors"] == 0


class TestIntegration:
    """Integration tests for the complete system."""
    
    @pytest.mark.asyncio
    async def test_transformer_chain(self):
        """Test transformer chain functionality."""
        from src.transformers.message_transformer import TransformerRegistry
        
        registry = TransformerRegistry()
        
        # Register transformers
        xml_to_json_config = TransformerConfig(
            name="xml-to-json",
            type="xml-to-json",
            config={}
        )
        xml_to_json_transformer = MessageTransformer("xml-to-json", xml_to_json_config)
        registry.register(xml_to_json_transformer)
        
        json_to_xml_config = TransformerConfig(
            name="json-to-xml",
            type="json-to-xml",
            config={}
        )
        json_to_xml_transformer = MessageTransformer("json-to-xml", json_to_xml_config)
        registry.register(json_to_xml_transformer)
        
        # Test transformation chain
        xml_input = """
        <user>
            <id>123</id>
            <name>John Doe</name>
        </user>
        """
        
        # Transform XML to JSON and back to XML
        result = await registry.transform_with_chain(
            xml_input, 
            ["xml-to-json", "json-to-xml"], 
            "request"
        )
        
        # Verify the result contains XML structure
        assert "<user>" in result
        assert "<id>123</id>" in result
        assert "<name>John Doe</name>" in result


if __name__ == "__main__":
    pytest.main([__file__]) 