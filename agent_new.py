# Copyright 2025
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
import os
import base64
import re
from collections.abc import AsyncIterable
from typing import Any, Dict, List

import jsonschema
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from google.adk.agents.llm_agent import LlmAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from a2ui.inference.schema.manager import A2uiSchemaManager
from a2ui.inference.schema.common_modifiers import remove_strict_validation

# Import the actual image generation SDK
import google.genai as genai

logger = logging.getLogger(__name__)

# Agent prompts
ROLE_DESCRIPTION = (
    "You are a helpful image generation assistant. Your goal is to generate images based on user requests. "
    "Your final output MUST be an a2ui UI JSON response that displays the generated image and any input widgets needed for customization."
)

WORKFLOW_DESCRIPTION = """
To generate the response, you MUST follow these rules:
1.  Your response MUST be in two parts, separated by the delimiter: `---a2ui_JSON---`.
2.  The first part is your conversational text response explaining what you generated.
3.  The second part is a single, raw JSON object which is a list of A2UI messages.
4.  The JSON part MUST validate against the A2UI JSON SCHEMA provided below.
"""

UI_DESCRIPTION = """
- You MUST always include an Image component to display the generated image, using the path "/generated_image" for the image data.
- If the user's request requires customization parameters (like color, size, style, etc.), generate appropriate input widgets:
  * Use TextField for text inputs (colors, descriptions)
  * Use Slider for numeric ranges (size, brightness, etc.)
  * Use Select (dropdown) for predefined choices (style, format, etc.)
- Bind each widget's value to a data model path (e.g., "/color", "/size", "/style").
- The widget values will be used to regenerate the image when the user changes them.
- For simple requests with no customization, you can show just the image without widgets.
- Use IMAGE_WITH_SINGLE_WIDGET_EXAMPLE for requests with one customization parameter.
- Use IMAGE_WITH_MULTIPLE_WIDGETS_EXAMPLE for requests with multiple customization parameters.
"""


class ImageGenerationAgent:
  """An agent that generates images based on user prompts."""

  SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

  def __init__(self, base_url: str, use_ui: bool = True):
    self.base_url = base_url
    self.use_ui = use_ui
    self._schema_manager = (
        A2uiSchemaManager(
            "0.8",
            basic_examples_path="examples/",
            schema_modifiers=[remove_strict_validation],
        )
        if use_ui
        else None
    )
    self._agent = self._build_agent(use_ui)
    self._user_id = "image_gen_user"
    self._runner = Runner(
        app_name=self._agent.name,
        agent=self._agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )
    
    # Initialize Gemini image generation client
    self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not self.api_key:
      raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY environment variable must be set")
    
    # Chat session state for multi-turn image generation
    self.chat_session = None
    self._client = None
    self.last_generated_image = None

  def get_agent_card(self) -> AgentCard:
    capabilities = AgentCapabilities(
        streaming=True,
        extensions=[self._schema_manager.get_agent_extension()] if self._schema_manager else [],
    )
    skill = AgentSkill(
        id="generate_images",
        name="Image Generation",
        description=(
            "Generates images based on text descriptions using Gemini 2.5 Flash Image model."
        ),
        tags=["image", "generation", "ai"],
        examples=["Generate a blue cat", "Create an image of a sunset with size 1024"],
    )

    return AgentCard(
        name="Image Generation Agent",
        description="This agent generates images based on user descriptions.",
        url=self.base_url,
        version="1.0.0",
        default_input_modes=ImageGenerationAgent.SUPPORTED_CONTENT_TYPES,
        default_output_modes=ImageGenerationAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill],
    )

  def get_processing_message(self) -> str:
    return "Generating your image..."

  def _build_agent(self, use_ui: bool) -> LlmAgent:
    """Builds the LLM agent for image generation."""
    LITELLM_MODEL = os.getenv("LITELLM_MODEL", "gemini/gemini-2.5-flash")

    instruction = (
        self._schema_manager.generate_system_prompt(
            role_description=ROLE_DESCRIPTION,
            workflow_description=WORKFLOW_DESCRIPTION,
            ui_description=UI_DESCRIPTION,
            include_schema=True,
            include_examples=True,
            validate_examples=True,
        )
        if use_ui
        else "You are a helpful image generation assistant."
    )

    return LlmAgent(
        model=LiteLlm(model=LITELLM_MODEL),
        name="image_generation_agent",
        description="An agent that generates images based on user descriptions.",
        instruction=instruction,
        tools=[],  # No tools needed for image generation
    )

  def _extract_widgets_from_prompt(self, prompt: str) -> Dict[str, Any]:
    """
    Extract widget parameters from the user prompt.
    Returns a dictionary of widget values to use for image generation.
    """
    # This is a simplified extraction - in production you'd use NLU
    widgets = {}
    
    # Look for common keywords
    prompt_lower = prompt.lower()
    
    # Color extraction
    colors = ["red", "blue", "green", "yellow", "orange", "purple", "pink", "black", "white"]
    for color in colors:
      if color in prompt_lower:
        widgets["color"] = color
        break
    
    # Size extraction
    size_match = re.search(r"\bsize\s*(?:is|=|:)?\s*(\d{2,4})\b", prompt_lower)
    if size_match:
      size_value = int(size_match.group(1))
      widgets["size"] = max(128, min(2048, size_value))
    elif "large" in prompt_lower:
      widgets["size"] = 1024
    elif "small" in prompt_lower:
      widgets["size"] = 256
    else:
      widgets["size"] = 512
    
    # Style extraction
    if "cartoon" in prompt_lower or "animated" in prompt_lower:
      widgets["style"] = "cartoon"
    elif "realistic" in prompt_lower or "photo" in prompt_lower:
      widgets["style"] = "realistic"
    elif "abstract" in prompt_lower:
      widgets["style"] = "abstract"
    
    return widgets

  async def _generate_image(self, prompt: str, widgets: Dict[str, Any]) -> str:
    """
    Generate an image using Gemini 2.5 Flash Image model with chat session.
    Returns base64-encoded image data.
    """
    from PIL import Image as PILImage
    import io
    
    # Enhance prompt with widget values
    enhanced_prompt = prompt
    if "color" in widgets:
      enhanced_prompt = f"{prompt}, {widgets['color']} color"
    if "style" in widgets:
      enhanced_prompt = f"{enhanced_prompt}, {widgets['style']} style"
    
    logger.info(f"Generating image with prompt: {enhanced_prompt}")
    
    try:
      # Initialize client (create fresh client each time)
      client = genai.Client(api_key=self.api_key)
      
      # Check if we need to create/recreate chat session
      if self.chat_session is None:
        self.chat_session = client.chats.create(
            model='gemini-2.5-flash-image',
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE'],
            )
        )
        self._client = client
        logger.info("Created new chat session for image generation")
      else:
        # Recreate session if needed
        try:
          if not hasattr(self, '_client') or self._client is None:
            raise Exception("Client was closed, recreating session")
        except:
          logger.info("Recreating chat session...")
          self.chat_session = client.chats.create(
              model='gemini-2.5-flash-image',
              config=types.GenerateContentConfig(
                  response_modalities=['TEXT', 'IMAGE'],
              )
          )
          self._client = client
      
      # Send message to chat session
      response = self.chat_session.send_message(enhanced_prompt)
      
      # Extract image from response
      image_data = None
      for part in response.candidates[0].content.parts:
        if hasattr(part, 'inline_data') and part.inline_data:
          image_data = part.inline_data.data
          break
      
      if image_data:
        # Convert to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        result = f"data:image/jpeg;base64,{base64_image}"
        self.last_generated_image = result
        return result
      else:
        raise ValueError("No image data found in response")
        
    except Exception as e:
      logger.error(f"Error generating image: {e}", exc_info=True)
      raise

  async def stream(self, query: str, session_id: str, widget_updates: Dict[str, Any] = None) -> AsyncIterable[dict[str, Any]]:
    """
    Process user query and stream A2UI responses.
    
    Args:
      query: User's text query
      session_id: Session identifier
      widget_updates: Optional dictionary of widget values from user interactions
    """
    session_state = {"base_url": self.base_url}

    session = await self._runner.session_service.get_session(
        app_name=self._agent.name,
        user_id=self._user_id,
        session_id=session_id,
    )
    if session is None:
      session = await self._runner.session_service.create_session(
          app_name=self._agent.name,
          user_id=self._user_id,
          state=session_state,
          session_id=session_id,
      )
    elif "base_url" not in session.state:
      session.state["base_url"] = self.base_url

    # Extract or use provided widget values
    if widget_updates:
      widgets = widget_updates
    else:
      widgets = self._extract_widgets_from_prompt(query)
    
    # Generate the image first
    try:
      yield {
          "is_task_complete": False,
          "updates": self.get_processing_message(),
      }
      
      image_data = await self._generate_image(query, widgets)
      
      # Store image data in session
      session.state["current_image"] = image_data
      session.state["current_prompt"] = query
      session.state["current_widgets"] = widgets
      
    except Exception as e:
      logger.error(f"Image generation failed: {e}")
      yield {
          "is_task_complete": True,
          "content": f"I'm sorry, I couldn't generate the image. Error: {str(e)}",
      }
      return

    # Now ask the LLM to generate A2UI response
    max_retries = 1
    attempt = 0
    
    # Construct the query for the LLM with image generation result
    llm_query = f"""
User request: {query}

I have generated an image based on this request.
The image data is available at path "/generated_image".

Detected customization parameters: {json.dumps(widgets, indent=2)}

Please generate an A2UI response that:
1. Displays the generated image
2. Shows appropriate input widgets for the detected parameters
3. Binds widgets to data model paths so they can be modified

Remember to follow the A2UI schema and use the delimiter ---a2ui_JSON---.
"""

    effective_catalog = self._schema_manager.get_effective_catalog()
    if self.use_ui and not effective_catalog.catalog_schema:
      logger.error("A2UI_SCHEMA is not loaded. Cannot perform UI validation.")
      yield {
          "is_task_complete": True,
          "content": "I'm sorry, I'm facing an internal configuration error with my UI components.",
      }
      return

    while attempt <= max_retries:
      attempt += 1
      logger.info(f"Attempt {attempt}/{max_retries + 1} for session {session_id}")

      current_message = types.Content(
          role="user", parts=[types.Part.from_text(text=llm_query)]
      )
      final_response_content = None

      async for event in self._runner.run_async(
          user_id=self._user_id,
          session_id=session.id,
          new_message=current_message,
      ):
        logger.info(f"Event from runner: {event}")
        if event.is_final_response():
          if event.content and event.content.parts and event.content.parts[0].text:
            final_response_content = "\n".join(
                [p.text for p in event.content.parts if p.text]
            )
          break
        else:
          logger.info(f"Intermediate event: {event}")

      if final_response_content is None:
        logger.warning(f"Received no final response content from runner (Attempt {attempt}).")
        if attempt <= max_retries:
          llm_query = f"I received no response. Please try again. {llm_query}"
          continue
        else:
          final_response_content = "I'm sorry, I encountered an error and couldn't process your request."

      is_valid = False
      error_message = ""

      if self.use_ui:
        logger.info(f"Validating UI response (Attempt {attempt})...")
        try:
          if "---a2ui_JSON---" not in final_response_content:
            raise ValueError("Delimiter '---a2ui_JSON---' not found.")

          text_part, json_string = final_response_content.split("---a2ui_JSON---", 1)

          if not json_string.strip():
            raise ValueError("JSON part is empty.")

          json_string_cleaned = (
              json_string.strip().lstrip("```json").rstrip("```").strip()
          )

          if not json_string_cleaned:
            raise ValueError("Cleaned JSON string is empty.")

          parsed_json_data = json.loads(json_string_cleaned)

          # Normalize/repair common A2UI issues for renderer compatibility.
          for ui_message in parsed_json_data:
            if "surfaceUpdate" in ui_message:
              components = ui_message["surfaceUpdate"].get("components", [])

              # De-duplicate components by id (keep last occurrence).
              deduped_by_id = {}
              for component_entry in components:
                component_id = component_entry.get("id")
                if component_id:
                  deduped_by_id[component_id] = component_entry
              if deduped_by_id:
                ui_message["surfaceUpdate"]["components"] = list(deduped_by_id.values())
                components = ui_message["surfaceUpdate"]["components"]

              for component_entry in components:
                component = component_entry.get("component", {})

                # Ensure image binding points to generated image path.
                if "Image" in component:
                  image_cfg = component.get("Image", {})
                  sources = image_cfg.get("sources", [])
                  if not sources:
                    image_cfg["sources"] = [{
                        "uri": {"path": "/generated_image"},
                        "mimeType": "image/jpeg",
                    }]
                  else:
                    for source in sources:
                      uri = source.get("uri", {})
                      path = uri.get("path")
                      if not path:
                        uri["path"] = "/generated_image"
                      elif isinstance(path, str) and not path.startswith("/"):
                        uri["path"] = f"/{path}"
                      source["uri"] = uri
                  component["Image"] = image_cfg

                # Ensure slider has sane range and value binding.
                if "Slider" in component:
                  slider_cfg = component.get("Slider", {})
                  if "value" not in slider_cfg:
                    slider_cfg["value"] = {"path": "/size"}
                  elif isinstance(slider_cfg.get("value"), dict):
                    value_path = slider_cfg["value"].get("path")
                    if isinstance(value_path, str) and not value_path.startswith("/"):
                      slider_cfg["value"]["path"] = f"/{value_path}"

                  if "minValue" not in slider_cfg:
                    slider_cfg["minValue"] = {"literalNumber": 128}
                  if "maxValue" not in slider_cfg:
                    slider_cfg["maxValue"] = {"literalNumber": 2048}

                  component["Slider"] = slider_cfg

                component_entry["component"] = component

          logger.info("Validating against A2UI_SCHEMA...")
          effective_catalog.validator.validate(parsed_json_data)
          
          # Inject the actual image data into the response
          for message in parsed_json_data:
            if "dataModelUpdate" in message:
              contents = message["dataModelUpdate"].get("contents", [])
              has_generated_image = False
              has_size = False
              for content in contents:
                if content.get("key") == "generated_image":
                  has_generated_image = True
                  content["valueString"] = image_data
                # Update widget values from session
                elif content.get("key") in widgets:
                  widget_key = content.get("key")
                  widget_value = widgets[widget_key]
                  if widget_key == "size":
                    has_size = True
                  if isinstance(widget_value, int):
                    content["valueInt"] = widget_value
                  else:
                    content["valueString"] = str(widget_value)

              if not has_generated_image:
                contents.append({
                    "key": "generated_image",
                    "valueString": image_data,
                })

              if "size" in widgets and not has_size:
                contents.append({
                    "key": "size",
                    "valueInt": int(widgets["size"]),
                })

              message["dataModelUpdate"]["contents"] = contents

          logger.info("UI JSON successfully parsed and validated.")
          is_valid = True
          
          # Update final response with injected data
          final_response_content = text_part + "---a2ui_JSON---\n" + json.dumps(parsed_json_data, indent=2)

        except (ValueError, json.JSONDecodeError, jsonschema.exceptions.ValidationError) as e:
          logger.warning(f"A2UI validation failed: {e} (Attempt {attempt})")
          logger.warning(f"Failed response content: {final_response_content[:500]}...")
          error_message = f"Validation failed: {e}."

      else:
        is_valid = True

      if is_valid:
        logger.info(f"Response is valid. Sending final response (Attempt {attempt}).")
        logger.info(f"Final response: {final_response_content[:500]}...")
        yield {
            "is_task_complete": True,
            "content": final_response_content,
        }
        return

      if attempt <= max_retries:
        logger.warning(f"Retrying... ({attempt}/{max_retries + 1})")
        llm_query = (
            f"Your previous response was invalid. {error_message} You MUST generate a "
            "valid response that strictly follows the A2UI JSON SCHEMA. {llm_query}"
        )

    logger.error("Max retries exhausted. Sending text-only error.")
    yield {
        "is_task_complete": True,
        "content": "I'm sorry, I'm having trouble generating the interface for that request right now.",
    }


if __name__ == "__main__":
  # For testing, create an agent and print its system prompt
  agent = ImageGenerationAgent(base_url="http://localhost:10002", use_ui=True)
  print("Agent created successfully!")
  print(f"Agent name: {agent._agent.name}")
  print(f"Agent description: {agent._agent.description}")
