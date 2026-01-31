"""Custom exceptions for the datawhisk library."""


class datawhiskError(Exception):
    """Base exception for all datawhisk errors."""

    pass


class ValidationError(datawhiskError):
    """Raised when input validation fails."""

    pass


class DataQualityError(datawhiskError):
    """Raised when data quality issues are detected."""

    pass


class OptimizationError(datawhiskError):
    """Raised when optimization operations fail."""

    pass


class AnalysisError(datawhiskError):
    """Raised when analysis operations fail."""

    pass


class InsufficientDataError(datawhiskError):
    """Raised when there is insufficient data for an operation."""

    pass
