from .base import BaseOperator

class Transform(BaseOperator):
    name = "Transform"

    @staticmethod
    def run(state, params):
        text = state.text

        # Basic normalization
        transformed = " ".join(text.split())

        state.update_text(transformed)
        state.add_history(Transform.name)
        state.write("Transform → normalized whitespace")

        return state
