from typing import Optional,  Literal

from tzafon import Computer

from .utils import singleton, get_logger
from .constants import Settings

logger = get_logger(__name__)
config = Settings()

@singleton
class TzafonClient:
    """Singleton class to ensure only one Tzafon client instance exists."""
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the TzafonClient.

        Args:
           api_key: The API key for Tzafon. If not provided, it will be retrieved from the environment variable `TZAFON_API_KEY`.
        """
        self._api_key = api_key or config.api_key.get_secret_value()
        self.computer = None

       
    def initialize(self, kind: Literal["browser", "desktop"] = "browser") -> Computer:
        """
        Initialize the Tzafon client and create a computer instance.

        Args:
            kind: The type of computer to create. Can be "browser" or "desktop". Defaults to "browser".

        Returns:
            The initialized Tzafon computer instance.

        Raises:
             ValueError: If the API key is missing.
        """
        if not self._api_key:
            logger.error("Tzafon API key is required. Read here on how to get your api key: https://docs.tzafon.ai/quickstart#get-your-api-key")
            raise ValueError("Tzafon API key is required. Read here on how to get your api key: https://docs.tzafon.ai/quickstart#get-your-api-key")


        client = Computer(api_key=self._api_key)

        self.computer = client.create(kind=kind)

        logger.info("Tzafon client initialized")
        logger.info("Synchronous computer created with id %s", self.computer.id)
    
        return self.computer

    def terminate(self):
        """Terminate the Tzafon computer instance."""
        self.computer.terminate()
    
    