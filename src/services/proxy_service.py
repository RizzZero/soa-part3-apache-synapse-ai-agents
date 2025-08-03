"""
Proxy Service Implementation

This module provides proxy service functionality for Apache Synapse MCP,
handling service proxying, message mediation, and routing.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from urllib.parse import urlparse
import aiohttp
import json
import xml.etree.ElementTree as ET

from ..transformers.message_transformer import MessageTransformer
from ..security.auth_manager import AuthManager

logger = logging.getLogger(__name__)


@dataclass
class ProxyConfig:
    """Configuration for a proxy service."""
    name: str
    target: str
    transforms: List[str] = None
    security: str = "none"
    rate_limit: int = 100
    timeout: int = 30
    retry_count: int = 3
    headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.transforms is None:
            self.transforms = []
        if self.headers is None:
            self.headers = {}


class ProxyService:
    """
    Proxy service that acts as an intermediary between clients and backend services.
    Handles message transformation, routing, and mediation.
    """
    
    def __init__(self, config: ProxyConfig, auth_manager: AuthManager):
        """Initialize the proxy service."""
        self.config = config
        self.auth_manager = auth_manager
        self.transformers: Dict[str, MessageTransformer] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.stats = {
            "requests": 0,
            "errors": 0,
            "avg_response_time": 0.0
        }
        
        # Validate target URL
        self._validate_target()
    
    def _validate_target(self):
        """Validate the target URL."""
        try:
            parsed = urlparse(self.config.target)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid target URL")
        except Exception as e:
            raise ValueError(f"Invalid target URL '{self.config.target}': {e}")
    
    async def start(self):
        """Start the proxy service."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        
        logger.info(f"Started proxy service '{self.config.name}' targeting {self.config.target}")
    
    async def stop(self):
        """Stop the proxy service."""
        if self.session:
            await self.session.close()
            self.session = None
        
        logger.info(f"Stopped proxy service '{self.config.name}'")
    
    def add_transformer(self, name: str, transformer: MessageTransformer):
        """Add a message transformer to the proxy service."""
        self.transformers[name] = transformer
        logger.debug(f"Added transformer '{name}' to proxy service '{self.config.name}'")
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming request through the proxy service.
        
        Args:
            request_data: Dictionary containing request information
            
        Returns:
            Dictionary containing response information
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Extract request components
            method = request_data.get("method", "GET")
            path = request_data.get("path", "/")
            headers = request_data.get("headers", {})
            body = request_data.get("body")
            query_params = request_data.get("query_params", {})
            
            # Apply security
            if self.config.security != "none":
                headers = await self._apply_security(headers)
            
            # Transform request if needed
            if body and self.config.transforms:
                body = await self._transform_request(body)
            
            # Make request to target service
            response = await self._make_request(
                method, path, headers, body, query_params
            )
            
            # Transform response if needed
            if response.get("body") and self.config.transforms:
                response["body"] = await self._transform_response(response["body"])
            
            # Update statistics
            self._update_stats(start_time, success=True)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing request in proxy '{self.config.name}': {e}")
            self._update_stats(start_time, success=False)
            raise
    
    async def _apply_security(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Apply security measures to the request."""
        if self.config.security == "jwt":
            token = await self.auth_manager.get_jwt_token()
            headers["Authorization"] = f"Bearer {token}"
        elif self.config.security == "oauth2":
            token = await self.auth_manager.get_oauth2_token()
            headers["Authorization"] = f"Bearer {token}"
        elif self.config.security == "api_key":
            api_key = await self.auth_manager.get_api_key()
            headers[self.auth_manager.config.api_key_header] = api_key
        
        return headers
    
    async def _transform_request(self, body: str) -> str:
        """Transform the request body using configured transformers."""
        transformed_body = body
        
        for transform_name in self.config.transforms:
            if transform_name in self.transformers:
                transformer = self.transformers[transform_name]
                transformed_body = await transformer.transform(transformed_body, "request")
            else:
                logger.warning(f"Transformer '{transform_name}' not found for proxy '{self.config.name}'")
        
        return transformed_body
    
    async def _transform_response(self, body: str) -> str:
        """Transform the response body using configured transformers."""
        transformed_body = body
        
        for transform_name in reversed(self.config.transforms):
            if transform_name in self.transformers:
                transformer = self.transformers[transform_name]
                transformed_body = await transformer.transform(transformed_body, "response")
            else:
                logger.warning(f"Transformer '{transform_name}' not found for proxy '{self.config.name}'")
        
        return transformed_body
    
    async def _make_request(
        self, 
        method: str, 
        path: str, 
        headers: Dict[str, str], 
        body: Optional[str], 
        query_params: Dict[str, str]
    ) -> Dict[str, Any]:
        """Make HTTP request to the target service."""
        if not self.session:
            raise RuntimeError("Proxy service not started")
        
        # Construct full URL
        url = f"{self.config.target.rstrip('/')}/{path.lstrip('/')}"
        
        # Add query parameters
        if query_params:
            query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
            url = f"{url}?{query_string}"
        
        # Prepare request data
        request_kwargs = {
            "method": method,
            "url": url,
            "headers": headers
        }
        
        if body:
            request_kwargs["data"] = body
        
        # Make request with retries
        for attempt in range(self.config.retry_count):
            try:
                async with self.session.request(**request_kwargs) as response:
                    response_body = await response.text()
                    
                    return {
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "body": response_body,
                        "url": str(response.url)
                    }
                    
            except asyncio.TimeoutError:
                if attempt == self.config.retry_count - 1:
                    raise
                logger.warning(f"Request timeout, retrying... (attempt {attempt + 1})")
                await asyncio.sleep(1)
                
            except Exception as e:
                if attempt == self.config.retry_count - 1:
                    raise
                logger.warning(f"Request failed, retrying... (attempt {attempt + 1}): {e}")
                await asyncio.sleep(1)
    
    def _update_stats(self, start_time: float, success: bool):
        """Update service statistics."""
        self.stats["requests"] += 1
        
        if not success:
            self.stats["errors"] += 1
        
        # Calculate average response time
        response_time = asyncio.get_event_loop().time() - start_time
        current_avg = self.stats["avg_response_time"]
        request_count = self.stats["requests"]
        
        self.stats["avg_response_time"] = (
            (current_avg * (request_count - 1) + response_time) / request_count
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "name": self.config.name,
            "target": self.config.target,
            "status": "active" if self.session else "stopped",
            "stats": self.stats.copy(),
            "config": {
                "transforms": self.config.transforms,
                "security": self.config.security,
                "rate_limit": self.config.rate_limit,
                "timeout": self.config.timeout
            }
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the proxy service."""
        try:
            # Basic health check - could be enhanced
            return {
                "status": "healthy",
                "service": self.config.name,
                "target": self.config.target,
                "session_active": self.session is not None
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": self.config.name,
                "error": str(e)
            }


class ProxyServiceManager:
    """
    Manager for multiple proxy services.
    Handles service lifecycle and coordination.
    """
    
    def __init__(self, auth_manager: AuthManager):
        """Initialize the proxy service manager."""
        self.auth_manager = auth_manager
        self.services: Dict[str, ProxyService] = {}
        self.running = False
    
    async def add_service(self, config: ProxyConfig) -> ProxyService:
        """Add a new proxy service."""
        if config.name in self.services:
            raise ValueError(f"Proxy service '{config.name}' already exists")
        
        service = ProxyService(config, self.auth_manager)
        self.services[config.name] = service
        
        if self.running:
            await service.start()
        
        logger.info(f"Added proxy service '{config.name}'")
        return service
    
    async def remove_service(self, name: str):
        """Remove a proxy service."""
        if name not in self.services:
            raise ValueError(f"Proxy service '{name}' not found")
        
        service = self.services[name]
        await service.stop()
        del self.services[name]
        
        logger.info(f"Removed proxy service '{name}'")
    
    async def start_all(self):
        """Start all proxy services."""
        self.running = True
        for service in self.services.values():
            await service.start()
        
        logger.info(f"Started {len(self.services)} proxy services")
    
    async def stop_all(self):
        """Stop all proxy services."""
        self.running = False
        for service in self.services.values():
            await service.stop()
        
        logger.info(f"Stopped {len(self.services)} proxy services")
    
    def get_service(self, name: str) -> Optional[ProxyService]:
        """Get a proxy service by name."""
        return self.services.get(name)
    
    def list_services(self) -> List[Dict[str, Any]]:
        """List all proxy services with their status."""
        return [
            {
                "name": name,
                "config": service.config.__dict__,
                "stats": service.get_stats()
            }
            for name, service in self.services.items()
        ]
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Perform health check on all services."""
        results = {}
        for name, service in self.services.items():
            results[name] = service.health_check()
        
        return results 