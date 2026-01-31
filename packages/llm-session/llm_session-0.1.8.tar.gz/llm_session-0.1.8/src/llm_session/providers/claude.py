import time
import logging
from typing import Optional, Callable
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect
from .base import LLMProvider
from ..exceptions import AuthenticationError, PromptError

logger = logging.getLogger(__name__)

class ClaudeProvider(LLMProvider):
    # * Claude.ai (Anthropic) implementation.
    # * Handles specific popup-based Google Auth flow and heavy DOM hydration checks.

    URL = "https://claude.ai/new"

    DEFAULT_SELECTORS = {
        # * Auth / Landing
        "login_google_btn": 'button[data-testid="login-with-google"]',
        "user_menu_btn": 'button[data-testid="user-menu-button"]', 
        
        # * Google Auth Flow (Inside Popup)
        "email_input": 'input[type="email"]',
        "email_next": 'button:has-text("Next")',
        "password_input": 'input[type="password"]',
        "password_next": 'button:has-text("Next")',
        "account_tile_base": 'div[role="link"][data-identifier]',
        "google_continue_btn": 'button:has-text("Continue")',
        
        # * Google Interstitials
        "passkey_not_now": 'button:has-text("Not now")',
        "recovery_cancel_btn": 'button[aria-label="Cancel"]',
        "recovery_skip_btn": 'button:has-text("Skip")',
        
        # * Chat Interface
        "chat_input": 'div[contenteditable="true"][data-testid="chat-input"]',
        "send_btn": 'button[aria-label="Send message"]',
        
        # * State Indicators
        "stop_btn": 'button[aria-label="Stop response"]', 
        
        # * Response Extraction
        "copy_btn": 'button[data-testid="action-bar-copy"]',
    }

    def __init__(self, page: Page, config: Optional[dict] = None, on_otp_required: Optional[Callable[[], str]] = None):
        super().__init__(page)
        self.config = config or {}
        self.on_otp_required = on_otp_required
        self.selectors = self.DEFAULT_SELECTORS.copy()
        
        if "selectors" in self.config:
            self.selectors.update(self.config["selectors"])
            
        # * Point this to chat_input so Automator knows we aren't ready until input is visible
        self.SEL_PROFILE_BTN = self.selectors["chat_input"]

    def login(self, credentials: dict) -> bool:
        logger.info("Starting Claude login process...")
        email = credentials.get("email")
        password = credentials.get("password")

        # 1. Navigate
        try:
            self.page.goto(self.URL, wait_until="domcontentloaded")
        except:
            pass 

        # 2. Check if already ready
        if self.is_fully_ready():
            logger.info("Already logged in and ready.")
            return True

        # 3. Check for Login Button
        if self.page.is_visible(self.selectors["login_google_btn"]):
            return self._perform_google_login(email, password)

        # 4. Check for Sidebar (Ghost Session)
        if self.page.is_visible(self.selectors["user_menu_btn"]):
            logger.info("Sidebar detected. Waiting for Chat Input...")
            if self._wait_for_chat_input_safe(timeout=10000):
                return True
            
            # ? Stalled session? Reloading helps hydration.
            logger.warning("Chat input stalled. Reloading...")
            self.page.reload()
            if self._wait_for_chat_input_safe(timeout=20000):
                return True
        
        # 5. Fallback Wait
        try:
            self.page.wait_for_selector(self.selectors["login_google_btn"], timeout=5000)
            return self._perform_google_login(email, password)
        except:
            raise AuthenticationError("Could not find Login button and Chat Input is missing.")

    def send_prompt(self, prompt: str) -> str:
        if not self.is_fully_ready():
            logger.warning("Chat input not ready. Waiting...")
            if not self._wait_for_chat_input_safe(timeout=10000):
                raise PromptError("Chat input missing. Cannot send prompt.")

        self.handle_dialogs()
        
        try:
            self._type_and_send(prompt)
        except Exception as e:
            raise PromptError(f"Failed to send prompt: {e}")

        logger.info("Waiting for response generation...")
        self._wait_for_response_completion()

        try:
            return self._extract_response_text()
        except Exception as e:
            raise PromptError(f"Failed to extract response: {e}")

    def is_fully_ready(self) -> bool:
        # * Check if chat input is visible.
        return self.page.is_visible(self.selectors["chat_input"])

    def handle_dialogs(self):
        try:
            # * Common "Next" / "Done" / "Dismiss" modals in Claude
            for btn_text in ["Next", "Done", "Dismiss", "Get started"]:
                selector = f"div[role='dialog'] button:has-text('{btn_text}')"
                if self.page.is_visible(selector):
                    self._delayed_click(selector)
        except:
            pass

    # --- Private Login Helpers ---

    def _perform_google_login(self, email, password):
        logger.info("Clicking 'Continue with Google' and waiting for popup...")
        
        try:
            # * Catch the popup window
            with self.page.expect_popup() as popup_info:
                self._delayed_click(self.selectors["login_google_btn"])
            
            popup = popup_info.value
            logger.info("Google Popup opened.")
            popup.wait_for_load_state("domcontentloaded")
            
            self._handle_google_popup(popup, email, password)
            
            # * Back to main page
            logger.info("Waiting for Claude Dashboard...")
            if self._wait_for_chat_input_safe(timeout=30000):
                logger.info("Login successful.")
                return True
            else:
                raise AuthenticationError("Popup closed but Claude did not load.")

        except Exception as e:
            raise AuthenticationError(f"Google Login Flow failed: {e}")

    def _handle_google_popup(self, popup, email, password):
        # * Logic to navigate inside the Google Auth Popup
        account_selector = f'div[role="link"][data-identifier="{email}"]'
        
        try:
            popup.wait_for_selector(f'{self.selectors["email_input"]}, {account_selector}', timeout=10000)
            
            if popup.locator(account_selector).is_visible():
                # * Case A: Account Tile exists
                logger.info(f"Found account tile for {email}. Clicking...")
                self._delayed_click(account_selector, page=popup)
                self._click_google_continue_if_present(popup)
            else:
                # * Case B: Manual Entry
                logger.info("Entering Email in popup...")
                popup.fill(self.selectors["email_input"], email)
                self._delayed_click(self.selectors["email_next"], page=popup)
                
                if password:
                    self._enter_password_in_popup(popup, password)
            
            # * Handle Passkey Enrollment Speedbump
            try:
                popup.wait_for_selector(self.selectors["passkey_not_now"], timeout=5000)
                logger.info("Passkey enrollment detected in popup. Dismissing...")
                self._delayed_click(self.selectors["passkey_not_now"], page=popup)
            except:
                pass

            # * Handle Recovery Options Update
            try:
                popup.wait_for_selector(self.selectors["recovery_cancel_btn"], timeout=5000)
                logger.info("Recovery options detected. Clicking Cancel...")
                self._delayed_click(self.selectors["recovery_cancel_btn"], page=popup)
            except:
                pass

            # * Handle "Recovery Info" Page (new screen identified)
            try:
                popup.wait_for_selector(self.selectors["recovery_skip_btn"], timeout=5000)
                logger.info("Recovery info page detected in popup. Clicking Skip...")
                self._delayed_click(self.selectors["recovery_skip_btn"], page=popup)
            except:
                pass

        except Exception as e:
            logger.error(f"Error inside Google Popup: {e}")
            # * User might be manually solving 2FA. Don't crash.
        
        self._wait_for_popup_close(popup)

    def _enter_password_in_popup(self, popup, password):
        try:
            popup.wait_for_selector(self.selectors["password_input"], state="visible", timeout=5000)
            logger.info("Entering Password...")
            popup.fill(self.selectors["password_input"], password)
            self._delayed_click(self.selectors["password_next"], page=popup)
        except:
            logger.info("Password field did not appear (possibly 2FA or passkey).")

    def _click_google_continue_if_present(self, popup):
        try:
            popup.wait_for_selector(self.selectors["google_continue_btn"], timeout=3000)
            self._delayed_click(self.selectors["google_continue_btn"], page=popup)
        except: 
            pass

    def _wait_for_popup_close(self, popup):
        logger.info("Waiting for popup to close (User should complete login)...")
        try:
            # * Long timeout for manual 2FA
            popup.wait_for_event("close", timeout=60000)
        except:
            logger.warning("Popup did not close automatically.")

    def _wait_for_chat_input_safe(self, timeout=30000) -> bool:
        start_time = time.time()
        while (time.time() - start_time) * 1000 < timeout:
            self.handle_dialogs()
            if self.page.is_visible(self.selectors["chat_input"]):
                return True
            time.sleep(1)
        return False

    # --- Private Prompt Helpers ---

    def _type_and_send(self, prompt: str):
        logger.info("Entering prompt...")
        input_loc = self.page.locator(self.selectors["chat_input"])
        input_loc.click()
        self.page.keyboard.type(prompt)
        
        logger.info("Clicking send...")
        send_btn = self.page.locator(self.selectors["send_btn"])
        expect(send_btn).not_to_be_disabled()
        send_btn.click()

    def _wait_for_response_completion(self):
        try:
            self.page.wait_for_selector(self.selectors["stop_btn"], timeout=10000)
            self.page.wait_for_selector(self.selectors["stop_btn"], state="hidden", timeout=120000)
        except PlaywrightTimeoutError:
            if not self.page.is_visible(f'{self.selectors["send_btn"]}:not([disabled])'):
                 raise PromptError("Timeout waiting for response generation.")

    def _extract_response_text(self) -> str:
        logger.info("Extracting response...")
        copy_btns = self.page.locator(self.selectors["copy_btn"])
        self.page.wait_for_timeout(1000)
        
        if copy_btns.count() > 0:
            copy_btns.last.click()
            text = self.page.evaluate("async () => await navigator.clipboard.readText()")
            if text: return text.strip()
        
        msgs = self.page.locator(".font-claude-message")
        if msgs.count() > 0:
            return msgs.last.inner_text()
            
        return ""