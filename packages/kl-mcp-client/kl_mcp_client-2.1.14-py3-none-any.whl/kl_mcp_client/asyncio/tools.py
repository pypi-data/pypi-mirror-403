# async_tools.py
import logging
from typing import Any, Dict, Optional

from .client import MCPClient

# ======================================================
# LOGGER
# ======================================================

logger = logging.getLogger(__name__)

# ======================================================
# CLASS
# ======================================================


class MCPTools:
    """
    Async wrapper cho Google ADK + MCP Server
    """

    # ======================================================
    # INIT
    # ======================================================

    def __init__(self, client: MCPClient):
        self.client = client
        logger.info("MCPTools initialized")

    # ======================================================
    # BROWSER RUNTIME (NO SESSION)
    # ======================================================

    async def create_browser(self, payload: Optional[Dict[str, Any]] = None):
        logger.info("create_browser")
        res = await self.client.call_tool("createBrowser", payload or {})
        return res.get("structuredContent", {})

    async def release_browser(self, pop_name: str):
        logger.info("release_browser | %s", pop_name)
        res = await self.client.call_tool(
            "releaseBrowser", {"pod_name": pop_name}
        )
        return res.get("structuredContent", {})

    # ======================================================
    # SESSION MANAGEMENT
    # ======================================================

    async def create_session(self, cdpUrl: str) -> Dict[str, Any]:
        logger.info("create_session | %s", cdpUrl)
        sid = await self.client.create_session(cdpUrl)
        return {"sessionId": sid}

    async def close_session(self, sessionId: str) -> Dict[str, Any]:
        logger.info("close_session | %s", sessionId)
        ok = await self.client.close_session(sessionId)
        return {"ok": bool(ok)}

    async def list_sessions(self) -> Dict[str, Any]:
        logger.debug("list_sessions")
        return {"sessions": self.client.list_local_sessions()}

    # ======================================================
    # TAB MANAGEMENT
    # ======================================================

    async def new_tab(self, sessionId: str, url: str = "about:blank"):
        logger.info("new_tab | %s", url)
        res = await self.client.call_tool(
            "newTab", {"sessionId": sessionId, "url": url}
        )
        return res.get("structuredContent", {})

    async def close_tab(self, sessionId: str, tabId: str):
        logger.info("close_tab | %s", tabId)
        res = await self.client.call_tool(
            "closeTab", {"sessionId": sessionId, "tabId": tabId}
        )
        return res.get("structuredContent", {})

    async def switch_tab(self, sessionId: str, targetId: str):
        logger.info("switch_tab | %s", targetId)
        res = await self.client.call_tool(
            "switchTab", {"sessionId": sessionId, "targetId": targetId}
        )
        return res.get("structuredContent", {})

    async def current_tab(self, sessionId: str):
        logger.debug("current_tab")
        res = await self.client.call_tool(
            "currentTab", {"sessionId": sessionId}
        )
        return res.get("structuredContent", {})

    # ======================================================
    # NAVIGATION & DOM
    # ======================================================

    async def open_page(self, sessionId: str, url: str):
        logger.info("open_page | %s", url)
        res = await self.client.call_tool(
            "openPage", {"sessionId": sessionId, "url": url}
        )
        return res.get("structuredContent", {})

    async def get_html(self, sessionId: str):
        logger.debug("get_html")
        res = await self.client.call_tool("getHTML", {"sessionId": sessionId})
        return res.get("structuredContent", {})

    async def evaluate(self, sessionId: str, expression: str):
        logger.debug("evaluate")
        res = await self.client.call_tool(
            "evaluate", {"sessionId": sessionId, "expression": expression}
        )
        return res.get("structuredContent", {})

    async def screenshot(self, sessionId: str):
        logger.info("screenshot")
        res = await self.client.call_tool("screenshot", {"sessionId": sessionId})
        return res["content"][0]

    async def wait_for_selector(
        self, sessionId: str, selector: str, timeoutMs: Optional[int] = None
    ):
        logger.debug("wait_for_selector | %s", selector)
        args = {"sessionId": sessionId, "selector": selector}
        if timeoutMs:
            args["timeoutMs"] = int(timeoutMs)

        res = await self.client.call_tool("waitForSelector", args)
        return res.get("structuredContent", {})

    # ======================================================
    # ELEMENT UTILITIES
    # ======================================================

    async def find_element(self, sessionId: str, selector: str):
        logger.debug("find_element | %s", selector)
        res = await self.client.call_tool(
            "findElement", {"sessionId": sessionId, "selector": selector}
        )
        return res.get("structuredContent", {})

    async def find_all(self, sessionId: str, selector: str):
        logger.debug("find_all | %s", selector)
        res = await self.client.call_tool(
            "findAll", {"sessionId": sessionId, "selector": selector}
        )
        return res.get("structuredContent", {})

    async def get_bounding_box(self, sessionId: str, selector: str):
        logger.debug("get_bounding_box | %s", selector)
        res = await self.client.call_tool(
            "getBoundingBox", {"sessionId": sessionId, "selector": selector}
        )
        return res.get("structuredContent", {})

    async def click_bounding_box(self, sessionId: str, selector: str):
        logger.debug("click_bounding_box | %s", selector)
        res = await self.client.call_tool(
            "clickBoundingBox", {"sessionId": sessionId, "selector": selector}
        )
        return res.get("structuredContent", {})

    # ======================================================
    # ADVANCED FIND / CLICK
    # ======================================================

    async def click(self, sessionId: str, selector: str):
        logger.debug("click | %s", selector)
        res = await self.client.call_tool(
            "click", {"sessionId": sessionId, "selector": selector}
        )
        return res.get("structuredContent", {})

    async def type(self, sessionId: str, selector: str, text: str):
        logger.debug("type | %s", selector)
        res = await self.client.call_tool(
            "type",
            {"sessionId": sessionId, "selector": selector, "text": text},
        )
        return res.get("structuredContent", {})

    async def click_to_text(self, sessionId: str, text: str):
        logger.debug("click_to_text | %s", text)
        res = await self.client.call_tool(
            "clickToText", {"sessionId": sessionId, "text": text}
        )
        return res.get("structuredContent", {})

    async def find_element_xpath(self, sessionId: str, xpath: str):
        logger.debug("find_element_xpath")
        res = await self.client.call_tool(
            "findElementByXPath", {"sessionId": sessionId, "xpath": xpath}
        )
        return res.get("structuredContent", {})

    async def find_element_by_text(self, sessionId: str, text: str):
        logger.debug("find_element_by_text | %s", text)
        res = await self.client.call_tool(
            "findElementByText", {"sessionId": sessionId, "text": text}
        )
        return res.get("structuredContent", {})

    async def click_by_node_id(self, sessionId: str, nodeId: int):
        logger.debug("click_by_node_id | %s", nodeId)
        res = await self.client.call_tool(
            "clickByNodeId", {"sessionId": sessionId, "nodeId": nodeId}
        )
        return res.get("structuredContent", {})

    async def upload_file(
        self, sessionId: str, selector: str, filename: str, base64data: str
    ):
        logger.info("upload_file | %s", filename)
        res = await self.client.call_tool(
            "uploadFile",
            {
                "sessionId": sessionId,
                "selector": selector,
                "filename": filename,
                "data": base64data,
            },
        )
        return res.get("structuredContent", {})

    async def import_cookies(self, sessionId: str, cookies: dict):
        logger.info("import_cookies")
        res = await self.client.call_tool(
            "importCookies", {"sessionId": sessionId, "cookies": cookies}
        )
        return res.get("structuredContent", {})

    # ======================================================
    # KEYBOARD
    # ======================================================

    async def send_key(self, sessionId: str, key: str):
        logger.debug("send_key | %s", key)
        return await self.client.call_tool(
            "sendKey", {"sessionId": sessionId, "key": key}
        )

    # ======================================================
    # MOUSE / PERFORM
    # ======================================================

    async def perform_click_xy(self, sessionId: str, x: float, y: float):
        logger.debug("perform_click_xy | %s,%s", x, y)
        return await self.client.call_tool(
            "perform",
            {"sessionId": sessionId, "action": "click", "x": x, "y": y},
        )

    async def perform_drag(
        self, sessionId: str, from_x: float, from_y: float, to_x: float, to_y: float
    ):
        logger.debug("perform_drag")
        return await self.client.call_tool(
            "perform",
            {
                "sessionId": sessionId,
                "action": "drag",
                "from": {"x": from_x, "y": from_y},
                "to": {"x": to_x, "y": to_y},
            },
        )

    async def perform_hover(self, sessionId: str, x: float, y: float):
        logger.debug("perform_hover | %s,%s", x, y)
        return await self.client.call_tool(
            "perform",
            {"sessionId": sessionId, "action": "hover", "x": x, "y": y},
        )

    # ======================================================
    # CLEAN TEXT
    # ======================================================

    async def get_clean_text(self, sessionId: str):
        logger.debug("get_clean_text")
        res = await self.client.call_tool(
            "getCleanText", {"sessionId": sessionId}
        )
        return res.get("structuredContent", {})

    # ======================================================
    # VIEWPORT
    # ======================================================

    async def get_viewport(self, sessionId: str):
        logger.debug("get_viewport")
        res = await self.client.call_tool(
            "viewport", {"sessionId": sessionId}
        )
        return res.get("structuredContent", {})

    async def set_viewport(
        self,
        sessionId: str,
        *,
        width: int,
        height: int,
        deviceScaleFactor: float = 1.0,
        mobile: bool = False,
    ):
        logger.info("set_viewport | %sx%s", width, height)
        res = await self.client.call_tool(
            "viewport",
            {
                "sessionId": sessionId,
                "viewport": {
                    "width": width,
                    "height": height,
                    "deviceScaleFactor": deviceScaleFactor,
                    "mobile": mobile,
                },
            },
        )
        return res.get("structuredContent", {})

    # ======================================================
    # AI / PARSING
    # ======================================================

    async def parse_html_by_prompt(self, html: str, prompt: str):
        logger.info("parse_html_by_prompt")
        res = await self.client.call_tool(
            "parseHTMLByPrompt",
            {"html": html, "prompt": prompt},
        )
        return res.get("structuredContent", {})

    async def current_url(self, sessionId: str):
        logger.debug("current_url")
        res = await self.client.call_tool(
            "getCurrentUrl", {"sessionId": sessionId}
        )
        data = res.get("structuredContent", {})
        return data.get("url", "")
