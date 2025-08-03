"""
MCP (Model Context Protocol) Servers Implementation
Two servers that AI agents can interact with
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MCPRequest:
    """MCP Request structure"""
    id: str
    method: str
    params: Dict[str, Any]
    timestamp: datetime

@dataclass
class MCPResponse:
    """MCP Response structure"""
    id: str
    result: Any
    error: Optional[str] = None
    timestamp: datetime = None

class BaseMCPServer:
    """Base class for MCP servers"""
    
    def __init__(self, name: str):
        self.name = name
        self.server_id = str(uuid.uuid4())
        self.is_running = False
        self.requests_processed = 0
    
    async def start(self):
        """Start the server"""
        self.is_running = True
        logger.info(f"{self.name} MCP Server started with ID: {self.server_id}")
    
    async def stop(self):
        """Stop the server"""
        self.is_running = False
        logger.info(f"{self.name} MCP Server stopped")
    
    async def process_request(self, request: MCPRequest) -> MCPResponse:
        """Process incoming request"""
        self.requests_processed += 1
        logger.info(f"{self.name}: Processing request {request.id} - {request.method}")
        
        # Default implementation
        return MCPResponse(
            id=request.id,
            result={"status": "not_implemented"},
            timestamp=datetime.now()
        )

class UserManagementMCPServer(BaseMCPServer):
    """MCP Server for User Management operations"""
    
    def __init__(self):
        super().__init__("UserManagement")
        self.users = {
            "user1": {"id": "user1", "name": "John Doe", "email": "john@example.com", "status": "active"},
            "user2": {"id": "user2", "name": "Jane Smith", "email": "jane@example.com", "status": "active"},
            "user3": {"id": "user3", "name": "Bob Johnson", "email": "bob@example.com", "status": "inactive"}
        }
    
    async def process_request(self, request: MCPRequest) -> MCPResponse:
        """Process user management requests"""
        self.requests_processed += 1
        logger.info(f"{self.name}: Processing {request.method}")
        
        try:
            if request.method == "get_user":
                user_id = request.params.get("user_id")
                if user_id in self.users:
                    return MCPResponse(
                        id=request.id,
                        result={"user": self.users[user_id]},
                        timestamp=datetime.now()
                    )
                else:
                    return MCPResponse(
                        id=request.id,
                        result={"error": "User not found"},
                        timestamp=datetime.now()
                    )
            
            elif request.method == "list_users":
                status_filter = request.params.get("status")
                if status_filter:
                    filtered_users = {k: v for k, v in self.users.items() if v["status"] == status_filter}
                    return MCPResponse(
                        id=request.id,
                        result={"users": list(filtered_users.values())},
                        timestamp=datetime.now()
                    )
                else:
                    return MCPResponse(
                        id=request.id,
                        result={"users": list(self.users.values())},
                        timestamp=datetime.now()
                    )
            
            elif request.method == "create_user":
                user_data = request.params.get("user_data", {})
                user_id = f"user{len(self.users) + 1}"
                new_user = {
                    "id": user_id,
                    "name": user_data.get("name", "Unknown"),
                    "email": user_data.get("email", ""),
                    "status": "active"
                }
                self.users[user_id] = new_user
                return MCPResponse(
                    id=request.id,
                    result={"user": new_user, "message": "User created successfully"},
                    timestamp=datetime.now()
                )
            
            elif request.method == "update_user":
                user_id = request.params.get("user_id")
                updates = request.params.get("updates", {})
                if user_id in self.users:
                    self.users[user_id].update(updates)
                    return MCPResponse(
                        id=request.id,
                        result={"user": self.users[user_id], "message": "User updated successfully"},
                        timestamp=datetime.now()
                    )
                else:
                    return MCPResponse(
                        id=request.id,
                        result={"error": "User not found"},
                        timestamp=datetime.now()
                    )
            
            else:
                return MCPResponse(
                    id=request.id,
                    result={"error": f"Unknown method: {request.method}"},
                    timestamp=datetime.now()
                )
        
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return MCPResponse(
                id=request.id,
                result={"error": str(e)},
                timestamp=datetime.now()
            )

class OrderProcessingMCPServer(BaseMCPServer):
    """MCP Server for Order Processing operations"""
    
    def __init__(self):
        super().__init__("OrderProcessing")
        self.orders = {
            "order1": {"id": "order1", "user_id": "user1", "items": ["item1", "item2"], "status": "pending", "total": 150.00},
            "order2": {"id": "order2", "user_id": "user2", "items": ["item3"], "status": "completed", "total": 75.50},
            "order3": {"id": "order3", "user_id": "user1", "items": ["item4", "item5", "item6"], "status": "processing", "total": 200.00}
        }
        self.inventory = {
            "item1": {"id": "item1", "name": "Laptop", "price": 100.00, "stock": 10},
            "item2": {"id": "item2", "name": "Mouse", "price": 50.00, "stock": 25},
            "item3": {"id": "item3", "name": "Keyboard", "price": 75.50, "stock": 15},
            "item4": {"id": "item4", "name": "Monitor", "price": 150.00, "stock": 8},
            "item5": {"id": "item5", "name": "Headphones", "price": 30.00, "stock": 30},
            "item6": {"id": "item6", "name": "Webcam", "price": 20.00, "stock": 20}
        }
    
    async def process_request(self, request: MCPRequest) -> MCPResponse:
        """Process order processing requests"""
        self.requests_processed += 1
        logger.info(f"{self.name}: Processing {request.method}")
        
        try:
            if request.method == "get_order":
                order_id = request.params.get("order_id")
                if order_id in self.orders:
                    return MCPResponse(
                        id=request.id,
                        result={"order": self.orders[order_id]},
                        timestamp=datetime.now()
                    )
                else:
                    return MCPResponse(
                        id=request.id,
                        result={"error": "Order not found"},
                        timestamp=datetime.now()
                    )
            
            elif request.method == "list_orders":
                user_id = request.params.get("user_id")
                status_filter = request.params.get("status")
                
                filtered_orders = self.orders.copy()
                if user_id:
                    filtered_orders = {k: v for k, v in filtered_orders.items() if v["user_id"] == user_id}
                if status_filter:
                    filtered_orders = {k: v for k, v in filtered_orders.items() if v["status"] == status_filter}
                
                return MCPResponse(
                    id=request.id,
                    result={"orders": list(filtered_orders.values())},
                    timestamp=datetime.now()
                )
            
            elif request.method == "create_order":
                user_id = request.params.get("user_id")
                items = request.params.get("items", [])
                
                # Check inventory
                total = 0
                for item_id in items:
                    if item_id in self.inventory:
                        total += self.inventory[item_id]["price"]
                    else:
                        return MCPResponse(
                            id=request.id,
                            result={"error": f"Item {item_id} not found in inventory"},
                            timestamp=datetime.now()
                        )
                
                order_id = f"order{len(self.orders) + 1}"
                new_order = {
                    "id": order_id,
                    "user_id": user_id,
                    "items": items,
                    "status": "pending",
                    "total": total
                }
                self.orders[order_id] = new_order
                
                return MCPResponse(
                    id=request.id,
                    result={"order": new_order, "message": "Order created successfully"},
                    timestamp=datetime.now()
                )
            
            elif request.method == "update_order_status":
                order_id = request.params.get("order_id")
                new_status = request.params.get("status")
                
                if order_id in self.orders:
                    self.orders[order_id]["status"] = new_status
                    return MCPResponse(
                        id=request.id,
                        result={"order": self.orders[order_id], "message": "Order status updated"},
                        timestamp=datetime.now()
                    )
                else:
                    return MCPResponse(
                        id=request.id,
                        result={"error": "Order not found"},
                        timestamp=datetime.now()
                    )
            
            elif request.method == "get_inventory":
                item_id = request.params.get("item_id")
                if item_id:
                    if item_id in self.inventory:
                        return MCPResponse(
                            id=request.id,
                            result={"item": self.inventory[item_id]},
                            timestamp=datetime.now()
                        )
                    else:
                        return MCPResponse(
                            id=request.id,
                            result={"error": "Item not found"},
                            timestamp=datetime.now()
                        )
                else:
                    return MCPResponse(
                        id=request.id,
                        result={"inventory": list(self.inventory.values())},
                        timestamp=datetime.now()
                    )
            
            else:
                return MCPResponse(
                    id=request.id,
                    result={"error": f"Unknown method: {request.method}"},
                    timestamp=datetime.now()
                )
        
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return MCPResponse(
                id=request.id,
                result={"error": str(e)},
                timestamp=datetime.now()
            )

# Server manager to handle multiple MCP servers
class MCPServerManager:
    """Manages multiple MCP servers"""
    
    def __init__(self):
        self.servers: Dict[str, BaseMCPServer] = {}
    
    def add_server(self, server: BaseMCPServer):
        """Add a server to the manager"""
        self.servers[server.name] = server
        logger.info(f"Added MCP server: {server.name}")
    
    async def start_all(self):
        """Start all servers"""
        for server in self.servers.values():
            await server.start()
    
    async def stop_all(self):
        """Stop all servers"""
        for server in self.servers.values():
            await server.stop()
    
    async def route_request(self, server_name: str, request: MCPRequest) -> MCPResponse:
        """Route request to appropriate server"""
        if server_name not in self.servers:
            return MCPResponse(
                id=request.id,
                result={"error": f"Server {server_name} not found"},
                timestamp=datetime.now()
            )
        
        return await self.servers[server_name].process_request(request)

# Example usage
async def main():
    """Example usage of MCP servers"""
    # Create server manager
    manager = MCPServerManager()
    
    # Create and add servers
    user_server = UserManagementMCPServer()
    order_server = OrderProcessingMCPServer()
    
    manager.add_server(user_server)
    manager.add_server(order_server)
    
    # Start all servers
    await manager.start_all()
    
    # Example requests
    requests = [
        MCPRequest("req1", "get_user", {"user_id": "user1"}, datetime.now()),
        MCPRequest("req2", "list_users", {"status": "active"}, datetime.now()),
        MCPRequest("req3", "get_order", {"order_id": "order1"}, datetime.now()),
        MCPRequest("req4", "list_orders", {"user_id": "user1"}, datetime.now()),
    ]
    
    # Process requests
    for request in requests:
        if "user" in request.method:
            response = await manager.route_request("UserManagement", request)
        else:
            response = await manager.route_request("OrderProcessing", request)
        
        print(f"Request {request.id}: {response.result}")
    
    # Stop all servers
    await manager.stop_all()

if __name__ == "__main__":
    asyncio.run(main()) 