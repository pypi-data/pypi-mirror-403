class BaseOperator:
    name = ""

    @staticmethod
    def run(state, params):
        raise NotImplementedError
