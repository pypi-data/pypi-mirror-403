"""ComfyUI API Client.

A clean, testable client for communicating with ComfyUI's REST API.
"""

import json
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import requests

from .models import ComfyUIConfig, ExecutionResult, OutputFile, QueueResponse

logger = logging.getLogger(__name__)


class ComfyUIError(Exception):
    """Base exception for ComfyUI errors."""

    pass


class ConnectionError(ComfyUIError):
    """Failed to connect to ComfyUI."""

    pass


class ExecutionError(ComfyUIError):
    """Workflow execution failed."""

    pass


class ComfyUIClient:
    """Client for ComfyUI API communication.

    This client handles:
    - Connection testing
    - Workflow queuing
    - Status polling
    - Image upload/download
    - Output file retrieval

    Example:
        ```python
        from cgc_common.comfyui import ComfyUIClient, ComfyUIConfig

        config = ComfyUIConfig(host="127.0.0.1", port=8188)
        client = ComfyUIClient(config)

        if client.is_connected():
            result = client.execute(workflow, timeout=300)
            if result.success:
                client.download(result.first_output, "/path/to/save.png")
        ```
    """

    def __init__(self, config: ComfyUIConfig | None = None):
        """Initialize the ComfyUI client.

        Args:
            config: ComfyUI configuration. Uses defaults if not provided.
        """
        self.config = config or ComfyUIConfig()
        self.client_id = str(uuid.uuid4())
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "CGC-ComfyUI-Client/1.0",
        })

    @property
    def base_url(self) -> str:
        """Get the ComfyUI base URL."""
        return self.config.base_url

    # ==================== Connection ====================

    def is_connected(self) -> bool:
        """Check if ComfyUI is reachable.

        Returns:
            True if ComfyUI responds, False otherwise.
        """
        try:
            response = self._session.get(
                f"{self.base_url}/system_stats",
                timeout=5
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

    def get_system_stats(self) -> dict[str, Any]:
        """Get ComfyUI system statistics.

        Returns:
            Dictionary with system info (devices, memory, etc.)

        Raises:
            ConnectionError: If ComfyUI is not reachable.
        """
        try:
            response = self._session.get(
                f"{self.base_url}/system_stats",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to get system stats: {e}") from e

    # ==================== Workflow Execution ====================

    def queue(self, workflow: dict[str, Any]) -> QueueResponse:
        """Queue a workflow for execution.

        Args:
            workflow: The workflow dictionary (ComfyUI API format).

        Returns:
            QueueResponse with prompt_id.

        Raises:
            ConnectionError: If queuing fails.
        """
        # Log workflow to file for debugging
        self._log_workflow(workflow)

        payload = {
            "prompt": workflow,
            "client_id": self.client_id,
        }

        try:
            response = self._session.post(
                f"{self.base_url}/prompt",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            return QueueResponse(
                prompt_id=data["prompt_id"],
                number=data.get("number", 0),
            )
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to queue workflow: {e}") from e

    def _log_workflow(self, workflow: dict[str, Any]) -> None:
        """Log workflow to file for debugging.

        Saves the complete workflow JSON to /tmp/cgc_comfyui_workflow.log
        and extracts key information like prompts and seeds.
        """
        log_file = Path("/tmp/cgc_comfyui_workflow.log")

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Extract key info from workflow
            prompts = []
            seeds = []

            for node_id, node_data in workflow.items():
                if not isinstance(node_data, dict):
                    continue

                title = node_data.get("_meta", {}).get("title", "")
                inputs = node_data.get("inputs", {})

                # Find prompts
                if "Prompt" in title or "prompt" in title.lower():
                    for key in ["value", "text"]:
                        if key in inputs and isinstance(inputs[key], str):
                            prompts.append(f"{title}: {inputs[key][:200]}")

                # Find seeds
                if "seed" in inputs:
                    seeds.append(f"{title}: seed={inputs['seed']}")
                if "noise_seed" in inputs:
                    seeds.append(f"{title}: noise_seed={inputs['noise_seed']}")

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"TIMESTAMP: {timestamp}\n")
                f.write(f"CLIENT_ID: {self.client_id}\n")
                f.write(f"{'='*80}\n")

                if prompts:
                    f.write("\n--- PROMPTS ---\n")
                    for p in prompts:
                        f.write(f"{p}\n")

                if seeds:
                    f.write("\n--- SEEDS ---\n")
                    for s in seeds:
                        f.write(f"{s}\n")

                f.write("\n--- FULL WORKFLOW JSON ---\n")
                f.write(json.dumps(workflow, indent=2, ensure_ascii=False))
                f.write("\n")

            logger.debug(f"Workflow logged to {log_file}")

        except Exception as e:
            logger.warning(f"Failed to log workflow: {e}")

    def get_status(self, prompt_id: str) -> dict[str, Any] | None:
        """Get execution status for a queued prompt.

        Args:
            prompt_id: The prompt ID from queue().

        Returns:
            History dict if execution completed, None if still running.
        """
        try:
            response = self._session.get(
                f"{self.base_url}/history/{prompt_id}",
                timeout=10
            )
            response.raise_for_status()
            history = response.json()
            return history.get(prompt_id)
        except requests.RequestException:
            return None

    def wait_for_completion(
        self,
        prompt_id: str,
        timeout: int | None = None,
        poll_interval: float = 1.0,
        on_progress: Callable[[str], None] | None = None,
    ) -> ExecutionResult:
        """Wait for workflow execution to complete.

        Args:
            prompt_id: The prompt ID to wait for.
            timeout: Maximum wait time in seconds (uses config default if None).
            poll_interval: Time between status checks.
            on_progress: Optional callback for progress updates.

        Returns:
            ExecutionResult with outputs or error.
        """
        timeout = timeout or self.config.timeout
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time

            if elapsed > timeout:
                return ExecutionResult(
                    prompt_id=prompt_id,
                    success=False,
                    error=f"Timeout after {timeout}s",
                    execution_time=elapsed,
                )

            history = self.get_status(prompt_id)

            if history and "outputs" in history:
                # Execution completed
                outputs = self._extract_outputs(history)
                return ExecutionResult(
                    prompt_id=prompt_id,
                    success=True,
                    outputs=outputs,
                    execution_time=elapsed,
                )

            if on_progress:
                on_progress(f"Waiting... ({int(elapsed)}s)")

            time.sleep(poll_interval)

    def execute(
        self,
        workflow: dict[str, Any],
        timeout: int | None = None,
        on_progress: Callable[[str], None] | None = None,
    ) -> ExecutionResult:
        """Execute a workflow and wait for completion.

        This is a convenience method combining queue() and wait_for_completion().

        Args:
            workflow: The workflow dictionary.
            timeout: Maximum execution time in seconds.
            on_progress: Optional progress callback.

        Returns:
            ExecutionResult with outputs or error.
        """
        try:
            queue_response = self.queue(workflow)
            logger.info(f"Queued workflow: {queue_response.prompt_id}")

            return self.wait_for_completion(
                queue_response.prompt_id,
                timeout=timeout,
                on_progress=on_progress,
            )
        except ComfyUIError as e:
            return ExecutionResult(
                prompt_id="",
                success=False,
                error=str(e),
            )

    # ==================== File Operations ====================

    def upload_image(self, image_path: str | Path) -> str:
        """Upload an image to ComfyUI.

        Args:
            image_path: Path to the image file.

        Returns:
            The filename to use in workflows.

        Raises:
            FileNotFoundError: If image doesn't exist.
            ConnectionError: If upload fails.
        """
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Create unique filename with timestamp
        timestamp = datetime.now().strftime("%H%M%S")
        unique_name = f"{image_path.stem}_{timestamp}{image_path.suffix}"

        try:
            with open(image_path, "rb") as f:
                files = {"image": (unique_name, f, "image/png")}
                response = self._session.post(
                    f"{self.base_url}/upload/image",
                    files=files,
                    timeout=60
                )
                response.raise_for_status()
                result = response.json()
                return result.get("name", unique_name)
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to upload image: {e}") from e

    def download(
        self,
        output: OutputFile,
        destination: str | Path,
    ) -> Path:
        """Download an output file from ComfyUI.

        Args:
            output: The OutputFile to download.
            destination: Where to save the file.

        Returns:
            Path to the downloaded file.

        Raises:
            ConnectionError: If download fails.
        """
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)

        params = {
            "filename": output.filename,
            "type": output.file_type,
        }
        if output.subfolder:
            params["subfolder"] = output.subfolder

        try:
            response = self._session.get(
                f"{self.base_url}/view",
                params=params,
                timeout=120
            )
            response.raise_for_status()

            with open(destination, "wb") as f:
                f.write(response.content)

            logger.info(f"Downloaded: {destination}")
            return destination

        except requests.RequestException as e:
            raise ConnectionError(f"Failed to download {output.filename}: {e}") from e

    def download_to_dir(
        self,
        output: OutputFile,
        directory: str | Path,
        filename: str | None = None,
    ) -> Path:
        """Download an output file to a directory.

        Args:
            output: The OutputFile to download.
            directory: Directory to save to.
            filename: Optional custom filename (uses original if None).

        Returns:
            Path to the downloaded file.
        """
        directory = Path(directory)
        filename = filename or output.filename
        return self.download(output, directory / filename)

    # ==================== Workflow Helpers ====================

    @staticmethod
    def load_workflow(workflow_path: str | Path) -> dict[str, Any]:
        """Load a workflow from a JSON file.

        Args:
            workflow_path: Path to the workflow JSON file.

        Returns:
            The workflow dictionary.

        Raises:
            FileNotFoundError: If workflow file doesn't exist.
            json.JSONDecodeError: If file is not valid JSON.
        """
        workflow_path = Path(workflow_path)

        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow not found: {workflow_path}")

        with open(workflow_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def find_node(
        workflow: dict[str, Any],
        title: str,
    ) -> tuple[str, dict[str, Any]] | None:
        """Find a node in the workflow by its title.

        Args:
            workflow: The workflow dictionary.
            title: The node title to search for (case-insensitive).

        Returns:
            Tuple of (node_id, node_data) or None if not found.
        """
        title_lower = title.lower()

        for node_id, node_data in workflow.items():
            # Skip non-dict entries (e.g., "last_node_id", "last_link_id")
            if not isinstance(node_data, dict):
                continue

            # Check _meta.title (API format from UI export)
            if "_meta" in node_data and isinstance(node_data["_meta"], dict):
                if "title" in node_data["_meta"]:
                    if node_data["_meta"]["title"].lower() == title_lower:
                        return (node_id, node_data)

            # Check class_type as fallback (some workflows use this)
            if "class_type" in node_data:
                if node_data["class_type"].lower() == title_lower:
                    return (node_id, node_data)

        return None

    @staticmethod
    def set_node_input(
        workflow: dict[str, Any],
        title: str,
        input_name: str,
        value: Any,
    ) -> bool:
        """Set an input value on a node.

        Args:
            workflow: The workflow dictionary (modified in-place).
            title: The node title to find.
            input_name: Name of the input to set.
            value: The value to set.

        Returns:
            True if node was found and updated, False otherwise.
        """
        result = ComfyUIClient.find_node(workflow, title)
        if result is None:
            return False

        node_id, node_data = result
        if "inputs" in node_data:
            node_data["inputs"][input_name] = value
            return True

        return False

    # ==================== Private Methods ====================

    def _extract_outputs(self, history: dict[str, Any]) -> list[OutputFile]:
        """Extract output files from execution history."""
        outputs = []

        if "outputs" not in history:
            return outputs

        for node_output in history["outputs"].values():
            # Images
            if "images" in node_output:
                for img in node_output["images"]:
                    outputs.append(OutputFile(
                        filename=img.get("filename", ""),
                        subfolder=img.get("subfolder", ""),
                        file_type=img.get("type", "output"),
                    ))

            # Videos
            if "videos" in node_output:
                for vid in node_output["videos"]:
                    outputs.append(OutputFile(
                        filename=vid.get("filename", ""),
                        subfolder=vid.get("subfolder", ""),
                        file_type=vid.get("type", "output"),
                    ))

        return outputs
