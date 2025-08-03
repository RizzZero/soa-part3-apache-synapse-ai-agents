# Apache Synapse MCP System Runner

This directory contains scripts to run the complete Apache Synapse MCP system with all its components, tests, and demonstrations.

## Quick Start

### Windows Users
```bash
# Run everything
run_everything.bat

# Run with interactive mode
run_everything.bat --interactive

# Run only tests
run_everything.bat --test-only

# Run only demonstrations
run_everything.bat --demo-only
```

### Unix/Linux/Mac Users
```bash
# Make script executable (first time only)
chmod +x run_everything.sh

# Run everything
./run_everything.sh

# Run with interactive mode
./run_everything.sh --interactive

# Run only tests
./run_everything.sh --test-only

# Run only demonstrations
./run_everything.sh --demo-only
```

### Python Direct (All Platforms)
```bash
# Install dependencies first
pip install -r requirements.txt

# Run everything
python run_everything.py

# Run with interactive mode
python run_everything.py --interactive

# Run only tests
python run_everything.py --test-only

# Run only demonstrations
python run_everything.py --demo-only

# Enable verbose output
python run_everything.py --verbose
```

## What the Runner Does

The system runner performs the following operations in sequence:

### 1. 🔍 Health Check
- Verifies Python version (3.8+)
- Checks for required files
- Validates dependencies
- Tests configuration files

### 2. 🚀 Server Initialization
- **Order Management MCP Server**: Handles orders, inventory, customers
- **Payment Processing MCP Server**: Handles payments, refunds, financial operations
- **Core Synapse MCP Server**: Main integration hub

### 3. 🧪 Test Execution
- Unit tests for all components
- Integration tests for server interaction
- Error handling tests
- Performance tests

### 4. 🎭 Demonstrations
- Complete e-commerce workflow
- Order creation and payment processing
- Error scenarios and recovery
- Cross-server communication

### 5. ⚡ Performance Benchmarks
- Order creation performance
- Payment processing performance
- System throughput metrics

### 6. 🎮 Interactive Mode (Optional)
- Manual testing interface
- Real-time server interaction
- Command-line operations

### 7. 📋 Report Generation
- Comprehensive system report
- Test results summary
- Performance metrics
- Error log (if any)

## Command Line Options

| Option | Description |
|--------|-------------|
| `--test-only` | Run only tests, skip demonstrations |
| `--demo-only` | Run only demonstrations, skip tests |
| `--interactive` | Enable interactive mode for manual testing |
| `--verbose` | Enable verbose logging output |
| `--no-cleanup` | Skip cleanup operations at the end |
| `--help` | Show help message |

## Interactive Mode Commands

When using `--interactive`, you can use these commands:

| Command | Description |
|---------|-------------|
| `create_order` | Create a new order |
| `process_payment` | Process a payment |
| `check_inventory` | Check product inventory |
| `get_customer_orders` | Get customer order history |
| `refund_payment` | Process a refund |
| `server_info` | Get server information |
| `help` | Show available commands |
| `quit` | Exit interactive mode |

## Output Files

The runner generates several output files:

- **`system_runner.log`**: Detailed execution log
- **`system_report_YYYYMMDD_HHMMSS.json`**: Comprehensive system report
- **`venv/`**: Virtual environment (created automatically)

## Example Output

```
╔══════════════════════════════════════════════════════════════╗
║                Apache Synapse MCP System Runner              ║
║                                                              ║
║  🚀 Order Management MCP Server                              ║
║  💳 Payment Processing MCP Server                            ║
║  🔧 Core Synapse MCP Server                                  ║
║  🧪 Tests & Demonstrations                                   ║
║  📊 Performance Benchmarks                                   ║
╚══════════════════════════════════════════════════════════════╝

📋 Health Check Results:
  Python Version: ✅ PASS
  Required Files: ✅ PASS
  Dependencies: ✅ PASS
  Config Files: ✅ PASS

🎯 Server Information:
  📦 Orders: 0
  👥 Customers: 2
  🛍️ Products: 3
  💳 Payments: 0
  🔄 Transactions: 0

📊 Test Results:
  Total: 15
  Passed: 15
  Failed: 0
  Success Rate: 100.0%

⚡ Performance Benchmarks:
  Order Creation: 45.23 ops/sec
  Payment Processing: 12.34 ops/sec

✅ System run completed successfully!
```

## Troubleshooting

### Common Issues

1. **Python not found**
   - Install Python 3.8+ from python.org
   - Ensure Python is in your PATH

2. **Dependencies installation fails**
   - Upgrade pip: `pip install --upgrade pip`
   - Try: `pip install -r requirements.txt --user`

3. **Import errors**
   - Ensure you're running from the project root directory
   - Check that all source files exist

4. **Permission errors (Linux/Mac)**
   - Make script executable: `chmod +x run_everything.sh`

### Getting Help

- Check the main README.md for detailed project information
- Review the generated log files for error details
- Ensure all dependencies are installed correctly

## System Requirements

- **Python**: 3.8 or higher
- **Memory**: 512MB RAM minimum
- **Disk Space**: 100MB free space
- **Network**: Internet connection for dependency installation

## Next Steps

After running the system successfully:

1. **Explore the Code**: Review the source files in `src/`
2. **Modify Configuration**: Edit `config/mcp-servers.yaml`
3. **Add Features**: Extend the MCP servers with new capabilities
4. **Integration**: Connect to real payment gateways and databases
5. **Deployment**: Deploy to production environment

---

**Happy coding! 🚀** 