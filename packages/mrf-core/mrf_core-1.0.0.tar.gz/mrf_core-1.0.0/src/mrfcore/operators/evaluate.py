from .base import BaseOperator

class Evaluate(BaseOperator):
    name = "Evaluate"

    @staticmethod
    def run(state, params):
        text = state.text

        # dumb heuristic: count sentences
        score = text.count(".") + text.count("!") + text.count("?")
        evaluation = f"Evaluation(score={score}): {text}"

        state.update_text(evaluation)
        state.add_history(Evaluate.name)
        state.write("Evaluate → heuristic scoring applied")

        return state
