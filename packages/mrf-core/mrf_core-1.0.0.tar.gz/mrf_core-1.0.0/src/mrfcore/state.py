from dataclasses import dataclass, field

@dataclass
class ReasoningState:
    text: str
    log: list = field(default_factory=list)
    meta: dict = field(default_factory=lambda: {"history": []})
    phase: str = "initialize"

    def write(self, message):
        self.log.append(message)

    def update_text(self, new_text):
        self.text = new_text

    def add_history(self, operator):
        self.meta["history"].append(operator)

    def log_violation(self, violation):
        self.write(f"[VIOLATION] {violation}")

    def advance_phase(self, operator):
        from .phases import next_phase
        new_phase = next_phase(operator, self.phase)
        if new_phase != self.phase:
            self.write(f"[PHASE] {self.phase} → {new_phase}")
        self.phase = new_phase

    def finalize(self):
        return {
            "text": self.text,
            "meta": self.meta,
            "phase": self.phase,
            "log": self.log
        }
