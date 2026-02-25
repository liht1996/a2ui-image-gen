"""
Test script to diagnose the sketch widget bug
"""

import asyncio
import base64
from agent import ImageGenerationAgent
import os
from dotenv import load_dotenv
from PIL import Image, ImageDraw
import io

load_dotenv()

def create_test_sketch():
    """Create a simple test sketch"""
    img = Image.new('RGB', (512, 512), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple circle
    draw.ellipse([150, 150, 350, 350], outline='black', width=3)
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

async def test_sketch_widget():
    """Test the sketch widget flow"""
    
    api_key = os.getenv('GOOGLE_API_KEY')
    agent = ImageGenerationAgent(api_key)
    
    print("=" * 80)
    print("TEST: Sketch Widget Bug Diagnosis")
    print("=" * 80)
    
    # Step 1: Initial image generation
    print("\n[Step 1] Generate initial image")
    print("-" * 40)
    response1 = await agent.process_message("Generate a simple landscape")
    
    print(f"Response has {len(response1['parts'])} parts:")
    has_image = False
    for i, part in enumerate(response1['parts']):
        if 'text' in part:
            print(f"  Part {i}: text")
        elif 'inlineData' in part:
            print(f"  Part {i}: inlineData (IMAGE) - {len(part['inlineData']['data'])} bytes")
            has_image = True
        elif 'a2ui' in part:
            print(f"  Part {i}: a2ui widget - {part['a2ui']['type']}")
    
    if not has_image:
        print("❌ PROBLEM: No image in initial response!")
    else:
        print("✓ Initial image generated successfully")
    
    # Step 2: Apply sketch adjustment
    print("\n[Step 2] Apply sketch adjustment")
    print("-" * 40)
    
    # Create test sketch
    test_sketch = create_test_sketch()
    print(f"Created test sketch: {len(test_sketch)} bytes")
    
    # Simulate widget update attachment (like frontend sends)
    attachment = {
        "type": "sketch-board-update",
        "data": {"sketch": test_sketch}
    }
    
    print(f"Sending attachment: type={attachment['type']}")
    response2 = await agent.process_message("Apply these adjustments", attachments=[attachment])
    
    print(f"\nResponse has {len(response2['parts'])} parts:")
    has_image = False
    for i, part in enumerate(response2['parts']):
        if 'text' in part:
            print(f"  Part {i}: text - '{part['text'][:50]}...'")
        elif 'inlineData' in part:
            print(f"  Part {i}: inlineData (IMAGE) - {len(part['inlineData']['data'])} bytes")
            has_image = True
        elif 'a2ui' in part:
            print(f"  Part {i}: a2ui widget - {part['a2ui']['type']}")
    
    print("\n" + "=" * 80)
    if not has_image:
        print("❌ BUG CONFIRMED: No image returned after sketch adjustment!")
        print("\nThis means either:")
        print("  1. generate_image() is not being called")
        print("  2. generate_image() is failing and returning None")
        print("  3. generate_a2ui_message() is not including the image")
    else:
        print("✓ BUG FIXED: Image returned successfully after sketch adjustment!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_sketch_widget())
