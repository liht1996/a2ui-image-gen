"""
A2UI Image Generation Agent with conditional widgets for color tone control and sketch board.
Uses Gemini 2.5 Flash for image generation.
"""

import os
import base64
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import json


@dataclass
class ColorTone:
    """Represents a color tone configuration"""
    hue: float  # 0-360
    saturation: float  # 0-100
    lightness: float  # 0-100
    temperature: str  # "warm" or "cool"


class ImageGenerationAgent:
    """Agent that generates images with conditional A2UI widgets"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.conversation_history: List[Dict] = []
        self.current_color_tone: Optional[ColorTone] = None
        self.current_sketch: Optional[str] = None  # Base64 encoded sketch
        self.chat_session = None  # Multi-turn chat session
        self._client = None  # Store client instance
        self.last_generated_image = None  # Store last image for context
        
    async def analyze_request(self, user_message: str) -> Dict:
        """
        Use Gemini to analyze the request and generate widget specifications dynamically.
        Returns dict with 'widgets' array containing widget specifications.
        """
        try:
            from google import genai
            from google.genai import types
            import json
            
            client = genai.Client(api_key=self.api_key)
            
            analysis_prompt = f"""Analyze this user request for image generation and determine what interactive controls (widgets) would be helpful.

User Request: "{user_message}"

IMPORTANT: Return empty widgets array if:
- The request is a command to apply/execute adjustments (e.g., "apply", "use these settings")
- The request is a simple generation without need for user fine-tuning

If the user would benefit from fine-tuning controls, generate widget specifications. You can create ANY type of widget that would be useful:

Available widget types:
- "slider": For numeric adjustments (brightness, size, intensity, etc.)
- "color-picker": For color selection
- "sketch-canvas": For drawing/sketching layouts
- "dropdown": For selecting from options
- "text-input": For text parameters
- "range-dual": For min/max range selection
- "toggle": For on/off options

For each widget, specify:
- id: unique identifier (e.g., "brightness-control", "style-selector")
- type: widget type from above
- label: user-friendly label
- properties: widget-specific config (min, max, default, options, etc.)

Examples:
{{
  "widgets": [
    {{
      "id": "brightness-slider",
      "type": "slider",
      "label": "Brightness",
      "properties": {{"min": 0, "max": 100, "default": 50, "step": 1}}
    }},
    {{
      "id": "style-dropdown",
      "type": "dropdown",
      "label": "Art Style",
      "properties": {{"options": ["Realistic", "Anime", "Oil Painting"], "default": "Realistic"}}
    }}
  ],
  "reasoning": "User wants to adjust brightness and style"
}}

Respond in JSON format:
{{
  "widgets": [/* array of widget specs, empty if none needed */],
  "reasoning": "brief explanation"
}}
"""
            
            print(f"\n{'='*60}")
            print("WIDGET ANALYSIS PROMPT:")
            print(f"{'='*60}")
            print(analysis_prompt)
            print(f"{'='*60}\n")
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=analysis_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json'
                )
            )
            
            # Print full model response
            print(f"\n{'='*60}")
            print("WIDGET ANALYSIS MODEL RESPONSE (gemini-2.5-flash):")
            print(f"{'='*60}")
            print(f"Raw response text:\n{response.text}")
            print(f"{'='*60}\n")
            
            # Parse JSON response
            result = json.loads(response.text)
            print(f"Widget analysis: {result['reasoning']}")
            
            widgets = result.get('widgets', [])
            if widgets:
                print(f"✓ Generated {len(widgets)} dynamic widgets:")
                for widget in widgets:
                    print(f"  - {widget['label']} ({widget['type']})")
            
            return {
                'widgets': widgets
            }
            
        except Exception as e:
            print(f"Error in widget analysis: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to no widgets
            return {
                'widgets': []
            }
    
    def generate_a2ui_message(
        self,
        text: str,
        image_data: Optional[str] = None,
        widgets: Optional[List[Dict]] = None
    ) -> Dict:
        """Generate an A2UI formatted message with dynamic widgets"""
        
        message = {
            "role": "assistant",
            "parts": []
        }
        
        # Add text part
        if text:
            message["parts"].append({"text": text})
        
        # Add image if available
        if image_data:
            message["parts"].append({
                "inlineData": {
                    "mimeType": "image/png",
                    "data": image_data
                }
            })
        
        # Add dynamically generated A2UI widgets
        if widgets:
            for widget_spec in widgets:
                message["parts"].append({
                    "a2ui": widget_spec
                })
        
        return message
    
    async def process_message(self, user_message: str, attachments: Optional[List] = None) -> Dict:
        """Process user message and generate response with conditional widgets"""
        
        print(f"\n{'='*60}")
        print(f"Processing message: '{user_message}'")
        print(f"Attachments: {attachments}")
        
        # Skip widget analysis if this is an apply adjustments command with attachments
        # (user is already using widgets, not requesting them)
        should_analyze_widgets = not (
            attachments and 
            any(word in user_message.lower() for word in ['apply', 'adjustment'])
        )
        
        if should_analyze_widgets:
            # Analyze if we need widgets (using Gemini model)
            widget_needs = await self.analyze_request(user_message)
            
            # If no attachments were sent, this is a fresh request
            # Clear old widget values and potentially reset session to prevent stale data
            if not attachments:
                if hasattr(self, 'widget_values') and self.widget_values:
                    print(f"⊘ Clearing stale widget values from previous session: {list(self.widget_values.keys())}")
                    self.widget_values = {}
                    
                    # Also clear other session state for a fresh start
                    self.current_color_tone = None
                    self.current_sketch = None
                    print("⊘ Cleared color tone and sketch state")
                    
                    # Optionally reset chat session for completely fresh context
                    # (Comment this out if you want to maintain conversation history across widget resets)
                    if self.chat_session is not None:
                        print("⊘ Resetting chat session for fresh start")
                        self.chat_session = None
                        self.last_generated_image = None
                        self._client = None
        else:
            print("⊘ Skipping widget analysis (applying existing widget values)")
            widget_needs = {'widgets': []}
        
        # Check for widget updates from user (now using generic widget data)
        if attachments:
            for attachment in attachments:
                widget_id = attachment.get("widget_id")
                widget_type = attachment.get("type")
                widget_data = attachment.get("data", {})
                
                # Store widget values generically
                if not hasattr(self, 'widget_values'):
                    self.widget_values = {}
                
                self.widget_values[widget_id] = widget_data
                print(f"✓ Widget '{widget_id}' (type: {widget_type}) updated: {widget_data}")
                
                # Handle special widget types for image generation
                # These are used by the generate_image method
                if widget_type == 'color-tone-control' or 'hue' in widget_data:
                    self.current_color_tone = ColorTone(
                        hue=widget_data.get("hue", 180),
                        saturation=widget_data.get("saturation", 50),
                        lightness=widget_data.get("lightness", 50),
                        temperature=widget_data.get("temperature", "neutral")
                    )
                elif widget_type in ['sketch-board', 'sketch-canvas'] or 'sketch' in widget_data:
                    self.current_sketch = widget_data.get("sketch")
        
        # Build enhanced prompt with dynamic widget values
        enhanced_prompt = self._build_prompt_with_widgets(user_message)
        
        # Generate image with Gemini 2.5 Flash Image (maintains chat context)
        print(f"Generating image with: color_tone={self.current_color_tone is not None}, sketch={self.current_sketch is not None}")
        if hasattr(self, 'widget_values') and self.widget_values:
            print(f"Active widget values: {list(self.widget_values.keys())}")
        
        image_data = await self.generate_image(
            prompt=enhanced_prompt,
            color_tone=self.current_color_tone,
            sketch=self.current_sketch
        )
        print(f"Image generated: {len(image_data) if image_data else 0} bytes")
        
        # Create response message
        response_text = self._generate_response_text(user_message, widget_needs)
        
        response = self.generate_a2ui_message(
            text=response_text,
            image_data=image_data,
            widgets=widget_needs.get('widgets', [])
        )
        
        print(f"Response parts: {len(response['parts'])} parts")
        for i, part in enumerate(response['parts']):
            if 'text' in part:
                print(f"  Part {i}: text ({len(part['text'])} chars)")
            elif 'inlineData' in part:
                print(f"  Part {i}: inlineData ({len(part['inlineData']['data'])} bytes)")
            elif 'a2ui' in part:
                print(f"  Part {i}: a2ui widget ({part['a2ui']['type']})")
        print(f"{'='*60}\n")
        
        return response
    
    def _build_prompt_with_widgets(self, base_prompt: str) -> str:
        """Build enhanced prompt incorporating dynamic widget values"""
        if not hasattr(self, 'widget_values') or not self.widget_values:
            return base_prompt
        
        enhanced = base_prompt
        widget_instructions = []
        
        for widget_id, widget_data in self.widget_values.items():
            # Skip old-style widgets (handled separately)
            if 'hue' in widget_data or 'sketch' in widget_data:
                continue
            
            # Universal format - convert widget ID to human-readable label
            human_label = widget_id.replace('-', ' ').replace('_', ' ').title()
            
            # Format widget data universally without caring about widget type
            if len(widget_data) == 1:
                # Single property - use simplified format
                key, val = list(widget_data.items())[0]
                widget_instructions.append(f"{human_label}: {val}")
            else:
                # Multiple properties - show all as key=value pairs
                parts = [f"{k}={v}" for k, v in widget_data.items() if v is not None]
                widget_instructions.append(f"{human_label} ({', '.join(parts)})")
        
        if widget_instructions:
            enhanced += "\n\nAdjustments: " + "; ".join(widget_instructions)
        
        return enhanced
    
    def _generate_response_text(self, user_message: str, widget_needs: Dict) -> str:
        """Generate contextual response text"""
        text = "I've generated an image based on your request."
        
        widgets = widget_needs.get('widgets', [])
        if widgets:
            text += "\n\nI've added some controls below for you to fine-tune:"
            for widget in widgets:
                text += f"\n  • {widget['label']}"
        
        return text
    
    async def generate_image(
        self,
        prompt: str,
        color_tone: Optional[ColorTone] = None,
        sketch: Optional[str] = None
    ) -> str:
        """Generate image using Gemini 2.5 Flash Image with conversation context"""
        try:
            from google import genai
            from google.genai import types
            from PIL import Image as PILImage
            import io
            
            # Initialize client (create fresh client each time to avoid "client closed" errors)
            client = genai.Client(api_key=self.api_key)
            
            # Check if we need to recreate chat session
            if self.chat_session is None:
                self.chat_session = client.chats.create(
                    model='gemini-2.5-flash-image',
                    config=types.GenerateContentConfig(
                        response_modalities=['TEXT', 'IMAGE'],
                    )
                )
                # Store the client instance with the session
                self._client = client
                print("✓ Created new chat session for multi-turn image generation")
            else:
                # Recreate session with new client if old one was closed
                try:
                    # Test if session is still valid by checking its state
                    if not hasattr(self, '_client') or self._client is None:
                        raise Exception("Client was closed, recreating session")
                except:
                    print("⚠ Chat session was closed, recreating...")
                    self.chat_session = client.chats.create(
                        model='gemini-2.5-flash-image',
                        config=types.GenerateContentConfig(
                            response_modalities=['TEXT', 'IMAGE'],
                        )
                    )
                    self._client = client
                    print("✓ Recreated chat session")
            
            # Build enhanced prompt with color and sketch guidance
            enhanced_prompt = prompt
            
            # Detect if this is an edit/modification request
            is_modification = (
                self.last_generated_image is not None and 
                (color_tone is not None or sketch is not None or 
                 any(word in prompt.lower() for word in ['change', 'modify', 'update', 'adjust', 'make it', 'add', 'remove']))
            )
            
            if color_tone:
                # Add color guidance to prompt
                temp_desc = color_tone.temperature
                enhanced_prompt += f"\n\nColor palette: {temp_desc} tones with "
                enhanced_prompt += f"hue around {color_tone.hue}°, "
                enhanced_prompt += f"{color_tone.saturation}% saturation, "
                enhanced_prompt += f"{color_tone.lightness}% lightness"
            
            if sketch:
                # Make it VERY clear the sketch is a layout guide, not content
                if is_modification and self.last_generated_image:
                    enhanced_prompt = f"""TASK: Modify the provided image using the sketch as a LAYOUT GUIDE.

The first image is the ORIGINAL image to modify.
The second image (sketch) shows the DESIRED LAYOUT - use it only as a guide for positioning and composition.

DO NOT:
- Include sketch lines in the final image
- Overlay or trace the sketch
- Treat the sketch as content

DO:
- Keep the style and content from the original image
- Rearrange elements to match the sketch's spatial layout
- Use the sketch as a blueprint for WHERE things should be positioned

Original request: {prompt}

Apply the color adjustments if specified, and use the sketch to guide the spatial arrangement."""
                else:
                    enhanced_prompt = f"""TASK: Generate an image using the provided sketch as a LAYOUT GUIDE ONLY.

The sketch shows WHERE objects should be positioned - it is NOT content to include in the final image.

DO NOT:
- Include sketch lines or drawing in the final image
- Overlay or trace the sketch
- Make the image look like a drawing

DO:
- Create a realistic/photographic image
- Position elements according to the sketch's spatial layout
- Use the sketch as a blueprint for composition

Request: {enhanced_prompt}

The sketch defines the spatial arrangement - generate content that follows this layout."""
            
            # Build contents for the message
            contents = []
            
            # Log the enhanced prompt being sent
            print(f"\n{'='*60}")
            print("IMAGE GENERATION PROMPT:")
            print(f"{'='*60}")
            print(enhanced_prompt)
            print(f"{'='*60}\n")
            
            # If this is a modification, include the previous image as reference
            # This ensures the model has explicit access to the image being edited
            if is_modification and self.last_generated_image:
                contents.append(self.last_generated_image)
                print("✓ Including previous image as reference for modification")
            
            # Add the prompt (must come before or after images based on context)
            contents.append(enhanced_prompt)
            
            # Add sketch as additional reference image if provided
            # Place it after the prompt to make the instruction clear
            if sketch:
                try:
                    sketch_bytes = base64.b64decode(sketch)
                    sketch_image = PILImage.open(io.BytesIO(sketch_bytes))
                    contents.append(sketch_image)
                    print("✓ Including sketch as layout guide")
                except Exception as e:
                    print(f"⚠ Warning: Could not process sketch: {e}")
            
            # Send message in chat (maintains context automatically)
            # Retry once if the client was closed
            try:
                response = self.chat_session.send_message(
                    contents,
                    config=types.GenerateContentConfig(
                        response_modalities=['TEXT', 'IMAGE'],
                    )
                )
            except Exception as e:
                if "client has been closed" in str(e).lower():
                    print("⚠ Client was closed, recreating session and retrying...")
                    # Recreate the session with a fresh client
                    client = genai.Client(api_key=self.api_key)
                    self.chat_session = client.chats.create(
                        model='gemini-2.5-flash-image',
                        config=types.GenerateContentConfig(
                            response_modalities=['TEXT', 'IMAGE'],
                        )
                    )
                    self._client = client
                    print("✓ Session recreated, retrying request...")
                    
                    # Retry the request
                    response = self.chat_session.send_message(
                        contents,
                        config=types.GenerateContentConfig(
                            response_modalities=['TEXT', 'IMAGE'],
                        )
                    )
                else:
                    raise
            
            # Print full model response (excluding image data)
            print(f"\n{'='*60}")
            print("IMAGE GENERATION MODEL RESPONSE (gemini-2.5-flash-image):")
            print(f"{'='*60}")
            print(f"Number of parts: {len(response.parts)}")
            for i, part in enumerate(response.parts):
                part_info = []
                if hasattr(part, 'text') and part.text:
                    # Print text content (not base64 image data)
                    text_preview = part.text[:200] if len(part.text) > 200 else part.text
                    part_info.append(f"text (len={len(part.text)}): {text_preview}")
                if hasattr(part, 'inline_data') and part.inline_data:
                    mime = part.inline_data.mime_type
                    data_len = len(part.inline_data.data) if hasattr(part.inline_data, 'data') else 0
                    part_info.append(f"inline_data (mime={mime}, size={data_len} bytes)")
                if hasattr(part, 'executable_code'):
                    part_info.append("executable_code")
                if hasattr(part, 'code_execution_result'):
                    part_info.append("code_execution_result")
                print(f"  Part {i}: {', '.join(part_info) if part_info else 'unknown'}")
            print(f"{'='*60}\n")
            
            # Extract image from response using the official API
            image_data = None
            for part in response.parts:
                # Try using as_image() method (official way)
                if hasattr(part, 'as_image'):
                    try:
                        image = part.as_image()
                        if image:
                            # Convert PIL Image to base64
                            buffer = io.BytesIO()
                            image.save(buffer, format='PNG')
                            image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                            # Store for conversation context
                            self.last_generated_image = image
                            print("✓ Image generated and stored in conversation context")
                            return image_data
                    except Exception as ex:
                        print(f"Warning: Error converting image: {ex}")
                
                # Fallback: check for inline_data
                if part.inline_data is not None:
                    # Image data is already in the inline_data
                    buffer = io.BytesIO()
                    # inline_data might have the image bytes
                    if hasattr(part.inline_data, 'data'):
                        image_data = base64.b64encode(part.inline_data.data).decode('utf-8')
                        print("✓ Image extracted from inline_data")
                        return image_data
                    # Or try to save if it's an image object
                    try:
                        part.inline_data.save(buffer, format='PNG')
                        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                        return image_data
                    except:
                        pass
            
            # Fallback to placeholder if no image in response
            print("Warning: No image in response, using placeholder")
            return self._generate_placeholder_image(prompt, color_tone, sketch)
            
        except Exception as e:
            print(f"Error generating image: {e}")
            return self._generate_placeholder_image(prompt, color_tone, sketch)
    
    def _generate_placeholder_image(self, 
                                    prompt: str = "Generated Image", 
                                    color_tone: Optional[ColorTone] = None,
                                    sketch: Optional[str] = None) -> str:
        """Generate a placeholder image with prompt text"""
        from PIL import Image, ImageDraw, ImageFont
        import io
        import textwrap
        
        # Create image with color tone if specified
        if color_tone:
            # Convert HSL to RGB approximation
            h = color_tone.hue / 360.0
            s = color_tone.saturation / 100.0
            l = color_tone.lightness / 100.0
            
            # Simple HSL to RGB conversion
            if s == 0:
                r = g = b = int(l * 255)
            else:
                def hue_to_rgb(p, q, t):
                    if t < 0: t += 1
                    if t > 1: t -= 1
                    if t < 1/6: return p + (q - p) * 6 * t
                    if t < 1/2: return q
                    if t < 2/3: return p + (q - p) * (2/3 - t) * 6
                    return p
                
                q = l * (1 + s) if l < 0.5 else l + s - l * s
                p = 2 * l - q
                r = int(hue_to_rgb(p, q, h + 1/3) * 255)
                g = int(hue_to_rgb(p, q, h) * 255)
                b = int(hue_to_rgb(p, q, h - 1/3) * 255)
            
            bg_color = (r, g, b)
        else:
            bg_color = (73, 109, 137)
        
        img = Image.new('RGB', (512, 512), color=bg_color)
        d = ImageDraw.Draw(img)
        
        # Add text
        wrapped_text = textwrap.fill(prompt, width=40)
        y_offset = 200
        
        # Draw title
        d.text((20, 20), "PLACEHOLDER IMAGE", fill=(255, 255, 255))
        d.text((20, 50), "(Gemini doesn't generate images)", fill=(200, 200, 200))
        
        # Draw prompt
        for line in wrapped_text.split('\n'):
            d.text((20, y_offset), line, fill=(255, 255, 255))
            y_offset += 25
        
        # Add color tone info if present
        if color_tone:
            y_offset += 30
            d.text((20, y_offset), f"Color: H{color_tone.hue}° S{color_tone.saturation}% L{color_tone.lightness}%", 
                   fill=(255, 255, 255))