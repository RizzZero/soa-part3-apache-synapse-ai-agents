"""
Core Synapse MCP Server Implementation

This module contains the main server class that implements the Model Context Protocol
and provides access to Apache Synapse capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from mcp import ServerSession, StdioServerParameters
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    Resource,
    ListResourcesRequest,
    ListResourcesResult,
    ReadResourceRequest,
    ReadResourceResult,
)

from ..config import SynapseMCPConfig
from ..services.proxy_service import ProxyService
from ..transformers.message_transformer import MessageTransformer
from ..security.auth_manager import AuthManager
from ..monitoring.metrics import MetricsCollector

logger = logging.getLogger(__name__)


@dataclass
class SynapseService:
    """Represents a Synapse service configuration."""
    name: str
    type: str  # 'proxy', 'transformer', 'endpoint'
    config: Dict[str, Any]
    status: str = "active"


class SynapseMCPServer:
    """
    Main Synapse MCP Server that implements the Model Context Protocol
    and provides access to Apache Synapse capabilities.
    """
    
    def __init__(self, config: Optional[SynapseMCPConfig] = None):
        """Initialize the Synapse MCP Server."""
        self.config = config or SynapseMCPConfig()
        self.auth_manager = AuthManager(self.config.security)
        self.metrics = MetricsCollector()
        self.services: Dict[str, SynapseService] = {}
        self.transformers: Dict[str, MessageTransformer] = {}
        
        # Initialize MCP server
        self.mcp_server = ServerSession(
            StdioServerParameters(
                name="synapse-mcp-server",
                version="1.0.0"
            )
        )
        
        # Register MCP handlers
        self._register_handlers()
        
        # Initialize default services
        self._initialize_default_services()
    
    def _register_handlers(self):
        """Register MCP protocol handlers."""
        
        @self.mcp_server.list_tools()
        async def handle_list_tools(request: ListToolsRequest) -> ListToolsResult:
            """Handle list tools request."""
            try:
                tools = await self._get_available_tools()
                return ListToolsResult(tools=tools)
            except Exception as e:
                logger.error(f"Error listing tools: {e}")
                return ListToolsResult(tools=[])
        
        @self.mcp_server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool call request."""
            try:
                # Authenticate request
                if not await self.auth_manager.authenticate_request(request):
                    return CallToolResult(
                        content=[TextContent(type="text", text="Authentication failed")]
                    )
                
                # Process tool call
                result = await self._process_tool_call(request)
                return CallToolResult(content=[TextContent(type="text", text=result)])
                
            except Exception as e:
                logger.error(f"Error calling tool {request.name}: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")]
                )
        
        @self.mcp_server.list_resources()
        async def handle_list_resources(request: ListResourcesRequest) -> ListResourcesResult:
            """Handle list resources request."""
            try:
                resources = await self._get_available_resources()
                return ListResourcesResult(resources=resources)
            except Exception as e:
                logger.error(f"Error listing resources: {e}")
                return ListResourcesResult(resources=[])
        
        @self.mcp_server.read_resource()
        async def handle_read_resource(request: ReadResourceRequest) -> ReadResourceResult:
            """Handle read resource request."""
            try:
                content = await self._read_resource(request.uri)
                return ReadResourceResult(
                    contents=[TextContent(type="text", text=content)]
                )
            except Exception as e:
                logger.error(f"Error reading resource {request.uri}: {e}")
                return ReadResourceResult(
                    contents=[TextContent(type="text", text=f"Error: {str(e)}")]
                )
    
    async def _get_available_tools(self) -> List[Tool]:
        """Get list of available MCP tools."""
        tools = [
            Tool(
                name="create_proxy_service",
                description="Create a new proxy service in Synapse",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Service name"},
                        "target": {"type": "string", "description": "Target URL"},
                        "transforms": {"type": "array", "items": {"type": "string"}},
                        "security": {"type": "string", "description": "Security type"}
                    },
                    "required": ["name", "target"]
                }
            ),
            Tool(
                name="list_services",
                description="List all available Synapse services",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="transform_message",
                description="Transform a message using specified transformer",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "transformer": {"type": "string", "description": "Transformer name"},
                        "message": {"type": "string", "description": "Message to transform"},
                        "format": {"type": "string", "description": "Input format"}
                    },
                    "required": ["transformer", "message"]
                }
            ),
            Tool(
                name="route_message",
                description="Route a message based on rules",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Message to route"},
                        "rules": {"type": "object", "description": "Routing rules"}
                    },
                    "required": ["message", "rules"]
                }
            ),
            Tool(
                name="get_service_metrics",
                description="Get performance metrics for a service",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "service_name": {"type": "string", "description": "Service name"}
                    },
                    "required": ["service_name"]
                }
            )
        ]
        return tools
    
    async def _process_tool_call(self, request: CallToolRequest) -> str:
        """Process a tool call request."""
        tool_name = request.name
        arguments = request.arguments
        
        if tool_name == "create_proxy_service":
            return await self._create_proxy_service(arguments)
        elif tool_name == "list_services":
            return await self._list_services()
        elif tool_name == "transform_message":
            return await self._transform_message(arguments)
        elif tool_name == "route_message":
            return await self._route_message(arguments)
        elif tool_name == "get_service_metrics":
            return await self._get_service_metrics(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _create_proxy_service(self, arguments: Dict[str, Any]) -> str:
        """Create a new proxy service."""
        name = arguments.get("name")
        target = arguments.get("target")
        transforms = arguments.get("transforms", [])
        security = arguments.get("security", "none")
        
        if not name or not target:
            return "Error: name and target are required"
        
        # Create proxy service
        service = SynapseService(
            name=name,
            type="proxy",
            config={
                "target": target,
                "transforms": transforms,
                "security": security
            }
        )
        
        self.services[name] = service
        
        # Record metrics
        self.metrics.record_service_creation(name)
        
        return f"Successfully created proxy service '{name}' targeting {target}"
    
    async def _list_services(self) -> str:
        """List all available services."""
        if not self.services:
            return "No services configured"
        
        service_list = []
        for name, service in self.services.items():
            service_list.append(f"- {name} ({service.type}): {service.status}")
        
        return "Available services:\n" + "\n".join(service_list)
    
    async def _transform_message(self, arguments: Dict[str, Any]) -> str:
        """Transform a message using specified transformer."""
        transformer_name = arguments.get("transformer")
        message = arguments.get("message")
        format_type = arguments.get("format", "xml")
        
        if not transformer_name or not message:
            return "Error: transformer and message are required"
        
        if transformer_name not in self.transformers:
            return f"Error: transformer '{transformer_name}' not found"
        
        try:
            transformer = self.transformers[transformer_name]
            result = await transformer.transform(message, format_type)
            return f"Transformed message:\n{result}"
        except Exception as e:
            return f"Error transforming message: {str(e)}"
    
    async def _route_message(self, arguments: Dict[str, Any]) -> str:
        """Route a message based on rules."""
        message = arguments.get("message")
        rules = arguments.get("rules", {})
        
        if not message:
            return "Error: message is required"
        
        try:
            # Simple routing logic - can be enhanced
            route_result = f"Message routed based on rules: {rules}"
            return route_result
        except Exception as e:
            return f"Error routing message: {str(e)}"
    
    async def _get_service_metrics(self, arguments: Dict[str, Any]) -> str:
        """Get performance metrics for a service."""
        service_name = arguments.get("service_name")
        
        if not service_name:
            return "Error: service_name is required"
        
        if service_name not in self.services:
            return f"Error: service '{service_name}' not found"
        
        try:
            metrics = self.metrics.get_service_metrics(service_name)
            return f"Metrics for {service_name}:\n{metrics}"
        except Exception as e:
            return f"Error getting metrics: {str(e)}"
    
    async def _get_available_resources(self) -> List[Resource]:
        """Get list of available MCP resources."""
        resources = []
        
        # Add service configurations as resources
        for name, service in self.services.items():
            resources.append(
                Resource(
                    uri=f"synapse://services/{name}",
                    name=name,
                    description=f"Synapse service: {service.type}",
                    mimeType="application/json"
                )
            )
        
        return resources
    
    async def _read_resource(self, uri: str) -> str:
        """Read a resource by URI."""
        if uri.startswith("synapse://services/"):
            service_name = uri.split("/")[-1]
            if service_name in self.services:
                service = self.services[service_name]
                return f"Service: {service.name}\nType: {service.type}\nConfig: {service.config}"
            else:
                return f"Service '{service_name}' not found"
        else:
            return f"Unknown resource URI: {uri}"
    
    def _initialize_default_services(self):
        """Initialize default services and transformers."""
        # Initialize default transformers
        self.transformers["xml-to-json"] = MessageTransformer("xml-to-json")
        self.transformers["json-to-xml"] = MessageTransformer("json-to-xml")
        self.transformers["xslt"] = MessageTransformer("xslt")
    
    async def start(self):
        """Start the MCP server."""
        logger.info("Starting Synapse MCP Server...")
        await self.mcp_server.run()
    
    async def stop(self):
        """Stop the MCP server."""
        logger.info("Stopping Synapse MCP Server...")
        # Cleanup resources
        self.metrics.close()


async def main():
    """Main entry point for the Synapse MCP Server."""
    config = SynapseMCPConfig()
    server = SynapseMCPServer(config)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main()) 