import time
import logging
from typing import Optional, Callable
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect
from .base import LLMProvider
from ..exceptions import AuthenticationError, SelectorError, PromptError

logger = logging.getLogger(__name__)

class GoogleAIStudioProvider(LLMProvider):
    # * Google AI Studio (Gemini) implementation.
    # * Relies on JS injection for the complex editor component.

    URL = "https://aistudio.google.com/prompts/new_chat"

    DEFAULT_SELECTORS = {
        # * Landmarks
        "main_landmark": "ms-chunk-editor",
        
        # * Login
        "email_input": 'input[type="email"]',
        "email_next": 'button:has-text("Next")',
        "password_input": 'input[type="password"]',
        "password_next": 'button:has-text("Next")',

        # * Interstitials
        "passkey_not_now": 'button:has-text("Not now")',
        "recovery_cancel_btn": 'button[aria-label="Cancel"]',
        "recovery_skip_btn": 'button:has-text("Skip")',

        # * Editor
        "textarea": 'textarea[aria-label*="prompt"]',
        "run_button": 'button[aria-label="Run"]',
        # "stoppable_button" removed as it is no longer reliable
        
        # * Response Extraction
        "response_block": "ms-chat-turn",
        "more_options_btn": "button[aria-label='Open options']",
        "copy_menu_item": "[role='menuitem']:has-text('Copy')",
        
        # * Dialogs
        "save_drive_cancel": "button:has-text('Cancel and use Temporary chat')"
    }

    def __init__(self, page: Page, config: Optional[dict] = None, on_otp_required: Optional[Callable[[], str]] = None):
        super().__init__(page)
        self.config = config or {}
        self.on_otp_required = on_otp_required
        self.selectors = self.DEFAULT_SELECTORS.copy()
        
        if "selectors" in self.config:
            self.selectors.update(self.config["selectors"])
            
        self.SEL_PROFILE_BTN = self.selectors["main_landmark"]

    def login(self, credentials: dict) -> bool:
        logger.info("Starting AI Studio login process...")
        
        try:
            self.page.goto(self.URL, wait_until="domcontentloaded")
            
            if self._is_logged_in():
                logger.info("Already logged in.")
                return True

            self._perform_login_flow(credentials)
            return True

        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise AuthenticationError(f"Login failed: {e}")

    def send_prompt(self, prompt: str) -> str:
        self.handle_dialogs()
        
        try:
            self._inject_prompt_text(prompt)
            self._click_run_button()
        except Exception as e:
            raise PromptError(f"Failed to send prompt: {e}")
            
        logger.info("Waiting for response generation...")
        self._wait_for_completion()

        try:
            return self._extract_via_clipboard()
        except Exception as e:
            raise PromptError(f"Failed to extract response: {e}")

    def handle_dialogs(self):
        try:
            if self.page.is_visible(self.selectors["save_drive_cancel"]):
                logger.info("Dismissing 'Save to Drive' dialog...")
                self._delayed_click(self.selectors["save_drive_cancel"])
                self.page.wait_for_selector(self.selectors["save_drive_cancel"], state="hidden")
        except:
            pass

    # --- Private Login Helpers ---

    def _is_logged_in(self) -> bool:
        try:
            self.page.wait_for_selector(self.selectors["main_landmark"], timeout=5000)
            return True
        except:
            return False

    def _perform_login_flow(self, credentials):
        email = credentials.get("email")
        password = credentials.get("password")

        if not email or not password:
            raise AuthenticationError("Email and password required for login.")

        logger.info("Attempting Google Authentication...")

        try:
            # * Email
            self.page.wait_for_selector(self.selectors["email_input"], timeout=10000)
            self.page.fill(self.selectors["email_input"], email)
            self._delayed_click(self.selectors["email_next"])
        except Exception as e:
            raise SelectorError(f"Email flow failed: {e}")

        try:
            # * Password
            self.page.wait_for_selector(self.selectors["password_input"], state="visible", timeout=10000)
            self.page.fill(self.selectors["password_input"], password)
            self._delayed_click(self.selectors["password_next"])
        except Exception as e:
            raise SelectorError(f"Password flow failed: {e}")
            
        try:
            # * Handle Passkey Speedbump
            self.page.wait_for_selector(self.selectors["passkey_not_now"], timeout=5000)
            logger.info("Passkey enrollment detected. Dismissing...")
            self._delayed_click(self.selectors["passkey_not_now"])
        except:
            pass

        # * Recovery Options check
        try:
            self.page.wait_for_selector(self.selectors["recovery_cancel_btn"], timeout=5000)
            self._delayed_click(self.selectors["recovery_cancel_btn"])
        except:
            pass

        # * Handle "Recovery Info" Page (new screen identified)
        try:
            self.page.wait_for_selector(self.selectors["recovery_skip_btn"], timeout=5000)
            logger.info("Recovery info page detected. Clicking Skip...")
            self._delayed_click(self.selectors["recovery_skip_btn"])
        except:
            pass

        try:
            # * Final Check
            self.page.wait_for_selector(self.selectors["main_landmark"], timeout=30000)
        except PlaywrightTimeoutError:
             raise AuthenticationError("Login timed out. OTP or 2FA might be required.")

    # --- Private Prompt Helpers ---

    def _inject_prompt_text(self, prompt: str):
        # * Directly manipulate DOM to bypass complex editor events
        logger.info("Injecting prompt via JS...")
        
        textarea_loc = self.page.locator(self.selectors["textarea"])
        expect(textarea_loc).to_be_visible()
        textarea_handle = textarea_loc.element_handle()
        
        self.page.evaluate(
            """
            ({ element, text }) => {
                element.value = text;
                element.dispatchEvent(new Event('input', { bubbles: true }));
            }
            """,
            { 'element': textarea_handle, 'text': prompt }
        )

    def _click_run_button(self):
        run_btn = self.page.locator(self.selectors["run_button"])
        expect(run_btn).to_be_enabled()
        run_btn.click()

    def _wait_for_completion(self):
        run_selector = self.selectors["run_button"]
        
        # 1. Wait for processing to start.
        # The "Run" button should disappear or change its label (e.g. to "Stop" or "Cancel").
        # We wait for the specific 'Run' labeled button to be hidden/detached.
        try:
            self.page.wait_for_selector(run_selector, state="hidden", timeout=10000)
        except PlaywrightTimeoutError:
            logger.warning("Run button did not disappear. Generation might not have started or UI state is ambiguous.")

        # 2. Wait for processing to end.
        # The "Run" button must reappear (visible).
        # ! CRITICAL: We DO NOT check if it is enabled. Empty input means it remains disabled.
        try:
            self.page.wait_for_selector(run_selector, state="visible", timeout=120000)
            logger.info("Generation finished.")
        except PlaywrightTimeoutError:
            raise PromptError("Timeout waiting for response generation (Run button did not reappear).")

    def _extract_via_clipboard(self) -> str:
        self.handle_dialogs()
        logger.info("Extracting response via clipboard...")
        
        response_blocks = self.page.locator(self.selectors["response_block"])
        last_block = response_blocks.last
        expect(last_block).to_be_visible()
        
        # * Hover to reveal 'More Options'
        last_block.hover()
        self.page.wait_for_timeout(500)
        
        more_opts = last_block.locator(self.selectors["more_options_btn"])
        more_opts.click()
        
        copy_btn = self.page.locator(self.selectors["copy_menu_item"]).last
        copy_btn.click()
        
        clipboard_text = self.page.evaluate("async () => await navigator.clipboard.readText()")
        return clipboard_text.strip() if clipboard_text else ""