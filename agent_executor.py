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
import base64
import re

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    DataPart,
    Part,
    Task,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import (
    new_agent_parts_message,
    new_agent_text_message,
    new_task,
)
from a2a.utils.errors import ServerError
from a2ui.extension.a2ui_extension import create_a2ui_part, try_activate_a2ui_extension
from agent_new import ImageGenerationAgent

logger = logging.getLogger(__name__)


class ImageGenerationAgentExecutor(AgentExecutor):
  """Image Generation AgentExecutor."""

  def __init__(self, ui_agent: ImageGenerationAgent, text_agent: ImageGenerationAgent):
    # Instantiate two agents: one for UI and one for text-only.
    # The appropriate one will be chosen at execution time.
    self.ui_agent = ui_agent
    self.text_agent = text_agent

  async def execute(
      self,
      context: RequestContext,
      event_queue: EventQueue,
  ) -> None:
    query = ""
    ui_event_part = None
    action = None
    widget_updates = {}

    logger.info(f"--- Client requested extensions: {context.requested_extensions} ---")
    use_ui = try_activate_a2ui_extension(context)

    # Determine which agent to use based on whether the a2ui extension is active.
    if use_ui:
      agent = self.ui_agent
      logger.info("--- AGENT_EXECUTOR: A2UI extension is active. Using UI agent. ---")
    else:
      agent = self.text_agent
      logger.info(
          "--- AGENT_EXECUTOR: A2UI extension is not active. Using text agent. ---"
      )

    if context.message and context.message.parts:
      logger.info(
          f"--- AGENT_EXECUTOR: Processing {len(context.message.parts)} message"
          " parts ---"
      )
      for i, part in enumerate(context.message.parts):
        if isinstance(part.root, DataPart):
          if "userAction" in part.root.data:
            logger.info(f"  Part {i}: Found a2ui UI ClientEvent payload.")
            ui_event_part = part.root.data["userAction"]
          else:
            logger.info(f"  Part {i}: DataPart (data: {part.root.data})")
        elif isinstance(part.root, TextPart):
          logger.info(f"  Part {i}: TextPart (text: {part.root.text})")
        else:
          logger.info(f"  Part {i}: Unknown part type ({type(part.root)})")

    if ui_event_part:
      logger.info(f"Received a2ui ClientEvent: {ui_event_part}")
      action = ui_event_part.get("actionName")
      ctx = ui_event_part.get("context", {})

      # Handle widget update actions (when user changes widget values)
      if action == "update_widgets":
        # Extract widget values from context
        widget_updates = ctx.get("widgets", {})
        # Use the previous prompt from session or a default
        query = ctx.get("prompt", "Regenerate image with updated parameters")
        logger.info(f"Widget updates received: {widget_updates}")
      else:
        query = f"User submitted an event: {action} with data: {ctx}"
    else:
      logger.info("No a2ui UI event part found. Falling back to text input.")
      query = context.get_user_input()

    logger.info(f"--- AGENT_EXECUTOR: Final query for agent: '{query}' ---")

    task = context.current_task

    if not task:
      task = new_task(context.message)
      await event_queue.enqueue_event(task)
    updater = TaskUpdater(event_queue, task.id, task.context_id)

    # Call the agent's stream method with widget updates if available
    async for item in agent.stream(query, task.context_id, widget_updates if widget_updates else None):
      is_task_complete = item["is_task_complete"]
      if not is_task_complete:
        await updater.update_status(
            TaskState.working,
            new_agent_text_message(item["updates"], task.context_id, task.id),
        )
        continue

      # Task complete - send final response
      final_state = TaskState.input_required  # Always require input for potential regeneration

      content = item["content"]
      final_parts = []
      
      if "---a2ui_JSON---" in content:
        logger.info("Splitting final response into text and UI parts.")
        text_content, json_string = content.split("---a2ui_JSON---", 1)

        if text_content.strip():
          final_parts.append(Part(root=TextPart(text=text_content.strip())))

        if json_string.strip():
          try:
            json_string_cleaned = (
                json_string.strip().lstrip("```json").rstrip("```").strip()
            )
            # Parse and send A2UI messages
            json_data = json.loads(json_string_cleaned)

            if isinstance(json_data, list):
              logger.info(
                  f"Found {len(json_data)} A2UI messages. Creating individual DataParts."
              )
              for message in json_data:
                final_parts.append(create_a2ui_part(message))
            else:
              # Handle the case where a single JSON object is returned
              logger.info("Received a single JSON object. Creating a DataPart.")
              final_parts.append(create_a2ui_part(json_data))

          except json.JSONDecodeError as e:
            logger.error(f"Failed to parse UI JSON: {e}")
            final_parts.append(Part(root=TextPart(text=json_string)))
      else:
        final_parts.append(Part(root=TextPart(text=content.strip())))

      logger.info("--- FINAL PARTS TO BE SENT (before adding inline image) ---")
      for i, part in enumerate(final_parts):
        logger.info(f"  - Part {i}: Type = {type(part.root)}")
        if isinstance(part.root, TextPart):
          logger.info(f"    - Text: {part.root.text[:200]}...")
        elif isinstance(part.root, DataPart):
          logger.info(f"    - Data keys: {part.root.data.keys() if isinstance(part.root.data, dict) else 'not a dict'}")
      
      # IMPORTANT: Also include the image as an inlineData part for simple frontends
      # Extract the base64 image data from the agent's last generated image
      if agent.last_generated_image:
        logger.info("Adding image as inlineData part for frontend compatibility")
        # Extract base64 data from data:image/jpeg;base64,... format
        match = re.match(r'data:image/(jpeg|png);base64,(.+)', agent.last_generated_image)
        if match:
          mime_type = f"image/{match.group(1)}"
          base64_data = match.group(2)
          
          # Create a DataPart with inlineData structure (A2A SDK format)
          inline_part = Part(root=DataPart(
            kind='data',
            data={
              'inlineData': {
                'mimeType': mime_type,
                'data': base64_data
              }
            }
          ))
          # Insert after text if exists, otherwise at beginning
          insert_index = 1 if len(final_parts) > 0 and isinstance(final_parts[0].root, TextPart) else 0
          final_parts.insert(insert_index, inline_part)
          logger.info(f"Inserted inlineData part at index {insert_index}")
        else:
          logger.warning("Could not parse image data URL format")
      
      logger.info("-----------------------------")

      await updater.update_status(
          final_state,
          new_agent_parts_message(final_parts, task.context_id, task.id),
          final=False,  # Keep task open for potential regeneration
      )
      break

  async def cancel(
      self, request: RequestContext, event_queue: EventQueue
  ) -> Task | None:
    raise ServerError(error=UnsupportedOperationError())
