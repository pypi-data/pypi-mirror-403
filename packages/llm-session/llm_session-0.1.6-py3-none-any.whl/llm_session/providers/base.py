from abc import ABC, abstractmethod
from playwright.sync_api import Page

class LLMProvider(ABC):
    # * Abstract base class defining the contract for all LLM providers.
    # * Ensures consistent API for the Automator class.

    def __init__(self, page: Page):
        self.page = page

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