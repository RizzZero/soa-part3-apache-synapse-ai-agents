"""
MCP Servers Interaction Example

This example demonstrates the interaction between two MCP servers:
1. Order Management MCP Server - Handles orders, inventory, and customers
2. Payment Processing MCP Server - Handles payments, refunds, and financial operations

The scenario simulates a complete e-commerce workflow where:
1. A customer places an order
2. The order is validated and inventory is checked
3. Payment is processed
4. Order status is updated based on payment result
5. Various operations like refunds and order tracking are demonstrated
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# Import our MCP servers
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.order_management_server import OrderManagementMCPServer
from services.payment_processing_server import PaymentProcessingMCPServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ECommerceWorkflow:
    """Demonstrates the interaction between Order Management and Payment Processing MCP servers."""
    
    def __init__(self):
        # Initialize both MCP servers
        self.order_server = OrderManagementMCPServer({
            "payment_server_url": "http://localhost:8081"
        })
        
        self.payment_server = PaymentProcessingMCPServer({
            "order_server_url": "http://localhost:8080"
        })
        
        logger.info("E-Commerce Workflow initialized with both MCP servers")
    
    async def run_complete_workflow(self):
        """Run a complete e-commerce workflow demonstration."""
        logger.info("=" * 80)
        logger.info("STARTING E-COMMERCE WORKFLOW DEMONSTRATION")
        logger.info("=" * 80)
        
        # Step 1: Display server information
        await self._display_server_info()
        
        # Step 2: Customer places an order
        order_result = await self._place_order()
        if not order_result.get("success"):
            logger.error("Failed to place order")
            return
        
        order_id = order_result["order_id"]
        logger.info(f"Order placed successfully: {order_id}")
        
        # Step 3: Process payment for the order
        payment_result = await self._process_payment(order_id)
        if not payment_result.get("success"):
            logger.error("Payment processing failed")
            await self._handle_payment_failure(order_id)
            return
        
        payment_id = payment_result["payment_id"]
        logger.info(f"Payment processed successfully: {payment_id}")
        
        # Step 4: Update order status
        await self._update_order_status(order_id, "confirmed")
        
        # Step 5: Demonstrate additional operations
        await self._demonstrate_additional_operations(order_id, payment_id)
        
        # Step 6: Generate reports
        await self._generate_reports()
        
        logger.info("=" * 80)
        logger.info("E-COMMERCE WORKFLOW DEMONSTRATION COMPLETED")
        logger.info("=" * 80)
    
    async def _display_server_info(self):
        """Display information about both MCP servers."""
        logger.info("\n" + "=" * 50)
        logger.info("SERVER INFORMATION")
        logger.info("=" * 50)
        
        # Order Management Server Info
        order_info = await self.order_server.get_server_info()
        logger.info(f"Order Management Server:")
        logger.info(f"  - Name: {order_info['name']}")
        logger.info(f"  - Version: {order_info['version']}")
        logger.info(f"  - Tools: {order_info['tools_count']}")
        logger.info(f"  - Orders: {order_info['orders_count']}")
        logger.info(f"  - Customers: {order_info['customers_count']}")
        logger.info(f"  - Products: {order_info['products_count']}")
        
        # Payment Processing Server Info
        payment_info = await self.payment_server.get_server_info()
        logger.info(f"\nPayment Processing Server:")
        logger.info(f"  - Name: {payment_info['name']}")
        logger.info(f"  - Version: {payment_info['version']}")
        logger.info(f"  - Tools: {payment_info['tools_count']}")
        logger.info(f"  - Payments: {payment_info['payments_count']}")
        logger.info(f"  - Customers: {payment_info['customers_count']}")
        logger.info(f"  - Transactions: {payment_info['transactions_count']}")
        
        # Display available tools
        logger.info(f"\nOrder Management Tools:")
        order_tools = await self.order_server.get_available_tools()
        for tool in order_tools:
            logger.info(f"  - {tool['name']}: {tool['description']}")
        
        logger.info(f"\nPayment Processing Tools:")
        payment_tools = await self.payment_server.get_available_tools()
        for tool in payment_tools:
            logger.info(f"  - {tool['name']}: {tool['description']}")
    
    async def _place_order(self) -> Dict[str, Any]:
        """Place a new order using the Order Management MCP Server."""
        logger.info("\n" + "=" * 50)
        logger.info("STEP 1: PLACING ORDER")
        logger.info("=" * 50)
        
        # First, check inventory for products
        logger.info("Checking inventory...")
        inventory_check = await self.order_server.call_tool("check_inventory", {
            "product_id": "prod_001"
        })
        logger.info(f"Inventory check result: {inventory_check}")
        
        # Place the order
        order_data = {
            "customer_id": "cust_001",
            "items": [
                {"product_id": "prod_001", "quantity": 1},  # Laptop
                {"product_id": "prod_002", "quantity": 2},  # Wireless Mouse
                {"product_id": "prod_003", "quantity": 1}   # Coffee Mug
            ],
            "shipping_address": {
                "street": "123 Main St",
                "city": "New York",
                "state": "NY",
                "zip": "10001",
                "country": "USA"
            }
        }
        
        logger.info(f"Placing order with data: {json.dumps(order_data, indent=2)}")
        
        result = await self.order_server.call_tool("create_order", order_data)
        logger.info(f"Order creation result: {json.dumps(result, indent=2)}")
        
        return result
    
    async def _process_payment(self, order_id: str) -> Dict[str, Any]:
        """Process payment for an order using the Payment Processing MCP Server."""
        logger.info("\n" + "=" * 50)
        logger.info("STEP 2: PROCESSING PAYMENT")
        logger.info("=" * 50)
        
        # Get order details to know the amount
        order_details = await self.order_server.call_tool("get_order", {"order_id": order_id})
        if not order_details.get("success"):
            logger.error(f"Failed to get order details: {order_details}")
            return {"success": False, "error": "Failed to get order details"}
        
        order = order_details["order"]
        total_amount = order["total_amount"]
        
        logger.info(f"Processing payment for order {order_id} - Amount: ${total_amount}")
        
        # Process payment
        payment_data = {
            "amount": total_amount,
            "currency": "USD",
            "payment_method": "credit_card",
            "payment_details": {
                "card_number": "4111111111111111",
                "expiry_month": 12,
                "expiry_year": 2025,
                "cvv": "123",
                "card_type": "Visa"
            },
            "order_id": order_id,
            "customer_id": order["customer_id"]
        }
        
        logger.info(f"Payment data: {json.dumps(payment_data, indent=2)}")
        
        result = await self.payment_server.call_tool("process_payment", payment_data)
        logger.info(f"Payment processing result: {json.dumps(result, indent=2)}")
        
        return result
    
    async def _handle_payment_failure(self, order_id: str):
        """Handle payment failure scenario."""
        logger.info("\n" + "=" * 50)
        logger.info("HANDLING PAYMENT FAILURE")
        logger.info("=" * 50)
        
        # Update order status to reflect payment failure
        await self.order_server.call_tool("update_order_status", {
            "order_id": order_id,
            "status": "cancelled"
        })
        
        logger.info(f"Order {order_id} cancelled due to payment failure")
        
        # Demonstrate alternative payment methods
        logger.info("Attempting payment with alternative method...")
        
        # Try with a different payment method
        alternative_payment = await self.payment_server.call_tool("process_payment", {
            "amount": 1359.96,  # Same amount
            "currency": "USD",
            "payment_method": "debit_card",
            "payment_details": {
                "card_number": "5555555555554444",
                "expiry_month": 8,
                "expiry_year": 2026,
                "cvv": "321",
                "card_type": "Mastercard"
            },
            "order_id": order_id,
            "customer_id": "cust_001"
        })
        
        logger.info(f"Alternative payment result: {json.dumps(alternative_payment, indent=2)}")
    
    async def _update_order_status(self, order_id: str, status: str):
        """Update order status."""
        logger.info("\n" + "=" * 50)
        logger.info("STEP 3: UPDATING ORDER STATUS")
        logger.info("=" * 50)
        
        result = await self.order_server.call_tool("update_order_status", {
            "order_id": order_id,
            "status": status
        })
        
        logger.info(f"Order status update result: {json.dumps(result, indent=2)}")
        
        # Get updated order details
        order_details = await self.order_server.call_tool("get_order", {"order_id": order_id})
        logger.info(f"Updated order details: {json.dumps(order_details, indent=2)}")
    
    async def _demonstrate_additional_operations(self, order_id: str, payment_id: str):
        """Demonstrate additional operations like refunds, order tracking, etc."""
        logger.info("\n" + "=" * 50)
        logger.info("STEP 4: ADDITIONAL OPERATIONS")
        logger.info("=" * 50)
        
        # 1. Get customer order history
        logger.info("\n--- Customer Order History ---")
        customer_orders = await self.order_server.call_tool("get_customer_orders", {
            "customer_id": "cust_001"
        })
        logger.info(f"Customer orders: {json.dumps(customer_orders, indent=2)}")
        
        # 2. Get payment details
        logger.info("\n--- Payment Details ---")
        payment_details = await self.payment_server.call_tool("get_payment", {
            "payment_id": payment_id
        })
        logger.info(f"Payment details: {json.dumps(payment_details, indent=2)}")
        
        # 3. Demonstrate partial refund
        logger.info("\n--- Processing Partial Refund ---")
        refund_result = await self.payment_server.call_tool("refund_payment", {
            "payment_id": payment_id,
            "amount": 29.99,  # Refund the mouse
            "reason": "Customer requested refund for wireless mouse"
        })
        logger.info(f"Refund result: {json.dumps(refund_result, indent=2)}")
        
        # 4. Add a new customer
        logger.info("\n--- Adding New Customer ---")
        new_customer = await self.order_server.call_tool("add_customer", {
            "name": "Alice Johnson",
            "email": "alice.johnson@example.com",
            "phone": "+1-555-0789",
            "address": {
                "street": "789 Pine St",
                "city": "Chicago",
                "state": "IL",
                "zip": "60601",
                "country": "USA"
            }
        })
        logger.info(f"New customer result: {json.dumps(new_customer, indent=2)}")
        
        # 5. Add payment method for customer
        logger.info("\n--- Adding Payment Method ---")
        payment_method = await self.payment_server.call_tool("add_payment_method", {
            "customer_id": "cust_001",
            "payment_method": {
                "type": "credit_card",
                "last_four": "9999",
                "expiry_month": 6,
                "expiry_year": 2028,
                "card_type": "Discover",
                "is_default": False
            }
        })
        logger.info(f"Payment method result: {json.dumps(payment_method, indent=2)}")
        
        # 6. Validate payment method
        logger.info("\n--- Validating Payment Method ---")
        validation = await self.payment_server.call_tool("validate_payment_method", {
            "payment_method": "credit_card",
            "payment_details": {
                "card_number": "4111111111111111",
                "expiry_month": 12,
                "expiry_year": 2025,
                "cvv": "123",
                "card_type": "Visa"
            }
        })
        logger.info(f"Validation result: {json.dumps(validation, indent=2)}")
    
    async def _generate_reports(self):
        """Generate various reports from both servers."""
        logger.info("\n" + "=" * 50)
        logger.info("STEP 5: GENERATING REPORTS")
        logger.info("=" * 50)
        
        # Payment statistics
        logger.info("\n--- Payment Statistics ---")
        payment_stats = await self.payment_server.call_tool("get_payment_statistics", {
            "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
            "end_date": datetime.now().isoformat(),
            "currency": "USD"
        })
        logger.info(f"Payment statistics: {json.dumps(payment_stats, indent=2)}")
        
        # Customer payments
        logger.info("\n--- Customer Payment History ---")
        customer_payments = await self.payment_server.call_tool("get_customer_payments", {
            "customer_id": "cust_001"
        })
        logger.info(f"Customer payments: {json.dumps(customer_payments, indent=2)}")
        
        # Inventory status
        logger.info("\n--- Current Inventory Status ---")
        for product_id in ["prod_001", "prod_002", "prod_003"]:
            inventory = await self.order_server.call_tool("check_inventory", {
                "product_id": product_id
            })
            logger.info(f"Inventory for {product_id}: {json.dumps(inventory, indent=2)}")


async def demonstrate_error_scenarios():
    """Demonstrate error handling scenarios."""
    logger.info("\n" + "=" * 80)
    logger.info("ERROR SCENARIOS DEMONSTRATION")
    logger.info("=" * 80)
    
    workflow = ECommerceWorkflow()
    
    # 1. Try to create order with non-existent customer
    logger.info("\n--- Error: Non-existent Customer ---")
    result = await workflow.order_server.call_tool("create_order", {
        "customer_id": "non_existent_customer",
        "items": [{"product_id": "prod_001", "quantity": 1}],
        "shipping_address": {"street": "123 Test St", "city": "Test City"}
    })
    logger.info(f"Error result: {json.dumps(result, indent=2)}")
    
    # 2. Try to create order with insufficient inventory
    logger.info("\n--- Error: Insufficient Inventory ---")
    result = await workflow.order_server.call_tool("create_order", {
        "customer_id": "cust_001",
        "items": [{"product_id": "prod_001", "quantity": 1000}],  # More than available
        "shipping_address": {"street": "123 Test St", "city": "Test City"}
    })
    logger.info(f"Error result: {json.dumps(result, indent=2)}")
    
    # 3. Try to process payment with invalid currency
    logger.info("\n--- Error: Invalid Currency ---")
    result = await workflow.payment_server.call_tool("process_payment", {
        "amount": 100.0,
        "currency": "INVALID_CURRENCY",
        "payment_method": "credit_card",
        "payment_details": {"card_number": "4111111111111111"},
        "order_id": "test_order",
        "customer_id": "cust_001"
    })
    logger.info(f"Error result: {json.dumps(result, indent=2)}")
    
    # 4. Try to refund non-existent payment
    logger.info("\n--- Error: Non-existent Payment ---")
    result = await workflow.payment_server.call_tool("refund_payment", {
        "payment_id": "non_existent_payment",
        "reason": "Test refund"
    })
    logger.info(f"Error result: {json.dumps(result, indent=2)}")


async def main():
    """Main function to run the complete demonstration."""
    try:
        # Run the main workflow
        workflow = ECommerceWorkflow()
        await workflow.run_complete_workflow()
        
        # Run error scenarios
        await demonstrate_error_scenarios()
        
        logger.info("\n" + "=" * 80)
        logger.info("ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error during demonstration: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 