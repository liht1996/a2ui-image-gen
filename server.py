"""
A2UI Server for Image Generation Agent
Handles A2A (Agent-to-Agent) communication protocol with A2UI extensions
"""

import asyncio
import json
import os
from typing import Any, Dict, Optional
from aiohttp import web
import logging
from dotenv import load_dotenv
from aiohttp_cors import setup as cors_setup, ResourceOptions

from agent import ImageGenerationAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class A2UIServer:
    """A2UI Server implementing A2A protocol"""
    
    def __init__(self, agent: ImageGenerationAgent, port: int = 10002):
        self.agent = agent
        self.port = port
        self.app = web.Application()
        self._setup_cors()
        self._setup_routes()
    
    def _setup_cors(self):
        """Setup CORS for frontend access"""
        self.cors = cors_setup(self.app, defaults={
            "*": ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
    
    def _setup_routes(self):
        """Setup HTTP routes"""
        # Add routes with CORS
        self.cors.add(self.app.router.add_post('/', self.handle_a2a_request))
        self.cors.add(self.app.router.add_get('/health', self.health_check))
    
    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.json_response({"status": "healthy"})
    
    async def handle_a2a_request(self, request: web.Request) -> web.Response:
        """Handle A2A JSON-RPC requests"""
        try:
            data = await request.json()
            
            # Validate JSON-RPC structure
            if not self._validate_jsonrpc(data):
                return self._error_response(-32600, "Invalid Request")
            
            method = data.get("method")
            params = data.get("params", {})
            request_id = data.get("id")
            
            # Handle different methods
            if method == "message/stream":
                response = await self._handle_message_stream(params)
            elif method == "agent/capabilities":
                response = await self._handle_capabilities()
            else:
                return self._error_response(-32601, "Method not found", request_id)
            
            return web.json_response({
                "jsonrpc": "2.0",
                "result": response,
                "id": request_id
            })
            
        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            return self._error_response(-32603, str(e))
    
    def _validate_jsonrpc(self, data: Dict) -> bool:
        """Validate JSON-RPC 2.0 structure"""
        return (
            data.get("jsonrpc") == "2.0" and
            "method" in data and
            "id" in data
        )
    
    def _error_response(self, code: int, message: str, request_id: Any = None) -> web.Response:
        """Generate JSON-RPC error response"""
        return web.json_response({
            "jsonrpc": "2.0",
            "error": {
                "code": code,
                "message": message
            },
            "id": request_id
        })
    
    async def _handle_message_stream(self, params: Dict) -> Dict:
        """Handle message/stream method"""
        message = params.get("message", {})
        user_text = ""
        attachments = []
        
        # Extract text and attachments from message parts
        for part in message.get("parts", []):
            if "text" in part:
                user_text += part["text"]
            elif "a2ui" in part:
                # Handle A2UI widget updates (preserve widget type per protocol)
                attachments.append({
                    "widget_id": part['a2ui'].get('id', 'unknown'),
                    "type": part['a2ui']['type'],
                    "data": part['a2ui'].get('properties', {})
                })
        
        # Process message with agent
        response = await self.agent.process_message(user_text, attachments)
        
        # Return streaming response
        return {
            "messageId": f"msg-{os.urandom(8).hex()}",
            "role": "assistant",
            "parts": response["parts"]
        }
    
    async def _handle_capabilities(self) -> Dict:
        """Return agent capabilities"""
        return {
            "capabilities": {
                "streaming": True,
                "multimodal": True,
                "a2ui": {
                    "version": "0.8",
                    "supportedWidgets": [
                        "slider",
                        "color-picker",
                        "sketch-canvas",
                        "dropdown",
                        "text-input",
                        "toggle",
                        "range-dual",
                        # Backward compatibility
                        "color-tone-control",
                        "sketch-board"
                    ]
                }
            },
            "model": "gemini-2.5-flash-image",
            "description": "Image generation agent with AI-generated dynamic A2UI widgets"
        }
    
    async def start(self):
        """Start the server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        logger.info(f"A2UI Server started on http://localhost:{self.port}")
        
        # Keep running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Shutting down server...")
        finally:
            await runner.cleanup()


async def main():
    """Main entry point"""
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API key from environment
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("Please set GOOGLE_API_KEY or GEMINI_API_KEY environment variable")
        return
    
    # Create agent and server
    agent = ImageGenerationAgent(api_key=api_key)
    server = A2UIServer(agent=agent, port=10002)
    
    # Start server
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
