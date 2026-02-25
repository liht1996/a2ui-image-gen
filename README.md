# A2UI Image Generation Agent

An intelligent image generation agent using **A2UI** (Agent-to-UI) protocol with **Gemini 2.5 Flash** that conditionally displays widgets for fine-grained control.

## Features

- 🎨 **Conditional Color Tone Control**: Widget appears only when color adjustments are mentioned
- ✏️ **Conditional Sketch Board**: Widget appears only when composition/layout control is needed
- 🤖 **Smart Widget Detection**: Agent analyzes user intent to show relevant controls
- 🚀 **Gemini 2.5 Flash**: Uses Google's latest multimodal model for image generation
- 🔌 **A2A Protocol**: Implements Agent-to-Agent communication standard
- 🌐 **Web Frontend**: Beautiful chat interface with interactive widgets

## Quick Start

### 1. Setup

```bash
# Run the setup script
./setup.sh

# Edit .env and add your GOOGLE_API_KEY
nano .env
```

Get your API key from: https://aistudio.google.com/app/apikey

### 2. Run the Application

**Option A: Run everything (recommended)**
```bash
./run.sh
```

Then open your browser to: **http://localhost:8080**

**Option B: Run separately**
```bash
# Terminal 1 - Backend
venv/bin/python server.py

# Terminal 2 - Frontend
python3 serve_frontend.py
```

### 3. Use the Web Interface

1. Open http://localhost:8080 in your browser
2. Type a message like: "Generate a sunset with warm orange tones"
3. Watch as widgets appear automatically for fine-tuning
4. Adjust colors or draw sketches
5. Click "Apply Changes" to refine your image

See [FRONTEND.md](FRONTEND.md) for detailed usage guide.

## Testing with curl

**Basic image generation (no widgets):**
```bash
curl -X POST http://localhost:10002/ \
  -H "Content-Type: application/json" \
  -H "X-A2A-Extensions: https://a2ui.org/a2a-extension/a2ui/v0.8" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/stream",
    "params": {
      "message": {
        "messageId": "msg-1",
        "role": "user",
        "parts": [{"text": "Generate an image of a sunset"}]
      }
    },
    "id": 1
  }'
```

**With color tone control (widget appears):**
```bash
curl -X POST http://localhost:10002/ \
  -H "Content-Type: application/json" \
  -H "X-A2A-Extensions: https://a2ui.org/a2a-extension/a2ui/v0.8" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/stream",
    "params": {
      "message": {
        "messageId": "msg-2",
        "role": "user",
        "parts": [{"text": "Generate an image with a blue tone and cool temperature"}]
      }
    },
    "id": 2
  }'
```

**With sketch board (widget appears):**
```bash
curl -X POST http://localhost:10002/ \
  -H "Content-Type: application/json" \
  -H "X-A2A-Extensions: https://a2ui.org/a2a-extension/a2ui/v0.8" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/stream",
    "params": {
      "message": {
        "messageId": "msg-3",
        "role": "user",
        "parts": [{"text": "Generate an image with a specific composition - circle on the left, square on the right"}]
      }
    },
    "id": 3
  }'
```

## How It Works

### Conditional Widget Logic

The agent analyzes user messages to determine if widgets are needed:

1. **Color Tone Widget** appears when user mentions:
   - Color names, tones, hues
   - Temperature (warm/cool)
   - Saturation, brightness
   - Color-related adjectives

2. **Sketch Board Widget** appears when user mentions:
   - Composition, layout, structure
   - Positioning, arrangement
   - Outlines, shapes
   - Specific spatial requirements

### Widget Interactions

When a widget appears:
1. User adjusts controls in the UI
2. Widget sends updated values back to agent
3. Agent uses values to refine image generation
4. Process repeats until user is satisfied

## Architecture

```
┌─────────────────┐
│   User/Client   │
└────────┬────────┘
         │ A2A JSON-RPC
         ▼
┌─────────────────┐
│  A2UI Server    │
│  (server.py)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Image Agent     │
│ (agent.py)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Gemini 2.5      │
│ Flash Model     │
└─────────────────┘
```

## API Reference

### Message Structure

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "message/stream",
  "params": {
    "message": {
      "messageId": "msg-id",
      "role": "user",
      "parts": [{"text": "your prompt"}]
    }
  },
  "id": 1
}
```

**Response with Widgets:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "messageId": "msg-response-id",
    "role": "assistant",
    "parts": [
      {"text": "Generated image with controls..."},
      {"inlineData": {"mimeType": "image/png", "data": "base64..."}},
      {
        "a2ui": {
          "type": "color-tone-control",
          "id": "color-tone-widget",
          "properties": {
            "hue": 180,
            "saturation": 50,
            "lightness": 50,
            "temperature": "neutral"
          }
        }
      }
    ]
  },
  "id": 1
}
```

## Customization

### Adjust Widget Detection

Edit the `analyze_request()` method in [agent.py](a2ui-image-gen/agent.py) to customize keyword detection:

```python
color_keywords = ['your', 'custom', 'keywords']
sketch_keywords = ['outline', 'layout', ...]
```

### Add More Widgets

1. Create widget specification in `generate_a2ui_message()`
2. Add detection logic in `analyze_request()`
3. Handle widget updates in `process_message()`

## Troubleshooting

**Server won't start:**
- Check if port 10002 is available
- Verify GOOGLE_API_KEY is set correctly

**No widgets appearing:**
- Use more explicit keywords in your prompts
- Check agent logs for widget detection analysis

**Image generation fails:**
- Verify API key has access to Gemini 2.5 Flash
- Check API quota limits

## License

MIT License - feel free to use and modify for your projects!

## Resources

- [A2UI Specification](https://github.com/google/A2UI)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [A2A Protocol](https://github.com/google/agent-to-agent)
