import pytest
from mrfcore.operators.base import BaseOperator
from mrfcore.operators.summarize import SummarizeOperator
from mrfcore.operators.transform import TransformOperator
from mrfcore.operators.reflect import ReflectOperator
from mrfcore.operators.evaluate import EvaluateOperator
from mrfcore.state import PipelineState

def test_base_operator_requires_override():
    class BadOp(BaseOperator):
        name = "bad"

    state = PipelineState("test")
    op = BadOp()

    with pytest.raises(NotImplementedError):
        op.execute(state)


def test_summarize_operator_basic():
    state = PipelineState("This is a long sentence that needs summarizing.")
    op = SummarizeOperator()

    result = op.execute(state)
    assert isinstance(result, str)
    assert len(result) < len(state.data)


def test_transform_operator_rewrites_text():
    state = PipelineState("hello world")
    op = TransformOperator()

    result = op.execute(state)
    assert isinstance(result, str)
    assert result != "hello world"


def test_reflect_operator_returns_metadata():
    state = PipelineState("some text")
    op = ReflectOperator()

    result = op.execute(state)
    assert isinstance(result, dict)
    assert "length" in result


def test_evaluate_operator_produces_score():
    state = PipelineState("test")
    op = EvaluateOperator()

    result = op.execute(state)
    assert isinstance(result, dict)
    assert "score" in result
    assert 0 <= result["score"] <= 1
