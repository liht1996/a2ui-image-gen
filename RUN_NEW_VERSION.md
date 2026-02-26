# Running the New A2UI-Compliant Image Generation Server

## What's New

The new implementation uses the official **A2UI and A2A SDK packages**:
- ✅ `a2a-sdk` (v0.3.24) - Official A2A protocol implementation  
- ✅ `google-adk[extensions]` - Agent Development Kit with LiteLLM
- ✅ `a2ui` module - Official schema manager and validation

This follows the exact pattern from [Google's A2UI Restaurant Finder](https://github.com/google/A2UI/tree/main/samples/agent/adk/restaurant_finder).

## Quick Start

### 1. Make sure your environment is set up

```bash
cd /Users/haotian.li/Repositories/a2ui-image-gen

# Activate virtual environment
source venv/bin/activate

# Verify packages are installed
pip list | grep -E "a2a-sdk|google-adk"
```

### 2. Check your .env file

Ensure `.env` contains your API key:
```bash
GOOGLE_API_KEY=your_api_key_here
# or
GEMINI_API_KEY=your_api_key_here
```

### 3. Start the new server

```bash
# Option 1: Direct command
/Users/haotian.li/Repositories/a2ui-image-gen/venv/bin/python server_new.py --host localhost --port 10002

# Option 2: Using bash (if you're in bash shell)
source venv/bin/activate
python server_new.py --host localhost --port 10002
```

The server will start on **http://localhost:10002**

### 4. Open the frontend

In a new terminal:
```bash
cd frontend
python -m http.server 8080
```

Then open **http://localhost:8080** in your browser.

## File Structure

### New Files (A2UI SDK Implementation)
- **server_new.py** - A2A Starlette server using `A2AStarletteApplication`
- **agent_new.py** - Agent using `A2uiSchemaManager` for proper A2UI message generation
- **agent_executor.py** - A2A protocol executor handling request/response streaming
- **examples/** - A2UI JSON examples for image generation widgets

### Original Files (Still Working)
- **server.py** - Original manual A2UI implementation
- **agent.py** - Original agent with dynamic widget generation
- **frontend/** - Web UI (works with both servers)

## Architecture

```
User Request → A2AStarletteApplication → AgentExecutor → ImageGenerationAgent
                                              ↓
                            A2uiSchemaManager (validates A2UI messages)
                                              ↓
                            Gemini 2.5 Flash (generates UI JSON)
                                              ↓
                            Gemini 2.5 Flash Image (generates images)
                                              ↓
                            A2UI Response → Frontend Renderer
```

## Testing the Server

### Check if server is running:
```bash
# Check process
ps aux | grep server_new

# Check port
lsof -i :10002

# Test endpoint (exact path may vary)
curl http://localhost:10002/
```

## Troubleshooting

### Import errors
```bash
# Ensure all SDK packages are installed
pip install -r requirements.txt

# Verify a2a-sdk is installed
python -c "import a2a; print(a2a.__version__)"
```

### Server won't start
```bash
# Kill any existing server on port 10002
lsof -ti:10002 | xargs kill -9

# Check logs
tail -f server.log  # if logging to file
```

### Frontend not connecting
- Make sure both frontend (port 8080) and backend (port 10002) are running
- Check browser console for CORS errors
- Verify the backend URL in frontend code

## Comparing Old vs New

| Feature | Old (server.py) | New (server_new.py) |
|---------|----------------|---------------------|
| A2UI Protocol | ✅ Manual implementation | ✅ Official SDK |
| A2A Server | ⚠️ Custom aiohttp | ✅ A2AStarletteApplication |
| Schema Management | ⚠️ Manual validation | ✅ A2uiSchemaManager |
| Widget Generation | ✅ Dynamic with Gemini | ✅ Dynamic with Gemini |
| Image Generation | ✅ Gemini 2.5 Flash Image | ✅ Gemini 2.5 Flash Image |
| Package Dependencies | aiohttp, google-genai | a2a-sdk, google-adk |

Both implementations are **fully functional** and A2UI v0.8 compliant!

## Next Steps

1. Test image generation with various prompts
2. Test widget interactions (color, style, size)
3. Verify A2UI message validation
4. Compare performance between old and new implementations

## Support

If you encounter issues:
1. Check the terminal output for error messages
2. Verify all packages are installed: `pip list`
3. Ensure .env file has your API key
4. Try the original server.py to verify setup works
