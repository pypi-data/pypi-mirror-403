from .sandbox_client import InstaVM, VMDetail
from .result import ExecutionResult, make_execution_result
from .exceptions import (
    InstaVMError,
    AuthenticationError,
    SessionError,
    ExecutionError,
    NetworkError,
    RateLimitError,
    BrowserError,
    BrowserSessionError,
    BrowserInteractionError,
    BrowserTimeoutError,
    BrowserNavigationError,
    ElementNotFoundError,
    QuotaExceededError,
    UnsupportedOperationError
)

# LLM integrations - optional imports
__all__ = [
    "InstaVM",
    "VMDetail",
    "ExecutionResult",
    "make_execution_result",
    "InstaVMError",
    "AuthenticationError",
    "SessionError",
    "ExecutionError",
    "NetworkError",
    "RateLimitError",
    "BrowserError",
    "BrowserSessionError",
    "BrowserInteractionError",
    "BrowserTimeoutError",
    "BrowserNavigationError",
    "ElementNotFoundError",
    "QuotaExceededError",
    "UnsupportedOperationError"
]
