PRESETS = {
    "default": [
        "Transform",
        "Summarize",
        "Reflect",
        "Evaluate",
    ],
    "analysis": [
        "Transform",
        "Inspect",
        "Evaluate",
        "Summarize",
    ],
    "creative": [
        "Transform",
        "Rewrite",
        "Reflect",
        "Summarize",
    ],
    "safety_filter": [
        "Transform",
        "Filter",
        "Summarize",
    ]
}


def get_preset(name: str):
    """Retrieve a preset operator sequence."""
    if name not in PRESETS:
        raise KeyError(f"Preset '{name}' not found.")
    return PRESETS[name]
