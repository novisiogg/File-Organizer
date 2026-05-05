class InvalidFolderError(Exception):
    """Checks for non-existent folders."""

    def __init__(self, message, foldername):
        super().__init__(message)
        self.message = message
        self.foldername = foldername

    def __str__(self):
        return f"{self.message}: '{self.foldername}'"


class ProtectedSystemFolder(InvalidFolderError):
    """Checks for system-protected folders. (System32, Windows, etc..)"""

    def __init__(self, message, foldername):
        super().__init__(message)
        self.message = message
        self.foldername = foldername

    def __str__(self):
        return f"{self.message}: '{self.foldername}'"
