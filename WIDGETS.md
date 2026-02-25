# A2UI Widget Specification

This document details the A2UI widgets used in the image generation agent.

## Color Tone Control Widget

### Widget Type
`color-tone-control`

### Purpose
Allows users to fine-tune color properties of generated images including hue, saturation, lightness, and temperature.

### Properties

```json
{
  "type": "color-tone-control",
  "id": "color-tone-widget",
  "properties": {
    "title": "Adjust Color Tone",
    "hue": 180,           // 0-360 degrees
    "saturation": 50,     // 0-100 percent
    "lightness": 50,      // 0-100 percent
    "temperature": "neutral"  // "warm" | "cool" | "neutral"
  }
}
```

### Behavior
- **hue**: Controls the color wheel position (0=red, 120=green, 240=blue)
- **saturation**: Controls color intensity (0=grayscale, 100=full color)
- **lightness**: Controls brightness (0=black, 50=normal, 100=white)
- **temperature**: Applies slight tint (warm=yellow/orange, cool=blue)

### When to Show
The widget appears when the user's message contains keywords related to:
- Color names or descriptions
- Tone, hue, saturation adjustments
- Warm/cool temperature preferences
- Brightness or darkness requests
- Color palette modifications

### Example Triggers
- "Generate with a blue tone"
- "Make it warmer"
- "Increase saturation"
- "Darker colors please"
- "Cool color palette"

---

## Sketch Board Widget

### Widget Type
`sketch-board`

### Purpose
Provides a canvas for users to draw rough outlines or compositions that guide image generation.

### Properties

```json
{
  "type": "sketch-board",
  "id": "sketch-board-widget",
  "properties": {
    "title": "Draw Image Outline",
    "width": 512,
    "height": 512,
    "tools": ["pen", "eraser", "clear"],
    "initialSketch": null  // Base64 encoded PNG or null
  }
}
```

### Behavior
- **width/height**: Canvas dimensions in pixels
- **tools**: Available drawing tools
  - `pen`: Draw black lines
  - `eraser`: Remove drawn lines
  - `clear`: Clear entire canvas
- **initialSketch**: Pre-populated sketch (null for empty canvas)

### When to Show
The widget appears when the user's message contains keywords related to:
- Composition and layout
- Spatial positioning
- Structural elements
- Specific arrangements
- Outline or shape requirements

### Example Triggers
- "Draw a specific composition"
- "Place tree on the left, house on the right"
- "I want to sketch the layout"
- "Specific positioning needed"
- "Follow this outline"

---

## Conditional Display Logic

### Algorithm

```python
def should_show_widgets(user_message: str) -> dict:
    """Determine which widgets to show based on user intent"""
    
    # Analyze message for color-related terms
    needs_color = any(keyword in user_message.lower() 
                     for keyword in COLOR_KEYWORDS)
    
    # Analyze message for composition-related terms
    needs_sketch = any(keyword in user_message.lower() 
                      for keyword in SKETCH_KEYWORDS)
    
    return {
        'color_control': needs_color,
        'sketch_board': needs_sketch
    }
```

### Smart Display
- **Neither widget**: Simple image generation requests
- **Color only**: Color-focused requests
- **Sketch only**: Composition-focused requests
- **Both widgets**: Complex requests requiring color AND composition control

---

## Widget State Management

### State Flow

```
1. User sends message
   ↓
2. Agent analyzes intent
   ↓
3. Agent decides which widgets to show
   ↓
4. Agent generates image + widgets
   ↓
5. User adjusts widgets
   ↓
6. User submits (sends updated values)
   ↓
7. Agent regenerates with new parameters
   ↓
8. Loop continues until satisfied
```

### State Persistence
- Widget states persist across conversation turns
- Latest values are used for subsequent generations
- User can reset by sending new base request

---

## Integration with Gemini 2.5 Flash

### Color Tone Integration
Color parameters are converted to prompt guidance:

```python
enhanced_prompt = f"{base_prompt}\n\n"
enhanced_prompt += f"Color guidance: Hue {hue}°, "
enhanced_prompt += f"Saturation {saturation}%, "
enhanced_prompt += f"Lightness {lightness}%, "
enhanced_prompt += f"Temperature: {temperature}"
```

### Sketch Board Integration
Sketch is passed as multimodal input:

```python
inputs = [
    text_prompt,
    sketch_image  # PIL Image from base64
]
response = model.generate_content(inputs)
```

---

## A2A Protocol Compliance

### Message Format
Following A2A (Agent-to-Agent) specification:

```json
{
  "role": "assistant",
  "parts": [
    {"text": "response text"},
    {"inlineData": {"mimeType": "image/png", "data": "..."}},
    {"a2ui": {"type": "widget-type", "properties": {...}}}
  ]
}
```

### Widget Updates
User sends widget updates in next message:

```json
{
  "role": "user",
  "parts": [
    {"text": "Adjust the image"},
    {
      "a2ui": {
        "type": "color-tone-control",
        "id": "color-tone-widget",
        "properties": {"hue": 240, "saturation": 70, ...}
      }
    }
  ]
}
```

---

## Best Practices

### For Agent Developers
1. **Be conservative**: Only show widgets when truly needed
2. **Clear intent**: Use explicit keywords to trigger widgets
3. **State tracking**: Maintain widget state across turns
4. **Graceful fallback**: Handle missing widget data elegantly

### For Users
1. **Explicit requests**: Use clear keywords for widgets
2. **Iterative refinement**: Adjust widgets incrementally
3. **Reset when needed**: Start fresh with new base prompt
4. **Combine wisely**: Use both widgets for complex control

---

## Future Enhancements

Potential widget additions:
- **Style selector**: Choose artistic styles (photorealistic, cartoon, etc.)
- **Aspect ratio**: Control image dimensions
- **Detail slider**: Control level of detail
- **Reference image**: Upload reference for style matching
- **Region selector**: Mark specific areas for editing
