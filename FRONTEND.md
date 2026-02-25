# Frontend Usage Guide

## Quick Start

### Option 1: Run Everything (Recommended)

```bash
./run.sh
```

This starts both the backend (port 10002) and frontend (port 8080).

Then open your browser to: **http://localhost:8080**

### Option 2: Run Separately

**Terminal 1 - Backend:**
```bash
venv/bin/python server.py
```

**Terminal 2 - Frontend:**
```bash
python3 serve_frontend.py
```

Then open: **http://localhost:8080**

## Using the Interface

### 1. Send a Message
- Type your image description in the text box
- Press Enter or click "Send"
- Wait for the image to generate

### 2. Conditional Widgets

Widgets appear automatically based on your message:

**Color Tone Control appears when you mention:**
- Colors: "blue tone", "warm colors", "cool palette"
- Adjustments: "brighter", "more saturated", "darker"
- Examples:
  - ✅ "Generate a sunset with warm orange tones"
  - ✅ "Make it more vibrant and saturated"

**Sketch Board appears when you mention:**
- Composition: "specific layout", "composition"
- Positioning: "tree on the left", "centered"
- Structure: "outline", "sketch the layout"
- Examples:
  - ✅ "Place mountains in background, lake in foreground"
  - ✅ "Draw a specific composition"

**Both widgets appear for:**
- "Generate with blue tones and specific positioning"
- "Create a warm-colored image with mountains on the left"

### 3. Using Widgets

**Color Tone Control:**
- Adjust **Hue** (0-360°) - Changes the base color
- Adjust **Saturation** (0-100%) - Color intensity
- Adjust **Lightness** (0-100%) - Brightness
- Select **Temperature** - Warm/Neutral/Cool

**Sketch Board:**
- Click **✏️ Pen** to draw outlines
- Click **🧹 Eraser** to erase
- Click **🗑️ Clear** to start over
- Draw rough shapes to guide composition

**Apply Changes:**
- Make your adjustments
- Click "Apply Changes" button
- Agent generates new image with your refinements

### 4. Iterations

You can iterate as many times as you want:
1. Generate initial image → "Generate a sunset"
2. Add color control → "Make it warmer"
3. Widgets appear → Adjust sliders
4. Apply → New image with adjustments
5. Add sketch → "Draw composition"
6. Sketch on board → Apply
7. Final refined image

## Interface Features

### Chat-like Interface
- Conversation history preserved
- Your messages on the right (blue)
- Agent responses on the left (gray)
- Images displayed inline
- Click images to view full size

### Connection Status
- Bottom right corner shows connection
- 🟢 Green: Connected to backend
- 🔴 Red: Connection error
- ⚪ Gray: Disconnected

### Loading Indicator
- Full-screen overlay when generating
- Shows spinner and "Generating..." text
- Blocks input during generation

## Tips

1. **Start Simple**: Begin with basic prompts
   - "Generate a mountain landscape"

2. **Add Details**: Mention colors or layout to get widgets
   - "Generate a mountain landscape with cool blue tones"

3. **Refine**: Use widgets to perfect the image
   - Adjust sliders, draw sketches, apply changes

4. **Iterate**: Keep refining until satisfied
   - "Make it darker"
   - "Adjust the composition"

## Troubleshooting

**Widgets not appearing?**
- Use explicit keywords (see examples above)
- Backend analyzes your message for intent
- Try: "I want to adjust the colors" or "I need to draw a layout"

**Image not generating?**
- Check backend is running (Terminal 1)
- Check connection status (bottom right)
- Check browser console for errors (F12)

**Can't draw on sketch board?**
- Make sure "Pen" tool is selected (blue)
- Canvas should have white background
- Try clearing and starting again

**Changes not applying?**
- Make sure to click "Apply Changes" button
- Check backend terminal for errors
- Widgets must be visible to apply

## Architecture

```
Browser (localhost:8080)
    ↕️ HTTP
Frontend Server (serve_frontend.py)
    ↕️ WebSocket/Fetch
Backend Server (localhost:10002)
    ↕️ A2A Protocol
Image Generation Agent
    ↕️ API
Gemini 2.5 Flash
```

## Keyboard Shortcuts

- **Enter**: Send message (Shift+Enter for new line)
- **Click image**: Open full size in new tab

## Browser Support

- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers (touch support for sketch)

## Development

### File Structure
```
frontend/
├── index.html      # Main HTML structure
├── styles.css      # All styling
├── app.js          # Main application logic
├── client.js       # Backend communication
└── widgets.js      # Widget rendering
```

### Customization

**Change colors:**
Edit CSS variables in `styles.css`:
```css
:root {
    --primary-color: #6366f1;
    --bg-color: #0f172a;
    ...
}
```

**Change backend URL:**
Edit `app.js`:
```javascript
this.client = new A2UIClient('http://localhost:10002');
```

**Add new widgets:**
1. Add rendering logic in `widgets.js`
2. Add widget detection keywords in backend `agent.py`
3. Style in `styles.css`

## Next Steps

- Experiment with different prompts
- Try the conditional widgets
- Iterate to create perfect images
- Share your results!

Enjoy creating! 🎨✨
