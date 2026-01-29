"""Custom exceptions for openapi-ts-client."""


class OutputDirectoryNotEmptyError(Exception):
    """Raised when output directory is not empty and neither clean nor force is set."""

    def __init__(self, path, file_count: int):
        self.path = path
        self.file_count = file_count
        super().__init__(
            f"Output directory '{path}' is not empty (contains {file_count} files). "
            f"Use clean=True to clear the directory first, or force=True to continue anyway."
        )
