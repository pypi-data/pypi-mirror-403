from mrfcore.pipeline import ReasoningPipeline

def test_pipeline_runs_end_to_end():
    pipeline = ReasoningPipeline(verbose=False)

    query = "Explain why modular reasoning reduces agent drift."
    result = pipeline.run(query)

    assert "answer" in result
    assert "confidence" in result
    assert "valid" in result
    assert result["answer"] != ""
    assert 0 <= result["confidence"] <= 1


def test_pipeline_context_contains_all_stages():
    pipeline = ReasoningPipeline(verbose=False)
    result = pipeline.run("test query")

    ctx = result["full_context"]

    assert "understanding" in ctx
    assert "planning" in ctx
    assert "execution" in ctx
    assert "synthesis" in ctx
    assert "verification" in ctx
