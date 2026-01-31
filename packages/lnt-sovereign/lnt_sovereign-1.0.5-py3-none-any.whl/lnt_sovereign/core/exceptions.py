class LNTError(Exception):
    """Base exception for all LNT-related errors."""
    pass

class LogicError(LNTError):
    """Base class for errors in logic evaluation."""
    pass

class ManifestError(LNTError):
    """Raised when there is an issue with a domain manifest."""
    pass

class ManifestValidationError(ManifestError):
    """Raised when a manifest fails schema or logical validation."""
    pass

class ManifestContradictionError(ManifestValidationError):
    """Raised when Z3 detects a mathematical contradiction in a manifest."""
    pass

class EvaluationError(LogicError):
    """Raised during the evaluation of a proposal against a manifest."""
    pass

class TypeMismatchError(EvaluationError):
    """Raised when input data types do not match manifest expectations."""
    pass

class PerformanceThresholdError(LNTError):
    """Raised when evaluation latency exceeds defined SLAs."""
    pass
