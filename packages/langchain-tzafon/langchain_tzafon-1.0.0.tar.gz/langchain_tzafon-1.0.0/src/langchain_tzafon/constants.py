import os

from pydantic_settings import BaseSettings
from pydantic import SecretStr

from .utils import singleton

@singleton
class Settings(BaseSettings):
    """
    Pydantic settings for the Tzafon LangChain integration.
    
    Attributes:
        api_base_url (str): The base URL for the Tzafon API. Defaults to "https://api.tzafon.ai".
    """
    api_base_url: str = "https://api.tzafon.ai"
    api_key: SecretStr =  SecretStr(os.getenv("TZAFON_API_KEY", default=""))
   