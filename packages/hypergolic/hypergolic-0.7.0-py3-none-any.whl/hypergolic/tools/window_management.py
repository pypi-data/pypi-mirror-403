import subprocess
from enum import Enum

from anthropic.types import ToolParam
from anthropic.types.tool_result_block_param import Content
from pydantic import BaseModel, Field
from Quartz import (
    CGWindowListCopyWindowInfo,  # type: ignore
    kCGNullWindowID,  # type: ignore
    kCGWindowListExcludeDesktopElements,  # type: ignore
)

from .enums import ToolName


class WindowOperation(str, Enum):
    LIST = "list"
    GET_INFO = "get_info"
    FOCUS = "focus"


class WindowInfo(BaseModel):
    window_id: int
    app_name: str
    window_title: str
    is_on_screen: bool = False
    bounds: dict | None = None


class WindowManagementToolInput(BaseModel):
    operation: WindowOperation = Field(
        description="The window operation to perform: 'list' to see available windows, 'get_info' for details about a specific window, 'focus' to bring a window/app to front"
    )
    app_name: str | None = Field(
        default=None,
        description="Filter windows by application name (case-insensitive partial match). For 'focus' operation, can be used to activate an app by name.",
    )
    include_all_spaces: bool = Field(
        default=True,
        description="Include windows from all Spaces/virtual desktops, not just the current one (default: True)",
    )
    include_untitled: bool = Field(
        default=False,
        description="Include windows with no title (default: False to reduce noise)",
    )
    title_contains: str | None = Field(
        default=None,
        description="Filter to windows whose title contains this string (case-insensitive)",
    )
    window_id: int | None = Field(
        default=None,
        description="Window ID for 'get_info' or 'focus' operations. For 'focus', if not provided, app_name must be specified to activate that app.",
    )


def escape_applescript_string(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def get_all_windows(
    include_all_spaces: bool = True,
    include_untitled: bool = False,
    app_name_filter: str | None = None,
    title_filter: str | None = None,
) -> list[WindowInfo]:
    if include_all_spaces:
        flags = kCGWindowListExcludeDesktopElements
    else:
        from Quartz import kCGWindowListOptionOnScreenOnly  # type: ignore

        flags = kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements

    windows = CGWindowListCopyWindowInfo(flags, kCGNullWindowID)

    result = []
    for w in windows:
        layer = w.get("kCGWindowLayer", -1)
        if layer != 0:
            continue

        window_id = w.get("kCGWindowNumber")
        if window_id is None:
            continue

        app_name = w.get("kCGWindowOwnerName", "Unknown")
        window_title = w.get("kCGWindowName", "") or ""
        is_on_screen = w.get("kCGWindowIsOnscreen", False)

        if not include_untitled and not window_title:
            continue

        if app_name_filter and app_name_filter.lower() not in app_name.lower():
            continue

        if title_filter and title_filter.lower() not in window_title.lower():
            continue

        bounds_dict = w.get("kCGWindowBounds")
        bounds = None
        if bounds_dict:
            bounds = {
                "x": bounds_dict.get("X", 0),
                "y": bounds_dict.get("Y", 0),
                "width": bounds_dict.get("Width", 0),
                "height": bounds_dict.get("Height", 0),
            }

        result.append(
            WindowInfo(
                window_id=window_id,
                app_name=app_name,
                window_title=window_title or "(untitled)",
                is_on_screen=is_on_screen,
                bounds=bounds,
            )
        )

    return result


def get_window_info(window_id: int) -> WindowInfo | None:
    windows = CGWindowListCopyWindowInfo(
        kCGWindowListExcludeDesktopElements, kCGNullWindowID
    )

    for w in windows:
        if w.get("kCGWindowNumber") == window_id:
            app_name = w.get("kCGWindowOwnerName", "Unknown")
            window_title = w.get("kCGWindowName", "") or "(untitled)"
            is_on_screen = w.get("kCGWindowIsOnscreen", False)

            bounds_dict = w.get("kCGWindowBounds")
            bounds = None
            if bounds_dict:
                bounds = {
                    "x": bounds_dict.get("X", 0),
                    "y": bounds_dict.get("Y", 0),
                    "width": bounds_dict.get("Width", 0),
                    "height": bounds_dict.get("Height", 0),
                }

            return WindowInfo(
                window_id=window_id,
                app_name=app_name,
                window_title=window_title,
                is_on_screen=is_on_screen,
                bounds=bounds,
            )

    return None


def activate_app(app_name: str) -> tuple[bool, str]:
    safe_name = escape_applescript_string(app_name)
    script = f'tell application "{safe_name}" to activate'
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return False, f"AppleScript error: {result.stderr}"
        return True, f"Activated {app_name}"
    except subprocess.TimeoutExpired:
        return False, f"Timed out waiting to activate {app_name}"


def focus_window(
    window_id: int | None = None, app_name: str | None = None
) -> tuple[bool, str]:
    """Focus by window_id (activates owning app) or by app_name directly."""
    if window_id is not None:
        window_info = get_window_info(window_id)
        if window_info is None:
            return False, f"Window with ID {window_id} not found"

        success, message = activate_app(window_info.app_name)
        if not success:
            return False, f"Failed to focus window: {message}"

        return True, f"Focused {window_info.app_name}: {window_info.window_title}"

    elif app_name is not None:
        success, message = activate_app(app_name)
        if not success:
            return False, f"Failed to activate {app_name}: {message}"

        return True, f"Activated {app_name}"

    else:
        return (
            False,
            "Either window_id or app_name must be provided for focus operation",
        )


def window_management(input: WindowManagementToolInput) -> list[Content]:
    match input.operation:
        case WindowOperation.LIST:
            windows = get_all_windows(
                include_all_spaces=input.include_all_spaces,
                include_untitled=input.include_untitled,
                app_name_filter=input.app_name,
                title_filter=input.title_contains,
            )

            if not windows:
                return [
                    {"type": "text", "text": "No windows found matching the criteria."}
                ]

            lines = [f"Found {len(windows)} window(s):"]
            for w in windows:
                space_indicator = "●" if w.is_on_screen else "○"
                lines.append(
                    f"  {space_indicator} [{w.window_id}] {w.app_name}: {w.window_title}"
                )

            lines.append("")
            lines.append("Legend: ● = current Space, ○ = other Space")

            return [{"type": "text", "text": "\n".join(lines)}]

        case WindowOperation.GET_INFO:
            if input.window_id is None:
                return [
                    {
                        "type": "text",
                        "text": "ERROR: window_id is required for get_info operation",
                    }
                ]

            window_info = get_window_info(input.window_id)
            if window_info is None:
                return [
                    {
                        "type": "text",
                        "text": f"ERROR: Window with ID {input.window_id} not found",
                    }
                ]

            lines = [
                f"Window ID: {window_info.window_id}",
                f"Application: {window_info.app_name}",
                f"Title: {window_info.window_title}",
                f"On Screen: {window_info.is_on_screen}",
            ]

            if window_info.bounds:
                b = window_info.bounds
                lines.append(f"Position: ({b['x']}, {b['y']})")
                lines.append(f"Size: {b['width']} x {b['height']}")

            return [{"type": "text", "text": "\n".join(lines)}]

        case WindowOperation.FOCUS:
            success, message = focus_window(
                window_id=input.window_id,
                app_name=input.app_name,
            )

            if success:
                return [{"type": "text", "text": message}]
            else:
                return [{"type": "text", "text": f"ERROR: {message}"}]

        case _:
            return [
                {"type": "text", "text": f"ERROR: Unknown operation: {input.operation}"}
            ]


WindowManagementTool: ToolParam = {
    "name": ToolName.WINDOW_MANAGEMENT,
    "description": "Manage macOS windows. Operations: 'list' to see available windows (across all Spaces by default), 'get_info' for details about a specific window, 'focus' to bring a window or app to the front (works across Spaces and fullscreen).",
    "input_schema": {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["list", "get_info", "focus"],
                "description": "The operation to perform",
            },
            "app_name": {
                "type": "string",
                "description": "Filter by app name (for 'list'), or app to activate (for 'focus' when window_id not provided)",
            },
            "include_all_spaces": {
                "type": "boolean",
                "description": "Include windows from all Spaces, not just current (default: true)",
                "default": True,
            },
            "include_untitled": {
                "type": "boolean",
                "description": "Include windows without titles (default: false)",
                "default": False,
            },
            "title_contains": {
                "type": "string",
                "description": "Filter to windows with titles containing this string (case-insensitive)",
            },
            "window_id": {
                "type": "integer",
                "description": "Window ID for 'get_info' or 'focus' operations",
            },
        },
        "required": ["operation"],
    },
}
