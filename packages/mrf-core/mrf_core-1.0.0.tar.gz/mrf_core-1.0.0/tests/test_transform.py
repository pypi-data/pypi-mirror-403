from mrfcore.operators.transform import TransformOperator
from mrfcore.state import PipelineState

def test_transform_operator_changes_structure():
    state = PipelineState("Transform this text.")
    op = TransformOperator()

    result = op.execute(state)

   # basic sanity checks
    assert isinstance(result, str)
    assert result != "Transform this text."
    assert len(result) > 0
