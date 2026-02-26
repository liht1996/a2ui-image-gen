#!/usr/bin/env python3
"""
Quick test to verify the new A2UI implementation works
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Testing New A2UI Image Generation Implementation")
print("=" * 60)

# Test 1: Import packages
print("\n[1] Testing package imports...")
try:
    import a2a
    print("✓ a2a-sdk imported successfully")
    from a2a.server.apps import A2AStarletteApplication
    print("✓ A2AStarletteApplication available")
except ImportError as e:
    print(f"✗ Failed to import a2a-sdk: {e}")
    sys.exit(1)

try:
    from google.adk.agents.llm_agent import LlmAgent
    print("✓ google-adk imported successfully")
except ImportError as e:
    print(f"✗ Failed to import google-adk: {e}")
    sys.exit(1)

try:
    from a2ui.inference.schema.manager import A2uiSchemaManager
    print("✓ a2ui module imported successfully")
except ImportError as e:
    print(f"✗ Failed to import a2ui: {e}")
    sys.exit(1)

# Test 2: Import our modules
print("\n[2] Testing local module imports...")
try:
    from agent_new import ImageGenerationAgent
    print("✓ ImageGenerationAgent imported")
except ImportError as e:
    print(f"✗ Failed to import agent_new: {e}")
    sys.exit(1)

try:
    from agent_executor import ImageGenerationAgentExecutor
    print("✓ ImageGenerationAgentExecutor imported")
except ImportError as e:
    print(f"✗ Failed to import agent_executor: {e}")
    sys.exit(1)

# Test 3: Check API key
print("\n[3] Checking environment...")
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if api_key:
    print(f"✓ API key found (length: {len(api_key)})")
else:
    print("✗ No API key found in environment")
    print("  Please set GOOGLE_API_KEY or GEMINI_API_KEY in .env")
    sys.exit(1)

# Test 4: Create agent instances
print("\n[4] Creating agent instances...")
try:
    base_url = "http://localhost:10002"
    ui_agent = ImageGenerationAgent(base_url=base_url, use_ui=True)
    print("✓ UI agent created")
    
    text_agent = ImageGenerationAgent(base_url=base_url, use_ui=False)
    print("✓ Text agent created")
except Exception as e:
    print(f"✗ Failed to create agents: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Create executor
print("\n[5] Creating agent executor...")
try:
    executor = ImageGenerationAgentExecutor(ui_agent, text_agent)
    print("✓ Agent executor created")
except Exception as e:
    print(f"✗ Failed to create executor: {e}")
    sys.exit(1)

# Test 6: Get agent card
print("\n[6] Getting agent card...")
try:
    card = ui_agent.get_agent_card()
    print(f"✓ Agent card: {card.name}")
    print(f"  Description: {card.description}")
    print(f"  Skills: {len(card.skills)}")
except Exception as e:
    print(f"✗ Failed to get agent card: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("All tests passed! ✓")
print("=" * 60)
print("\nYou can now start the server with:")
print("  python server_new.py --host localhost --port 10002")
print()
