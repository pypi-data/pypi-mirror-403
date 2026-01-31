from .base import BaseOperator

class Reflect(BaseOperator):
    name = "Reflect"

    @staticmethod
    def run(state, params):
        text = state.text

        question = params.get("question", "What is the core implication?")
        
        response = f"Reflection: {question} → {text}"

        state.update_text(response)
        state.add_history(Reflect.name)
        state.write(f"Reflect → asked: {question}")

        return state
