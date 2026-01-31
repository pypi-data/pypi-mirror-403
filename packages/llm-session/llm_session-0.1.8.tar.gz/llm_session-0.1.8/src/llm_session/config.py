import os
from typing import Optional, Dict

class Config:
    # * Configuration handler for LLM Automator.
    # * Centralizes environment variable reading and default credential mapping.

    @staticmethod
    def get_credentials(provider: str) -> Dict[str, Optional[str]]:
        # * Retrieves credentials based on the provider strategy.
        # * Currently standardizes around Google Auth for supported providers.
        
        provider_key = provider.lower()
        
        # * Fetch from environment
        email = os.environ.get("LLM_EMAIL")
        password = os.environ.get("LLM_PASSWORD")
        
        # ? Should we add specific env vars per provider (e.g. CLAUDE_EMAIL)?
        # * Current logic uses shared credentials for all providers.
        
        if provider_key in ["chatgpt", "aistudio", "claude"]:
            return {
                "email": email,
                "password": password,
                "method": "google"
            }
            
        return {}

    @staticmethod
    def is_headless_mode_enabled() -> bool:
        # * Determines if the browser should run without a UI.
        # * Defaults to True unless explicitly disabled via env var.
        return os.environ.get("LLM_AUTOMATOR_HEADLESS", "true").lower() == "true"