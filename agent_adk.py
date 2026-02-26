"""
A2UI Image Generation Agent using Google ADK
Implements dynamic widget generation following A2UI v0.8 protocol
"""

import os
import base64
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import json

from google.adk.agents import llm_agent
from google.adk import runners
from google import genai
from google.genai import types as genai_types
from PIL import Image as PILImage
import io


@dataclass
class ColorTone:
    """Represents a color tone configuration"""
    hue: float  # 0-360
    saturation: float  # 0-100
    lightness: float  # 0-100
    temperature: str  # "warm" or "cool"


class ImageGenerationAgent(llm_agent.LlmAgent):
    """
    Image Generation Agent extending Google ADK's LlmAgent
    Generates images with AI-determined dynamic widgets following A2UI protocol
    """
    
    def __init__(self, api_key: str, **kwargs):
        """Initialize the agent with Gemini API key"""
        super().__init__(
            model=api_key,  # Will override this
            **kwargs
        )
        self.api_key = api_key
        self.current_color_tone: Optional[ColorTone] = None
        self.current_sketch: Optional[str] = None
        self.widget_values: Dict[str, Any] = {}
        self.chat_session = None
        self._client = None
        self.last_generated_image = None
        
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
    
    async def process_message(self, user_message: str, attachments: Optional[List] = None) -> Dict:
        """Process user message and generate A2UI response with dynamic widgets"""
        
        print(f"\n{'='*60}")
        print(f"Processing message: '{user_message}'")
        print(f"Attachments: {attachments}")
        
        # Skip widget analysis if this is an apply adjustments command with attachments
        should_analyze_widgets = not (
            attachments and 
            any(word in user_message.lower() for word in ['apply', 'adjustment'])
        )
        
        if should_analyze_widgets:
            widget_needs = await self.analyze_request(user_message)
            
            # Clear stale widget values and state for fresh requests
            if not attachments:
                if hasattr(self, 'widget_values') and self.widget_values:
                    print(f"⊘ Clearing stale widget values: {list(self.widget_values.keys())}")
                    self.widget_values = {}
                    self.current_color_tone = None
                    self.current_sketch = None
                    print("⊘ Cleared color tone and sketch state")
                    
                    if self.chat_session is not None:
                        print("⊘ Resetting chat session for fresh start")
                        self.chat_session = None
                        self.last_generated_image = None
                        self._client = None
        else:
            print("⊘ Skipping widget analysis (applying existing widget values)")
            widget_needs = {'widgets': []}
        
        # Process widget attachments
        if attachments:
            for attachment in attachments:
                widget_id = attachment.get("widget_id")
                widget_type = attachment.get("type")
                widget_data = attachment.get("data", {})
                
                self.widget_values[widget_id] = widget_data
                print(f"✓ Widget '{widget_id}' (type: {widget_type}) updated: {widget_data}")
                
                # Handle special widget types for image generation
                if widget_type == 'color-tone-control' or 'hue' in widget_data:
                    self.current_color_tone = ColorTone(
                        hue=widget_data.get("hue", 180),
                        saturation=widget_data.get("saturation", 50),
                        lightness=widget_data.get("lightness", 50),
                        temperature=widget_data.get("temperature", "neutral")
                    )
                elif widget_type in ['sketch-board', 'sketch-canvas'] or 'sketch' in widget_data:
                    self.current_sketch = widget_data.get("sketch")
        
        # Build enhanced prompt with widget values
        enhanced_prompt = self._build_prompt_with_widgets(user_message)
        
        # Generate image
        print(f"Generating image with: color_tone={self.current_color_tone is not None}, sketch={self.current_sketch is not None}")
        if self.widget_values:
            print(f"Active widget values: {list(self.widget_values.keys())}")
        
        image_data = await self.generate_image(
            prompt=enhanced_prompt,
            color_tone=self.current_color_tone,
            sketch=self.current_sketch
        )
        print(f"Image generated: {len(image_data) if image_data else 0} bytes")
        
        # Create A2UI response
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
        if not self.widget_values:
            return base_prompt
        
        enhanced = base_prompt
        widget_instructions = []
        
        for widget_id, widget_data in self.widget_values.items():
            # Skip old-style widgets (handled separately)
            if 'hue' in widget_data or 'sketch' in widget_data:
                continue
            
            # Universal format - convert widget ID to human-readable label
            human_label = widget_id.replace('-', ' ').replace('_', ' ').title()
            
            # Format widget data universally
            if len(widget_data) == 1:
                key, val = list(widget_data.items())[0]
                widget_instructions.append(f"{human_label}: {val}")
            else:
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
        
        if text:
            message["parts"].append({"text": text})
        
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
    
    async def generate_image(
        self,
        prompt: str,
        color_tone: Optional[ColorTone] = None,
        sketch: Optional[str] = None
    ) -> str:
        """Generate image using Gemini 2.5 Flash Image"""
        try:
            from google import genai
            from google.genai import types
            from PIL import Image as PILImage
            import io
            
            client = genai.Client(api_key=self.api_key)
            
            # Create or reuse chat session
            if self.chat_session is None:
                self.chat_session = client.chats.create(
                    model='gemini-2.5-flash-image',
                    config=types.GenerateContentConfig(
                        response_modalities=['TEXT', 'IMAGE'],
                    )
                )
                self._client = client
                print("✓ Created new chat session")
            else:
                if not hasattr(self, '_client') or self._client is None:
                    self.chat_session = client.chats.create(
                        model='gemini-2.5-flash-image',
                        config=types.GenerateContentConfig(
                            response_modalities=['TEXT', 'IMAGE'],
                        )
                    )
                    self._client = client
                    print("✓ Recreated chat session")
            
            # Build enhanced prompt
            enhanced_prompt = prompt
            
            is_modification = (
                self.last_generated_image is not None and 
                (color_tone is not None or sketch is not None or 
                 any(word in prompt.lower() for word in ['change', 'modify', 'update', 'adjust', 'make it', 'add', 'remove']))
            )
            
            if color_tone:
                temp_desc = color_tone.temperature
                enhanced_prompt += f"\n\nColor palette: {temp_desc} tones with "
                enhanced_prompt += f"hue around {color_tone.hue}°, "
                enhanced_prompt += f"{color_tone.saturation}% saturation, "
                enhanced_prompt += f"{color_tone.lightness}% lightness"
            
            if sketch:
                if is_modification and self.last_generated_image:
                    enhanced_prompt = f"""TASK: Modify the provided image using the sketch as a LAYOUT GUIDE.

DO NOT:
- Include sketch lines in the final image

DO:
- Keep the style and content from the original image
- Rearrange elements to match the sketch's spatial layout

Original request: {prompt}"""
                else:
                    enhanced_prompt = f"""TASK: Generate an image using the provided sketch as a LAYOUT GUIDE ONLY.

DO NOT:
- Include sketch lines or drawing in the final image

DO:
- Create a realistic/photographic image
- Position elements according to the sketch's spatial layout

Request: {enhanced_prompt}"""
            
            # Build contents
            contents = []
            
            print(f"\n{'='*60}")
            print("IMAGE GENERATION PROMPT:")
            print(f"{'='*60}")
            print(enhanced_prompt)
            print(f"{'='*60}\n")
            
            if is_modification and self.last_generated_image:
                contents.append(self.last_generated_image)
                print("✓ Including previous image as reference")
            
            contents.append(enhanced_prompt)
            
            if sketch:
                try:
                    sketch_bytes = base64.b64decode(sketch)
                    sketch_image = PILImage.open(io.BytesIO(sketch_bytes))
                    contents.append(sketch_image)
                    print("✓ Including sketch as layout guide")
                except Exception as e:
                    print(f"⚠ Warning: Could not process sketch: {e}")
            
            # Send message
            try:
                response = self.chat_session.send_message(
                    contents,
                    config=types.GenerateContentConfig(
                        response_modalities=['TEXT', 'IMAGE'],
                    )
                )
            except Exception as e:
                if "client has been closed" in str(e).lower():
                    print("⚠ Client closed, recreating session...")
                    client = genai.Client(api_key=self.api_key)
                    self.chat_session = client.chats.create(
                        model='gemini-2.5-flash-image',
                        config=types.GenerateContentConfig(
                            response_modalities=['TEXT', 'IMAGE'],
                        )
                    )
                    self._client = client
                    print("✓ Session recreated, retrying...")
                    
                    response = self.chat_session.send_message(
                        contents,
                        config=types.GenerateContentConfig(
                            response_modalities=['TEXT', 'IMAGE'],
                        )
                    )
                else:
                    raise
            
            # Print model response
            print(f"\n{'='*60}")
            print("IMAGE GENERATION MODEL RESPONSE (gemini-2.5-flash-image):")
            print(f"{'='*60}")
            print(f"Number of parts: {len(response.parts)}")
            for i, part in enumerate(response.parts):
                part_info = []
                if hasattr(part, 'text') and part.text:
                    text_preview = part.text[:200] if len(part.text) > 200 else part.text
                    part_info.append(f"text (len={len(part.text)}): {text_preview}")
                if hasattr(part, 'inline_data') and part.inline_data:
                    mime = part.inline_data.mime_type
                    data_len = len(part.inline_data.data) if hasattr(part.inline_data, 'data') else 0
                    part_info.append(f"inline_data (mime={mime}, size={data_len} bytes)")
                print(f"  Part {i}: {', '.join(part_info) if part_info else 'unknown'}")
            print(f"{'='*60}\n")
            
            # Extract image
            image_data = None
            for part in response.parts:
                if hasattr(part, 'as_image'):
                    try:
                        image = part.as_image()
                        if image:
                            buffer = io.BytesIO()
                            image.save(buffer, format='PNG')
                            image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                            self.last_generated_image = image
                            print("✓ Image generated and stored")
                            break
                    except Exception as e:
                        print(f"⚠ as_image() failed: {e}")
                
                if part.inline_data is not None:
                    if hasattr(part.inline_data, 'data'):
                        image_data = base64.b64encode(part.inline_data.data).decode('utf-8')
                        print("✓ Image extracted from inline_data")
                        break
                    else:
                        try:
                            buffer = io.BytesIO()
                            part.inline_data.save(buffer, format='PNG')
                            image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                            print("✓ Image extracted by saving inline_data")
                            break
                        except:
                            pass
            
            if not image_data:
                print("Warning: No image in response, using placeholder")
            
            return image_data
            
        except Exception as e:
            print(f"Error generating image: {e}")
            import traceback
            traceback.print_exc()
            return None
