from typing import (
    Iterator, 
    AsyncIterator,
    Optional, 
    Sequence, 
    Union
    )

from langchain_core.documents import Document
from langchain_core.document_loaders.base import BaseLoader
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright

from langchain_tzafon.core import TzafonClient
from langchain_tzafon.utils import get_logger
from langchain_tzafon.constants import Settings

logger = get_logger(__name__)

config = Settings()

class TzafonLoader(BaseLoader):
    """
    Load pre-rendered web pages using a headless browser hosted on Tzafon.

    This loader uses the Tzafon service to render web pages and extract their content.
    It supports both synchronous and asynchronous loading.

    Attributes:
        urls (List[str]): List of URLs to load.
        api_key (Optional[str]): The Tzafon API key.
        text_content (bool): Whether to extract only text content (True) or full HTML (False).
    """
    def __init__(
        self,
        urls: Union[str, Sequence[str]],
        api_key: Optional[str] = None,   
        text_content: Optional[bool] = True,  
    ):
        """
        Initialize the TzafonLoader.

        Args:
            urls: A single URL or a list of URLs to load.
            api_key: The Tzafon API key. If not provided, it will be retrieved from the `TZAFON_API_KEY` environment variable.
            text_content: If True, extracts text content. If False, extracts the raw HTML. Defaults to True.
        """

        if isinstance(urls, str):
            self.urls = [urls]
        else:
            self.urls = urls

        self.api_key = api_key or config.api_key.get_secret_value()
        self.text_content = text_content

        self.client = TzafonClient(api_key=self.api_key)


    def lazy_load(self) -> Iterator[Document]:
        """
        Load pages from URLs synchronously.

        Yields:
             Iterator[Document]: An iterator of Document objects containing the page content.
        """
        computer = self.client.initialize()
        cdp_url = f"{config.api_base_url}/computers/{computer.id}/cdp?token={self.api_key}"

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.connect_over_cdp(cdp_url)
                context =  browser.contexts[0] if browser.contexts else browser.new_context()
                for url in self.urls:
                    page = context.new_page()
                    
                    page.goto(url)
                    if self.text_content:
                        page_text = page.inner_text("body")
                        content = str(page_text)
                    else:
                        page_html = page.content()
                        content = str(page_html)

                    page.close()
                browser.close()

                yield Document(
                    page_content=content,
                    metadata={
                        "url": url,
                    },
                )
        except Exception as e:
            logger.error(f"Error loading page: {e}")
            raise
        finally:
            computer.terminate()

    async def alazy_load(self) -> AsyncIterator[Document]:
        """
        Load pages from URLs asynchronously.

        Yields:
             AsyncIterator[Document]: An async iterator of Document objects containing the page content.
        """
        computer = self.client.initialize()
        cdp_url = f"{config.api_base_url}/computers/{computer.id}/cdp?token={self.api_key}"

        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.connect_over_cdp(cdp_url)
                context = browser.contexts[0] if browser.contexts else await browser.new_context()
                
                for url in self.urls:
                    page = await context.new_page()

                    await page.goto(url)
                    if self.text_content:
                        page_text = await page.inner_text("body")
                        content = str(page_text)
                    else:
                        page_html = await page.content()
                        content = str(page_html)

                    await page.close()
                await browser.close()

                yield Document(
                    page_content=content,
                    metadata={
                        "url": url,
                        },
                    )
        except Exception as e:
            logger.error(f"Error loading page: {e}")
            raise
        finally:
            computer.terminate()