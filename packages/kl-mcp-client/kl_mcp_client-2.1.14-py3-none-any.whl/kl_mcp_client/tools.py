import logging
from functools import wraps
from typing import Any, Dict, Optional

from .client import MCPClient

# ======================================================
# LOGGER
# ======================================================

logger = logging.getLogger(__name__)

# ======================================================
# DECORATOR
# ======================================================


def _ensure_client(func):
    """Decorator kiểm tra self.client != None trước khi gọi tool."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.client is None:
            logger.error("MCP client not connected")
            return {
                "ok": False,
                "error": "MCP client not connected. Call connect mcp server first.",
            }
        return func(self, *args, **kwargs)

    return wrapper


# ======================================================
# CLASS
# ======================================================

class MCPTools:
    """
    Wrapper chuẩn cho Google ADK + MCP Server.
    """

    # ======================================================
    # INIT / CONNECT
    # ======================================================

    def __init__(self):
        self.client = None
        logger.info("MCPTools initialized")

    def connect_mcp(self, mcpUrl: str) -> Dict[str, Any]:
        logger.info("connect_mcp | %s", mcpUrl)

        self.client = MCPClient(
            base_url=mcpUrl,
            headers=None,
            timeout=30,
            retries=2
        )
        return {"ok": True, "cdpUrl": "http://localhost:9222"}

    # ======================================================
    # SESSION MANAGEMENT
    # ======================================================

    @_ensure_client
    def create_session(self, cdpUrl: str):
        logger.info("create_session | %s", cdpUrl)
        sid = self.client.create_session(cdpUrl)
        return {"sessionId": sid}

    @_ensure_client
    def close_session(self, sessionId: str):
        logger.info("close_session | %s", sessionId)
        ok = self.client.close_session(sessionId)
        return {"ok": bool(ok)}

    @_ensure_client
    def list_sessions(self):
        logger.debug("list_sessions")
        return {"sessions": self.client.list_local_sessions()}

    # ======================================================
    # TAB MANAGEMENT
    # ======================================================

    @_ensure_client
    def new_tab(self, sessionId: str, url: Optional[str] = "about:blank"):
        logger.info("new_tab | %s", url)
        return self.client.call_tool(
            "newTab", {"sessionId": sessionId, "url": url}
        ).get("structuredContent", {})

    @_ensure_client
    def switch_tab(self, sessionId: str, targetId: str):
        logger.info("switch_tab | %s", targetId)
        return self.client.call_tool(
            "switchTab", {"sessionId": sessionId, "targetId": targetId}
        ).get("structuredContent", {})

    @_ensure_client
    def close_tab(self, sessionId: str, tabId: str):
        logger.info("close_tab | %s", tabId)
        return self.client.call_tool(
            "closeTab", {"sessionId": sessionId, "tabId": tabId}
        ).get("structuredContent", {})

    @_ensure_client
    def current_tab(self, sessionId: str):
        logger.debug("current_tab")
        return self.client.call_tool(
            "currentTab", {"sessionId": sessionId}
        ).get("structuredContent", {})

    # ======================================================
    # NAVIGATION / DOM
    # ======================================================

    @_ensure_client
    def open_page(self, sessionId: str, url: str):
        logger.info("open_page | %s", url)
        return self.client.call_tool(
            "openPage", {"sessionId": sessionId, "url": url}
        ).get("structuredContent", {})

    @_ensure_client
    def get_html(self, sessionId: str):
        logger.debug("get_html")
        return self.client.call_tool(
            "getHTML", {"sessionId": sessionId}
        ).get("structuredContent", {})

    @_ensure_client
    def evaluate(self, sessionId: str, expression: str):
        logger.debug("evaluate")
        return self.client.call_tool(
            "evaluate", {"sessionId": sessionId, "expression": expression}
        ).get("structuredContent", {})

    @_ensure_client
    def screenshot(self, sessionId: str):
        logger.info("screenshot")
        full = self.client.call_tool(
            "screenshot", {"sessionId": sessionId}
        )
        return full["content"][0]

    @_ensure_client
    def wait_for_selector(
        self, sessionId: str, selector: str, timeoutMs: Optional[int] = None
    ):
        logger.debug("wait_for_selector | %s", selector)
        args = {"sessionId": sessionId, "selector": selector}
        if timeoutMs is not None:
            args["timeout"] = int(timeoutMs)

        return self.client.call_tool(
            "waitForSelector", args
        ).get("structuredContent", {})

    # ======================================================
    # ELEMENT UTILITIES
    # ======================================================

    @_ensure_client
    def find_element(self, sessionId: str, selector: str):
        logger.debug("find_element | %s", selector)
        return self.client.call_tool(
            "findElement", {"sessionId": sessionId, "selector": selector}
        ).get("structuredContent", {})

    @_ensure_client
    def find_all(self, sessionId: str, selector: str):
        logger.debug("find_all | %s", selector)
        return self.client.call_tool(
            "findAll", {"sessionId": sessionId, "selector": selector}
        ).get("structuredContent", {})

    @_ensure_client
    def get_bounding_box(self, sessionId: str, selector: str):
        logger.debug("get_bounding_box | %s", selector)
        return self.client.call_tool(
            "getBoundingBox", {"sessionId": sessionId, "selector": selector}
        ).get("structuredContent", {})

    @_ensure_client
    def click_bounding_box(self, sessionId: str, selector: str):
        logger.debug("click_bounding_box | %s", selector)
        return self.client.call_tool(
            "clickBoundingBox", {"sessionId": sessionId, "selector": selector}
        ).get("structuredContent", {})

    # ======================================================
    # BASIC ACTIONS
    # ======================================================

    @_ensure_client
    def click(self, sessionId: str, selector: str):
        logger.debug("click | %s", selector)
        return self.client.call_tool(
            "click", {"sessionId": sessionId, "selector": selector}
        ).get("structuredContent", {})

    @_ensure_client
    def type(self, sessionId: str, selector: str, text: str):
        logger.debug("type | %s", selector)
        return self.client.call_tool(
            "type", {"sessionId": sessionId,
                     "selector": selector, "text": text}
        ).get("structuredContent", {})

    # ======================================================
    # ADVANCED FIND / CLICK
    # ======================================================

    @_ensure_client
    def click_to_text(self, sessionId: str, text: str):
        logger.debug("click_to_text | %s", text)
        return self.client.call_tool(
            "clickToText", {"sessionId": sessionId, "text": text}
        ).get("structuredContent", {})

    @_ensure_client
    def find_element_xpath(self, sessionId: str, xpath: str):
        logger.debug("find_element_xpath")
        return self.client.call_tool(
            "findElementByXPath", {"sessionId": sessionId, "xpath": xpath}
        ).get("structuredContent", {})

    @_ensure_client
    def find_element_by_text(self, sessionId: str, text: str):
        logger.debug("find_element_by_text | %s", text)
        return self.client.call_tool(
            "findElementByText", {"sessionId": sessionId, "text": text}
        ).get("structuredContent", {})

    @_ensure_client
    def click_by_node_id(self, sessionId: str, nodeId: int):
        logger.debug("click_by_node_id | %s", nodeId)
        return self.client.call_tool(
            "clickByNodeId", {"sessionId": sessionId, "nodeId": nodeId}
        ).get("structuredContent", {})

    @_ensure_client
    def find_element_by_prompt(self, sessionId: str, prompt: str):
        logger.info("find_element_by_prompt")
        return self.client.call_tool(
            "findElementByPrompt", {"sessionId": sessionId, "prompt": prompt}
        ).get("structuredContent", {})

    # ======================================================
    # FILE / COOKIE
    # ======================================================

    @_ensure_client
    def upload_file(self, sessionId: str, selector: str, file_path: str):
        logger.info("upload_file | %s", file_path)

        if not file_path:
            return {"ok": False, "error": "file_path is required"}

        try:
            with open(file_path, "rb") as f:
                resp = self.client.http.post(
                    "/upload",
                    files={"file": f},
                    timeout=300,
                )
        except Exception as e:
            logger.exception("upload http failed")
            return {"ok": False, "error": f"upload http failed: {e}"}

        if resp.status_code != 200:
            return {
                "ok": False,
                "error": f"http {resp.status_code}: {resp.text}",
            }

        upload_id = resp.json().get("uploadId")
        if not upload_id:
            return {"ok": False, "error": "uploadId not returned"}

        return self.client.call_tool(
            "uploadFile",
            {
                "sessionId": sessionId,
                "selector": selector,
                "uploadId": upload_id,
            },
        ).get("structuredContent", {})

    @_ensure_client
    def import_cookies(self, sessionId: str, cookies: dict):
        logger.info("import_cookies")
        return self.client.call_tool(
            "importCookies", {"sessionId": sessionId, "cookies": cookies}
        ).get("structuredContent", {})

    # ======================================================
    # AI / PARSING
    # ======================================================

    @_ensure_client
    def parse_html_by_prompt(self, html: str, prompt: str):
        logger.info("parse_html_by_prompt")
        return self.client.call_tool(
            "parseHTMLByPrompt",
            {"html": html, "prompt": prompt}
        ).get("structuredContent", {})

    # ======================================================
    # CLEAN TEXT
    # ======================================================

    @_ensure_client
    def get_clean_text(self, sessionId: str):
        logger.debug("get_clean_text")
        return self.client.call_tool(
            "getCleanText",
            {"sessionId": sessionId}
        ).get("structuredContent", {})

    # ======================================================
    # STREAM
    # ======================================================

    @_ensure_client
    def evaluate_stream(self, sessionId: str, expression: str, chunkSize: int = 100):
        logger.debug("evaluate_stream")
        return self.client.call_tool(
            "evaluate.stream",
            {
                "sessionId": sessionId,
                "expression": expression,
                "chunkSize": chunkSize,
            },
        ).get("structuredContent", {})

    @_ensure_client
    def stream_pull(self, stream_id: str, offset: int = 0, limit: int = 100):
        logger.debug("stream_pull")
        return self.client.call_tool(
            "stream.pull",
            {
                "stream_id": stream_id,
                "offset": offset,
                "limit": limit,
            },
        ).get("structuredContent", {})

    @_ensure_client
    def evaluate_stream_all(
        self,
        sessionId: str,
        expression: str,
        chunkSize: int = 100,
        max_items: Optional[int] = None,
    ):
        logger.info("evaluate_stream_all")

        init = self.evaluate_stream(sessionId, expression, chunkSize)
        stream_id = init.get("stream_id")

        if not stream_id:
            return []

        items = []
        offset = 0

        while True:
            chunk = self.stream_pull(stream_id, offset, chunkSize)
            items.extend(chunk.get("items", []))

            if max_items and len(items) >= max_items:
                return items[:max_items]

            if not chunk.get("has_more"):
                break

            offset += chunkSize

        return items

    # ======================================================
    # KEYBOARD
    # ======================================================

    @_ensure_client
    def send_keys(self, sessionId: str, key: str, interval: int = 100):
        logger.debug("send_keys | %s", key)
        return self.client.call_tool(
            "sendKeys",
            {"sessionId": sessionId, "text": key, "interval": interval}
        ).get("structuredContent", {})

    # ======================================================
    # PERFORM / MOUSE
    # ======================================================

    @_ensure_client
    def perform(
        self,
        sessionId: str,
        action: str,
        target: Optional[str] = None,
        value: Optional[str] = None,
        x: Optional[float] = None,
        y: Optional[float] = None,
        from_point: Optional[dict] = None,
        to_point: Optional[dict] = None,
    ):
        logger.debug("perform | %s", action)

        args = {"sessionId": sessionId, "action": action}

        if target is not None:
            args["target"] = target
        if value is not None:
            args["value"] = value
        if x is not None:
            args["x"] = float(x)
        if y is not None:
            args["y"] = float(y)
        if from_point is not None:
            args["from"] = from_point
        if to_point is not None:
            args["to"] = to_point

        return self.client.call_tool(
            "perform", args
        ).get("structuredContent", {})

    @_ensure_client
    def drag_and_drop(
        self,
        sessionId: str,
        from_x: float,
        from_y: float,
        to_x: float,
        to_y: float,
    ):
        logger.debug("drag_and_drop")
        return self.perform(
            sessionId=sessionId,
            action="drag",
            from_point={"x": from_x, "y": from_y},
            to_point={"x": to_x, "y": to_y},
        )

    @_ensure_client
    def hover(self, sessionId: str, x: float, y: float):
        logger.debug("hover")
        return self.perform(
            sessionId=sessionId,
            action="hover",
            x=x,
            y=y,
        )

    @_ensure_client
    def scroll(
        self,
        sessionId: str,
        *,
        x: Optional[float] = None,
        y: Optional[float] = None,
        selector: Optional[str] = None,
        position: Optional[str] = None,
    ):
        logger.debug("scroll")

        args = {"sessionId": sessionId}

        if x is not None:
            args["x"] = float(x)
        if y is not None:
            args["y"] = float(y)
        if selector is not None:
            args["selector"] = selector
        if position is not None:
            args["position"] = position

        if len(args) == 1:
            return {"ok": False, "error": "scroll requires x/y or selector or position"}

        return self.client.call_tool(
            "scroll", args
        ).get("structuredContent", {})

    # ======================================================
    # BROWSER RUNTIME (NO SESSION)
    # ======================================================

    @_ensure_client
    def create_browser(self, payload: Optional[Dict[str, Any]] = None):
        logger.info("create_browser")
        return self.client.call_tool(
            "createBrowser", payload or {}
        ).get("structuredContent", {})

    @_ensure_client
    def release_browser(self, pop_name: str):
        logger.info("release_browser | %s", pop_name)
        return self.client.call_tool(
            "releaseBrowser", {"pod_name": pop_name}
        ).get("structuredContent", {})

    # ======================================================
    # VIEWPORT
    # ======================================================

    @_ensure_client
    def get_viewport(self, sessionId: str):
        logger.debug("get_viewport")
        return self.client.call_tool(
            "viewport", {"sessionId": sessionId}
        ).get("structuredContent", {})

    @_ensure_client
    def current_url(self, sessionId: str):
        logger.debug("current_url")
        return self.client.call_tool(
            "getCurrentUrl", {"sessionId": sessionId}
        ).get("structuredContent", {}).get("url")

    @_ensure_client
    def set_viewport(
        self,
        sessionId: str,
        *,
        width: int,
        height: int,
        deviceScaleFactor: float = 1.0,
        mobile: bool = False,
    ):
        logger.info("set_viewport | %sx%s", width, height)
        return self.client.call_tool(
            "viewport",
            {
                "sessionId": sessionId,
                "viewport": {
                    "width": int(width),
                    "height": int(height),
                    "deviceScaleFactor": float(deviceScaleFactor),
                    "mobile": bool(mobile),
                },
            },
        ).get("structuredContent", {})
