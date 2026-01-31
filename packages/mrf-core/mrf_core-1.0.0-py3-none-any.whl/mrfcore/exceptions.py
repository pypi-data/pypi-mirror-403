class MRFError(Exception):
    """Base class for all MRF-related errors."""
    pass


class OperatorNotFound(MRFError):
    """Raised when a pipeline references an operator that does not exist."""
    def __init__(self, operator_name):
        super().__init__(f"Operator not found: {operator_name}")
        self.operator_name = operator_name


class OperatorExecutionError(MRFError):
    """Raised when an operator fails internally."""
    def __init__(self, operator_name, original_exception):
        super().__init__(f"Operator '{operator_name}' failed: {str(original_exception)}")
        self.operator_name = operator_name
        self.original_exception = original_exception


class InvalidPipelineConfig(MRFError):
    """Raised when a pipeline config is malformed or incomplete."""
    pass


class DiagnosticsWarning(MRFError):
    """Non-fatal diagnostic issue detected."""
    pass
