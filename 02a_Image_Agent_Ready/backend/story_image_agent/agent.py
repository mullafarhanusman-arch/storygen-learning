from typing import AsyncGenerator
from pydantic import PrivateAttr

from google.adk.agents import Agent, BaseAgent, InvocationContext
from google.adk.events import Event
from story_image_agent.imagen_tool import ImagenTool


class CustomImageAgent(BaseAgent):
    """A custom agent that generates an image based on a story scene."""
    _imagen_tool: ImagenTool = PrivateAttr()

    def __init__(self, imagen_tool: ImagenTool | None = None):
        super().__init__()
        self._imagen_tool = imagen_tool or ImagenTool()

    @property
    def name(self) -> str:
        return "custom_image_agent"

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """Generates an image based on the provided scene and character descriptions."""
        try:
            # 1. Parse Input
            input_json = ctx.input.text
            input_data = json.loads(input_json)
            scene_description = input_data.get("scene_description")
            character_descriptions = input_data.get("character_descriptions", [])

            # 2. Build Prompt
            prompt_prefix = "Children's book cartoon illustration with bright vibrant colors, simple shapes, friendly characters."
            character_str = ", ".join(character_descriptions)
            prompt = f"{prompt_prefix} Scene: {scene_description}. Characters: {character_str}."

            yield Event.agent_thought(
                observation=f"Generating image with prompt: {prompt}"
            )

            # 3. Execute Tool
            image_result = await self._imagen_tool.run(prompt=prompt)

            # 4. Store Result in Session State
            ctx.session.state["image_result"] = image_result
            yield Event.agent_thought(
                observation=f"Image generated successfully: {image_result}"
            )
            yield Event.agent_output(text=image_result)

        except Exception as e:
            error_message = f"An error occurred: {e}"
            ctx.session.state["image_result"] = json.dumps(
                {"success": False, "error": error_message}
            )
            yield Event.agent_thought(observation=error_message)
            yield Event.agent_output(text=error_message)