from typing import Optional


class SplitNowError(Exception):
    # Base exception for API errors
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
    
    def __repr__(self) -> str:
        if self.status_code:
            return f"{self.__class__.__name__}(message={self.message!r}, status_code={self.status_code})"
        return f"{self.__class__.__name__}(message={self.message!r})"


class SplitNowAuthError(SplitNowError):
    # Authentication error (401)
    pass


class SplitNowForbiddenError(SplitNowError):
    # Forbidden error (403)
    pass


class SplitNowNotFoundError(SplitNowError):
    # Not found error (404)
    pass


class SplitNowValidationError(SplitNowError):
    # Validation error (400/422)
    pass


class SplitNowRateLimitError(SplitNowError):
    # Rate limit error (429)
    pass


class SplitNowServerError(SplitNowError):
    # Server error (500)
    pass
