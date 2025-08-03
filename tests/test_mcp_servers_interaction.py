"""
Test MCP Servers Interaction

Tests for the interaction between Order Management and Payment Processing MCP servers.
"""

import pytest
import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# Import our MCP servers
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.order_management_server import OrderManagementMCPServer
from services.payment_processing_server import PaymentProcessingMCPServer


class TestMCPServersInteraction:
    """Test class for MCP servers interaction."""
    
    @pytest.fixture
    async def order_server(self):
        """Create Order Management MCP Server instance."""
        return OrderManagementMCPServer({
            "payment_server_url": "http://localhost:8081"
        })
    
    @pytest.fixture
    async def payment_server(self):
        """Create Payment Processing MCP Server instance."""
        return PaymentProcessingMCPServer({
            "order_server_url": "http://localhost:8080"
        })
    
    @pytest.mark.asyncio
    async def test_server_initialization(self, order_server, payment_server):
        """Test that both servers initialize correctly."""
        # Test Order Management Server
        order_info = await order_server.get_server_info()
        assert order_info["name"] == "Order Management MCP Server"
        assert order_info["version"] == "1.0.0"
        assert order_info["tools_count"] > 0
        assert order_info["customers_count"] > 0
        assert order_info["products_count"] > 0
        
        # Test Payment Processing Server
        payment_info = await payment_server.get_server_info()
        assert payment_info["name"] == "Payment Processing MCP Server"
        assert payment_info["version"] == "1.0.0"
        assert payment_info["tools_count"] > 0
        assert payment_info["customers_count"] > 0
    
    @pytest.mark.asyncio
    async def test_complete_ecommerce_workflow(self, order_server, payment_server):
        """Test complete e-commerce workflow from order to payment."""
        # Step 1: Create an order
        order_result = await order_server.call_tool("create_order", {
            "customer_id": "cust_001",
            "items": [
                {"product_id": "prod_001", "quantity": 1},
                {"product_id": "prod_002", "quantity": 1}
            ],
            "shipping_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "zip": "12345",
                "country": "USA"
            }
        })
        
        assert order_result["success"] is True
        assert "order_id" in order_result
        order_id = order_result["order_id"]
        
        # Step 2: Get order details
        order_details = await order_server.call_tool("get_order", {"order_id": order_id})
        assert order_details["success"] is True
        assert order_details["order"]["id"] == order_id
        assert order_details["order"]["status"] == "pending"
        assert order_details["order"]["payment_status"] == "pending"
        
        total_amount = order_details["order"]["total_amount"]
        
        # Step 3: Process payment
        payment_result = await payment_server.call_tool("process_payment", {
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
            "customer_id": "cust_001"
        })
        
        # Payment might succeed or fail due to simulation
        assert "payment_id" in payment_result or "error" in payment_result
        
        if payment_result.get("success"):
            payment_id = payment_result["payment_id"]
            
            # Step 4: Get payment details
            payment_details = await payment_server.call_tool("get_payment", {"payment_id": payment_id})
            assert payment_details["success"] is True
            assert payment_details["payment"]["id"] == payment_id
            assert payment_details["payment"]["order_id"] == order_id
    
    @pytest.mark.asyncio
    async def test_payment_failure_handling(self, order_server, payment_server):
        """Test handling of payment failures."""
        # Create an order
        order_result = await order_server.call_tool("create_order", {
            "customer_id": "cust_001",
            "items": [{"product_id": "prod_003", "quantity": 1}],
            "shipping_address": {"street": "123 Test St", "city": "Test City"}
        })
        
        assert order_result["success"] is True
        order_id = order_result["order_id"]
        
        # Try to process payment with invalid currency (should fail)
        payment_result = await payment_server.call_tool("process_payment", {
            "amount": 12.99,
            "currency": "INVALID_CURRENCY",
            "payment_method": "credit_card",
            "payment_details": {"card_number": "4111111111111111"},
            "order_id": order_id,
            "customer_id": "cust_001"
        })
        
        assert payment_result["success"] is False
        assert "error" in payment_result
    
    @pytest.mark.asyncio
    async def test_refund_processing(self, order_server, payment_server):
        """Test refund processing workflow."""
        # Create an order and process payment
        order_result = await order_server.call_tool("create_order", {
            "customer_id": "cust_001",
            "items": [{"product_id": "prod_002", "quantity": 1}],
            "shipping_address": {"street": "123 Test St", "city": "Test City"}
        })
        
        assert order_result["success"] is True
        order_id = order_result["order_id"]
        
        # Process payment
        payment_result = await payment_server.call_tool("process_payment", {
            "amount": 29.99,
            "currency": "USD",
            "payment_method": "credit_card",
            "payment_details": {
                "card_number": "4111111111111111",
                "expiry_month": 12,
                "expiry_year": 2025,
                "cvv": "123"
            },
            "order_id": order_id,
            "customer_id": "cust_001"
        })
        
        if payment_result.get("success"):
            payment_id = payment_result["payment_id"]
            
            # Process refund
            refund_result = await payment_server.call_tool("refund_payment", {
                "payment_id": payment_id,
                "amount": 29.99,
                "reason": "Customer requested refund"
            })
            
            assert refund_result["success"] is True
            assert "refund_id" in refund_result
            assert refund_result["amount"] == 29.99
    
    @pytest.mark.asyncio
    async def test_customer_operations(self, order_server, payment_server):
        """Test customer-related operations."""
        # Add a new customer
        new_customer = await order_server.call_tool("add_customer", {
            "name": "Test Customer",
            "email": "test@example.com",
            "phone": "+1-555-9999",
            "address": {
                "street": "999 Test Ave",
                "city": "Test City",
                "state": "TS",
                "zip": "99999",
                "country": "USA"
            }
        })
        
        assert new_customer["success"] is True
        assert "customer_id" in new_customer
        
        customer_id = new_customer["customer_id"]
        
        # Add payment method for the customer
        payment_method = await payment_server.call_tool("add_payment_method", {
            "customer_id": customer_id,
            "payment_method": {
                "type": "credit_card",
                "last_four": "9999",
                "expiry_month": 12,
                "expiry_year": 2028,
                "card_type": "Test Card",
                "is_default": True
            }
        })
        
        assert payment_method["success"] is True
        assert "payment_method_id" in payment_method
    
    @pytest.mark.asyncio
    async def test_inventory_management(self, order_server):
        """Test inventory management operations."""
        # Check inventory before order
        inventory_before = await order_server.call_tool("check_inventory", {
            "product_id": "prod_001"
        })
        
        assert inventory_before["success"] is True
        initial_stock = inventory_before["product"]["stock_quantity"]
        
        # Create an order
        order_result = await order_server.call_tool("create_order", {
            "customer_id": "cust_001",
            "items": [{"product_id": "prod_001", "quantity": 1}],
            "shipping_address": {"street": "123 Test St", "city": "Test City"}
        })
        
        assert order_result["success"] is True
        
        # Check inventory after order
        inventory_after = await order_server.call_tool("check_inventory", {
            "product_id": "prod_001"
        })
        
        assert inventory_after["success"] is True
        final_stock = inventory_after["product"]["stock_quantity"]
        
        # Stock should be reduced by 1
        assert final_stock == initial_stock - 1
    
    @pytest.mark.asyncio
    async def test_error_handling(self, order_server, payment_server):
        """Test error handling scenarios."""
        # Test non-existent customer
        result = await order_server.call_tool("create_order", {
            "customer_id": "non_existent_customer",
            "items": [{"product_id": "prod_001", "quantity": 1}],
            "shipping_address": {"street": "123 Test St", "city": "Test City"}
        })
        
        assert result["success"] is False
        assert "error" in result
        
        # Test non-existent product
        result = await order_server.call_tool("create_order", {
            "customer_id": "cust_001",
            "items": [{"product_id": "non_existent_product", "quantity": 1}],
            "shipping_address": {"street": "123 Test St", "city": "Test City"}
        })
        
        assert result["success"] is False
        assert "error" in result
        
        # Test non-existent payment
        result = await payment_server.call_tool("get_payment", {
            "payment_id": "non_existent_payment"
        })
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_payment_statistics(self, payment_server):
        """Test payment statistics generation."""
        # Generate payment statistics
        stats = await payment_server.call_tool("get_payment_statistics", {
            "start_date": (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).isoformat(),
            "end_date": datetime.now().isoformat(),
            "currency": "USD"
        })
        
        assert stats["success"] is True
        assert "statistics" in stats
        assert "total_payments" in stats["statistics"]
        assert "total_amount" in stats["statistics"]
        assert "success_rate" in stats["statistics"]
    
    @pytest.mark.asyncio
    async def test_payment_method_validation(self, payment_server):
        """Test payment method validation."""
        # Test valid payment method
        validation = await payment_server.call_tool("validate_payment_method", {
            "payment_method": "credit_card",
            "payment_details": {
                "card_number": "4111111111111111",
                "expiry_month": 12,
                "expiry_year": 2025,
                "cvv": "123",
                "card_type": "Visa"
            }
        })
        
        assert validation["success"] is True
        assert "validation" in validation
        assert validation["validation"]["valid"] is True
        
        # Test expired card
        validation = await payment_server.call_tool("validate_payment_method", {
            "payment_method": "credit_card",
            "payment_details": {
                "card_number": "4111111111111111",
                "expiry_month": 1,
                "expiry_year": 2020,
                "cvv": "123",
                "card_type": "Visa"
            }
        })
        
        assert validation["success"] is True
        assert "validation" in validation
        # Should be invalid due to expired card
        assert validation["validation"]["expiry_valid"] is False


class TestMCPServersIntegration:
    """Integration tests for MCP servers."""
    
    @pytest.mark.asyncio
    async def test_cross_server_communication(self):
        """Test communication between servers."""
        order_server = OrderManagementMCPServer({
            "payment_server_url": "http://localhost:8081"
        })
        
        payment_server = PaymentProcessingMCPServer({
            "order_server_url": "http://localhost:8080"
        })
        
        # Create order
        order_result = await order_server.call_tool("create_order", {
            "customer_id": "cust_001",
            "items": [{"product_id": "prod_001", "quantity": 1}],
            "shipping_address": {"street": "123 Test St", "city": "Test City"}
        })
        
        assert order_result["success"] is True
        order_id = order_result["order_id"]
        
        # Process payment
        payment_result = await payment_server.call_tool("process_payment", {
            "amount": 1299.99,
            "currency": "USD",
            "payment_method": "credit_card",
            "payment_details": {
                "card_number": "4111111111111111",
                "expiry_month": 12,
                "expiry_year": 2025,
                "cvv": "123"
            },
            "order_id": order_id,
            "customer_id": "cust_001"
        })
        
        # Verify both servers have consistent data
        if payment_result.get("success"):
            payment_id = payment_result["payment_id"]
            
            # Check order status in order server
            order_details = await order_server.call_tool("get_order", {"order_id": order_id})
            assert order_details["success"] is True
            
            # Check payment details in payment server
            payment_details = await payment_server.call_tool("get_payment", {"payment_id": payment_id})
            assert payment_details["success"] is True
            
            # Verify order ID matches
            assert payment_details["payment"]["order_id"] == order_id


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 