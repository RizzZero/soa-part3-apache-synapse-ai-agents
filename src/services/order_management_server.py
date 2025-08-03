"""
Order Management MCP Server

A Model Context Protocol (MCP) server that provides order management capabilities
including order processing, inventory management, and customer operations.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

import aiohttp
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class Customer:
    id: str
    name: str
    email: str
    phone: str
    address: Dict[str, str]
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Product:
    id: str
    name: str
    description: str
    price: float
    category: str
    stock_quantity: int
    sku: str


@dataclass
class OrderItem:
    product_id: str
    quantity: int
    unit_price: float
    total_price: float


@dataclass
class Order:
    id: str
    customer_id: str
    items: List[OrderItem]
    total_amount: float
    status: OrderStatus
    payment_status: PaymentStatus
    shipping_address: Dict[str, str]
    created_at: datetime
    updated_at: datetime
    payment_id: Optional[str] = None


class OrderManagementMCPServer:
    """Order Management MCP Server for handling orders, inventory, and customers."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.orders: Dict[str, Order] = {}
        self.customers: Dict[str, Customer] = {}
        self.products: Dict[str, Product] = {}
        self.payment_server_url = self.config.get("payment_server_url", "http://localhost:8081")
        
        # Initialize with sample data
        self._initialize_sample_data()
        
        logger.info("Order Management MCP Server initialized")
    
    def _initialize_sample_data(self):
        """Initialize with sample data for demonstration."""
        # Sample customers
        self.customers = {
            "cust_001": Customer(
                id="cust_001",
                name="John Doe",
                email="john.doe@example.com",
                phone="+1-555-0123",
                address={
                    "street": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "zip": "10001",
                    "country": "USA"
                }
            ),
            "cust_002": Customer(
                id="cust_002",
                name="Jane Smith",
                email="jane.smith@example.com",
                phone="+1-555-0456",
                address={
                    "street": "456 Oak Ave",
                    "city": "Los Angeles",
                    "state": "CA",
                    "zip": "90210",
                    "country": "USA"
                }
            )
        }
        
        # Sample products
        self.products = {
            "prod_001": Product(
                id="prod_001",
                name="Laptop Computer",
                description="High-performance laptop with 16GB RAM",
                price=1299.99,
                category="Electronics",
                stock_quantity=50,
                sku="LAPTOP-001"
            ),
            "prod_002": Product(
                id="prod_002",
                name="Wireless Mouse",
                description="Ergonomic wireless mouse",
                price=29.99,
                category="Electronics",
                stock_quantity=200,
                sku="MOUSE-001"
            ),
            "prod_003": Product(
                id="prod_003",
                name="Coffee Mug",
                description="Ceramic coffee mug, 12oz",
                price=12.99,
                category="Home & Kitchen",
                stock_quantity=150,
                sku="MUG-001"
            )
        }
        
        logger.info(f"Initialized with {len(self.customers)} customers and {len(self.products)} products")
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available MCP tools."""
        return [
            {
                "name": "create_order",
                "description": "Create a new order for a customer",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string", "description": "Customer ID"},
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "product_id": {"type": "string"},
                                    "quantity": {"type": "integer", "minimum": 1}
                                },
                                "required": ["product_id", "quantity"]
                            }
                        },
                        "shipping_address": {"type": "object"}
                    },
                    "required": ["customer_id", "items", "shipping_address"]
                }
            },
            {
                "name": "get_order",
                "description": "Get order details by order ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string", "description": "Order ID"}
                    },
                    "required": ["order_id"]
                }
            },
            {
                "name": "update_order_status",
                "description": "Update order status",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string"},
                        "status": {"type": "string", "enum": [s.value for s in OrderStatus]}
                    },
                    "required": ["order_id", "status"]
                }
            },
            {
                "name": "check_inventory",
                "description": "Check product inventory levels",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "string", "description": "Product ID"}
                    },
                    "required": ["product_id"]
                }
            },
            {
                "name": "process_payment",
                "description": "Process payment for an order using the Payment MCP Server",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string"},
                        "payment_method": {"type": "string"},
                        "payment_details": {"type": "object"}
                    },
                    "required": ["order_id", "payment_method", "payment_details"]
                }
            },
            {
                "name": "get_customer_orders",
                "description": "Get all orders for a customer",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string"}
                    },
                    "required": ["customer_id"]
                }
            },
            {
                "name": "add_customer",
                "description": "Add a new customer",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "phone": {"type": "string"},
                        "address": {"type": "object"}
                    },
                    "required": ["name", "email", "phone", "address"]
                }
            }
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool by name with arguments."""
        try:
            if name == "create_order":
                return await self._create_order(arguments)
            elif name == "get_order":
                return await self._get_order(arguments)
            elif name == "update_order_status":
                return await self._update_order_status(arguments)
            elif name == "check_inventory":
                return await self._check_inventory(arguments)
            elif name == "process_payment":
                return await self._process_payment(arguments)
            elif name == "get_customer_orders":
                return await self._get_customer_orders(arguments)
            elif name == "add_customer":
                return await self._add_customer(arguments)
            else:
                return {"error": f"Unknown tool: {name}"}
        except Exception as e:
            logger.error(f"Error calling tool {name}: {str(e)}")
            return {"error": str(e)}
    
    async def _create_order(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new order."""
        customer_id = args["customer_id"]
        items_data = args["items"]
        shipping_address = args["shipping_address"]
        
        if customer_id not in self.customers:
            return {"error": f"Customer {customer_id} not found"}
        
        # Validate items and calculate totals
        order_items = []
        total_amount = 0.0
        
        for item_data in items_data:
            product_id = item_data["product_id"]
            quantity = item_data["quantity"]
            
            if product_id not in self.products:
                return {"error": f"Product {product_id} not found"}
            
            product = self.products[product_id]
            if product.stock_quantity < quantity:
                return {"error": f"Insufficient stock for product {product_id}"}
            
            unit_price = product.price
            total_price = unit_price * quantity
            total_amount += total_price
            
            order_items.append(OrderItem(
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price
            ))
        
        # Create order
        order_id = f"order_{len(self.orders) + 1:06d}"
        order = Order(
            id=order_id,
            customer_id=customer_id,
            items=order_items,
            total_amount=total_amount,
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            shipping_address=shipping_address,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.orders[order_id] = order
        
        # Update inventory
        for item in order_items:
            self.products[item.product_id].stock_quantity -= item.quantity
        
        logger.info(f"Created order {order_id} for customer {customer_id}")
        
        return {
            "success": True,
            "order_id": order_id,
            "total_amount": total_amount,
            "status": order.status.value,
            "message": "Order created successfully"
        }
    
    async def _get_order(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get order details."""
        order_id = args["order_id"]
        
        if order_id not in self.orders:
            return {"error": f"Order {order_id} not found"}
        
        order = self.orders[order_id]
        
        return {
            "success": True,
            "order": {
                "id": order.id,
                "customer_id": order.customer_id,
                "items": [
                    {
                        "product_id": item.product_id,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "total_price": item.total_price
                    }
                    for item in order.items
                ],
                "total_amount": order.total_amount,
                "status": order.status.value,
                "payment_status": order.payment_status.value,
                "shipping_address": order.shipping_address,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat(),
                "payment_id": order.payment_id
            }
        }
    
    async def _update_order_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update order status."""
        order_id = args["order_id"]
        status = args["status"]
        
        if order_id not in self.orders:
            return {"error": f"Order {order_id} not found"}
        
        try:
            order_status = OrderStatus(status)
        except ValueError:
            return {"error": f"Invalid status: {status}"}
        
        order = self.orders[order_id]
        order.status = order_status
        order.updated_at = datetime.now()
        
        logger.info(f"Updated order {order_id} status to {status}")
        
        return {
            "success": True,
            "order_id": order_id,
            "status": status,
            "message": "Order status updated successfully"
        }
    
    async def _check_inventory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check product inventory."""
        product_id = args["product_id"]
        
        if product_id not in self.products:
            return {"error": f"Product {product_id} not found"}
        
        product = self.products[product_id]
        
        return {
            "success": True,
            "product": {
                "id": product.id,
                "name": product.name,
                "stock_quantity": product.stock_quantity,
                "sku": product.sku
            }
        }
    
    async def _process_payment(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment using the Payment MCP Server."""
        order_id = args["order_id"]
        payment_method = args["payment_method"]
        payment_details = args["payment_details"]
        
        if order_id not in self.orders:
            return {"error": f"Order {order_id} not found"}
        
        order = self.orders[order_id]
        
        # Prepare payment request for Payment MCP Server
        payment_request = {
            "amount": order.total_amount,
            "currency": "USD",
            "payment_method": payment_method,
            "payment_details": payment_details,
            "order_id": order_id,
            "customer_id": order.customer_id
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.payment_server_url}/process_payment",
                    json=payment_request,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        payment_result = await response.json()
                        
                        if payment_result.get("success"):
                            # Update order payment status
                            order.payment_status = PaymentStatus.PAID
                            order.payment_id = payment_result.get("payment_id")
                            order.updated_at = datetime.now()
                            
                            logger.info(f"Payment processed successfully for order {order_id}")
                            
                            return {
                                "success": True,
                                "payment_id": payment_result.get("payment_id"),
                                "message": "Payment processed successfully"
                            }
                        else:
                            return {"error": payment_result.get("error", "Payment processing failed")}
                    else:
                        return {"error": f"Payment server error: {response.status}"}
        
        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}")
            return {"error": f"Payment processing error: {str(e)}"}
    
    async def _get_customer_orders(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get all orders for a customer."""
        customer_id = args["customer_id"]
        
        if customer_id not in self.customers:
            return {"error": f"Customer {customer_id} not found"}
        
        customer_orders = [
            {
                "id": order.id,
                "total_amount": order.total_amount,
                "status": order.status.value,
                "payment_status": order.payment_status.value,
                "created_at": order.created_at.isoformat()
            }
            for order in self.orders.values()
            if order.customer_id == customer_id
        ]
        
        return {
            "success": True,
            "customer_id": customer_id,
            "orders": customer_orders,
            "count": len(customer_orders)
        }
    
    async def _add_customer(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new customer."""
        customer_id = f"cust_{len(self.customers) + 1:03d}"
        
        customer = Customer(
            id=customer_id,
            name=args["name"],
            email=args["email"],
            phone=args["phone"],
            address=args["address"]
        )
        
        self.customers[customer_id] = customer
        
        logger.info(f"Added new customer {customer_id}: {customer.name}")
        
        return {
            "success": True,
            "customer_id": customer_id,
            "message": "Customer added successfully"
        }
    
    async def get_server_info(self) -> Dict[str, Any]:
        """Get server information."""
        return {
            "name": "Order Management MCP Server",
            "version": "1.0.0",
            "description": "Handles order processing, inventory management, and customer operations",
            "tools_count": len(await self.get_available_tools()),
            "orders_count": len(self.orders),
            "customers_count": len(self.customers),
            "products_count": len(self.products)
        }


# Example usage and testing
async def main():
    """Example usage of the Order Management MCP Server."""
    server = OrderManagementMCPServer()
    
    # Get server info
    info = await server.get_server_info()
    logger.info(f"Server Info: {info}")
    
    # Get available tools
    tools = await server.get_available_tools()
    logger.info(f"Available tools: {[tool['name'] for tool in tools]}")
    
    # Example: Create an order
    order_result = await server.call_tool("create_order", {
        "customer_id": "cust_001",
        "items": [
            {"product_id": "prod_001", "quantity": 1},
            {"product_id": "prod_002", "quantity": 2}
        ],
        "shipping_address": {
            "street": "123 Main St",
            "city": "New York",
            "state": "NY",
            "zip": "10001",
            "country": "USA"
        }
    })
    
    logger.info(f"Order creation result: {order_result}")


if __name__ == "__main__":
    asyncio.run(main()) 