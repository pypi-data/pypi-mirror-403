"""Data models for ComfyUI integration."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ComfyUIConfig:
    """Configuration for ComfyUI connection.

    Attributes:
        host: ComfyUI server host (default: 127.0.0.1)
        port: ComfyUI server port (default: 8188)
        output_dir: Directory where ComfyUI saves outputs
        workflow_dir: Directory containing workflow JSON files
        timeout: Default timeout for operations in seconds
    """

    host: str = "127.0.0.1"
    port: int = 8188
    output_dir: str = "/tmp/comfyui_output"
    workflow_dir: str = ""
    timeout: int = 300

    @property
    def base_url(self) -> str:
        """Get the full base URL for ComfyUI API."""
        return f"http://{self.host}:{self.port}"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "host": self.host,
            "port": self.port,
            "output_dir": self.output_dir,
            "workflow_dir": self.workflow_dir,
            "timeout": self.timeout,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ComfyUIConfig":
        """Create from dictionary."""
        return cls(
            host=data.get("host", "127.0.0.1"),
            port=data.get("port", 8188),
            output_dir=data.get("output_dir", "/tmp/comfyui_output"),
            workflow_dir=data.get("workflow_dir", ""),
            timeout=data.get("timeout", 300),
        )


@dataclass
class OutputFile:
    """Represents an output file from ComfyUI.

    Attributes:
        filename: Name of the file
        subfolder: Subfolder within output directory
        file_type: Type of output (output, temp, input)
        format: File format (e.g., png, mp4, webm)
    """

    filename: str
    subfolder: str = ""
    file_type: str = "output"
    format: str = ""

    def __post_init__(self):
        """Determine format from filename if not provided."""
        if not self.format and self.filename:
            suffix = Path(self.filename).suffix.lower()
            self.format = suffix.lstrip(".")


@dataclass
class QueueResponse:
    """Response from queuing a workflow.

    Attributes:
        prompt_id: Unique ID for the queued prompt
        number: Queue position number
    """

    prompt_id: str
    number: int = 0


@dataclass
class ExecutionResult:
    """Result of a workflow execution.

    Attributes:
        prompt_id: The prompt ID that was executed
        success: Whether execution completed successfully
        outputs: List of output files generated
        error: Error message if execution failed
        execution_time: Time taken for execution in seconds
    """

    prompt_id: str
    success: bool = False
    outputs: list[OutputFile] = field(default_factory=list)
    error: str | None = None
    execution_time: float = 0.0

    @property
    def has_images(self) -> bool:
        """Check if result contains image outputs."""
        return any(o.format in ("png", "jpg", "jpeg", "webp") for o in self.outputs)

    @property
    def has_videos(self) -> bool:
        """Check if result contains video outputs."""
        return any(o.format in ("mp4", "webm", "avi", "mov") for o in self.outputs)

    @property
    def first_output(self) -> OutputFile | None:
        """Get the first output file, if any."""
        return self.outputs[0] if self.outputs else None
