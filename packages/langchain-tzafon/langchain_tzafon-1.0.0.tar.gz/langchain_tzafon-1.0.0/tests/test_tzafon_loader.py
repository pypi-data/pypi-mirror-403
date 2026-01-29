
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from langchain_tzafon.tzafon_loader import TzafonLoader

@pytest.fixture
def mock_settings():
    with patch("langchain_tzafon.tzafon_loader.config") as mock_config:
        mock_config.api_base_url = "http://mock-api"
        mock_config.api_key.get_secret_value.return_value = "default_key"
        yield mock_config

@pytest.fixture
def mock_client():
    with patch("langchain_tzafon.tzafon_loader.TzafonClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_browser = MagicMock()
        mock_browser.id = "computer-123"
        mock_instance.initialize.return_value = mock_browser
        yield MockClient

@pytest.fixture
def mock_sync_playwright():
    with patch("langchain_tzafon.tzafon_loader.sync_playwright") as mock_pw:
        yield mock_pw

@pytest.fixture
def mock_async_playwright():
    with patch("langchain_tzafon.tzafon_loader.async_playwright") as mock_pw:
        yield mock_pw

def test_initialization(mock_settings, mock_client):
    # Test 1: Single URL
    loader = TzafonLoader(urls="http://example.com", api_key="test_key")
    assert loader.urls == ["http://example.com"]
    assert loader.api_key == "test_key"
    mock_client.assert_called_with(api_key="test_key")
    mock_client.return_value.initialize.assert_called()
    assert loader.browser == mock_client.return_value.initialize.return_value

    # Test 2: List of URLs
    loader = TzafonLoader(urls=["http://a.com", "http://b.com"], api_key="test_key")
    assert loader.urls == ["http://a.com", "http://b.com"]

def test_lazy_load_text(mock_settings, mock_client, mock_sync_playwright):
    # Setup Playwright mocks
    mock_pw_context = mock_sync_playwright.return_value.__enter__.return_value
    mock_browser = mock_pw_context.chromium.connect_over_cdp.return_value
    mock_context = mock_browser.new_context.return_value
    mock_page = mock_context.new_page.return_value
    
    # Setup Page behavior
    mock_page.inner_text.return_value = "Mock Page Content"
    
    # Execute
    loader = TzafonLoader(urls="http://example.com", api_key="test_key")
    docs = list(loader.lazy_load())
    
    # Assertions
    assert len(docs) == 1
    assert docs[0].page_content == "Mock Page Content"
    assert docs[0].metadata["url"] == "http://example.com"
    
    # Verify Playwright calls
    mock_pw_context.chromium.connect_over_cdp.assert_called_with(
        "http://mock-api/computers/computer-123/cdp?token=test_key"
    )
    mock_page.goto.assert_called_with("http://example.com")
    mock_page.inner_text.assert_called_with("body")
    mock_page.close.assert_called()
    mock_browser.close.assert_called()
    mock_client.return_value.initialize.return_value.terminate.assert_called()

def test_lazy_load_html(mock_settings, mock_client, mock_sync_playwright):
    mock_pw_context = mock_sync_playwright.return_value.__enter__.return_value
    mock_page = mock_pw_context.chromium.connect_over_cdp.return_value.new_context.return_value.new_page.return_value
    mock_page.content.return_value = "<html><body>Mock HTML</body></html>"
    
    loader = TzafonLoader(urls="http://example.com", api_key="test_key", text_content=False)
    docs = list(loader.lazy_load())
    
    assert len(docs) == 1
    assert docs[0].page_content == "<html><body>Mock HTML</body></html>"
    mock_page.content.assert_called()

@pytest.mark.asyncio
async def test_alazy_load_text(mock_settings, mock_client, mock_async_playwright):
    # Setup Async Playwright Mock
    mock_pw_context = mock_async_playwright.return_value.__aenter__.return_value
    
    mock_browser = AsyncMock()
    mock_pw_context.chromium.connect_over_cdp.return_value = mock_browser
    
    mock_context = AsyncMock()
    mock_browser.new_context.return_value = mock_context
    
    mock_page = AsyncMock()
    mock_context.new_page.return_value = mock_page
    
    mock_page.inner_text.return_value = "Async Mock Page Content"
    
    # Execute
    loader = TzafonLoader(urls="http://example.com", api_key="test_key")
    
    docs = []
    async for doc in loader.alazy_load():
        docs.append(doc)
        
    # Assertions
    assert len(docs) == 1
    assert docs[0].page_content == "Async Mock Page Content"
    
    # Verify Async Calls
    mock_pw_context.chromium.connect_over_cdp.assert_awaited_with(
            "http://mock-api/computers/computer-123/cdp?token=test_key"
    )
    mock_page.goto.assert_awaited_with("http://example.com")
    mock_page.inner_text.assert_awaited_with("body")
    mock_page.close.assert_awaited()
    mock_browser.close.assert_awaited()
    mock_client.return_value.initialize.return_value.terminate.assert_called()
