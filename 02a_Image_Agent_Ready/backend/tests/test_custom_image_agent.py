import pytest
import json
from unittest.mock import AsyncMock, MagicMock

from google.adk.agents import InvocationContext
from google.adk.events import Event
from story_image_agent.agent import CustomImageAgent
from story_image_agent.imagen_tool import ImagenTool
from google.adk.sessions import Session
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.agents import Agent
from google.adk.framework import Input

@pytest.fixture
def mock_imagen_tool():
    """Provides a mock ImagenTool that returns a predefined image URL."""
    mock_tool = MagicMock(spec=ImagenTool)
    mock_tool.run = AsyncMock(return_value=json.dumps({
        "success": True,
        "images": [{
            "gcs_url": "https://storage.googleapis.com/fake-bucket/fake-image.png"
        }]
    }))
    return mock_tool


@pytest.fixture
def image_agent(mock_imagen_tool):
    """Provides a CustomImageAgent with a mocked ImagenTool."""
    agent = CustomImageAgent()
    agent._imagen_tool = mock_imagen_tool
    return agent

@pytest.fixture
def mock_invocation_context():
    """Provides a mock InvocationContext."""
    mock_session = MagicMock(spec=Session)
    mock_session.state = {}
    mock_input = MagicMock(spec=Input)
    mock_input.text = ""
    ctx = InvocationContext(
        session_service=InMemorySessionService(),
        invocation_id="test_invocation",
        agent=MagicMock(spec=Agent),
        session=mock_session,
        input=mock_input
    )
    return ctx


@pytest.mark.asyncio
async def test_custom_image_agent_success(image_agent, mock_imagen_tool, mock_invocation_context):
    """Tests the successful generation of an image by the CustomImageAgent."""
    # 1. Setup
    input_data = {
        "scene_description": "A friendly robot waving hello.",
        "character_descriptions": ["A small, round robot with a single blue eye."]
    }
    mock_invocation_context.input.text = json.dumps(input_data)

    # 2. Execution
    events = [event async for event in image_agent._run_async_impl(mock_invocation_context)]

    # 3. Assertions
    # Check prompt construction
    expected_prompt_prefix = "Children's book cartoon illustration with bright vibrant colors, simple shapes, friendly characters."
    expected_character_str = "A small, round robot with a single blue eye."
    expected_prompt = f"{expected_prompt_prefix} Scene: {input_data['scene_description']}. Characters: {expected_character_str}."
    mock_imagen_tool.run.assert_called_once_with(prompt=expected_prompt)

    # Check session state
    assert "image_result" in mock_invocation_context.session.state
    result_json = mock_invocation_context.session.state["image_result"]
    result_data = json.loads(result_json)
    assert result_data["success"] is True
    assert "https://storage.googleapis.com/fake-bucket/fake-image.png" in result_data["images"][0]["gcs_url"]

    # Check yielded events
    assert any(e.type == "agent_thought" for e in events)
    assert any(e.type == "agent_output" for e in events)
    output_event = next(e for e in events if e.type == "agent_output")
    assert "https://storage.googleapis.com/fake-bucket/fake-image.png" in output_event.text


@pytest.mark.asyncio
async def test_custom_image_agent_error(image_agent, mock_imagen_tool, mock_invocation_context):
    """Tests the agent's error handling when the ImagenTool fails."""
    # 1. Setup
    mock_imagen_tool.run.side_effect = Exception("Test error from ImagenTool")

    input_data = {
        "scene_description": "A cat chasing a butterfly.",
        "character_descriptions": []
    }
    mock_invocation_context.input.text = json.dumps(input_data)

    # 2. Execution
    events = [event async for event in image_agent._run_async_impl(mock_invocation_context)]

    # 3. Assertions
    # Check session state for error
    assert "image_result" in mock_invocation_context.session.state
    result_json = mock_invocation_context.session.state["image_result"]
    result_data = json.loads(result_json)
    assert result_data["success"] is False
    assert "Test error from ImagenTool" in result_data["error"]

    # Check yielded events for error
    assert any(e.type == "agent_thought" and "An error occurred" in e.observation for e in events)
    output_event = next(e for e in events if e.type == "agent_output")
    assert "An error occurred" in output_event.text