from mrfcore.operators.summarize import SummarizeOperator
from mrfcore.state import PipelineState

def test_summarize_operator_shortens_text():
    text = (
        "Autonomous agents tend to drift because they lack a modular constraint "
        "layer that allows them to check intermediate reasoning steps."
    )
    state = PipelineState(text)
    op = SummarizeOperator()

    result = op.execute(state)

    assert isinstance(result, str)
    assert len(result) < len(text)
    assert "agents" in result or "drift" in result
