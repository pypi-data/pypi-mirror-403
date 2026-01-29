class RedenvError(Exception):
    """Base exception for Redenv."""
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(f"[{code}] {message}")
