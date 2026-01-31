import time
import os
import logging
from typing import Optional, Callable
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from .base import LLMProvider
from ..exceptions import AuthenticationError, SelectorError, PromptError, OTPRequiredError

logger = logging.getLogger(__name__)

class ChatGPTProvider(LLMProvider):
    # * Implementation for ChatGPT (OpenAI).
    # * Handles both standard Email/Password and Google OAuth flows.

    URL = "https://chatgpt.com/?temporary-chat=true"
    
    # * UI Selectors configuration
    DEFAULT_SELECTORS = {
        # * Login Flow
        "landing_login_btn": '[data-testid="login-button"]',
        "login_google_btn": 'button:has-text("Continue with Google")',
        "email_input": '#email',
        "email_continue_btn": 'button[type="submit"]',
        "password_input": 'input[name="password"]', 
        "password_continue_btn": 'button[type="submit"]',

        # * Google Interstitials
        "passkey_not_now": 'button:has-text("Not now")',
        "recovery_cancel_btn": 'button[aria-label="Cancel"]', 
        "recovery_skip_btn": 'button:has-text("Skip")',
        
        # * Session Indicators
        "profile_btn": '[data-testid="accounts-profile-button"]',
        
        # * Chat Interface
        "textarea": '#prompt-textarea',
        "send_btn": 'button[data-testid="send-button"]',
        "stop_btn": 'button[data-testid="stop-button"]',
        "assistant_msg": 'div[data-message-author-role="assistant"]',
        
        # * Modals / Popups
        "upsell_maybe_later": 'button:has-text("Maybe later")',
        "temp_chat_continue": 'button:has-text("Continue")',
        "upsell_modal": '[data-testid="modal-no-auth-free-trial-upsell"]',
        
        # * OTP / 2FA
        "otp_input": 'input[name="code"]',
        "otp_validate": 'button[type="submit"]'
    }

    def __init__(self, page: Page, config: Optional[dict] = None, on_otp_required: Optional[Callable[[], str]] = None):
        super().__init__(page)
        self.config = config or {}
        self.on_otp_required = on_otp_required
        self.selectors = self.DEFAULT_SELECTORS.copy()
        
        if "selectors" in self.config:
            self.selectors.update(self.config["selectors"])
            
        # * Public properties for external checks
        self.SEL_PROFILE_BTN = self.selectors["profile_btn"]

    def login(self, credentials: dict) -> bool:
        # * Orchestrates the login process.
        logger.info("Starting login process...")
        
        try:
            self.page.goto(self.URL)
            self.handle_dialogs()
            
            if self._is_already_logged_in():
                logger.info("Already logged in.")
                return True

            self._initiate_login_flow()
            
            email = credentials.get("email")
            password = credentials.get("password")
            method = credentials.get("method", "email")

            if not email or not password:
                raise AuthenticationError("Email and password are required.")

            if method == "google":
                self._perform_google_login(email, password)
            else:
                self._perform_email_login(email, password)
            
            return self._wait_for_auth_completion()

        except Exception as e:
            self._handle_login_failure(e)
            # ! CRITICAL: Logic dictates we re-raise to inform the automator.
            if isinstance(e, (AuthenticationError, SelectorError, OTPRequiredError)):
                raise
            raise AuthenticationError(f"Login failed: {e}")

    def send_prompt(self, prompt: str) -> str:
        # * Sends a message to the chat and retrieves the result.
        
        self.handle_dialogs()
        
        try:
            self._enter_prompt(prompt)
            self._click_send()
        except Exception as e:
            raise PromptError(f"Failed to send prompt: {e}")

        logger.info("Waiting for response...")
        self._wait_for_generation()

        try:
            return self._extract_last_response()
        except Exception as e:
            raise PromptError(f"Failed to extract response: {e}")

    def handle_dialogs(self):
        # * Dismisses "Try Go" upsell and "Temporary Chat" notices.
        self._dismiss_upsell_modal()
        self._dismiss_temp_chat_notice()

    # --- Private Helper Methods (Login) ---

    def _is_already_logged_in(self) -> bool:
        try:
            self.page.wait_for_selector(self.selectors["profile_btn"], timeout=3000)
            return True
        except:
            return False

    def _initiate_login_flow(self):
        try:
            logger.info("Clicking 'Log in' from landing page...")
            self.page.click(self.selectors["landing_login_btn"])
        except Exception as e:
            raise SelectorError(f"Could not find Login button on landing page: {e}")

    def _perform_google_login(self, email, password):
        logger.info("Logging in via Google...")
        self.page.wait_for_selector(self.selectors["login_google_btn"])
        self.page.click(self.selectors["login_google_btn"])
        
        # * Google Email Step
        logger.info("Entering Google email...")
        self.page.wait_for_selector('input[type="email"]')
        self.page.fill('input[type="email"]', email)
        self.page.click('button:has-text("Next")')
        
        # * Google Password Step
        logger.info("Entering Google password...")
        self.page.wait_for_selector('input[type="password"]', state="visible")
        self.page.fill('input[type="password"]', password)
        self.page.click('button:has-text("Next")')
        
        # * Handle "Passkey Enrollment" Speedbump
        try:
            self.page.wait_for_selector(self.selectors["passkey_not_now"], timeout=5000)
            logger.info("Passkey enrollment detected. Dismissing...")
            self.page.click(self.selectors["passkey_not_now"])
        except:
            pass

        # * Handle "Recovery Options" Speedbump (The new case)
        try:
            self.page.wait_for_selector(self.selectors["recovery_cancel_btn"], timeout=5000)
            logger.info("Recovery options update detected. Clicking Cancel...")
            self.page.click(self.selectors["recovery_cancel_btn"])
        except:
            pass

        # * Handle "Recovery Info" Page (new screen identified)
        try:
            self.page.wait_for_selector(self.selectors["recovery_skip_btn"], timeout=5000)
            logger.info("Recovery info page detected. Clicking Skip...")
            self.page.click(self.selectors["recovery_skip_btn"])
        except:
            pass

    def _perform_email_login(self, email, password):
        logger.info("Entering email...")
        self.page.wait_for_selector(self.selectors["email_input"])
        self.page.fill(self.selectors["email_input"], email)
        self.page.click(self.selectors["email_continue_btn"])
        
        logger.info("Entering password...")
        self.page.wait_for_selector(self.selectors["password_input"])
        self.page.fill(self.selectors["password_input"], password)
        self.page.click(self.selectors["password_continue_btn"])

    def _wait_for_auth_completion(self) -> bool:
        logger.info("Waiting for authentication or OTP...")
        
        # * Polling loop for 30 seconds
        for _ in range(30):
            if self.page.is_visible(self.selectors["profile_btn"]):
                logger.info("Login successful.")
                return True
            
            if self.page.is_visible(self.selectors["otp_input"]):
                self._handle_otp_challenge()
                return True
            
            time.sleep(1)
        
        raise TimeoutError("Login timed out.")

    def _handle_otp_challenge(self):
        logger.warning("OTP verification required.")
        if not self.on_otp_required:
            raise OTPRequiredError("OTP required but no callback provided.")
        
        otp_code = self.on_otp_required()
        self.page.fill(self.selectors["otp_input"], otp_code)
        self.page.click(self.selectors["otp_validate"])
        
        logger.info("OTP submitted. Waiting for authentication...")
        self.page.wait_for_selector(self.selectors["profile_btn"], timeout=30000)
        logger.info("Login successful.")

    def _handle_login_failure(self, error: Exception):
        # * Takes a screenshot for debugging in headless environments.
        screenshot_path = "/app/output/login_failure.png" if os.path.exists("/app/output") else "login_failure.png"
        logger.error(f"Login failed: {error}")
        logger.info(f"Taking screenshot: {screenshot_path}")
        self.page.screenshot(path=screenshot_path)

    # --- Private Helper Methods (Prompting) ---

    def _enter_prompt(self, prompt: str):
        self.page.wait_for_selector(self.selectors["textarea"])
        self.page.fill(self.selectors["textarea"], prompt)

    def _click_send(self):
        self.page.wait_for_selector(self.selectors["send_btn"])
        if self.page.is_disabled(self.selectors["send_btn"]):
            # ? Small wait for UI state update?
            self.page.wait_for_timeout(500)
        self.page.click(self.selectors["send_btn"])

    def _wait_for_generation(self):
        try:
            # * Wait for Stop button (generation active)
            self.page.wait_for_selector(self.selectors["stop_btn"], timeout=5000)
            # * Wait for Stop button to vanish (generation complete)
            self.page.wait_for_selector(self.selectors["stop_btn"], state="hidden", timeout=120000)
        except PlaywrightTimeoutError:
            # * If stop button never appeared, ensure send button is back.
            if not self.page.is_visible(self.selectors["send_btn"]):
                raise PromptError("Timeout waiting for response generation.")

    def _extract_last_response(self) -> str:
        self.page.wait_for_selector(self.selectors["assistant_msg"], timeout=5000)
        assistant_msgs = self.page.query_selector_all(self.selectors["assistant_msg"])
        
        if not assistant_msgs:
            raise SelectorError("No assistant messages found.")
        
        last_msg = assistant_msgs[-1]
        
        # * Prefer markdown content if available
        markdown_div = last_msg.query_selector('.markdown')
        if markdown_div:
            return markdown_div.inner_text()
        return last_msg.inner_text()

    # --- Private Helper Methods (Dialogs) ---

    def _dismiss_upsell_modal(self):
        try:
            # * Wait briefly for modal
            self.page.wait_for_selector(self.selectors["upsell_modal"], timeout=5000, state="visible")
            logger.info("Upsell modal detected, dismissing...")
            self.page.click(self.selectors["upsell_maybe_later"])
            self.page.wait_for_selector(self.selectors["upsell_modal"], timeout=5000, state="hidden")
            self.page.wait_for_timeout(500)
        except Exception:
            # * No modal found, proceed.
            pass

    def _dismiss_temp_chat_notice(self):
        try:
            if self.page.is_visible('h2:has-text("Temporary Chat")'):
                self.page.click(self.selectors["temp_chat_continue"])
                self.page.wait_for_timeout(500)
        except:
            pass