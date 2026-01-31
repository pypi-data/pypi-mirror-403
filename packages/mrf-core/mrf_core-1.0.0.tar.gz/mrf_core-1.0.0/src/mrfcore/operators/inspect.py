from .base import BaseOperator

class Inspect(BaseOperator):
    name = "Inspect"

    @staticmethod
    def run(state, params):
        text = state.text
        
        word_count = len(text.split())
        inspection = f"Inspection(words={word_count}): {text}"

        state.update_text(inspection)
        state.add_history(Inspect.name)
        state.write("Inspect → structural metadata added")

        return state
