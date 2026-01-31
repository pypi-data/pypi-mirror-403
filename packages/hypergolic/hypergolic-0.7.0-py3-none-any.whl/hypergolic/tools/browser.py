import base64
import logging
import re
from enum import Enum

from anthropic.types import ToolParam
from anthropic.types.tool_result_block_param import Content
from pydantic import BaseModel, Field

from .enums import ToolName

logger = logging.getLogger(__name__)

# Lazy import playwright to make it optional
_playwright = None
_browser = None
_context = None
_page = None


class BrowserOperation(str, Enum):
    LAUNCH = "launch"
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SCREENSHOT = "screenshot"
    GET_CONTENT = "get_content"
    EVALUATE = "evaluate"
    WAIT = "wait"
    CLOSE = "close"


class BrowserToolInput(BaseModel):
    operation: BrowserOperation = Field(description="The browser operation to perform")
    url: str | None = Field(
        default=None,
        description="URL to navigate to (for 'navigate' operation)",
    )
    selector: str | None = Field(
        default=None,
        description="CSS selector for element operations (click, type, get_content, wait)",
    )
    text: str | None = Field(
        default=None,
        description="Text to type (for 'type' operation)",
    )
    script: str | None = Field(
        default=None,
        description="JavaScript to execute (for 'evaluate' operation)",
    )
    headless: bool = Field(
        default=False,
        description="Run browser in headless mode (for 'launch' operation). Default is visible.",
    )
    timeout: int = Field(
        default=30000,
        description="Timeout in milliseconds for operations (default: 30000)",
    )
    full_page: bool = Field(
        default=False,
        description="Capture full page screenshot (for 'screenshot' operation)",
    )


LOCALHOST_PATTERNS = [
    r"^https?://localhost(:\d+)?(/.*)?$",
    r"^https?://127\.0\.0\.1(:\d+)?(/.*)?$",
    r"^https?://\[::1\](:\d+)?(/.*)?$",
    r"^https?://0\.0\.0\.0(:\d+)?(/.*)?$",
]


def is_localhost_url(url: str | None) -> bool:
    """Check if a URL points to localhost."""
    if not url:
        return False
    return any(re.match(pattern, url, re.IGNORECASE) for pattern in LOCALHOST_PATTERNS)


def get_current_page_url() -> str | None:
    """Get the URL of the current page, if any."""
    global _page
    if _page is None:
        return None
    try:
        return _page.url
    except Exception as e:
        logger.debug("Could not get current page URL: %s", e)
        return None


async def _get_playwright():
    """Lazily import and return playwright."""
    global _playwright
    if _playwright is None:
        try:
            from playwright.async_api import async_playwright

            _playwright = await async_playwright().start()
        except ImportError:
            raise RuntimeError(
                "Playwright is not installed. Install it with:\n"
                "  pip install playwright\n"
                "  playwright install chromium"
            ) from None
    return _playwright


async def _launch_browser(headless: bool = False) -> str:
    """Launch browser and return status message."""
    global _browser, _context, _page

    if _browser is not None:
        return "Browser already running. Use 'close' first to restart."

    pw = await _get_playwright()
    _browser = await pw.chromium.launch(headless=headless)
    _context = await _browser.new_context(
        viewport={"width": 1280, "height": 720},
    )
    _page = await _context.new_page()

    mode = "headless" if headless else "visible"
    return f"Browser launched in {mode} mode."


async def _navigate(url: str, timeout: int) -> str:
    """Navigate to URL and return status."""
    global _page

    if _page is None:
        return "ERROR: Browser not launched. Use 'launch' operation first."

    try:
        await _page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        title = await _page.title()
        return f"Navigated to: {url}\nPage title: {title}"
    except Exception as e:
        return f"ERROR: Navigation failed: {str(e)}"


async def _click(selector: str, timeout: int) -> str:
    """Click an element and return status."""
    global _page

    if _page is None:
        return "ERROR: Browser not launched. Use 'launch' operation first."

    try:
        await _page.click(selector, timeout=timeout)
        return f"Clicked element: {selector}"
    except Exception as e:
        return f"ERROR: Click failed: {str(e)}"


async def _type_text(selector: str, text: str, timeout: int) -> str:
    """Type text into an element."""
    global _page

    if _page is None:
        return "ERROR: Browser not launched. Use 'launch' operation first."

    try:
        await _page.fill(selector, text, timeout=timeout)
        return f"Typed text into: {selector}"
    except Exception as e:
        return f"ERROR: Type failed: {str(e)}"


async def _screenshot(
    selector: str | None, full_page: bool, timeout: int
) -> Content | str:
    """Take a screenshot and return as base64 image."""
    global _page

    if _page is None:
        return "ERROR: Browser not launched. Use 'launch' operation first."

    try:
        if selector:
            element = await _page.wait_for_selector(selector, timeout=timeout)
            if element is None:
                return f"ERROR: Element not found: {selector}"
            screenshot_bytes = await element.screenshot()
        else:
            screenshot_bytes = await _page.screenshot(full_page=full_page)

        image_base64 = base64.standard_b64encode(screenshot_bytes).decode("utf-8")
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": image_base64,
            },
        }
    except Exception as e:
        return f"ERROR: Screenshot failed: {str(e)}"


async def _get_content(selector: str | None, timeout: int) -> str:
    """Get text content from page or element."""
    global _page

    if _page is None:
        return "ERROR: Browser not launched. Use 'launch' operation first."

    try:
        if selector:
            element = await _page.wait_for_selector(selector, timeout=timeout)
            if element is None:
                return f"ERROR: Element not found: {selector}"
            content = await element.text_content()
            return content or "(empty)"
        else:
            # Get full page text content
            content = await _page.evaluate("() => document.body.innerText")
            # Truncate if too long
            if len(content) > 50000:
                content = content[:50000] + "\n\n... (truncated)"
            return content
    except Exception as e:
        return f"ERROR: Get content failed: {str(e)}"


async def _evaluate(script: str, timeout: int) -> str:
    """Execute JavaScript and return result."""
    global _page

    if _page is None:
        return "ERROR: Browser not launched. Use 'launch' operation first."

    try:
        result = await _page.evaluate(script)
        if result is None:
            return "(no return value)"
        return str(result)
    except Exception as e:
        return f"ERROR: Script execution failed: {str(e)}"


async def _wait(selector: str, timeout: int) -> str:
    """Wait for an element to appear."""
    global _page

    if _page is None:
        return "ERROR: Browser not launched. Use 'launch' operation first."

    try:
        await _page.wait_for_selector(selector, timeout=timeout)
        return f"Element found: {selector}"
    except Exception as e:
        return f"ERROR: Wait failed: {str(e)}"


async def _close_browser() -> str:
    """Close the browser."""
    global _playwright, _browser, _context, _page

    if _browser is None:
        return "Browser is not running."

    try:
        await _browser.close()
    except Exception:
        pass

    _browser = None
    _context = None
    _page = None

    # Don't close playwright itself - it can be reused
    return "Browser closed."


async def browser_control(input: BrowserToolInput) -> list[Content]:
    """Execute browser operation and return result."""

    match input.operation:
        case BrowserOperation.LAUNCH:
            result = await _launch_browser(headless=input.headless)
            return [{"type": "text", "text": result}]

        case BrowserOperation.NAVIGATE:
            if not input.url:
                return [
                    {
                        "type": "text",
                        "text": "ERROR: 'url' is required for navigate operation",
                    }
                ]
            result = await _navigate(input.url, input.timeout)
            return [{"type": "text", "text": result}]

        case BrowserOperation.CLICK:
            if not input.selector:
                return [
                    {
                        "type": "text",
                        "text": "ERROR: 'selector' is required for click operation",
                    }
                ]
            result = await _click(input.selector, input.timeout)
            return [{"type": "text", "text": result}]

        case BrowserOperation.TYPE:
            if not input.selector:
                return [
                    {
                        "type": "text",
                        "text": "ERROR: 'selector' is required for type operation",
                    }
                ]
            if not input.text:
                return [
                    {
                        "type": "text",
                        "text": "ERROR: 'text' is required for type operation",
                    }
                ]
            result = await _type_text(input.selector, input.text, input.timeout)
            return [{"type": "text", "text": result}]

        case BrowserOperation.SCREENSHOT:
            result = await _screenshot(input.selector, input.full_page, input.timeout)
            if isinstance(result, str):
                return [{"type": "text", "text": result}]
            return [result]

        case BrowserOperation.GET_CONTENT:
            result = await _get_content(input.selector, input.timeout)
            return [{"type": "text", "text": result}]

        case BrowserOperation.EVALUATE:
            if not input.script:
                return [
                    {
                        "type": "text",
                        "text": "ERROR: 'script' is required for evaluate operation",
                    }
                ]
            result = await _evaluate(input.script, input.timeout)
            return [{"type": "text", "text": result}]

        case BrowserOperation.WAIT:
            if not input.selector:
                return [
                    {
                        "type": "text",
                        "text": "ERROR: 'selector' is required for wait operation",
                    }
                ]
            result = await _wait(input.selector, input.timeout)
            return [{"type": "text", "text": result}]

        case BrowserOperation.CLOSE:
            result = await _close_browser()
            return [{"type": "text", "text": result}]

        case _:
            return [
                {"type": "text", "text": f"ERROR: Unknown operation: {input.operation}"}
            ]


BrowserTool: ToolParam = {
    "name": ToolName.BROWSER,
    "description": "Control a web browser for testing, scraping, and automation. Operations: 'launch' (start browser), 'navigate' (go to URL), 'click' (click element), 'type' (enter text), 'screenshot' (capture page/element), 'get_content' (extract text), 'evaluate' (run JavaScript), 'wait' (wait for element), 'close' (close browser). Auto-approved for localhost URLs; requires approval for external sites.",
    "input_schema": {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": [
                    "launch",
                    "navigate",
                    "click",
                    "type",
                    "screenshot",
                    "get_content",
                    "evaluate",
                    "wait",
                    "close",
                ],
                "description": "The browser operation to perform",
            },
            "url": {
                "type": "string",
                "description": "URL to navigate to (for 'navigate' operation)",
            },
            "selector": {
                "type": "string",
                "description": "CSS selector for element operations (click, type, get_content, screenshot, wait)",
            },
            "text": {
                "type": "string",
                "description": "Text to type (for 'type' operation)",
            },
            "script": {
                "type": "string",
                "description": "JavaScript to execute (for 'evaluate' operation)",
            },
            "headless": {
                "type": "boolean",
                "description": "Run browser in headless mode (for 'launch'). Default is visible (false).",
                "default": False,
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in milliseconds (default: 30000)",
                "default": 30000,
            },
            "full_page": {
                "type": "boolean",
                "description": "Capture full page screenshot (for 'screenshot')",
                "default": False,
            },
        },
        "required": ["operation"],
    },
}
