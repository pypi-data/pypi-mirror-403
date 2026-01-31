from .base import BaseOperator

class Filter(BaseOperator):
    name = "Filter"

    @staticmethod
    def run(state, params):
        text = state.text

        banned_words = params.get("banned", [])
        filtered = text

        for b in banned_words:
            filtered = filtered.replace(b, "[FILTERED]")

        state.update_text(filtered)
        state.add_history(Filter.name)
        state.write(f"Filter → removed: {banned_words}")

        return state
