"""
Simple Apache Synapse-like Architecture Implementation
This is a basic implementation inspired by Apache Synapse ESB
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    FAULT = "fault"

@dataclass
class Message:
    """Represents a message in the ESB"""
    id: str
    type: MessageType
    headers: Dict[str, str]
    body: Any
    properties: Dict[str, Any]

class Mediator(ABC):
    """Abstract base class for all mediators"""
    
    @abstractmethod
    def mediate(self, message: Message) -> Message:
        """Process the message and return modified message"""
        pass

class LogMediator(Mediator):
    """Simple logging mediator"""
    
    def __init__(self, level: str = "INFO"):
        self.level = level
    
    def mediate(self, message: Message) -> Message:
        logger.info(f"LogMediator: Processing message {message.id}")
        logger.info(f"Message body: {message.body}")
        return message

class TransformMediator(Mediator):
    """Simple transformation mediator"""
    
    def __init__(self, transformation_rules: Dict[str, str]):
        self.transformation_rules = transformation_rules
    
    def mediate(self, message: Message) -> Message:
        logger.info(f"TransformMediator: Transforming message {message.id}")
        
        # Simple transformation example
        if isinstance(message.body, dict):
            for old_key, new_key in self.transformation_rules.items():
                if old_key in message.body:
                    message.body[new_key] = message.body.pop(old_key)
        
        return message

class Endpoint:
    """Represents an endpoint (service)"""
    
    def __init__(self, name: str, url: str, method: str = "GET"):
        self.name = name
        self.url = url
        self.method = method
    
    def invoke(self, message: Message) -> Message:
        logger.info(f"Endpoint {self.name}: Invoking {self.method} {self.url}")
        # Simulate service call
        response_message = Message(
            id=f"resp_{message.id}",
            type=MessageType.RESPONSE,
            headers={"Content-Type": "application/json"},
            body={"status": "success", "data": "processed"},
            properties={}
        )
        return response_message

class Proxy:
    """Represents a proxy service"""
    
    def __init__(self, name: str, target_endpoint: Endpoint):
        self.name = name
        self.target_endpoint = target_endpoint
        self.mediators: List[Mediator] = []
    
    def add_mediator(self, mediator: Mediator):
        self.mediators.append(mediator)
    
    def process(self, message: Message) -> Message:
        logger.info(f"Proxy {self.name}: Processing message {message.id}")
        
        # Apply mediators in sequence
        for mediator in self.mediators:
            message = mediator.mediate(message)
        
        # Invoke target endpoint
        response = self.target_endpoint.invoke(message)
        
        return response

class ESB:
    """Simple Enterprise Service Bus"""
    
    def __init__(self):
        self.proxies: Dict[str, Proxy] = {}
        self.endpoints: Dict[str, Endpoint] = {}
    
    def add_endpoint(self, endpoint: Endpoint):
        self.endpoints[endpoint.name] = endpoint
        logger.info(f"Added endpoint: {endpoint.name}")
    
    def add_proxy(self, proxy: Proxy):
        self.proxies[proxy.name] = proxy
        logger.info(f"Added proxy: {proxy.name}")
    
    def route_message(self, proxy_name: str, message: Message) -> Message:
        if proxy_name not in self.proxies:
            raise ValueError(f"Proxy {proxy_name} not found")
        
        return self.proxies[proxy_name].process(message)

# Example usage
def create_sample_esb():
    """Create a sample ESB configuration"""
    esb = ESB()
    
    # Create endpoints
    user_service = Endpoint("UserService", "http://localhost:8080/users", "GET")
    order_service = Endpoint("OrderService", "http://localhost:8081/orders", "POST")
    
    esb.add_endpoint(user_service)
    esb.add_endpoint(order_service)
    
    # Create proxies with mediators
    user_proxy = Proxy("UserProxy", user_service)
    user_proxy.add_mediator(LogMediator())
    user_proxy.add_mediator(TransformMediator({"user_id": "id"}))
    
    order_proxy = Proxy("OrderProxy", order_service)
    order_proxy.add_mediator(LogMediator())
    
    esb.add_proxy(user_proxy)
    esb.add_proxy(order_proxy)
    
    return esb

if __name__ == "__main__":
    # Create and test the ESB
    esb = create_sample_esb()
    
    # Test message
    test_message = Message(
        id="msg_001",
        type=MessageType.REQUEST,
        headers={"Content-Type": "application/json"},
        body={"user_id": "123", "action": "get_user"},
        properties={}
    )
    
    # Route through user proxy
    response = esb.route_message("UserProxy", test_message)
    print(f"Response: {response.body}") 