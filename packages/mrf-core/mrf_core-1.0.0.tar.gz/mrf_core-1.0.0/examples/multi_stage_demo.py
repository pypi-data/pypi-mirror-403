from mrfcore.pipeline import MRFPipeline

pipeline = MRFPipeline([
    [("Transform", {}), ("Summarize", {})],
    [("Reflect", {"question": "implication"})],
    [("Evaluate", {}), ("Rewrite", {})]
])

result = pipeline.run("Most failures in complex systems do not begin...")
print(result)
