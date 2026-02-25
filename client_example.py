"""
Example client for testing the A2UI Image Generation Agent
"""

import asyncio
import aiohttp
import json
import sys


class A2UIClient:
    """Simple client for testing A2UI agent"""
    
    def __init__(self, base_url: str = "http://localhost:10002"):
        self.base_url = base_url
        self.message_counter = 0
    
    async def send_message(self, text: str, widget_data: dict = None) -> dict:
        """Send a message to the agent"""
        self.message_counter += 1
        
        # Build message parts
        parts = [{"text": text}]
        
        # Add widget data if provided
        if widget_data:
            if "color_tone" in widget_data:
                parts.append({
                    "a2ui": {
                        "type": "color-tone-control",
                        "id": "color-tone-widget",
                        "properties": widget_data["color_tone"]
                    }
                })
            if "sketch" in widget_data:
                parts.append({
                    "a2ui": {
                        "type": "sketch-board",
                        "id": "sketch-board-widget",
                        "properties": {"sketch": widget_data["sketch"]}
                    }
                })
        
        # Build A2A request
        request = {
            "jsonrpc": "2.0",
            "method": "message/stream",
            "params": {
                "message": {
                    "messageId": f"msg-{self.message_counter}",
                    "role": "user",
                    "parts": parts
                }
            },
            "id": self.message_counter
        }
        
        # Send request
        headers = {
            "Content-Type": "application/json",
            "X-A2A-Extensions": "https://a2ui.org/a2a-extension/a2ui/v0.8"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url, json=request, headers=headers) as response:
                return await response.json()
    
    async def get_capabilities(self) -> dict:
        """Get agent capabilities"""
        request = {
            "jsonrpc": "2.0",
            "method": "agent/capabilities",
            "params": {},
            "id": 0
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url, json=request) as response:
                return await response.json()
    
    def print_response(self, response: dict):
        """Pretty print response"""
        print("\n" + "="*60)
        
        if "error" in response:
            print(f"ERROR: {response['error']}")
            return
        
        result = response.get("result", {})
        
        # Print text
        for part in result.get("parts", []):
            if "text" in part:
                print(f"Text: {part['text']}")
            
            if "inlineData" in part:
                print(f"Image: {part['inlineData']['mimeType']} "
                      f"({len(part['inlineData']['data'])} bytes)")
            
            if "a2ui" in part:
                widget = part["a2ui"]
                print(f"\nWidget: {widget['type']}")
                print(f"Properties: {json.dumps(widget.get('properties', {}), indent=2)}")
        
        print("="*60 + "\n")


async def run_examples():
    """Run example scenarios"""
    client = A2UIClient()
    
    print("A2UI Image Generation Agent - Client Examples")
    print("=" * 60)
    
    # Example 1: Basic generation (no widgets)
    print("\n1. Basic Image Generation (no widgets expected)")
    response = await client.send_message("Generate an image of a mountain landscape")
    client.print_response(response)
    
    # Example 2: Color tone control
    print("\n2. Image with Color Tone Control")
    response = await client.send_message(
        "Generate an image of a sunset with warm orange tones"
    )
    client.print_response(response)
    
    # Example 3: Sketch board
    print("\n3. Image with Sketch Board")
    response = await client.send_message(
        "Generate an image with a specific composition - large tree on the left, house on the right"
    )
    client.print_response(response)
    
    # Example 4: Both widgets
    print("\n4. Image with Both Widgets")
    response = await client.send_message(
        "Generate an image with blue cool tones, with mountains in the background and a lake in the foreground"
    )
    client.print_response(response)
    
    # Example 5: Widget update simulation
    print("\n5. Updating Color Tone")
    response = await client.send_message(
        "Adjust the previous image",
        widget_data={
            "color_tone": {
                "hue": 240,  # Blue
                "saturation": 70,
                "lightness": 60,
                "temperature": "cool"
            }
        }
    )
    client.print_response(response)


async def interactive_mode():
    """Run in interactive mode"""
    client = A2UIClient()
    
    print("\nA2UI Image Generation Agent - Interactive Mode")
    print("Type your prompts, or 'quit' to exit\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if not user_input:
                continue
            
            response = await client.send_message(user_input)
            client.print_response(response)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("\nGoodbye!")


async def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        await interactive_mode()
    else:
        await run_examples()


if __name__ == "__main__":
    asyncio.run(main())
