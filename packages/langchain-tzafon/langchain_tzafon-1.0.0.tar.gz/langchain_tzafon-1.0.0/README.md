# 🦜 langchain-tzafon

An integration package connecting **[Tzafon](https://tzafon.ai)** and **[LangChain](https://www.langchain.com/)**.

`langchain-tzafon` allows you to seamlessly use Tzafon's headless browser infrastructure as a [Document Loader](https://python.langchain.com/docs/modules/data_connection/document_loaders/) in your LangChain applications. It handles complex web page rendering (including JavaScript) and extracts clean text or raw HTML for your LLM pipelines.

---

## ✨ Features

- **Headless Browser Rendering**: Power by Tzafon's cloud-based browser instances.
- **JavaScript Support**: Naturally handles SPAs and dynamically loaded content.
- **Sync & Async Support**: Features both `lazy_load` and `alazy_load` for high-performance applications.
- **Configurable Extraction**: Choice between clean text content or full source HTML.
- **Seamless Integration**: Fully compatible with LangChain's `BaseLoader` interface.

---

## 🚀 Installation

```bash
pip install langchain-tzafon
```

---

## 🔑 Configuration

To use this package, you need a Tzafon API Key.

1.  Sign up or log in at **[tzafon.ai](https://tzafon.ai)** to get your API key.
2.  Set it as an environment variable (recommended):

```bash
export TZAFON_API_KEY="your_api_key_here"
```

Alternatively, you can pass the API key directly when initializing the loader.

---

## 📖 Usage

### Basic Usage (Text Extraction)

By default, `TzafonLoader` extracts the visible text from the `<body>` of the page.

```python
from langchain_tzafon import TzafonLoader

# Initialize with one or more URLs
loader = TzafonLoader(urls=["https://example.com"])

# Load documents
documents = loader.load()

for doc in documents:
    print(f"Content from {doc.metadata['url']}:")
    print(doc.page_content[:200])
```

### Async Loading

For better performance when handling multiple URLs, use the asynchronous loader:

```python
import asyncio
from langchain_tzafon import TzafonLoader

async def main():
    loader = TzafonLoader(urls=[
        "https://example.com",
        "https://tzafon.ai"
    ])
    
    async for doc in loader.alazy_load():
        print(f"Loaded {doc.metadata['url']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Loading Raw HTML

If you need the full HTML structure for custom parsing:

```python
loader = TzafonLoader(
    urls="https://example.com",
    text_content=False  # Set to False for raw HTML
)
documents = loader.load()
```

---

## 🛠️ API Reference

### `TzafonLoader`

| Argument | Type | Description |
| :--- | :--- | :--- |
| `urls` | `str \| List[str]` | A single URL or a list of URLs to load. |
| `api_key` | `Optional[str]` | Your Tzafon API key. Defaults to `TZAFON_API_KEY` env var. |
| `text_content` | `bool` | If `True` (default), extracts visible text. If `False`, returns raw HTML. |

---

## 🧪 Development

This project uses `uv` for dependency management and `pytest` for testing.

### Running Tests

```bash
uv run pytest
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details (if available).
