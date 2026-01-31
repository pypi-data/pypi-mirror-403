from .exceptions import DiagnosticsWarning

class MRFDiagnostics:
    """Diagnostic engine for checking pipeline health, operator behavior,
    and state consistency."""

    def __init__(self, pipeline):
        self.pipeline = pipeline

    def check_operator_registry(self):
        """Verify all operators are importable and named correctly."""
        missing = []
        for op_name in self.pipeline.operators:
            if op_name not in self.pipeline.operator_registry:
                missing.append(op_name)

        if missing:
            raise DiagnosticsWarning(
                f"Unregistered operators detected: {missing}"
            )

        return True

    def check_pipeline_integrity(self):
        """Ensure pipeline has valid structure."""
        if not self.pipeline.operators:
            raise DiagnosticsWarning("Pipeline has no operators.")

        # Check for duplicate operators unless explicitly allowed
        if len(self.pipeline.operators) != len(set(self.pipeline.operators)):
            raise DiagnosticsWarning("Duplicate operators in pipeline.")

        return True

    def check_state(self, state):
        """Ensure state object remains internally consistent."""
        if state.text is None:
            raise DiagnosticsWarning("State text is None.")

        if not isinstance(state.history, list):
            raise DiagnosticsWarning("State history corrupted.")

        return True

    def run_full_diagnostics(self, state=None):
        """Perform all diagnostics checks at once."""
        results = {
            "registry": self.check_operator_registry(),
            "pipeline_integrity": self.check_pipeline_integrity(),
        }

        if state:
            results["state"] = self.check_state(state)

        return results
