class LLMAutomatorError(Exception):
    # * Base exception class for the LLM Automator package.
    pass

class SetupError(LLMAutomatorError):
    # ! CRITICAL: Raised when the environment or browser cannot be initialized.
    pass

class AuthenticationError(LLMAutomatorError):
    # * Raised when the login flow fails (wrong credentials, timeout, or detection).
    pass

class PromptError(LLMAutomatorError):
    # * Raised when sending a message or retrieving a response fails.
    pass

class SelectorError(LLMAutomatorError):
    # ? Should we merge this with PromptError? keeping separate for DOM debugging.
    # * Raised when a specific DOM element cannot be found on the page.
    pass

class OTPRequiredError(LLMAutomatorError):
    # * Raised when 2FA is triggered but no callback handler was provided.
    pass