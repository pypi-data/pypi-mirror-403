"""
velmu.errors
~~~~~~~~~~~~

Exception classes for Velmu SDK.
"""

class VelmuException(Exception):
    """Base exception class for all Velmu exceptions."""
    pass

class ClientException(VelmuException):
    """Exception that occurs from the client side."""
    pass

class LoginFailure(ClientException):
    """Exception that occurs when the client fails to log in."""
    pass

class GatewayError(VelmuException):
    """Exception that occurs from the Gateway (WebSocket)."""
    def __init__(self, code=None, message=None, missing_intents=None):
        self.code = code
        self.message = message
        self.missing_intents = missing_intents
        
        fmt = f"Gateway Error {code}: {message}"
        if missing_intents:
            fmt += f" (Missing Intents: {', '.join(missing_intents)})"
        super().__init__(fmt)

class HTTPException(VelmuException):
    """Exception that occurs when an HTTP request fails."""
    def __init__(self, response, message):
        self.response = response
        self.status = response.status
        self.text = message
        if isinstance(message, dict):
            self.text = message.get('message', str(message))
            self.code = message.get('code', 0)
        else:
            self.code = 0
            
        super().__init__(f"{self.status} {self.response.reason}: {self.text}")

class Forbidden(HTTPException):
    """Exception that occurs when the client is forbidden (403)."""
    pass

class NotFound(HTTPException):
    """Exception that occurs when a resource is not found (404)."""
    pass

class VelmuServerError(HTTPException):
    """Exception that occurs when the server returns a 500 error."""
    pass

class RateLimited(HTTPException):
    """Exception that occurs when the client is rate limited (429)."""
    def __init__(self, response, data):
        self.retry_after = data.get('retry_after', 0)
        super().__init__(response, f"Rate limited. Retry in {self.retry_after}s")

# --- Command Errors ---

class CommandError(VelmuException):
    """Base class for command errors."""
    pass

class CheckFailure(CommandError):
    """Exception raised when a check fails."""
    pass

class CommandNotFound(CommandError):
    """Exception raised when a command is not found."""
    pass

class MissingRequiredArgument(CommandError):
    """Exception raised when a required argument is missing."""
    def __init__(self, param):
        self.param = param
        super().__init__(f'{param.name} is a required argument that is missing.')

class BadArgument(CommandError):
    """Exception raised when a bad argument is passed."""
    pass

class CommandOnCooldown(CommandError):
    """Exception raised when the command is on cooldown."""
    def __init__(self, retry_after):
        self.retry_after = retry_after
        super().__init__(f"You are on cooldown. Try again in {retry_after:.2f}s")
