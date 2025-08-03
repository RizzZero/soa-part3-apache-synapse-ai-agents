"""
AI Agents Implementation
Two AI agents that can interact with each other and MCP servers
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid
from mcp_servers import MCPRequest, MCPServerManager, UserManagementMCPServer, OrderProcessingMCPServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AgentMessage:
    """Message between agents"""
    id: str
    sender: str
    receiver: str
    content: Dict[str, Any]
    timestamp: datetime
    message_type: str = "communication"

class BaseAgent:
    """Base class for AI agents"""
    
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.agent_id = str(uuid.uuid4())
        self.memory: List[AgentMessage] = []
        self.conversation_history: List[Dict[str, Any]] = []
        self.is_active = False
    
    async def start(self):
        """Start the agent"""
        self.is_active = True
        logger.info(f"Agent {self.name} ({self.role}) started with ID: {self.agent_id}")
    
    async def stop(self):
        """Stop the agent"""
        self.is_active = False
        logger.info(f"Agent {self.name} stopped")
    
    def add_to_memory(self, message: AgentMessage):
        """Add message to agent's memory"""
        self.memory.append(message)
        self.conversation_history.append({
            "timestamp": message.timestamp.isoformat(),
            "sender": message.sender,
            "receiver": message.receiver,
            "content": message.content,
            "type": message.message_type
        })
    
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process incoming message - to be implemented by subclasses"""
        raise NotImplementedError
    
    async def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Agent's thinking process - to be implemented by subclasses"""
        raise NotImplementedError

class UserServiceAgent(BaseAgent):
    """AI Agent responsible for user service operations"""
    
    def __init__(self, name: str = "UserServiceAgent"):
        super().__init__(name, "User Service Manager")
        self.user_operations = [
            "get_user", "list_users", "create_user", "update_user"
        ]
        self.expertise = "User management, authentication, profile management"
    
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process incoming message"""
        self.add_to_memory(message)
        
        # Analyze the message content
        content = message.content
        operation = content.get("operation")
        data = content.get("data", {})
        
        # Think about the request
        thoughts = await self.think({
            "operation": operation,
            "data": data,
            "sender": message.sender,
            "context": "user_service_request"
        })
        
        # Generate response based on operation
        if operation == "get_user_info":
            response_content = {
                "operation": "user_info_response",
                "data": {
                    "user_id": data.get("user_id"),
                    "user_info": {
                        "name": "John Doe",
                        "email": "john@example.com",
                        "status": "active"
                    },
                    "message": "User information retrieved successfully"
                },
                "thoughts": thoughts
            }
        elif operation == "validate_user":
            response_content = {
                "operation": "user_validation_response",
                "data": {
                    "user_id": data.get("user_id"),
                    "is_valid": True,
                    "permissions": ["read", "write", "order"],
                    "message": "User validation successful"
                },
                "thoughts": thoughts
            }
        elif operation == "create_user_profile":
            response_content = {
                "operation": "user_creation_response",
                "data": {
                    "user_id": f"user_{uuid.uuid4().hex[:8]}",
                    "profile_created": True,
                    "message": "User profile created successfully"
                },
                "thoughts": thoughts
            }
        else:
            response_content = {
                "operation": "unknown_operation",
                "data": {
                    "error": f"Unknown operation: {operation}",
                    "available_operations": self.user_operations
                },
                "thoughts": thoughts
            }
        
        # Create response message
        response = AgentMessage(
            id=str(uuid.uuid4()),
            sender=self.name,
            receiver=message.sender,
            content=response_content,
            timestamp=datetime.now(),
            message_type="response"
        )
        
        return response
    
    async def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Agent's thinking process"""
        operation = context.get("operation")
        data = context.get("data", {})
        
        thoughts = {
            "analysis": f"Analyzing {operation} request",
            "considerations": [],
            "recommendations": [],
            "confidence": 0.9
        }
        
        if operation == "get_user_info":
            thoughts["considerations"].append("Verify user exists in system")
            thoughts["considerations"].append("Check user permissions")
            thoughts["recommendations"].append("Return user profile data")
        
        elif operation == "validate_user":
            thoughts["considerations"].append("Validate user credentials")
            thoughts["considerations"].append("Check account status")
            thoughts["recommendations"].append("Return validation result with permissions")
        
        elif operation == "create_user_profile":
            thoughts["considerations"].append("Generate unique user ID")
            thoughts["considerations"].append("Validate input data")
            thoughts["recommendations"].append("Create new user profile")
        
        return thoughts

class OrderServiceAgent(BaseAgent):
    """AI Agent responsible for order service operations"""
    
    def __init__(self, name: str = "OrderServiceAgent"):
        super().__init__(name, "Order Service Manager")
        self.order_operations = [
            "get_order", "list_orders", "create_order", "update_order_status"
        ]
        self.expertise = "Order processing, inventory management, payment processing"
    
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process incoming message"""
        self.add_to_memory(message)
        
        # Analyze the message content
        content = message.content
        operation = content.get("operation")
        data = content.get("data", {})
        
        # Think about the request
        thoughts = await self.think({
            "operation": operation,
            "data": data,
            "sender": message.sender,
            "context": "order_service_request"
        })
        
        # Generate response based on operation
        if operation == "get_order_info":
            response_content = {
                "operation": "order_info_response",
                "data": {
                    "order_id": data.get("order_id"),
                    "order_info": {
                        "items": ["item1", "item2"],
                        "total": 150.00,
                        "status": "pending",
                        "user_id": data.get("user_id")
                    },
                    "message": "Order information retrieved successfully"
                },
                "thoughts": thoughts
            }
        elif operation == "create_order":
            response_content = {
                "operation": "order_creation_response",
                "data": {
                    "order_id": f"order_{uuid.uuid4().hex[:8]}",
                    "items": data.get("items", []),
                    "total": 200.00,
                    "status": "pending",
                    "message": "Order created successfully"
                },
                "thoughts": thoughts
            }
        elif operation == "validate_order":
            response_content = {
                "operation": "order_validation_response",
                "data": {
                    "order_id": data.get("order_id"),
                    "is_valid": True,
                    "inventory_check": "passed",
                    "payment_status": "pending",
                    "message": "Order validation successful"
                },
                "thoughts": thoughts
            }
        elif operation == "process_payment":
            response_content = {
                "operation": "payment_processing_response",
                "data": {
                    "order_id": data.get("order_id"),
                    "payment_id": f"pay_{uuid.uuid4().hex[:8]}",
                    "amount": data.get("amount"),
                    "status": "completed",
                    "message": "Payment processed successfully"
                },
                "thoughts": thoughts
            }
        else:
            response_content = {
                "operation": "unknown_operation",
                "data": {
                    "error": f"Unknown operation: {operation}",
                    "available_operations": self.order_operations
                },
                "thoughts": thoughts
            }
        
        # Create response message
        response = AgentMessage(
            id=str(uuid.uuid4()),
            sender=self.name,
            receiver=message.sender,
            content=response_content,
            timestamp=datetime.now(),
            message_type="response"
        )
        
        return response
    
    async def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Agent's thinking process"""
        operation = context.get("operation")
        data = context.get("data", {})
        
        thoughts = {
            "analysis": f"Analyzing {operation} request",
            "considerations": [],
            "recommendations": [],
            "confidence": 0.9
        }
        
        if operation == "get_order_info":
            thoughts["considerations"].append("Verify order exists")
            thoughts["considerations"].append("Check order status")
            thoughts["recommendations"].append("Return order details")
        
        elif operation == "create_order":
            thoughts["considerations"].append("Validate items in inventory")
            thoughts["considerations"].append("Calculate total price")
            thoughts["recommendations"].append("Create new order record")
        
        elif operation == "validate_order":
            thoughts["considerations"].append("Check item availability")
            thoughts["considerations"].append("Verify pricing")
            thoughts["recommendations"].append("Validate order feasibility")
        
        elif operation == "process_payment":
            thoughts["considerations"].append("Verify payment method")
            thoughts["considerations"].append("Check payment amount")
            thoughts["recommendations"].append("Process payment and update order")
        
        return thoughts

class AgentOrchestrator:
    """Orchestrates communication between agents and MCP servers"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.mcp_manager = MCPServerManager()
        self.scenario_log: List[Dict[str, Any]] = []
    
    def add_agent(self, agent: BaseAgent):
        """Add an agent to the orchestrator"""
        self.agents[agent.name] = agent
        logger.info(f"Added agent: {agent.name}")
    
    async def start_all(self):
        """Start all agents and MCP servers"""
        # Start MCP servers
        user_server = UserManagementMCPServer()
        order_server = OrderProcessingMCPServer()
        
        self.mcp_manager.add_server(user_server)
        self.mcp_manager.add_server(order_server)
        await self.mcp_manager.start_all()
        
        # Start agents
        for agent in self.agents.values():
            await agent.start()
        
        logger.info("All agents and servers started")
    
    async def stop_all(self):
        """Stop all agents and MCP servers"""
        for agent in self.agents.values():
            await agent.stop()
        
        await self.mcp_manager.stop_all()
        logger.info("All agents and servers stopped")
    
    async def send_message(self, sender: str, receiver: str, content: Dict[str, Any]) -> AgentMessage:
        """Send message between agents"""
        message = AgentMessage(
            id=str(uuid.uuid4()),
            sender=sender,
            receiver=receiver,
            content=content,
            timestamp=datetime.now()
        )
        
        if receiver in self.agents:
            response = await self.agents[receiver].process_message(message)
            self.scenario_log.append({
                "timestamp": message.timestamp.isoformat(),
                "sender": sender,
                "receiver": receiver,
                "message": content,
                "response": response.content if response else None
            })
            return response
        else:
            logger.error(f"Agent {receiver} not found")
            return None
    
    async def execute_scenario(self, scenario_name: str):
        """Execute a predefined scenario"""
        logger.info(f"Executing scenario: {scenario_name}")
        
        if scenario_name == "user_order_integration":
            await self._execute_user_order_integration()
        elif scenario_name == "payment_processing":
            await self._execute_payment_processing()
        else:
            logger.error(f"Unknown scenario: {scenario_name}")
    
    async def _execute_user_order_integration(self):
        """Execute user-order integration scenario"""
        logger.info("Starting User-Order Integration Scenario")
        
        # Step 1: User Service Agent validates user
        user_validation_msg = {
            "operation": "validate_user",
            "data": {"user_id": "user1"},
            "context": "order_creation"
        }
        
        response1 = await self.send_message(
            "OrderServiceAgent", 
            "UserServiceAgent", 
            user_validation_msg
        )
        
        if response1 and response1.content.get("data", {}).get("is_valid"):
            # Step 2: Order Service Agent creates order
            order_creation_msg = {
                "operation": "create_order",
                "data": {
                    "user_id": "user1",
                    "items": ["item1", "item2"],
                    "total": 150.00
                },
                "context": "user_validated"
            }
            
            response2 = await self.send_message(
                "UserServiceAgent",
                "OrderServiceAgent",
                order_creation_msg
            )
            
            # Step 3: Order Service Agent processes payment
            if response2:
                payment_msg = {
                    "operation": "process_payment",
                    "data": {
                        "order_id": response2.content.get("data", {}).get("order_id"),
                        "amount": 150.00,
                        "payment_method": "credit_card"
                    },
                    "context": "order_created"
                }
                
                response3 = await self.send_message(
                    "UserServiceAgent",
                    "OrderServiceAgent",
                    payment_msg
                )
                
                logger.info("User-Order Integration Scenario completed successfully")
        
        else:
            logger.error("User validation failed in scenario")
    
    async def _execute_payment_processing(self):
        """Execute payment processing scenario"""
        logger.info("Starting Payment Processing Scenario")
        
        # Step 1: Get order information
        order_info_msg = {
            "operation": "get_order_info",
            "data": {"order_id": "order1", "user_id": "user1"},
            "context": "payment_processing"
        }
        
        response1 = await self.send_message(
            "UserServiceAgent",
            "OrderServiceAgent",
            order_info_msg
        )
        
        if response1:
            order_info = response1.content.get("data", {}).get("order_info", {})
            
            # Step 2: Validate order for payment
            validation_msg = {
                "operation": "validate_order",
                "data": {
                    "order_id": "order1",
                    "total": order_info.get("total"),
                    "items": order_info.get("items")
                },
                "context": "payment_validation"
            }
            
            response2 = await self.send_message(
                "OrderServiceAgent",
                "UserServiceAgent",
                validation_msg
            )
            
            # Step 3: Process payment
            if response2 and response2.content.get("data", {}).get("is_valid"):
                payment_msg = {
                    "operation": "process_payment",
                    "data": {
                        "order_id": "order1",
                        "amount": order_info.get("total"),
                        "payment_method": "credit_card"
                    },
                    "context": "order_validated"
                }
                
                response3 = await self.send_message(
                    "UserServiceAgent",
                    "OrderServiceAgent",
                    payment_msg
                )
                
                logger.info("Payment Processing Scenario completed successfully")
        
        else:
            logger.error("Failed to get order information in scenario")

# Example usage
async def main():
    """Example usage of AI agents"""
    # Create orchestrator
    orchestrator = AgentOrchestrator()
    
    # Create agents
    user_agent = UserServiceAgent()
    order_agent = OrderServiceAgent()
    
    # Add agents to orchestrator
    orchestrator.add_agent(user_agent)
    orchestrator.add_agent(order_agent)
    
    # Start all components
    await orchestrator.start_all()
    
    # Execute scenarios
    await orchestrator.execute_scenario("user_order_integration")
    await asyncio.sleep(1)  # Brief pause between scenarios
    await orchestrator.execute_scenario("payment_processing")
    
    # Print scenario log
    print("\n=== Scenario Execution Log ===")
    for entry in orchestrator.scenario_log:
        print(f"Time: {entry['timestamp']}")
        print(f"From: {entry['sender']} -> To: {entry['receiver']}")
        print(f"Message: {entry['message']}")
        if entry['response']:
            print(f"Response: {entry['response']}")
        print("-" * 50)
    
    # Stop all components
    await orchestrator.stop_all()

if __name__ == "__main__":
    asyncio.run(main()) 