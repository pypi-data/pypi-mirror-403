from typing import Any, Dict

import pytest
from kl_mcp_client import MCPTools  # đổi đúng import path của bạn

# ======================================================
# MOCK MCP CLIENT (SYNC)
# ======================================================

class MockMCPClient:
    def __init__(self):
        self.calls = []

    def create_session(self, cdpUrl: str):
        self.calls.append(("create_session", cdpUrl))
        return "session-123"

    def close_session(self, sessionId: str):
        self.calls.append(("close_session", sessionId))
        return True

    def list_local_sessions(self):
        return ["session-123", "session-456"]

    def call_tool(self, name: str, payload: Dict[str, Any]):
        self.calls.append((name, payload))

        if name == "screenshot":
            return {
                "content": [
                    {
                        "type": "image",
                        "mimeType": "image/png",
                        "data": "BASE64DATA",
                    }
                ]
            }

        if name in ("create_browser", "release_browser"):
            return {
                "structuredContent": {
                    "success": True,
                }
            }

        return {
            "structuredContent": {
                "ok": True,
                "tool": name,
                "payload": payload,
            }
        }


# ======================================================
# FIXTURES
# ======================================================

@pytest.fixture
def tools():
    t = MCPTools()
    t.client = MockMCPClient()
    return t


# ======================================================
# SESSION MANAGEMENT
# ======================================================

def test_connect_mcp(tools):
    res = tools.connect_mcp("http://localhost:3000")
    assert res["ok"] is True


def test_create_session(tools):
    res = tools.create_session("http://localhost:9222")
    assert res["sessionId"] == "session-123"


def test_close_session(tools):
    res = tools.close_session("session-123")
    assert res["ok"] is True


def test_list_sessions(tools):
    res = tools.list_sessions()
    assert len(res["sessions"]) == 2


# ======================================================
# BROWSER RUNTIME (NO SESSION)
# ======================================================

def test_create_browser(tools):
    res = tools.create_browser({"image": "chrome"})
    assert res["success"] is True


def test_release_browser(tools):
    res = tools.release_browser()
    assert res["success"] is True


# ======================================================
# NAVIGATION & DOM
# ======================================================

def test_open_page(tools):
    res = tools.open_page("session-123", "https://example.com")
    assert res["ok"] is True


def test_get_html(tools):
    res = tools.get_html("session-123")
    assert res["ok"] is True


def test_screenshot(tools):
    res = tools.screenshot("session-123")
    assert res["type"] == "image"


def test_evaluate(tools):
    res = tools.evaluate("session-123", "1+1")
    assert res["ok"] is True


# ======================================================
# ELEMENT UTILITIES
# ======================================================

def test_find_element(tools):
    res = tools.find_element("session-123", "#main")
    assert res["ok"] is True


def test_find_all(tools):
    res = tools.find_all("session-123", "div")
    assert res["ok"] is True


def test_get_bounding_box(tools):
    res = tools.get_bounding_box("session-123", "#box")
    assert res["ok"] is True


def test_click_bounding_box(tools):
    res = tools.click_bounding_box("session-123", "#btn")
    assert res["ok"] is True


# ======================================================
# TAB MANAGEMENT
# ======================================================

def test_new_tab(tools):
    res = tools.new_tab("session-123", "https://example.com")
    assert res["ok"] is True


def test_switch_tab(tools):
    res = tools.switch_tab("session-123", "tab-1")
    assert res["ok"] is True


# ======================================================
# ADVANCED ACTIONS
# ======================================================

def test_click_to_text(tools):
    res = tools.click_to_text("session-123", "Login")
    assert res["ok"] is True


def test_find_element_xpath(tools):
    res = tools.find_element_xpath("session-123", "//div")
    assert res["ok"] is True


def test_find_element_by_text(tools):
    res = tools.find_element_by_text("session-123", "Submit")
    assert res["ok"] is True


def test_click_by_node_id(tools):
    res = tools.click_by_node_id("session-123", 10)
    assert res["ok"] is True


def test_import_cookies(tools):
    res = tools.import_cookies("session-123", {"a": "b"})
    assert res["ok"] is True


# ======================================================
# SCROLL / PERFORM
# ======================================================

def test_scroll_pixel(tools):
    res = tools.scroll("session-123", y=500)
    assert res["ok"] is True


def test_perform_drag(tools):
    res = tools.drag_and_drop("session-123", 0, 0, 100, 100)
    assert res["ok"] is True
