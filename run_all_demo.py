"""
Complete Demo Runner - Runs All Part 3 Components
This script runs all the codes and shows their outputs clearly
"""

import asyncio
import subprocess
import sys
import os
import time
from datetime import datetime

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*100)
    print(f"🎯 {title}")
    print("="*100)

def print_section(title):
    """Print a formatted section"""
    print(f"\n📋 {title}")
    print("-" * 80)

def run_command(command, description):
    """Run a command and capture its output"""
    print_section(f"Running: {description}")
    print(f"Command: {command}")
    print("-" * 40)
    
    try:
        # Run the command and capture output
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        if result.stdout:
            print("✅ OUTPUT:")
            print(result.stdout)
        
        if result.stderr:
            print("⚠️  WARNINGS/ERRORS:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ Command completed successfully!")
        else:
            print(f"❌ Command failed with exit code: {result.returncode}")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ Command timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

async def run_async_command(command, description):
    """Run an async command"""
    print_section(f"Running Async: {description}")
    print(f"Command: {command}")
    print("-" * 40)
    
    try:
        # Run the async command
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
        
        if stdout:
            print("✅ OUTPUT:")
            print(stdout.decode())
        
        if stderr:
            print("⚠️  WARNINGS/ERRORS:")
            print(stderr.decode())
        
        if process.returncode == 0:
            print("✅ Async command completed successfully!")
        else:
            print(f"❌ Async command failed with exit code: {process.returncode}")
            
        return process.returncode == 0
        
    except asyncio.TimeoutError:
        print("⏰ Async command timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"❌ Error running async command: {e}")
        return False

def check_files():
    """Check if all required files exist"""
    print_section("Checking Required Files")
    
    required_files = [
        "simple-synapse-architecture.py",
        "mcp_servers.py",
        "ai_agents.py",
        "demo.py",
        "show_agent_chat.py",
        "verify_success.py",
        "README.md",
        "requirements.txt"
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            all_exist = False
    
    return all_exist

def show_file_contents():
    """Show brief contents of key files"""
    print_section("Key File Contents Preview")
    
    files_to_show = [
        ("simple-synapse-architecture.py", 20),
        ("mcp_servers.py", 20),
        ("ai_agents.py", 20)
    ]
    
    for filename, lines in files_to_show:
        if os.path.exists(filename):
            print(f"\n📄 {filename} (first {lines} lines):")
            print("-" * 40)
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.readlines()[:lines]
                    for line in content:
                        print(line.rstrip())
                print("...")
            except Exception as e:
                print(f"Error reading file: {e}")

async def run_all_components():
    """Run all components and show outputs"""
    print_header("COMPLETE PART 3 DEMONSTRATION")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check files first
    if not check_files():
        print("❌ Some required files are missing. Please ensure all files are present.")
        return False
    
    # Show file contents
    show_file_contents()
    
    # Run individual components
    print_header("RUNNING INDIVIDUAL COMPONENTS")
    
    # 1. Apache Synapse Architecture
    success1 = run_command("python simple-synapse-architecture.py", "Apache Synapse Architecture")
    
    # 2. MCP Servers
    success2 = run_command("python mcp_servers.py", "MCP Servers")
    
    # 3. AI Agents
    success3 = run_command("python ai_agents.py", "AI Agents")
    
    # 4. Agent Chat Display
    success4 = await run_async_command("python show_agent_chat.py", "Agent Chat Display")
    
    # 5. Success Verification
    success5 = run_command("python verify_success.py", "Success Verification")
    
    # 6. Comprehensive Demo
    success6 = await run_async_command("python demo.py", "Comprehensive Demo")
    
    # Summary
    print_header("FINAL SUMMARY")
    
    results = [
        ("Apache Synapse Architecture", success1),
        ("MCP Servers", success2),
        ("AI Agents", success3),
        ("Agent Chat Display", success4),
        ("Success Verification", success5),
        ("Comprehensive Demo", success6)
    ]
    
    print("\n📊 COMPONENT RESULTS:")
    all_success = True
    for name, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"   {name}: {status}")
        if not success:
            all_success = False
    
    print(f"\n🎯 OVERALL RESULT: {'✅ ALL COMPONENTS WORKING!' if all_success else '❌ SOME COMPONENTS FAILED'}")
    
    if all_success:
        print("\n🏆 CONGRATULATIONS!")
        print("All Part 3 components are working perfectly!")
        print("Your SOA assignment is complete and ready for submission!")
    
    print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return all_success

def show_usage_instructions():
    """Show how to use the different components"""
    print_header("USAGE INSTRUCTIONS")
    
    print("\n🚀 QUICK START COMMANDS:")
    print("   python run_all_demo.py          # Run everything (this script)")
    print("   python demo.py                  # Run comprehensive demo")
    print("   python show_agent_chat.py       # See agent conversations")
    print("   python verify_success.py        # Verify all components")
    
    print("\n🔧 INDIVIDUAL COMPONENTS:")
    print("   python simple-synapse-architecture.py  # Apache Synapse ESB")
    print("   python mcp_servers.py                  # MCP Servers")
    print("   python ai_agents.py                    # AI Agents")
    
    print("\n📚 DOCUMENTATION:")
    print("   README.md                              # Complete project documentation")
    print("   requirements.txt                       # Python dependencies")

async def main():
    """Main function"""
    try:
        # Show usage instructions
        show_usage_instructions()
        
        # Run all components
        success = await run_all_components()
        
        # Final message
        if success:
            print("\n" + "="*100)
            print("🎊 PART 3 DEMONSTRATION COMPLETE!")
            print("="*100)
            print("All components are working perfectly!")
            print("Your SOA assignment is ready for submission!")
        else:
            print("\n" + "="*100)
            print("⚠️  DEMONSTRATION COMPLETED WITH ISSUES")
            print("="*100)
            print("Some components had issues. Check the output above for details.")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demonstration interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 