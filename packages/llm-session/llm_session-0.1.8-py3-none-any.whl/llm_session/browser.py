import os
import sys
import logging
from pathlib import Path
from typing import Optional, List
from playwright.sync_api import sync_playwright, BrowserContext, Page, Playwright
import appdirs

from .exceptions import SetupError

logger = logging.getLogger(__name__)

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
        logger.info(f"BrowserManager.__init__ starting (app_name={app_name})...")
        self.default_user_data_dir = Path(appdirs.user_data_dir(app_name, appauthor=False))
        logger.info(f"Default user data dir: {self.default_user_data_dir}")
        self.playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        logger.info("BrowserManager.__init__ completed")

    def start(self, headless: bool = True, session_path: Optional[str] = None) -> Page:
        # * Main entry point to launch the browser environment.
        logger.info(f"BrowserManager.start() called (headless={headless}, session_path={session_path})")

        logger.info("Resolving user data path...")
        user_data_dir = self._resolve_user_data_path(session_path)
        logger.info(f"User data path resolved: {user_data_dir}")

        logger.info("Initializing Playwright...")
        self._initialize_playwright()
        logger.info("Playwright initialized successfully")

        logger.info("Launching persistent context...")
        self._launch_persistent_context(user_data_dir, headless)
        logger.info("Persistent context launched successfully")

        logger.info("Getting active page...")
        page = self._get_active_page()
        logger.info(f"Active page obtained: {page is not None}")

        return page

    def stop(self):
        # * Teardown resources to prevent zombie processes.
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()

    def is_authenticated(self, check_url: str, check_selector: str) -> bool:
        # * Verifies if the session cookies are valid by checking for a known UI element.
        logger.info(f"is_authenticated called: url={check_url}, selector={check_selector}")

        if not self.page:
            # ! CRITICAL: Browser must be started before checking auth.
            logger.error("Browser not started - page is None")
            raise SetupError("Browser not started.")

        try:
            logger.info(f"Navigating to {check_url}...")
            self.page.goto(check_url, wait_until="domcontentloaded")
            logger.info("Navigation complete (domcontentloaded)")
            try:
                # ? Is 5000ms enough for slow connections?
                logger.info(f"Waiting for selector: {check_selector} (timeout=5000ms)...")
                self.page.wait_for_selector(check_selector, timeout=5000)
                logger.info("Selector found - user is authenticated")
                return True
            except Exception as e:
                # * Timeout or selector missing implies not logged in.
                logger.info(f"Selector not found (timeout/error): {e}")
                return False
        except Exception as e:
            # ! CRITICAL: Navigation failed entirely (network issue?).
            logger.error(f"Navigation failed: {e}")
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
        logger.info(f"Target path: {target_path}, exists: {target_path.exists()}")

        if not target_path.exists():
            logger.info(f"Creating directory: {target_path}")
            target_path.mkdir(parents=True, exist_ok=True)
            logger.info("Directory created")

        return target_path

    def _initialize_playwright(self):
        try:
            logger.info("Calling sync_playwright().start()...")
            self.playwright = sync_playwright().start()
            logger.info("sync_playwright().start() completed successfully")
        except Exception as e:
            # ! CRITICAL: Playwright binary might be missing.
            logger.error(f"Failed to start Playwright: {e}")
            raise SetupError(f"Failed to start Playwright. Make sure it is installed: {e}")

    def _launch_persistent_context(self, user_data_dir: Path, headless: bool):
        try:
            logger.info(f"Launching chromium persistent context...")
            logger.info(f"  user_data_dir: {user_data_dir}")
            logger.info(f"  headless: {headless}")
            logger.info(f"  args: {self._BROWSER_ARGS}")
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                headless=headless,
                args=self._BROWSER_ARGS
            )
            logger.info("Chromium persistent context launched successfully")
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            raise SetupError(f"Failed to launch browser: {e}")

    def _get_active_page(self) -> Page:
        # * Returns the existing page or creates a new one if context is empty.
        page_count = len(self.context.pages)
        logger.info(f"Context has {page_count} existing page(s)")

        if page_count > 0:
            logger.info("Using existing page from context")
            self.page = self.context.pages[0]
        else:
            logger.info("Creating new page in context...")
            self.page = self.context.new_page()
            logger.info("New page created")

        return self.page