class InputRejected(Exception):
    """The upload is not usable. `message` is shown to the user as is. Never charged."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class RunFailed(Exception):
    """Our side failed. Never charged, never uses the free run."""
