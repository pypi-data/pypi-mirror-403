from .engine import MRFCcoreEngine

class MRFPipeline:
    def __init__(self, stages):
        self.stages = stages
        self.engine = MRFCcoreEngine(enforce_phases=True)

    def run(self, text):
        state = None
        for stage in self.stages:
            state = self.engine.run_chain(stage, text if state is None else state["text"])
        return state
