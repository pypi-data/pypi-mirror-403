from .base import BaseOperator

class Summarize(BaseOperator):
    name = "Summarize"

    @staticmethod
    def run(state, params):
        text = state.text.strip()

        # Super crude fallback summary
        if len(text.split()) <= 12:
            summary = text
        else:
            words = text.split()
            summary = " ".join(words[:12]) + " …"

        state.update_text(summary)
        state.add_history(Summarize.name)
        state.write("Summarize → simple truncation summary")

        return state
