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

import logging
import os

import click
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from agent_new import ImageGenerationAgent
from agent_executor import ImageGenerationAgentExecutor
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
  """Exception for missing API key."""


@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=10002)
def main(host, port):
  try:
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
      raise MissingAPIKeyError(
          "GOOGLE_API_KEY or GEMINI_API_KEY environment variable must be set."
      )

    base_url = f"http://{host}:{port}"

    ui_agent = ImageGenerationAgent(base_url=base_url, use_ui=True)
    text_agent = ImageGenerationAgent(base_url=base_url, use_ui=False)

    agent_executor = ImageGenerationAgentExecutor(ui_agent, text_agent)

    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
    )
    server = A2AStarletteApplication(
        agent_card=ui_agent.get_agent_card(), http_handler=request_handler
    )
    import uvicorn

    app = server.build()

    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://localhost:\d+",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files for generated images if needed
    # app.mount("/static", StaticFiles(directory="images"), name="static")

    logger.info(f"Starting Image Generation Agent server on {host}:{port}")
    logger.info(f"Agent card: {ui_agent.get_agent_card()}")
    
    uvicorn.run(app, host=host, port=port)
  except MissingAPIKeyError as e:
    logger.error(f"Error: {e}")
    exit(1)
  except Exception as e:
    logger.error(f"An error occurred during server startup: {e}", exc_info=True)
    exit(1)


if __name__ == "__main__":
  main()
