from typing import List, Optional, Callable, Union
import logging
from .browser import BrowserManager
from .config import Config
from .providers.chatgpt import ChatGPTProvider
from .providers.aistudio import GoogleAIStudioProvider
from .providers.claude import ClaudeProvider
from .exceptions import SetupError

logger = logging.getLogger(__name__)

class Automator:
    # * Main entry point for the LLM Web Automator.
    # * Acts as a Facade over BrowserManager and specific Provider implementations.

    def __init__(self, provider: str = "chatgpt", headless: bool = True, credentials: Optional[dict] = None, session_path: Optional[str] = None, config: Optional[dict] = None, on_otp_required: Optional[Callable[[], str]] = None):
        logger.info("Automator.__init__ starting...")
        logger.info(f"  provider={provider}, headless={headless}, session_path={session_path}")
        logger.info(f"  credentials provided: {credentials is not None}")
        logger.info(f"  config keys: {list((config or {}).keys())}")

        self.provider_name = provider.lower()
        self.headless = headless
        self.credentials = credentials
        self.session_path = session_path
        self.config = config or {}
        self.on_otp_required = on_otp_required

        logger.info("Creating BrowserManager instance...")
        self.browser_manager = BrowserManager()
        logger.info("BrowserManager instance created")

        self.provider = None

        logger.info("Calling _initialize_environment()...")
        self._initialize_environment()
        logger.info("Automator.__init__ completed successfully")

    def process_prompt(self, prompt: str, system_prompt: Optional[str] = None, conversation_history: Optional[Union[str, List[str]]] = None) -> str:
        # * Process a single prompt and return the text response.
        # * Optionally includes system prompt and conversation history formatted into the message.
        if not self.provider:
            raise SetupError("Provider not initialized.")
        
        full_prompt = self._construct_full_prompt(prompt, system_prompt, conversation_history)
        return self.provider.send_prompt(full_prompt)

    def _construct_full_prompt(self, prompt: str, system_prompt: Optional[str] = None, conversation_history: Optional[Union[str, List[str]]] = None) -> str:
        # * Helper to format the prompt with system instructions and history.
        parts = []
        
        if system_prompt:
            parts.append(system_prompt)
            parts.append("---")
            
        if conversation_history:
            if isinstance(conversation_history, list):
                history_text = "\n".join(str(item) for item in conversation_history)
                parts.append(history_text)
            else:
                parts.append(str(conversation_history))
            parts.append("---")
            
        parts.append(prompt)
        
        return "\n".join(parts)

    def process_chain(self, prompts: List[Union[str, Callable[[str], str]]]) -> List[str]:
        # * Process a list of prompts, passing previous context if requested.
        # @param prompts - List of strings or callables. strings can contain {{previous}}.
        
        responses = []
        last_response = ""
        
        for i, prompt_item in enumerate(prompts):
            logger.info(f"Processing prompt {i+1}/{len(prompts)}...")
            
            current_prompt = self._resolve_prompt_content(prompt_item, last_response)
            
            response = self.process_prompt(current_prompt)
            responses.append(response)
            last_response = response
            
        return responses

    def close(self):
        # * Cleanup browser resources.
        self.browser_manager.stop()

    # --- Private Initialization Methods ---

    def _initialize_environment(self):
        # * Setup browser, provider, and handle initial authentication.

        # 1. Launch Browser
        logger.info("Step 1: Launching browser via browser_manager.start()...")
        logger.info(f"  headless={self.headless}, session_path={self.session_path}")
        page = self.browser_manager.start(headless=self.headless, session_path=self.session_path)
        logger.info(f"Browser started, page obtained: {page is not None}")

        # * Enable clipboard for response extraction
        logger.info("Granting clipboard permissions...")
        self.browser_manager.context.grant_permissions(["clipboard-read", "clipboard-write"])
        logger.info("Clipboard permissions granted")

        # 2. Instantiate Provider
        logger.info(f"Step 2: Creating provider instance for '{self.provider_name}'...")
        self.provider = self._create_provider_instance(page)
        logger.info(f"Provider instance created: {type(self.provider).__name__}")

        # 3. Authenticate
        logger.info("Step 3: Ensuring authentication...")
        self._ensure_authenticated()
        logger.info("Authentication check completed")

    def _create_provider_instance(self, page):
        logger.info(f"_create_provider_instance: Creating '{self.provider_name}' provider...")
        if self.provider_name == "chatgpt":
            logger.info("Instantiating ChatGPTProvider...")
            provider = ChatGPTProvider(page, config=self.config, on_otp_required=self.on_otp_required)
            logger.info("ChatGPTProvider instantiated")
            return provider
        elif self.provider_name == "aistudio":
            logger.info("Instantiating GoogleAIStudioProvider...")
            provider = GoogleAIStudioProvider(page, config=self.config, on_otp_required=self.on_otp_required)
            logger.info("GoogleAIStudioProvider instantiated")
            return provider
        elif self.provider_name == "claude":
            logger.info("Instantiating ClaudeProvider...")
            provider = ClaudeProvider(page, config=self.config, on_otp_required=self.on_otp_required)
            logger.info("ClaudeProvider instantiated")
            return provider
        else:
            logger.error(f"Provider '{self.provider_name}' not supported")
            raise NotImplementedError(f"Provider {self.provider_name} not supported.")

    def _ensure_authenticated(self):
        # * Checks session persistence; logs in if necessary.
        logger.info(f"_ensure_authenticated: Checking auth for URL={self.provider.URL}")
        logger.info(f"  Profile button selector: {self.provider.SEL_PROFILE_BTN}")

        logger.info("Calling browser_manager.is_authenticated()...")
        is_auth = self.browser_manager.is_authenticated(self.provider.URL, self.provider.SEL_PROFILE_BTN)
        logger.info(f"is_authenticated result: {is_auth}")

        if not is_auth:
            logger.info("Not authenticated. Initiating login...")

            logger.info("Getting credentials...")
            creds = self.credentials or Config.get_credentials(self.provider_name)
            logger.info(f"Credentials obtained: email={'***' if creds.get('email') else 'None'}")

            if not creds.get("email"):
                logger.error(f"No email found in credentials for {self.provider_name}")
                raise SetupError(f"Credentials (email) not found for {self.provider_name}.")

            logger.info("Calling provider.login()...")
            self.provider.login(creds)
            logger.info("provider.login() completed")

            if self.session_path:
                logger.info(f"Saving session to: {self.session_path}")
                self.browser_manager.save_session(self.session_path)
                logger.info("Session saved")
        else:
            logger.info("Session authenticated - no login needed")

    # --- Private Utility Methods ---

    def _resolve_prompt_content(self, prompt_item: Union[str, Callable], previous_response: str) -> str:
        # * Formats the prompt string using the previous response if valid placeholders exist.
        if callable(prompt_item):
            return prompt_item(previous_response)
        
        if isinstance(prompt_item, str):
            if "{{previous}}" in prompt_item:
                    return prompt_item.replace("{{previous}}", previous_response)
            elif "{}" in prompt_item:
                try:
                    return prompt_item.format(previous_response)
                except ValueError:
                    return prompt_item
            elif "{{}}" in prompt_item:
                return prompt_item.replace("{{}}", previous_response)
            return prompt_item
            
        return str(prompt_item)