"""Exception classes for HookPulse SDK"""


class HookPulseError(Exception):
    """Base exception for all HookPulse errors"""
    pass


class HookPulseAPIError(HookPulseError):
    """Exception raised when API returns an error response"""
    
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class HookPulseAuthError(HookPulseError):
    """Exception raised when authentication fails"""
    pass


class HookPulseValidationError(HookPulseError):
    """Exception raised when request validation fails"""
    pass
