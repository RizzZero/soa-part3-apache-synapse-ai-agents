# Apache Synapse Architecture with Model Context Protocol (MCP)

## Overview

This project implements a comprehensive Apache Synapse architecture that leverages the Model Context Protocol (MCP) framework to provide secure, controlled access to enterprise integration capabilities. The architecture combines Apache Synapse's ESB (Enterprise Service Bus) capabilities with MCP's standardized protocol for AI model interactions, featuring two interactive MCP servers for e-commerce operations.

## MCP Servers

### 1. Order Management MCP Server
- **Purpose**: Handles order processing, inventory management, and customer operations
- **Features**:
  - Order creation and management
  - Inventory tracking and updates
  - Customer management
  - Order status tracking
  - Integration with Payment Processing Server

### 2. Payment Processing MCP Server
- **Purpose**: Handles payment validation, processing, and financial operations
- **Features**:
  - Payment processing and validation
  - Refund management
  - Payment method management
  - Financial reporting and statistics
  - Integration with Order Management Server

### 3. Server Interaction
- **Cross-Server Communication**: Seamless integration between order and payment processing
- **Event-Driven Architecture**: Real-time updates between services
- **Data Consistency**: Maintains consistency across both servers
- **Error Handling**: Robust error handling and recovery mechanisms

## Architecture Components

### 1. Core Synapse MCP Server
- **Purpose**: Main integration hub that exposes Synapse capabilities through MCP
- **Features**: 
  - Proxy service management
  - Message transformation
  - Routing and mediation
  - Security and authentication
  - Monitoring and logging

### 2. Order Management MCP Server
- **Purpose**: Dedicated server for e-commerce order operations
- **Features**:
  - Order lifecycle management
  - Inventory control
  - Customer data management
  - Integration with payment processing
  - Real-time status updates

### 3. Payment Processing MCP Server
- **Purpose**: Dedicated server for financial transactions
- **Features**:
  - Payment gateway integration
  - Transaction processing
  - Refund management
  - Financial reporting
  - Fraud detection

### 4. MCP Client Integration Layer
- **Purpose**: Connects AI models and clients to Synapse services
- **Features**:
  - Standardized MCP protocol implementation
  - Authentication and authorization
  - Request/response handling
  - Error management

### 5. Service Registry
- **Purpose**: Manages available services and their metadata
- **Features**:
  - Service discovery
  - Version management
  - Health monitoring
  - Load balancing

### 6. Message Processing Pipeline
- **Purpose**: Handles message transformation and routing
- **Features**:
  - XML/JSON transformation
  - XSLT processing
  - Message validation
  - Error handling

## Directory Structure

```
apache-synapse-mcp/
├── src/
│   ├── core/                 # Core Synapse MCP server
│   ├── services/             # Service definitions
│   │   ├── order_management_server.py    # Order Management MCP Server
│   │   ├── payment_processing_server.py  # Payment Processing MCP Server
│   │   └── proxy_service.py              # Proxy service management
│   ├── transformers/         # Message transformers
│   ├── security/             # Security and authentication
│   └── monitoring/           # Monitoring and logging
├── config/                   # Configuration files
│   ├── synapse-mcp.example.yaml          # Main configuration
│   └── mcp-servers.yaml                   # MCP servers configuration
├── tests/                    # Unit and integration tests
│   ├── test_basic_functionality.py       # Basic functionality tests
│   └── test_mcp_servers_interaction.py   # MCP servers interaction tests
├── docs/                     # Documentation
└── examples/                 # Usage examples
│   ├── basic_usage.py                    # Basic usage examples
│   └── mcp_servers_interaction.py        # MCP servers interaction demo
```

## Key Features

### MCP Integration
- **Standardized Protocol**: Implements MCP specification for consistent AI model interactions
- **Tool Access**: Provides secure access to Synapse capabilities as MCP tools
- **Resource Management**: Manages Synapse resources through MCP resource system
- **Multi-Server Architecture**: Two specialized MCP servers for different domains

### E-commerce Integration
- **Order Management**: Complete order lifecycle from creation to fulfillment
- **Payment Processing**: Secure payment handling with multiple payment methods
- **Inventory Management**: Real-time inventory tracking and updates
- **Customer Management**: Comprehensive customer data and payment method management

### Enterprise Integration
- **Service Proxy**: Acts as a proxy for backend services
- **Message Mediation**: Transforms messages between different formats
- **Routing**: Intelligent message routing based on content and headers
- **Load Balancing**: Distributes load across multiple service instances

### Security
- **Authentication**: OAuth2, JWT, and API key support
- **Authorization**: Role-based access control
- **Encryption**: End-to-end message encryption
- **Audit Logging**: Comprehensive security audit trails

### Monitoring
- **Metrics Collection**: Performance and health metrics
- **Logging**: Structured logging with correlation IDs
- **Alerting**: Proactive monitoring and alerting
- **Dashboard**: Real-time monitoring dashboard

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+ (for TypeScript components)
- Apache Synapse 4.x
- MCP client (Claude Desktop, Cursor, etc.)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd apache-synapse-mcp
```

2. Install dependencies:
```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies
npm install
```

3. Configure the server:
```bash
cp config/synapse-mcp.example.yaml config/synapse-mcp.yaml
# Edit configuration file with your settings
```

4. Start the MCP server:
```bash
python -m synapse_mcp.server
```

5. Run the MCP servers interaction demo:
```bash
python examples/mcp_servers_interaction.py
```

6. Run tests:
```bash
# Run basic functionality tests
pytest tests/test_basic_functionality.py -v

# Run MCP servers interaction tests
pytest tests/test_mcp_servers_interaction.py -v
```

### MCP Client Configuration

Add to your MCP client configuration (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "synapse": {
      "command": "python",
      "args": ["-m", "synapse_mcp.server"],
      "env": {
        "SYNAPSE_CONFIG": "/path/to/config/synapse-mcp.yaml"
      }
    },
    "order-management": {
      "command": "python",
      "args": ["-m", "src.services.order_management_server"],
      "env": {
        "MCP_CONFIG": "/path/to/config/mcp-servers.yaml"
      }
    },
    "payment-processing": {
      "command": "python",
      "args": ["-m", "src.services.payment_processing_server"],
      "env": {
        "MCP_CONFIG": "/path/to/config/mcp-servers.yaml"
      }
    }
  }
}
```

## Usage Examples

### E-commerce Workflow with MCP Servers
```python
from src.services.order_management_server import OrderManagementMCPServer
from src.services.payment_processing_server import PaymentProcessingMCPServer

# Initialize both servers
order_server = OrderManagementMCPServer()
payment_server = PaymentProcessingMCPServer()

# Step 1: Create an order
order_result = await order_server.call_tool("create_order", {
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

# Step 2: Process payment
payment_result = await payment_server.call_tool("process_payment", {
    "amount": 1359.96,
    "currency": "USD",
    "payment_method": "credit_card",
    "payment_details": {
        "card_number": "4111111111111111",
        "expiry_month": 12,
        "expiry_year": 2025,
        "cvv": "123"
    },
    "order_id": order_result["order_id"],
    "customer_id": "cust_001"
})

# Step 3: Update order status
await order_server.call_tool("update_order_status", {
    "order_id": order_result["order_id"],
    "status": "confirmed"
})
```

### Creating a Proxy Service
```python
from synapse_mcp import SynapseMCPServer

# Initialize server
server = SynapseMCPServer()

# Create proxy service
proxy_config = {
    "name": "user-service-proxy",
    "target": "http://backend-service:8080",
    "transforms": ["xml-to-json"],
    "security": "oauth2"
}

server.create_proxy_service(proxy_config)
```

### Message Transformation
```python
# Transform XML to JSON
transformer = server.get_transformer("xml-to-json")
result = transformer.transform(xml_message)
```

### Service Discovery
```python
# List available services
services = server.list_services()

# Get service details
service_info = server.get_service_info("user-service-proxy")
```

## API Reference

### Core Methods

#### `create_proxy_service(config)`
Creates a new proxy service with the specified configuration.

#### `list_services()`
Returns a list of all available services.

#### `get_service_info(service_name)`
Returns detailed information about a specific service.

#### `transform_message(transformer_name, message)`
Transforms a message using the specified transformer.

#### `route_message(message, routing_rules)`
Routes a message based on the specified rules.

### Configuration

The server configuration supports:

- **Service Definitions**: Proxy services, transformers, and endpoints
- **Security Settings**: Authentication and authorization configuration
- **Monitoring**: Metrics collection and logging settings
- **Performance**: Connection pooling and timeout settings

## Security Considerations

1. **Authentication**: All requests must be authenticated
2. **Authorization**: Role-based access control for all operations
3. **Encryption**: Sensitive data is encrypted in transit and at rest
4. **Audit**: All operations are logged for security auditing
5. **Rate Limiting**: Prevents abuse through rate limiting

## Monitoring and Observability

### Metrics
- Request/response times
- Error rates
- Throughput
- Resource utilization

### Logging
- Structured JSON logging
- Correlation IDs for request tracing
- Security event logging
- Performance metrics

### Alerting
- Service health monitoring
- Performance threshold alerts
- Security incident alerts
- Resource utilization alerts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the Apache License 2.0.

## References

- [Model Context Protocol](https://modelcontextprotocol.io)
- [Apache Synapse](https://synapse.apache.org)
- [MCP Servers Repository](https://github.com/modelcontextprotocol/servers) 