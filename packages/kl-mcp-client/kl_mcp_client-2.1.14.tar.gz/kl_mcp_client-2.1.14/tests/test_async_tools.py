from typing import Any, Dict

import pytest
from kl_mcp_client.asyncio import MCPTools

# ======================================================
# MOCK MCP CLIENT
# ======================================================

class MockMCPClient:
    def __init__(self):
        self.calls = []

    async def create_session(self, cdpUrl: str):
        self.calls.append(("create_session", cdpUrl))
        return "session-123"

    async def close_session(self, sessionId: str):
        self.calls.append(("close_session", sessionId))
        return True

    def list_local_sessions(self):
        return ["session-123", "session-456"]

    async def call_tool(self, name: str, payload: Dict[str, Any]):
        self.calls.append((name, payload))

        # ---- fake responses ----
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
def mock_client():
    return MockMCPClient()


@pytest.fixture
def tools(mock_client):
    return MCPTools(client=mock_client)


# ======================================================
# SESSION MANAGEMENT
# ======================================================

@pytest.mark.asyncio
async def test_create_session(tools):
    res = await tools.create_session("http://localhost:9222")
    assert res["sessionId"] == "session-123"


@pytest.mark.asyncio
async def test_close_session(tools):
    res = await tools.close_session("session-123")
    assert res["ok"] is True


@pytest.mark.asyncio
async def test_list_sessions(tools):
    res = await tools.list_sessions()
    assert "sessions" in res
    assert len(res["sessions"]) == 2


# ======================================================
# BROWSER RUNTIME (NO SESSION)
# ======================================================

@pytest.mark.asyncio
async def test_create_browser(tools):
    res = await tools.create_browser({"image": "chrome"})
    assert res["success"] is True


@pytest.mark.asyncio
async def test_release_browser(tools):
    res = await tools.release_browser()
    assert res["success"] is True


# ======================================================
# NAVIGATION & DOM
# ======================================================

@pytest.mark.asyncio
async def test_open_page(tools):
    res = await tools.open_page("session-123", "https://example.com")
    assert res["ok"] is True


@pytest.mark.asyncio
async def test_get_html(tools):
    res = await tools.get_html("session-123")
    assert res["ok"] is True


@pytest.mark.asyncio
async def test_screenshot(tools):
    res = await tools.screenshot("session-123")
    assert res["type"] == "image"
    assert res["mimeType"] == "image/png"


@pytest.mark.asyncio
async def test_evaluate(tools):
    res = await tools.evaluate("session-123", "1+1")
    assert res["ok"] is True


# ======================================================
# ELEMENT UTILITIES
# ======================================================

@pytest.mark.asyncio
async def test_find_element(tools):
    res = await tools.find_element("session-123", "#main")
    assert res["ok"] is True


@pytest.mark.asyncio
async def test_find_all(tools):
    res = await tools.find_all("session-123", "div")
    assert res["ok"] is True


@pytest.mark.asyncio
async def test_get_bounding_box(tools):
    res = await tools.get_bounding_box("session-123", "#main")
    assert res["ok"] is True


@pytest.mark.asyncio
async def test_click_bounding_box(tools):
    res = await tools.click_bounding_box("session-123", "#btn")
    assert res["ok"] is True


# ======================================================
# TAB MANAGEMENT
# ======================================================

@pytest.mark.asyncio
async def test_new_tab(tools):
    res = await tools.new_tab("session-123", "https://example.com")
    assert res["ok"] is True


@pytest.mark.asyncio
async def test_switch_tab(tools):
    res = await tools.switch_tab("session-123", "tab-1")
    assert res["ok"] is True


# ======================================================
# ADVANCED ACTIONS
# ======================================================

@pytest.mark.asyncio
async def test_click_to_text(tools):
    res = await tools.click_to_text("session-123", "Login")
    assert res["ok"] is True


@pytest.mark.asyncio
async def test_find_element_xpath(tools):
    res = await tools.find_element_xpath("session-123", "//div")
    assert res["ok"] is True


@pytest.mark.asyncio
async def test_find_element_by_text(tools):
    res = await tools.find_element_by_text("session-123", "Submit")
    assert res["ok"] is True


@pytest.mark.asyncio
async def test_click_by_node_id(tools):
    res = await tools.click_by_node_id("session-123", 1001)
    assert res["ok"] is True


@pytest.mark.asyncio
async def test_import_cookies(tools):
    res = await tools.import_cookies("session-123", {"a": "b"})
    assert res["ok"] is True


# ======================================================
# PERFORM / MOUSE
# ======================================================

@pytest.mark.asyncio
async def test_perform_click_xy(tools):
    res = await tools.perform_click_xy("session-123", 10, 20)
    assert res["ok"] is True


@pytest.mark.asyncio
async def test_perform_drag(tools):
    res = await tools.perform_drag("session-123", 0, 0, 100, 100)
    assert res["ok"] is True


@pytest.mark.asyncio
async def test_perform_hover(tools):
    res = await tools.perform_hover("session-123", 50, 50)
    assert res["ok"] is True


# ======================================================
# CLEAN TEXT
# ======================================================

@pytest.mark.asyncio
async def test_get_clean_text(tools):
    res = await tools.get_clean_text("session-123")
    assert res["ok"] is True
