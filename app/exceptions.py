"""Application exceptions shared without importing heavyweight pipelines."""


class IngestionCancelledError(Exception):
    """Raised after an ingestion cancellation signal is observed."""
