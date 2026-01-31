import os
import sys
from pathlib import Path
from typing import Optional, List
from playwright.sync_api import sync_playwright, BrowserContext, Page, Playwright
import appdirs

from .exceptions import SetupError

class BrowserManager:
    # * Manages the Playwright browser instance and persistent context.
    # * Ensures user data is stored correctly across sessions.

    # * Chromium arguments to reduce bot detection flags.
    _BROWSER_ARGS: List[str] = [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-infobars",
        "--exclude-switches=enable-automation",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding"
    ]

    def __init__(self, app_name: str = "LLMSession"):
        self.default_user_data_dir = Path(appdirs.user_data_dir(app_name, appauthor=False))
        self.playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def start(self, headless: bool = True, session_path: Optional[str] = None) -> Page:
        # * Main entry point to launch the browser environment.
        
        user_data_dir = self._resolve_user_data_path(session_path)
        self._initialize_playwright()
        self._launch_persistent_context(user_data_dir, headless)
        
        return self._get_active_page()

    def stop(self):
        # * Teardown resources to prevent zombie processes.
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()

    def is_authenticated(self, check_url: str, check_selector: str) -> bool:
        # * Verifies if the session cookies are valid by checking for a known UI element.
        
        if not self.page:
            # ! CRITICAL: Browser must be started before checking auth.
            raise SetupError("Browser not started.")
            
        try:
            self.page.goto(check_url, wait_until="domcontentloaded")
            try:
                # ? Is 5000ms enough for slow connections?
                self.page.wait_for_selector(check_selector, timeout=5000)
                return True
            except Exception:
                # * Timeout or selector missing implies not logged in.
                return False
        except Exception as e:
            # ! CRITICAL: Navigation failed entirely (network issue?).
            return False

    def save_session(self, path: str):
        # * Manually dumps storage state (cookies/local storage) to a file.
        if self.context:
            try:
                self.context.storage_state(path=path)
            except Exception:
                # ? Log this failure? logic kept from original.
                pass

    # --- Private Helpers ---

    def _resolve_user_data_path(self, session_path: Optional[str]) -> Path:
        target_path = Path(session_path) if session_path else self.default_user_data_dir
        
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            
        return target_path

    def _initialize_playwright(self):
        try:
            self.playwright = sync_playwright().start()
        except Exception as e:
            # ! CRITICAL: Playwright binary might be missing.
            raise SetupError(f"Failed to start Playwright. Make sure it is installed: {e}")

    def _launch_persistent_context(self, user_data_dir: Path, headless: bool):
        try:
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                headless=headless,
                args=self._BROWSER_ARGS
            )
        except Exception as e:
            raise SetupError(f"Failed to launch browser: {e}")

    def _get_active_page(self) -> Page:
        # * Returns the existing page or creates a new one if context is empty.
        if len(self.context.pages) > 0:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()
        return self.page