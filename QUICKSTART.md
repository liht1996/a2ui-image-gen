# Quick Start Guide

Get your A2UI Image Generation Agent running in 3 minutes!

## Prerequisites
- Python 3.9+ installed
- Google AI API key ([Get one here](https://aistudio.google.com/app/apikey))

## Installation

```bash
# 1. Navigate to project
cd /Users/haotian.li/Repositories/a2ui-image-gen

# 2. Run setup script
./setup.sh

# 3. Edit .env file
nano .env  # or use your preferred editor
# Add your API key: GOOGLE_API_KEY=your_actual_key_here

# 4. Activate virtual environment
source venv/bin/activate
```

## Running the Server

```bash
python server.py
```

You should see:
```
INFO:__main__:A2UI Server started on http://localhost:10002
```

## Testing

### Option 1: Run Example Scenarios
```bash
# In a new terminal
cd /Users/haotian.li/Repositories/a2ui-image-gen
source venv/bin/activate
python client_example.py
```

### Option 2: Interactive Mode
```bash
python client_example.py --interactive
```

### Option 3: Using curl

**Basic image (no widgets):**
```bash
curl -X POST http://localhost:10002/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/stream",
    "params": {
      "message": {
        "messageId": "1",
        "role": "user",
        "parts": [{"text": "Generate a sunset"}]
      }
    },
    "id": 1
  }'
```

**With color widget:**
```bash
curl -X POST http://localhost:10002/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/stream",
    "params": {
      "message": {
        "messageId": "2",
        "role": "user",
        "parts": [{"text": "Generate with blue cool tones"}]
      }
    },
    "id": 2
  }'
```

## Widget Triggers

### Color Tone Widget appears when you mention:
- Color names: "blue tone", "red hue"
- Temperature: "warm", "cool"
- Adjustments: "saturation", "brightness"

### Sketch Board appears when you mention:
- Layout: "composition", "arrangement"
- Positioning: "left side", "place at"
- Structure: "outline", "sketch"

## Example Prompts

| Prompt | Widgets Shown |
|--------|--------------|
| "Generate a mountain" | None |
| "Generate with warm orange tones" | Color Control |
| "Place trees on left, house on right" | Sketch Board |
| "Blue tones with specific composition" | Both |

## Troubleshooting

**Server won't start:**
```bash
# Check if port is in use
lsof -i :10002

# Kill process if needed
kill -9 <PID>
```

**Import errors:**
```bash
# Make sure you're in virtual environment
which python  # Should show venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt
```

**API errors:**
```bash
# Verify API key is set
echo $GOOGLE_API_KEY

# Or check .env file
cat .env
```

## Next Steps

1. **Read [README.md](README.md)** for detailed documentation
2. **Check [WIDGETS.md](WIDGETS.md)** for widget specifications
3. **Run tests:** `pytest test_agent.py -v`
4. **Customize:** Edit [agent.py](agent.py) to adjust widget detection logic

## Project Structure

```
a2ui-image-gen/
├── agent.py              # Main agent logic with Gemini 2.5 Flash
├── server.py             # A2A protocol server
├── client_example.py     # Test client with examples
├── test_agent.py         # Unit tests
├── requirements.txt      # Python dependencies
├── .env.example          # Environment template
├── setup.sh             # Setup script
├── README.md            # Full documentation
├── WIDGETS.md           # Widget specifications
└── QUICKSTART.md        # This file
```

## Support

Need help? Check:
- [A2UI Specification](https://github.com/google/A2UI)
- [Gemini API Docs](https://ai.google.dev/docs)
- Issues in this project

Happy generating! 🎨✨
