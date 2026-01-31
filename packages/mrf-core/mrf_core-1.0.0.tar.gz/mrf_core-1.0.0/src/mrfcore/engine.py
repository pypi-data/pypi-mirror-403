from .state import ReasoningState
from .phases import validate_phase, next_phase
from .operators import OperatorRegistry

class MRFCcoreEngine:
    def __init__(self, enforce_phases=True):
        self.enforce_phases = enforce_phases

    def run_chain(self, operators, text):
        state = ReasoningState(text=text)
        
        for op_name, params in operators:
            if self.enforce_phases:
                violation = validate_phase(op_name, state.phase)
                if violation:
                    state.log_violation(violation)
                    continue
            
            operator_fn = OperatorRegistry.get(op_name)
            state = operator_fn(state, params)
            state.advance_phase(op_name)
        
        return state.finalize()
