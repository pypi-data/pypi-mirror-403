"""
simple_run.py
-------------
A minimal example showing how to execute the MRF reasoning pipeline.

Run with:
    python examples/simple_run.py
"""

from mrfcore.pipeline import ReasoningPipeline

if __name__ == "__main__":
    pipeline = ReasoningPipeline(verbose=True)

    query = "Summarize the main challenges of deploying autonomous AI agents."

    result = pipeline.run(query)

    print("\n=== FINAL OUTPUT ===")
    print("Answer:", result["answer"])
    print("Confidence:", result["confidence"])
    print("Valid:", result["valid"])
