PHASE_PERMISSIONS = {
    "initialize": ["Transform", "Summarize"],
    "analyze": ["Reflect", "Evaluate"],
    "refine": ["Rewrite", "Inspect", "Filter"],
    "finalize": []
}

PHASE_TRANSITIONS = {
    "initialize": {"Transform": "analyze", "Summarize": "analyze"},
    "analyze": {"Reflect": "evaluate", "Evaluate": "refine"},
    "refine": {"Rewrite": "finalize", "Inspect": "finalize", "Filter": "finalize"},
    "finalize": {}
}

def validate_phase(operator, phase):
    allowed = PHASE_PERMISSIONS.get(phase, [])
    return None if operator in allowed else f"{operator} not allowed in phase {phase}"

def next_phase(operator, phase):
    return PHASE_TRANSITIONS.get(phase, {}).get(operator, phase)
