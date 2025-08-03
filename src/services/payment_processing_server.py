"""
Payment Processing MCP Server

A Model Context Protocol (MCP) server that provides payment processing capabilities
including payment validation, processing, refunds, and financial reporting.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

import aiohttp
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PaymentStatus(Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"
    CRYPTOCURRENCY = "cryptocurrency"


class TransactionType(Enum):
    PAYMENT = "payment"
    REFUND = "refund"
    AUTHORIZATION = "authorization"
    CAPTURE = "capture"
    VOID = "void"


@dataclass
class PaymentMethod:
    id: str
    type: str
    last_four: str
    expiry_month: int
    expiry_year: int
    card_type: str
    is_default: bool = False


@dataclass
class Customer:
    id: str
    name: str
    email: str
    phone: str
    payment_methods: List[PaymentMethod] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Transaction:
    id: str
    payment_id: str
    type: TransactionType
    amount: float
    currency: str
    status: PaymentStatus
    gateway_response: Dict[str, Any]
    created_at: datetime
    processed_at: Optional[datetime] = None


@dataclass
class Payment:
    id: str
    order_id: str
    customer_id: str
    amount: float
    currency: str
    payment_method: str
    status: PaymentStatus
    transactions: List[Transaction]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    refunded_amount: float = 0.0


class PaymentProcessingMCPServer:
    """Payment Processing MCP Server for handling payments, refunds, and financial operations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.payments: Dict[str, Payment] = {}
        self.customers: Dict[str, Customer] = {}
        self.transactions: Dict[str, Transaction] = {}
        self.order_server_url = self.config.get("order_server_url", "http://localhost:8080")
        
        # Payment gateway simulation
        self.gateway_config = {
            "success_rate": 0.95,  # 95% success rate
            "processing_time": 2.0,  # 2 seconds average processing time
            "supported_currencies": ["USD", "EUR", "GBP", "JPY"],
            "supported_methods": ["credit_card", "debit_card", "bank_transfer", "digital_wallet"]
        }
        
        # Initialize with sample data
        self._initialize_sample_data()
        
        logger.info("Payment Processing MCP Server initialized")
    
    def _initialize_sample_data(self):
        """Initialize with sample data for demonstration."""
        # Sample customers with payment methods
        self.customers = {
            "cust_001": Customer(
                id="cust_001",
                name="John Doe",
                email="john.doe@example.com",
                phone="+1-555-0123",
                payment_methods=[
                    PaymentMethod(
                        id="pm_001",
                        type="credit_card",
                        last_four="1234",
                        expiry_month=12,
                        expiry_year=2025,
                        card_type="Visa",
                        is_default=True
                    ),
                    PaymentMethod(
                        id="pm_002",
                        type="debit_card",
                        last_four="5678",
                        expiry_month=8,
                        expiry_year=2026,
                        card_type="Mastercard",
                        is_default=False
                    )
                ]
            ),
            "cust_002": Customer(
                id="cust_002",
                name="Jane Smith",
                email="jane.smith@example.com",
                phone="+1-555-0456",
                payment_methods=[
                    PaymentMethod(
                        id="pm_003",
                        type="credit_card",
                        last_four="9012",
                        expiry_month=3,
                        expiry_year=2027,
                        card_type="American Express",
                        is_default=True
                    )
                ]
            )
        }
        
        logger.info(f"Initialized with {len(self.customers)} customers")
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available MCP tools."""
        return [
            {
                "name": "process_payment",
                "description": "Process a payment for an order",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number", "description": "Payment amount"},
                        "currency": {"type": "string", "description": "Currency code (USD, EUR, etc.)"},
                        "payment_method": {"type": "string", "description": "Payment method type"},
                        "payment_details": {"type": "object", "description": "Payment method details"},
                        "order_id": {"type": "string", "description": "Associated order ID"},
                        "customer_id": {"type": "string", "description": "Customer ID"}
                    },
                    "required": ["amount", "currency", "payment_method", "payment_details", "order_id", "customer_id"]
                }
            },
            {
                "name": "get_payment",
                "description": "Get payment details by payment ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "payment_id": {"type": "string", "description": "Payment ID"}
                    },
                    "required": ["payment_id"]
                }
            },
            {
                "name": "refund_payment",
                "description": "Refund a payment (full or partial)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "payment_id": {"type": "string"},
                        "amount": {"type": "number", "description": "Refund amount (optional for full refund)"},
                        "reason": {"type": "string", "description": "Refund reason"}
                    },
                    "required": ["payment_id", "reason"]
                }
            },
            {
                "name": "authorize_payment",
                "description": "Authorize a payment without capturing funds",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number"},
                        "currency": {"type": "string"},
                        "payment_method": {"type": "string"},
                        "payment_details": {"type": "object"},
                        "order_id": {"type": "string"},
                        "customer_id": {"type": "string"}
                    },
                    "required": ["amount", "currency", "payment_method", "payment_details", "order_id", "customer_id"]
                }
            },
            {
                "name": "capture_payment",
                "description": "Capture a previously authorized payment",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "payment_id": {"type": "string"},
                        "amount": {"type": "number", "description": "Amount to capture (optional for full amount)"}
                    },
                    "required": ["payment_id"]
                }
            },
            {
                "name": "void_payment",
                "description": "Void a payment before it's captured",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "payment_id": {"type": "string"},
                        "reason": {"type": "string"}
                    },
                    "required": ["payment_id", "reason"]
                }
            },
            {
                "name": "get_customer_payments",
                "description": "Get all payments for a customer",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string"},
                        "status": {"type": "string", "description": "Filter by status (optional)"}
                    },
                    "required": ["customer_id"]
                }
            },
            {
                "name": "add_payment_method",
                "description": "Add a new payment method for a customer",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string"},
                        "payment_method": {"type": "object"}
                    },
                    "required": ["customer_id", "payment_method"]
                }
            },
            {
                "name": "validate_payment_method",
                "description": "Validate a payment method",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "payment_method": {"type": "string"},
                        "payment_details": {"type": "object"}
                    },
                    "required": ["payment_method", "payment_details"]
                }
            },
            {
                "name": "get_payment_statistics",
                "description": "Get payment processing statistics",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "description": "Start date (ISO format)"},
                        "end_date": {"type": "string", "description": "End date (ISO format)"},
                        "currency": {"type": "string", "description": "Filter by currency (optional)"}
                    }
                }
            }
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool by name with arguments."""
        try:
            if name == "process_payment":
                return await self._process_payment(arguments)
            elif name == "get_payment":
                return await self._get_payment(arguments)
            elif name == "refund_payment":
                return await self._refund_payment(arguments)
            elif name == "authorize_payment":
                return await self._authorize_payment(arguments)
            elif name == "capture_payment":
                return await self._capture_payment(arguments)
            elif name == "void_payment":
                return await self._void_payment(arguments)
            elif name == "get_customer_payments":
                return await self._get_customer_payments(arguments)
            elif name == "add_payment_method":
                return await self._add_payment_method(arguments)
            elif name == "validate_payment_method":
                return await self._validate_payment_method(arguments)
            elif name == "get_payment_statistics":
                return await self._get_payment_statistics(arguments)
            else:
                return {"error": f"Unknown tool: {name}"}
        except Exception as e:
            logger.error(f"Error calling tool {name}: {str(e)}")
            return {"error": str(e)}
    
    async def _process_payment(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Process a payment."""
        amount = args["amount"]
        currency = args["currency"]
        payment_method = args["payment_method"]
        payment_details = args["payment_details"]
        order_id = args["order_id"]
        customer_id = args["customer_id"]
        
        # Validate customer
        if customer_id not in self.customers:
            return {"error": f"Customer {customer_id} not found"}
        
        # Validate currency
        if currency not in self.gateway_config["supported_currencies"]:
            return {"error": f"Unsupported currency: {currency}"}
        
        # Validate payment method
        if payment_method not in self.gateway_config["supported_methods"]:
            return {"error": f"Unsupported payment method: {payment_method}"}
        
        # Simulate payment gateway processing
        await asyncio.sleep(self.gateway_config["processing_time"])
        
        # Simulate success/failure based on configured rate
        import random
        success = random.random() < self.gateway_config["success_rate"]
        
        # Create payment
        payment_id = f"pay_{uuid.uuid4().hex[:8]}"
        
        if success:
            # Create transaction
            transaction = Transaction(
                id=f"txn_{uuid.uuid4().hex[:8]}",
                payment_id=payment_id,
                type=TransactionType.PAYMENT,
                amount=amount,
                currency=currency,
                status=PaymentStatus.COMPLETED,
                gateway_response={
                    "transaction_id": f"gateway_{uuid.uuid4().hex[:12]}",
                    "status": "approved",
                    "authorization_code": f"AUTH{uuid.uuid4().hex[:6].upper()}",
                    "response_code": "00"
                },
                created_at=datetime.now(),
                processed_at=datetime.now()
            )
            
            # Create payment
            payment = Payment(
                id=payment_id,
                order_id=order_id,
                customer_id=customer_id,
                amount=amount,
                currency=currency,
                payment_method=payment_method,
                status=PaymentStatus.COMPLETED,
                transactions=[transaction],
                metadata={
                    "gateway": "simulated_gateway",
                    "processing_time": self.gateway_config["processing_time"]
                },
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.payments[payment_id] = payment
            self.transactions[transaction.id] = transaction
            
            # Update order status in Order Management Server
            await self._update_order_payment_status(order_id, "paid", payment_id)
            
            logger.info(f"Payment {payment_id} processed successfully for order {order_id}")
            
            return {
                "success": True,
                "payment_id": payment_id,
                "transaction_id": transaction.id,
                "status": "completed",
                "amount": amount,
                "currency": currency,
                "message": "Payment processed successfully"
            }
        else:
            # Failed payment
            transaction = Transaction(
                id=f"txn_{uuid.uuid4().hex[:8]}",
                payment_id=payment_id,
                type=TransactionType.PAYMENT,
                amount=amount,
                currency=currency,
                status=PaymentStatus.FAILED,
                gateway_response={
                    "transaction_id": f"gateway_{uuid.uuid4().hex[:12]}",
                    "status": "declined",
                    "error_code": "05",
                    "error_message": "Insufficient funds"
                },
                created_at=datetime.now(),
                processed_at=datetime.now()
            )
            
            payment = Payment(
                id=payment_id,
                order_id=order_id,
                customer_id=customer_id,
                amount=amount,
                currency=currency,
                payment_method=payment_method,
                status=PaymentStatus.FAILED,
                transactions=[transaction],
                metadata={
                    "gateway": "simulated_gateway",
                    "processing_time": self.gateway_config["processing_time"]
                },
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.payments[payment_id] = payment
            self.transactions[transaction.id] = transaction
            
            logger.warning(f"Payment {payment_id} failed for order {order_id}")
            
            return {
                "success": False,
                "payment_id": payment_id,
                "status": "failed",
                "error": "Payment declined by gateway",
                "message": "Payment processing failed"
            }
    
    async def _get_payment(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get payment details."""
        payment_id = args["payment_id"]
        
        if payment_id not in self.payments:
            return {"error": f"Payment {payment_id} not found"}
        
        payment = self.payments[payment_id]
        
        return {
            "success": True,
            "payment": {
                "id": payment.id,
                "order_id": payment.order_id,
                "customer_id": payment.customer_id,
                "amount": payment.amount,
                "currency": payment.currency,
                "payment_method": payment.payment_method,
                "status": payment.status.value,
                "refunded_amount": payment.refunded_amount,
                "transactions": [
                    {
                        "id": txn.id,
                        "type": txn.type.value,
                        "amount": txn.amount,
                        "status": txn.status.value,
                        "created_at": txn.created_at.isoformat(),
                        "processed_at": txn.processed_at.isoformat() if txn.processed_at else None
                    }
                    for txn in payment.transactions
                ],
                "metadata": payment.metadata,
                "created_at": payment.created_at.isoformat(),
                "updated_at": payment.updated_at.isoformat()
            }
        }
    
    async def _refund_payment(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Refund a payment."""
        payment_id = args["payment_id"]
        reason = args["reason"]
        refund_amount = args.get("amount")  # Optional, defaults to full amount
        
        if payment_id not in self.payments:
            return {"error": f"Payment {payment_id} not found"}
        
        payment = self.payments[payment_id]
        
        if payment.status != PaymentStatus.COMPLETED:
            return {"error": "Payment must be completed to be refunded"}
        
        if refund_amount is None:
            refund_amount = payment.amount - payment.refunded_amount
        
        if refund_amount > (payment.amount - payment.refunded_amount):
            return {"error": "Refund amount exceeds available amount"}
        
        # Create refund transaction
        refund_transaction = Transaction(
            id=f"txn_{uuid.uuid4().hex[:8]}",
            payment_id=payment_id,
            type=TransactionType.REFUND,
            amount=refund_amount,
            currency=payment.currency,
            status=PaymentStatus.COMPLETED,
            gateway_response={
                "transaction_id": f"gateway_{uuid.uuid4().hex[:12]}",
                "status": "approved",
                "refund_id": f"REFUND{uuid.uuid4().hex[:6].upper()}",
                "reason": reason
            },
            created_at=datetime.now(),
            processed_at=datetime.now()
        )
        
        # Update payment
        payment.transactions.append(refund_transaction)
        payment.refunded_amount += refund_amount
        payment.updated_at = datetime.now()
        
        if payment.refunded_amount >= payment.amount:
            payment.status = PaymentStatus.REFUNDED
        else:
            payment.status = PaymentStatus.PARTIALLY_REFUNDED
        
        self.transactions[refund_transaction.id] = refund_transaction
        
        logger.info(f"Refunded {refund_amount} from payment {payment_id}")
        
        return {
            "success": True,
            "refund_id": refund_transaction.id,
            "amount": refund_amount,
            "currency": payment.currency,
            "status": payment.status.value,
            "message": "Refund processed successfully"
        }
    
    async def _authorize_payment(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Authorize a payment without capturing funds."""
        # Similar to process_payment but with status AUTHORIZED
        payment_result = await self._process_payment(args)
        
        if payment_result.get("success"):
            payment_id = payment_result["payment_id"]
            payment = self.payments[payment_id]
            payment.status = PaymentStatus.AUTHORIZED
            payment.updated_at = datetime.now()
            
            # Update transaction status
            for transaction in payment.transactions:
                transaction.status = PaymentStatus.AUTHORIZED
            
            payment_result["status"] = "authorized"
            payment_result["message"] = "Payment authorized successfully"
        
        return payment_result
    
    async def _capture_payment(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Capture a previously authorized payment."""
        payment_id = args["payment_id"]
        capture_amount = args.get("amount")
        
        if payment_id not in self.payments:
            return {"error": f"Payment {payment_id} not found"}
        
        payment = self.payments[payment_id]
        
        if payment.status != PaymentStatus.AUTHORIZED:
            return {"error": "Payment must be authorized to be captured"}
        
        if capture_amount is None:
            capture_amount = payment.amount
        
        # Create capture transaction
        capture_transaction = Transaction(
            id=f"txn_{uuid.uuid4().hex[:8]}",
            payment_id=payment_id,
            type=TransactionType.CAPTURE,
            amount=capture_amount,
            currency=payment.currency,
            status=PaymentStatus.COMPLETED,
            gateway_response={
                "transaction_id": f"gateway_{uuid.uuid4().hex[:12]}",
                "status": "approved",
                "capture_id": f"CAPTURE{uuid.uuid4().hex[:6].upper()}"
            },
            created_at=datetime.now(),
            processed_at=datetime.now()
        )
        
        # Update payment
        payment.transactions.append(capture_transaction)
        payment.status = PaymentStatus.COMPLETED
        payment.updated_at = datetime.now()
        
        self.transactions[capture_transaction.id] = capture_transaction
        
        logger.info(f"Captured {capture_amount} from payment {payment_id}")
        
        return {
            "success": True,
            "capture_id": capture_transaction.id,
            "amount": capture_amount,
            "currency": payment.currency,
            "status": "completed",
            "message": "Payment captured successfully"
        }
    
    async def _void_payment(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Void a payment before it's captured."""
        payment_id = args["payment_id"]
        reason = args["reason"]
        
        if payment_id not in self.payments:
            return {"error": f"Payment {payment_id} not found"}
        
        payment = self.payments[payment_id]
        
        if payment.status != PaymentStatus.AUTHORIZED:
            return {"error": "Payment must be authorized to be voided"}
        
        # Create void transaction
        void_transaction = Transaction(
            id=f"txn_{uuid.uuid4().hex[:8]}",
            payment_id=payment_id,
            type=TransactionType.VOID,
            amount=0.0,
            currency=payment.currency,
            status=PaymentStatus.COMPLETED,
            gateway_response={
                "transaction_id": f"gateway_{uuid.uuid4().hex[:12]}",
                "status": "approved",
                "void_id": f"VOID{uuid.uuid4().hex[:6].upper()}",
                "reason": reason
            },
            created_at=datetime.now(),
            processed_at=datetime.now()
        )
        
        # Update payment
        payment.transactions.append(void_transaction)
        payment.status = PaymentStatus.CANCELLED
        payment.updated_at = datetime.now()
        
        self.transactions[void_transaction.id] = void_transaction
        
        logger.info(f"Voided payment {payment_id}")
        
        return {
            "success": True,
            "void_id": void_transaction.id,
            "status": "cancelled",
            "message": "Payment voided successfully"
        }
    
    async def _get_customer_payments(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get all payments for a customer."""
        customer_id = args["customer_id"]
        status_filter = args.get("status")
        
        if customer_id not in self.customers:
            return {"error": f"Customer {customer_id} not found"}
        
        customer_payments = []
        for payment in self.payments.values():
            if payment.customer_id == customer_id:
                if status_filter and payment.status.value != status_filter:
                    continue
                
                customer_payments.append({
                    "id": payment.id,
                    "order_id": payment.order_id,
                    "amount": payment.amount,
                    "currency": payment.currency,
                    "status": payment.status.value,
                    "refunded_amount": payment.refunded_amount,
                    "created_at": payment.created_at.isoformat()
                })
        
        return {
            "success": True,
            "customer_id": customer_id,
            "payments": customer_payments,
            "count": len(customer_payments)
        }
    
    async def _add_payment_method(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new payment method for a customer."""
        customer_id = args["customer_id"]
        payment_method_data = args["payment_method"]
        
        if customer_id not in self.customers:
            return {"error": f"Customer {customer_id} not found"}
        
        customer = self.customers[customer_id]
        
        # Create new payment method
        payment_method = PaymentMethod(
            id=f"pm_{uuid.uuid4().hex[:8]}",
            type=payment_method_data["type"],
            last_four=payment_method_data["last_four"],
            expiry_month=payment_method_data["expiry_month"],
            expiry_year=payment_method_data["expiry_year"],
            card_type=payment_method_data.get("card_type", "Unknown"),
            is_default=payment_method_data.get("is_default", False)
        )
        
        # If this is set as default, unset others
        if payment_method.is_default:
            for pm in customer.payment_methods:
                pm.is_default = False
        
        customer.payment_methods.append(payment_method)
        
        logger.info(f"Added payment method {payment_method.id} for customer {customer_id}")
        
        return {
            "success": True,
            "payment_method_id": payment_method.id,
            "message": "Payment method added successfully"
        }
    
    async def _validate_payment_method(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a payment method."""
        payment_method = args["payment_method"]
        payment_details = args["payment_details"]
        
        # Simulate validation
        validation_result = {
            "valid": True,
            "card_type": payment_details.get("card_type", "Unknown"),
            "last_four": payment_details.get("last_four", "****"),
            "expiry_valid": True,
            "cvv_valid": True
        }
        
        # Check expiry
        current_date = datetime.now()
        expiry_month = payment_details.get("expiry_month")
        expiry_year = payment_details.get("expiry_year")
        
        if expiry_month and expiry_year:
            expiry_date = datetime(expiry_year, expiry_month, 1)
            if expiry_date < current_date:
                validation_result["expiry_valid"] = False
                validation_result["valid"] = False
        
        return {
            "success": True,
            "validation": validation_result,
            "message": "Payment method validation completed"
        }
    
    async def _get_payment_statistics(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get payment processing statistics."""
        start_date = args.get("start_date")
        end_date = args.get("end_date")
        currency_filter = args.get("currency")
        
        # Filter payments by date range
        filtered_payments = []
        for payment in self.payments.values():
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                if payment.created_at < start_dt:
                    continue
            
            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                if payment.created_at > end_dt:
                    continue
            
            if currency_filter and payment.currency != currency_filter:
                continue
            
            filtered_payments.append(payment)
        
        # Calculate statistics
        total_payments = len(filtered_payments)
        total_amount = sum(p.amount for p in filtered_payments)
        successful_payments = len([p for p in filtered_payments if p.status == PaymentStatus.COMPLETED])
        failed_payments = len([p for p in filtered_payments if p.status == PaymentStatus.FAILED])
        total_refunds = sum(p.refunded_amount for p in filtered_payments)
        
        success_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 0
        
        return {
            "success": True,
            "statistics": {
                "total_payments": total_payments,
                "total_amount": total_amount,
                "successful_payments": successful_payments,
                "failed_payments": failed_payments,
                "success_rate": round(success_rate, 2),
                "total_refunds": total_refunds,
                "net_amount": total_amount - total_refunds
            },
            "period": {
                "start_date": start_date,
                "end_date": end_date,
                "currency": currency_filter
            }
        }
    
    async def _update_order_payment_status(self, order_id: str, status: str, payment_id: str):
        """Update order payment status in Order Management Server."""
        try:
            async with aiohttp.ClientSession() as session:
                update_data = {
                    "order_id": order_id,
                    "payment_status": status,
                    "payment_id": payment_id
                }
                
                async with session.post(
                    f"{self.order_server_url}/update_payment_status",
                    json=update_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        logger.info(f"Updated order {order_id} payment status to {status}")
                    else:
                        logger.warning(f"Failed to update order {order_id} payment status")
        
        except Exception as e:
            logger.error(f"Error updating order payment status: {str(e)}")
    
    async def get_server_info(self) -> Dict[str, Any]:
        """Get server information."""
        return {
            "name": "Payment Processing MCP Server",
            "version": "1.0.0",
            "description": "Handles payment processing, validation, and financial operations",
            "tools_count": len(await self.get_available_tools()),
            "payments_count": len(self.payments),
            "customers_count": len(self.customers),
            "transactions_count": len(self.transactions),
            "gateway_config": self.gateway_config
        }


# Example usage and testing
async def main():
    """Example usage of the Payment Processing MCP Server."""
    server = PaymentProcessingMCPServer()
    
    # Get server info
    info = await server.get_server_info()
    logger.info(f"Server Info: {info}")
    
    # Get available tools
    tools = await server.get_available_tools()
    logger.info(f"Available tools: {[tool['name'] for tool in tools]}")
    
    # Example: Process a payment
    payment_result = await server.call_tool("process_payment", {
        "amount": 1299.99,
        "currency": "USD",
        "payment_method": "credit_card",
        "payment_details": {
            "card_number": "4111111111111111",
            "expiry_month": 12,
            "expiry_year": 2025,
            "cvv": "123"
        },
        "order_id": "order_000001",
        "customer_id": "cust_001"
    })
    
    logger.info(f"Payment processing result: {payment_result}")


if __name__ == "__main__":
    asyncio.run(main()) 