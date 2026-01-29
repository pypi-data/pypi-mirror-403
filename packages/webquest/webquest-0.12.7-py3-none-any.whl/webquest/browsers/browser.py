from abc import ABC, abstractmethod
from typing import AsyncContextManager, ClassVar, Generic, TypeVar

from playwright.async_api import BrowserContext
from pydantic_settings import BaseSettings

TSettings = TypeVar("TSettings", bound=BaseSettings)


class Browser(ABC, Generic[TSettings]):
    """
    Abstract base class for browser implementations.

    This class defines the interface for obtaining a browser context, which is used
    for performing web scraping operations.

    Type Parameters:
        TSettings: The type of the settings object for the browser.
    """

    settings_model: ClassVar[type[TSettings]]

    def __init__(self, settings: TSettings | None = None) -> None:
        """
        Initialize the Browser.

        Args:
            settings (TSettings | None): Optional settings for the browser.
        """

        if settings is None:
            settings = self.settings_model()
        self._settings: TSettings = settings

    @abstractmethod
    def get_context(self) -> AsyncContextManager[BrowserContext]:
        """
        Get an asynchronous context manager that yields a Playwright BrowserContext.

        Returns:
            AsyncContextManager[BrowserContext]: An async context manager that yields a BrowserContext.
        """
        ...
