import base64
import os
import subprocess
import tempfile
from enum import Enum

from anthropic.types import ToolParam
from anthropic.types.tool_result_block_param import Content
from pydantic import BaseModel, Field
from Quartz import (
    CGWindowListCopyWindowInfo,  # type: ignore
    kCGNullWindowID,  # type: ignore
    kCGWindowListExcludeDesktopElements,  # type: ignore
    kCGWindowListOptionOnScreenOnly,  # type: ignore
)

from .enums import ToolName


class ScreenshotTarget(str, Enum):
    FULLSCREEN = "fullscreen"
    WINDOW = "window"


class ScreenshotToolInput(BaseModel):
    target: ScreenshotTarget = Field(
        default=ScreenshotTarget.FULLSCREEN,
        description="What to capture: 'fullscreen' for entire screen, 'window' for a specific window",
    )
    window_id: int | None = Field(
        default=None,
        description="Window ID to capture (use with 'window' target). If not provided, captures the frontmost application window. Use window_management tool with operation='list' to see available window IDs.",
    )
    high_resolution: bool = Field(
        default=False,
        description="If true, captures at full native resolution. Default (false) optimizes for API efficiency by resizing to max 1568px. Use high_resolution=true only if a previous screenshot lacked sufficient detail.",
    )


# ~3MB raw -> ~4MB base64 (safe margin under 5MB API limit)
MAX_IMAGE_SIZE = int(4 * 1024 * 1024 / 1.34)

# Anthropic resizes to 1568px max anyway, so sending larger is wasteful
OPTIMAL_MAX_DIMENSION = 1568


def get_frontmost_window_id() -> int | None:
    windows = CGWindowListCopyWindowInfo(
        kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements,
        kCGNullWindowID,
    )

    for w in windows:
        layer = w.get("kCGWindowLayer", -1)
        if layer == 0:
            return w.get("kCGWindowNumber")

    return None


def get_image_dimensions(image_path: str) -> tuple[int, int]:
    result = subprocess.run(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", image_path],
        capture_output=True,
        text=True,
    )

    width = height = 0
    for line in result.stdout.strip().split("\n"):
        if "pixelWidth" in line:
            width = int(line.split(":")[1].strip())
        elif "pixelHeight" in line:
            height = int(line.split(":")[1].strip())

    return width, height


def resize_image_to_max_dimension(image_path: str, max_dim: int) -> bool:
    width, height = get_image_dimensions(image_path)

    if width == 0 or height == 0:
        return False

    if width <= max_dim and height <= max_dim:
        return False

    if width > height:
        new_width = max_dim
        new_height = int(height * max_dim / width)
    else:
        new_height = max_dim
        new_width = int(width * max_dim / height)

    subprocess.run(
        ["sips", "-z", str(new_height), str(new_width), image_path], capture_output=True
    )

    return True


def compress_image_if_needed(
    image_path: str, max_size: int = MAX_IMAGE_SIZE
) -> tuple[bytes, bool]:
    with open(image_path, "rb") as f:
        image_data = f.read()

    if len(image_data) <= max_size:
        return image_data, False

    current_size = len(image_data)
    scale_factor = 0.9

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        with open(tmp_path, "wb") as f:
            f.write(image_data)

        attempts = 0
        max_attempts = 10

        while current_size > max_size and attempts < max_attempts:
            width, height = get_image_dimensions(tmp_path)

            if width == 0 or height == 0:
                break

            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)

            subprocess.run(
                ["sips", "-z", str(new_height), str(new_width), tmp_path],
                capture_output=True,
            )

            with open(tmp_path, "rb") as f:
                image_data = f.read()
            current_size = len(image_data)

            attempts += 1
            scale_factor = 0.8

        return image_data, True

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def take_screenshot(input: ScreenshotToolInput) -> list[Content]:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        cmd = ["screencapture", "-x"]

        if input.target == ScreenshotTarget.WINDOW:
            window_id = input.window_id

            if window_id is None:
                window_id = get_frontmost_window_id()
                if window_id is None:
                    return [
                        {
                            "type": "text",
                            "text": "ERROR: Could not find any windows to capture. Try using the window_management tool with operation='list' to see available windows.",
                        }
                    ]

            cmd.extend(["-l", str(window_id)])

        cmd.append(tmp_path)

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            return [
                {
                    "type": "text",
                    "text": f"ERROR: screencapture failed: {result.stderr}",
                }
            ]

        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
            return [
                {
                    "type": "text",
                    "text": "ERROR: Screenshot file was not created or is empty. The window may have been closed.",
                }
            ]

        if not input.high_resolution:
            resize_image_to_max_dimension(tmp_path, OPTIMAL_MAX_DIMENSION)

        image_data, was_compressed = compress_image_if_needed(tmp_path)

        image_base64 = base64.standard_b64encode(image_data).decode("utf-8")

        return [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_base64,
                },
            }
        ]

    except subprocess.TimeoutExpired:
        return [
            {
                "type": "text",
                "text": "ERROR: Screenshot operation timed out",
            }
        ]
    except Exception as e:
        return [{"type": "text", "text": f"Screenshot failed: {str(e)}"}]
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


ScreenshotTool: ToolParam = {
    "name": ToolName.SCREENSHOT,
    "description": "Take a screenshot on macOS. Can capture the entire screen ('fullscreen') or a specific window ('window'). Use the window_management tool to list available windows and get their IDs. Returns base64 encoded PNG (max 5MB, auto-compressed if larger).",
    "input_schema": {
        "type": "object",
        "properties": {
            "target": {
                "type": "string",
                "enum": ["fullscreen", "window"],
                "description": "What to capture: 'fullscreen' for entire screen, 'window' for a specific window",
                "default": "fullscreen",
            },
            "window_id": {
                "type": "integer",
                "description": "Window ID to capture (only for 'window' target). If omitted, captures the frontmost window. Use window_management tool to list available windows.",
            },
            "high_resolution": {
                "type": "boolean",
                "description": "If true, captures at full native resolution. Default (false) resizes to max 1568px for API efficiency. Only use if prior screenshot lacked detail.",
                "default": False,
            },
        },
    },
}
