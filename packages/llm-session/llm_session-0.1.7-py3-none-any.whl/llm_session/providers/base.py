import random
import time
from abc import ABC, abstractmethod
from playwright.sync_api import Page

class LLMProvider(ABC):
    # * Abstract base class defining the contract for all LLM providers.
    # * Ensures consistent API for the Automator class.
    
    # * Delay configuration for anti-bot detection (in seconds)
    MIN_CLICK_DELAY = 0.5
    MAX_CLICK_DELAY = 1.5

    def __init__(self, page: Page):
        self.page = page
    
    def _delayed_click(self, selector: str, page: Page = None, timeout: int = None):
        # * Adds a random delay before clicking to appear more human-like.
        # @param selector - The selector to click.
        # @param page - Optional page object (useful for popups). Defaults to self.page.
        # @param timeout - Optional timeout for the click operation.
        target_page = page or self.page
        delay = random.uniform(self.MIN_CLICK_DELAY, self.MAX_CLICK_DELAY)
        time.sleep(delay)
        if timeout is not None:
            target_page.click(selector, timeout=timeout)
        else:
            target_page.click(selector)

    @abstractmethod
    def login(self, credentials: dict) -> bool:
        # * Perform the full login sequence including handling 2FA/OTP if applicable.
        # @param credentials - Dictionary containing 'email', 'password', etc.
        # @returns - True if login was successful.
        pass

    @abstractmethod
    def send_prompt(self, prompt: str) -> str:
        # * Submits a text prompt to the LLM and extracts the text response.
        # @param prompt - The message string to send.
        # @returns - The extracted response string.
        pass
    
    @abstractmethod
    def handle_dialogs(self):
        # * Checks for and dismisses annoying popups (upsells, cookie banners, intros).
        pass