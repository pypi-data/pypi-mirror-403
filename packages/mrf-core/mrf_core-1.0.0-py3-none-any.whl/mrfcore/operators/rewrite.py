from .base import BaseOperator

class Rewrite(BaseOperator):
    name = "Rewrite"

    @staticmethod
    def run(state, params):
        text = state.text

        prefix = params.get("prefix", "")
        suffix = params.get("suffix", "")

        rewritten = f"{prefix}{text}{suffix}"

        state.update_text(rewritten)
        state.add_history(Rewrite.name)
        state.write("Rewrite → applied prefix/suffix")

        return state
