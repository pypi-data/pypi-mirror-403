"""Comprehensive tests for structural streaming components."""

import pytest
import json
from unittest.mock import Mock, MagicMock
from march_agent.structural.artifact import Artifact
from march_agent.structural.surface import Surface
from march_agent.structural.text_block import TextBlock
from march_agent.structural.stepper import Stepper
from march_agent.structural.base import StructuralStreamer
from march_agent.streamer import Streamer


class TestArtifact:
    """Test Artifact structural streamer."""

    def test_artifact_id_generation(self):
        """Test that Artifact generates unique IDs."""
        artifact1 = Artifact()
        artifact2 = Artifact()
        assert artifact1.id.startswith("artifact-")
        assert artifact2.id.startswith("artifact-")
        assert artifact1.id != artifact2.id

    def test_artifact_custom_id(self):
        """Test Artifact with custom ID."""
        artifact = Artifact(id="custom-id")
        assert artifact.id == "custom-id"

    def test_artifact_event_type_prefix(self):
        """Test event type prefix."""
        artifact = Artifact()
        assert artifact.get_event_type_prefix() == "artifact"

    def test_artifact_generating_basic(self):
        """Test generating event without parameters."""
        mock_streamer = Mock(spec=Streamer)
        artifact = Artifact()
        artifact._bind_streamer(mock_streamer)

        artifact.generating()

        mock_streamer._send.assert_called_once()
        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["id"] == artifact.id
        assert args[1]["event_type"] == "artifact:generating"
        assert args[1]["persist"] is False

    def test_artifact_generating_with_message(self):
        """Test generating event with message."""
        mock_streamer = Mock(spec=Streamer)
        artifact = Artifact()
        artifact._bind_streamer(mock_streamer)

        artifact.generating(message="Creating chart...")

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["message"] == "Creating chart..."

    def test_artifact_generating_with_progress(self):
        """Test generating event with progress."""
        mock_streamer = Mock(spec=Streamer)
        artifact = Artifact()
        artifact._bind_streamer(mock_streamer)

        artifact.generating(progress=0.75)

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["progress"] == 0.75

    def test_artifact_generating_with_message_and_progress(self):
        """Test generating event with both message and progress."""
        mock_streamer = Mock(spec=Streamer)
        artifact = Artifact()
        artifact._bind_streamer(mock_streamer)

        artifact.generating(message="Processing...", progress=0.5)

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["message"] == "Processing..."
        assert content["progress"] == 0.5

    def test_artifact_done_minimal(self):
        """Test done event with minimal required parameters."""
        mock_streamer = Mock(spec=Streamer)
        artifact = Artifact()
        artifact._bind_streamer(mock_streamer)

        artifact.done(url="https://example.com/chart.png", type="image")

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["url"] == "https://example.com/chart.png"
        assert content["type"] == "image"
        assert args[1]["event_type"] == "artifact:done"

    def test_artifact_done_with_title(self):
        """Test done event with title."""
        mock_streamer = Mock(spec=Streamer)
        artifact = Artifact()
        artifact._bind_streamer(mock_streamer)

        artifact.done(
            url="https://example.com/report.pdf",
            type="document",
            title="Sales Report"
        )

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["title"] == "Sales Report"

    def test_artifact_done_with_description(self):
        """Test done event with description."""
        mock_streamer = Mock(spec=Streamer)
        artifact = Artifact()
        artifact._bind_streamer(mock_streamer)

        artifact.done(
            url="https://example.com/video.mp4",
            type="video",
            description="Tutorial video"
        )

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["description"] == "Tutorial video"

    def test_artifact_done_with_metadata(self):
        """Test done event with metadata."""
        mock_streamer = Mock(spec=Streamer)
        artifact = Artifact()
        artifact._bind_streamer(mock_streamer)

        metadata = {"size": 1024, "mimeType": "image/png", "dimensions": {"width": 800, "height": 600}}
        artifact.done(
            url="https://example.com/image.png",
            type="image",
            metadata=metadata
        )

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["metadata"] == metadata

    def test_artifact_done_all_parameters(self):
        """Test done event with all parameters."""
        mock_streamer = Mock(spec=Streamer)
        artifact = Artifact()
        artifact._bind_streamer(mock_streamer)

        artifact.done(
            url="https://example.com/file.pdf",
            type="document",
            title="Report",
            description="Annual report",
            metadata={"size": 2048}
        )

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["url"] == "https://example.com/file.pdf"
        assert content["type"] == "document"
        assert content["title"] == "Report"
        assert content["description"] == "Annual report"
        assert content["metadata"] == {"size": 2048}

    def test_artifact_error(self):
        """Test error event."""
        mock_streamer = Mock(spec=Streamer)
        artifact = Artifact()
        artifact._bind_streamer(mock_streamer)

        artifact.error(message="Failed to generate chart")

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["message"] == "Failed to generate chart"
        assert args[1]["event_type"] == "artifact:error"

    def test_artifact_method_chaining(self):
        """Test method chaining returns self."""
        mock_streamer = Mock(spec=Streamer)
        artifact = Artifact()
        artifact._bind_streamer(mock_streamer)

        result = artifact.generating(message="Creating...")
        assert result is artifact

        result = artifact.done(url="https://example.com", type="image")
        assert result is artifact

        result = artifact.error(message="Failed")
        assert result is artifact

    def test_artifact_not_bound_error(self):
        """Test error when trying to send event without bound streamer."""
        artifact = Artifact()

        with pytest.raises(RuntimeError, match="not bound to a Streamer"):
            artifact.generating()


class TestSurface:
    """Test Surface structural streamer."""

    def test_surface_id_generation(self):
        """Test that Surface generates unique IDs."""
        surface1 = Surface()
        surface2 = Surface()
        assert surface1.id.startswith("surface-")
        assert surface2.id.startswith("surface-")
        assert surface1.id != surface2.id

    def test_surface_custom_id(self):
        """Test Surface with custom ID."""
        surface = Surface(id="custom-surface")
        assert surface.id == "custom-surface"

    def test_surface_event_type_prefix(self):
        """Test event type prefix."""
        surface = Surface()
        assert surface.get_event_type_prefix() == "surface"

    def test_surface_generating_basic(self):
        """Test generating event without parameters."""
        mock_streamer = Mock(spec=Streamer)
        surface = Surface()
        surface._bind_streamer(mock_streamer)

        surface.generating()

        mock_streamer._send.assert_called_once()
        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["id"] == surface.id
        assert args[1]["event_type"] == "surface:generating"

    def test_surface_generating_with_message(self):
        """Test generating event with message."""
        mock_streamer = Mock(spec=Streamer)
        surface = Surface()
        surface._bind_streamer(mock_streamer)

        surface.generating(message="Loading calendar...")

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["message"] == "Loading calendar..."

    def test_surface_generating_with_progress(self):
        """Test generating event with progress."""
        mock_streamer = Mock(spec=Streamer)
        surface = Surface()
        surface._bind_streamer(mock_streamer)

        surface.generating(progress=0.3)

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["progress"] == 0.3

    def test_surface_done_minimal(self):
        """Test done event with minimal parameters (iframe default)."""
        mock_streamer = Mock(spec=Streamer)
        surface = Surface()
        surface._bind_streamer(mock_streamer)

        surface.done(url="https://cal.com/embed")

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["url"] == "https://cal.com/embed"
        assert content["type"] == "iframe"
        assert args[1]["event_type"] == "surface:done"

    def test_surface_done_with_custom_type(self):
        """Test done event with custom type."""
        mock_streamer = Mock(spec=Streamer)
        surface = Surface()
        surface._bind_streamer(mock_streamer)

        surface.done(url="https://example.com/widget", type="widget")

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["type"] == "widget"

    def test_surface_done_all_parameters(self):
        """Test done event with all parameters."""
        mock_streamer = Mock(spec=Streamer)
        surface = Surface()
        surface._bind_streamer(mock_streamer)

        surface.done(
            url="https://calendar.com",
            type="iframe",
            title="My Calendar",
            description="Interactive calendar",
            metadata={"height": 600}
        )

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["url"] == "https://calendar.com"
        assert content["type"] == "iframe"
        assert content["title"] == "My Calendar"
        assert content["description"] == "Interactive calendar"
        assert content["metadata"] == {"height": 600}

    def test_surface_error(self):
        """Test error event."""
        mock_streamer = Mock(spec=Streamer)
        surface = Surface()
        surface._bind_streamer(mock_streamer)

        surface.error(message="Failed to load surface")

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["message"] == "Failed to load surface"
        assert args[1]["event_type"] == "surface:error"

    def test_surface_method_chaining(self):
        """Test method chaining returns self."""
        mock_streamer = Mock(spec=Streamer)
        surface = Surface()
        surface._bind_streamer(mock_streamer)

        result = surface.generating(message="Loading...")
        assert result is surface

        result = surface.done(url="https://example.com")
        assert result is surface


class TestTextBlock:
    """Test TextBlock structural streamer."""

    def test_text_block_id_generation(self):
        """Test that TextBlock generates unique IDs."""
        block1 = TextBlock()
        block2 = TextBlock()
        assert block1.id.startswith("text_block-")
        assert block2.id.startswith("text_block-")
        assert block1.id != block2.id

    def test_text_block_custom_id(self):
        """Test TextBlock with custom ID."""
        block = TextBlock(id="custom-block")
        assert block.id == "custom-block"

    def test_text_block_with_initial_title(self):
        """Test TextBlock with initial title."""
        block = TextBlock(title="Initial Title")
        assert block.initial_title == "Initial Title"

    def test_text_block_event_type_prefix(self):
        """Test event type prefix."""
        block = TextBlock()
        assert block.get_event_type_prefix() == "text_block"

    def test_text_block_stream_title(self):
        """Test stream_title event."""
        mock_streamer = Mock(spec=Streamer)
        block = TextBlock()
        block._bind_streamer(mock_streamer)

        block.stream_title("Deep ")

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["content"] == "Deep "
        assert args[1]["event_type"] == "text_block:stream_title"

    def test_text_block_stream_title_multiple_chunks(self):
        """Test streaming title in multiple chunks."""
        mock_streamer = Mock(spec=Streamer)
        block = TextBlock()
        block._bind_streamer(mock_streamer)

        block.stream_title("Part ")
        block.stream_title("by ")
        block.stream_title("part")

        assert mock_streamer._send.call_count == 3

    def test_text_block_stream_body(self):
        """Test stream_body event."""
        mock_streamer = Mock(spec=Streamer)
        block = TextBlock()
        block._bind_streamer(mock_streamer)

        block.stream_body("Step 1: Analyze\n")

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["content"] == "Step 1: Analyze\n"
        assert args[1]["event_type"] == "text_block:stream_body"

    def test_text_block_stream_body_multiple_chunks(self):
        """Test streaming body in multiple chunks."""
        mock_streamer = Mock(spec=Streamer)
        block = TextBlock()
        block._bind_streamer(mock_streamer)

        block.stream_body("Line 1\n")
        block.stream_body("Line 2\n")

        assert mock_streamer._send.call_count == 2

    def test_text_block_update_title(self):
        """Test update_title event (replaces)."""
        mock_streamer = Mock(spec=Streamer)
        block = TextBlock()
        block._bind_streamer(mock_streamer)

        block.update_title("Final Title")

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["title"] == "Final Title"
        assert args[1]["event_type"] == "text_block:update_title"

    def test_text_block_update_body(self):
        """Test update_body event (replaces)."""
        mock_streamer = Mock(spec=Streamer)
        block = TextBlock()
        block._bind_streamer(mock_streamer)

        block.update_body("Complete body text")

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["body"] == "Complete body text"
        assert args[1]["event_type"] == "text_block:update_body"

    def test_text_block_set_variant(self):
        """Test set_variant event."""
        mock_streamer = Mock(spec=Streamer)
        block = TextBlock()
        block._bind_streamer(mock_streamer)

        block.set_variant("thinking")

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["variant"] == "thinking"
        assert args[1]["event_type"] == "text_block:set_variant"

    def test_text_block_all_variants(self):
        """Test all supported variants."""
        mock_streamer = Mock(spec=Streamer)
        block = TextBlock()
        block._bind_streamer(mock_streamer)

        for variant in ["thinking", "note", "warning", "error", "success"]:
            block.set_variant(variant)
            args = mock_streamer._send.call_args
            content = json.loads(args[1]["content"])
            assert content["variant"] == variant

    def test_text_block_done(self):
        """Test done event."""
        mock_streamer = Mock(spec=Streamer)
        block = TextBlock()
        block._bind_streamer(mock_streamer)

        block.done()

        args = mock_streamer._send.call_args
        assert args[1]["event_type"] == "text_block:done"

    def test_text_block_method_chaining(self):
        """Test method chaining returns self."""
        mock_streamer = Mock(spec=Streamer)
        block = TextBlock()
        block._bind_streamer(mock_streamer)

        result = block.set_variant("thinking")
        assert result is block

        result = block.stream_title("Title")
        assert result is block

        result = block.stream_body("Body")
        assert result is block

        result = block.update_title("New Title")
        assert result is block

        result = block.update_body("New Body")
        assert result is block

        result = block.done()
        assert result is block

    def test_text_block_complete_workflow(self):
        """Test complete workflow: stream then update."""
        mock_streamer = Mock(spec=Streamer)
        block = TextBlock()
        block._bind_streamer(mock_streamer)

        block.set_variant("thinking")
        block.stream_title("Ana")
        block.stream_title("lyzing...")
        block.stream_body("Step 1\n")
        block.stream_body("Step 2\n")
        block.update_title("Analysis Complete")
        block.done()

        assert mock_streamer._send.call_count == 7


class TestStepper:
    """Test Stepper structural streamer."""

    def test_stepper_id_generation(self):
        """Test that Stepper generates unique IDs."""
        stepper1 = Stepper()
        stepper2 = Stepper()
        assert stepper1.id.startswith("stepper-")
        assert stepper2.id.startswith("stepper-")
        assert stepper1.id != stepper2.id

    def test_stepper_custom_id(self):
        """Test Stepper with custom ID."""
        stepper = Stepper(id="custom-stepper")
        assert stepper.id == "custom-stepper"

    def test_stepper_with_initial_steps(self):
        """Test Stepper with initial steps."""
        stepper = Stepper(steps=["Fetch", "Process", "Report"])
        assert stepper.steps == ["Fetch", "Process", "Report"]

    def test_stepper_without_initial_steps(self):
        """Test Stepper without initial steps."""
        stepper = Stepper()
        assert stepper.steps == []

    def test_stepper_event_type_prefix(self):
        """Test event type prefix."""
        stepper = Stepper()
        assert stepper.get_event_type_prefix() == "stepper"

    def test_stepper_initialization_with_steps(self):
        """Test that initialization event is sent on first action with steps."""
        mock_streamer = Mock(spec=Streamer)
        stepper = Stepper(steps=["Step 1", "Step 2"])
        stepper._bind_streamer(mock_streamer)

        stepper.start_step(0)

        # Should have sent init event first, then start_step
        assert mock_streamer._send.call_count == 2

        # First call should be init
        first_call = mock_streamer._send.call_args_list[0]
        content = json.loads(first_call[1]["content"])
        assert first_call[1]["event_type"] == "stepper:init"
        assert content["steps"] == ["Step 1", "Step 2"]

        # Second call should be start_step
        second_call = mock_streamer._send.call_args_list[1]
        assert second_call[1]["event_type"] == "stepper:start_step"

    def test_stepper_initialization_only_once(self):
        """Test that initialization event is sent only once."""
        mock_streamer = Mock(spec=Streamer)
        stepper = Stepper(steps=["Step 1", "Step 2"])
        stepper._bind_streamer(mock_streamer)

        stepper.start_step(0)
        stepper.complete_step(0)
        stepper.start_step(1)

        # init + start + complete + start = 4 calls
        assert mock_streamer._send.call_count == 4

        # Verify init was only called once (first call)
        init_calls = [call for call in mock_streamer._send.call_args_list
                     if call[1]["event_type"] == "stepper:init"]
        assert len(init_calls) == 1

    def test_stepper_no_initialization_without_steps(self):
        """Test that no initialization event is sent when steps list is empty."""
        mock_streamer = Mock(spec=Streamer)
        stepper = Stepper()  # No initial steps
        stepper._bind_streamer(mock_streamer)

        stepper.start_step(0)

        # Should only have start_step, no init
        assert mock_streamer._send.call_count == 1
        args = mock_streamer._send.call_args
        assert args[1]["event_type"] == "stepper:start_step"

    def test_stepper_start_step(self):
        """Test start_step event."""
        mock_streamer = Mock(spec=Streamer)
        stepper = Stepper()
        stepper._bind_streamer(mock_streamer)

        stepper.start_step(0)

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["index"] == 0
        assert args[1]["event_type"] == "stepper:start_step"

    def test_stepper_complete_step(self):
        """Test complete_step event."""
        mock_streamer = Mock(spec=Streamer)
        stepper = Stepper()
        stepper._bind_streamer(mock_streamer)

        stepper.complete_step(1)

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["index"] == 1
        assert args[1]["event_type"] == "stepper:complete_step"

    def test_stepper_fail_step_without_error(self):
        """Test fail_step event without error message."""
        mock_streamer = Mock(spec=Streamer)
        stepper = Stepper()
        stepper._bind_streamer(mock_streamer)

        stepper.fail_step(2)

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["index"] == 2
        assert "error" not in content
        assert args[1]["event_type"] == "stepper:fail_step"

    def test_stepper_fail_step_with_error(self):
        """Test fail_step event with error message."""
        mock_streamer = Mock(spec=Streamer)
        stepper = Stepper()
        stepper._bind_streamer(mock_streamer)

        stepper.fail_step(2, error="Connection timeout")

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["index"] == 2
        assert content["error"] == "Connection timeout"

    def test_stepper_add_step_basic(self):
        """Test add_step event without index."""
        mock_streamer = Mock(spec=Streamer)
        stepper = Stepper()
        stepper._bind_streamer(mock_streamer)

        stepper.add_step("New Step")

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["label"] == "New Step"
        assert "index" not in content
        assert args[1]["event_type"] == "stepper:add_step"

    def test_stepper_add_step_with_index(self):
        """Test add_step event with index."""
        mock_streamer = Mock(spec=Streamer)
        stepper = Stepper()
        stepper._bind_streamer(mock_streamer)

        stepper.add_step("Inserted Step", index=1)

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["label"] == "Inserted Step"
        assert content["index"] == 1

    def test_stepper_update_step_label(self):
        """Test update_step_label event."""
        mock_streamer = Mock(spec=Streamer)
        stepper = Stepper()
        stepper._bind_streamer(mock_streamer)

        stepper.update_step_label(0, "Updated Label")

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["index"] == 0
        assert content["label"] == "Updated Label"
        assert args[1]["event_type"] == "stepper:update_step_label"

    def test_stepper_done(self):
        """Test done event."""
        mock_streamer = Mock(spec=Streamer)
        stepper = Stepper()
        stepper._bind_streamer(mock_streamer)

        stepper.done()

        args = mock_streamer._send.call_args
        assert args[1]["event_type"] == "stepper:done"

    def test_stepper_method_chaining(self):
        """Test method chaining returns self."""
        mock_streamer = Mock(spec=Streamer)
        stepper = Stepper(steps=["Step 1"])
        stepper._bind_streamer(mock_streamer)

        result = stepper.start_step(0)
        assert result is stepper

        result = stepper.complete_step(0)
        assert result is stepper

        result = stepper.fail_step(0)
        assert result is stepper

        result = stepper.add_step("New")
        assert result is stepper

        result = stepper.update_step_label(0, "Updated")
        assert result is stepper

        result = stepper.done()
        assert result is stepper

    def test_stepper_complete_workflow(self):
        """Test complete stepper workflow."""
        mock_streamer = Mock(spec=Streamer)
        stepper = Stepper(steps=["Fetch", "Process", "Report"])
        stepper._bind_streamer(mock_streamer)

        stepper.start_step(0)
        stepper.complete_step(0)
        stepper.start_step(1)
        stepper.add_step("Verify")  # Dynamic step
        stepper.complete_step(1)
        stepper.start_step(2)
        stepper.complete_step(2)
        stepper.done()

        # init + 3*start + 3*complete + 1*add + 1*done = 9 calls
        assert mock_streamer._send.call_count == 9


class TestStructuralStreamerBase:
    """Test base StructuralStreamer functionality."""

    def test_bind_streamer(self):
        """Test binding streamer."""
        mock_streamer = Mock(spec=Streamer)
        artifact = Artifact()

        result = artifact._bind_streamer(mock_streamer)

        assert artifact._streamer is mock_streamer
        assert result is artifact  # Should return self for chaining

    def test_send_event_without_binding_raises_error(self):
        """Test that sending event without binding raises RuntimeError."""
        artifact = Artifact()

        with pytest.raises(RuntimeError, match="not bound to a Streamer"):
            artifact._send_event("test", key="value")

    def test_send_event_builds_correct_payload(self):
        """Test that _send_event builds correct JSON payload."""
        mock_streamer = Mock(spec=Streamer)
        artifact = Artifact()
        artifact._bind_streamer(mock_streamer)

        artifact._send_event("custom_action", key1="value1", key2=123)

        args = mock_streamer._send.call_args
        content = json.loads(args[1]["content"])
        assert content["id"] == artifact.id
        assert content["key1"] == "value1"
        assert content["key2"] == 123

    def test_send_event_uses_correct_event_type(self):
        """Test that _send_event constructs event type correctly."""
        mock_streamer = Mock(spec=Streamer)
        artifact = Artifact()
        artifact._bind_streamer(mock_streamer)

        artifact._send_event("my_action")

        args = mock_streamer._send.call_args
        assert args[1]["event_type"] == "artifact:my_action"

    def test_send_event_sets_persist_false(self):
        """Test that structural events are not persisted."""
        mock_streamer = Mock(spec=Streamer)
        artifact = Artifact()
        artifact._bind_streamer(mock_streamer)

        artifact._send_event("test")

        args = mock_streamer._send.call_args
        assert args[1]["persist"] is False

    def test_send_event_sets_done_false(self):
        """Test that structural events set done=False."""
        mock_streamer = Mock(spec=Streamer)
        artifact = Artifact()
        artifact._bind_streamer(mock_streamer)

        artifact._send_event("test")

        args = mock_streamer._send.call_args
        assert args[1]["done"] is False

    def test_multiple_structural_types_have_unique_prefixes(self):
        """Test that each structural type has unique event prefix."""
        artifact = Artifact()
        surface = Surface()
        text_block = TextBlock()
        stepper = Stepper()

        assert artifact.get_event_type_prefix() == "artifact"
        assert surface.get_event_type_prefix() == "surface"
        assert text_block.get_event_type_prefix() == "text_block"
        assert stepper.get_event_type_prefix() == "stepper"
