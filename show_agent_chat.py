"""
Agent Chat Display Script
This script shows the conversations between AI agents clearly
"""

import asyncio
import json
from datetime import datetime
import importlib.util
import sys

# Import the ai_agents module
spec = importlib.util.spec_from_file_location("ai_agents", "ai_agents.py")
ai_agents = importlib.util.module_from_spec(spec)
sys.modules["ai_agents"] = ai_agents
spec.loader.exec_module(ai_agents)

async def show_agent_conversations():
    """Show detailed agent conversations"""
    print("🤖 AI AGENT CONVERSATIONS")
    print("="*80)
    
    # Create orchestrator
    orchestrator = ai_agents.AgentOrchestrator()
    
    # Create agents
    user_agent = ai_agents.UserServiceAgent()
    order_agent = ai_agents.OrderServiceAgent()
    
    # Add agents to orchestrator
    orchestrator.add_agent(user_agent)
    orchestrator.add_agent(order_agent)
    
    print("✅ Agents created: UserServiceAgent and OrderServiceAgent")
    
    # Start all components
    await orchestrator.start_all()
    print("✅ All agents started and ready to chat")
    
    print("\n" + "="*80)
    print("💬 CONVERSATION 1: USER-ORDER INTEGRATION SCENARIO")
    print("="*80)
    
    # Execute first scenario
    await orchestrator.execute_scenario("user_order_integration")
    
    print("\n" + "="*80)
    print("💬 CONVERSATION 2: PAYMENT PROCESSING SCENARIO")
    print("="*80)
    
    # Execute second scenario
    await orchestrator.execute_scenario("payment_processing")
    
    print("\n" + "="*80)
    print("📋 COMPLETE CONVERSATION LOG")
    print("="*80)
    
    # Display all conversations in a chat-like format
    for i, entry in enumerate(orchestrator.scenario_log, 1):
        print(f"\n💬 Message #{i}")
        print(f"⏰ Time: {entry['timestamp']}")
        print(f"👤 From: {entry['sender']}")
        print(f"👥 To: {entry['receiver']}")
        print(f"📝 Message: {json.dumps(entry['message'], indent=2)}")
        
        if entry['response']:
            print(f"💭 Response: {json.dumps(entry['response'], indent=2)}")
        else:
            print("💭 Response: No response")
        
        print("-" * 80)
    
    # Stop all components
    await orchestrator.stop_all()
    
    print(f"\n✅ Total messages exchanged: {len(orchestrator.scenario_log)}")
    print("🎉 Agent conversations completed!")

def show_chat_summary():
    """Show a summary of what the agents discussed"""
    print("\n" + "="*80)
    print("📊 CHAT SUMMARY")
    print("="*80)
    
    print("\n🤖 AGENTS INVOLVED:")
    print("   • UserServiceAgent - Manages user operations")
    print("   • OrderServiceAgent - Manages order operations")
    
    print("\n💬 CONVERSATION TOPICS:")
    print("   1. User Validation")
    print("   2. Order Creation")
    print("   3. Payment Processing")
    print("   4. Order Information Retrieval")
    print("   5. Order Validation")
    
    print("\n🔄 BUSINESS WORKFLOWS:")
    print("   • User-Order Integration: User validation → Order creation → Payment")
    print("   • Payment Processing: Order info → Validation → Payment processing")
    
    print("\n🎯 KEY INTERACTIONS:")
    print("   • Agents coordinate to validate users before creating orders")
    print("   • Agents work together to process payments securely")
    print("   • Agents share information about orders and users")
    print("   • Agents handle complex business logic collaboratively")

async def main():
    """Main function to show agent chat"""
    print("🎭 AI AGENT CHAT DISPLAY")
    print("="*80)
    print("This will show you the conversations between the AI agents!")
    print("="*80)
    
    try:
        await show_agent_conversations()
        show_chat_summary()
        
        print("\n" + "="*80)
        print("🎊 AGENT CHAT DISPLAY COMPLETE!")
        print("="*80)
        
    except Exception as e:
        print(f"❌ Error showing agent chat: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 