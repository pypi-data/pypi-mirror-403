"""
agent_embedding_example.py
--------------------------
Shows how to embed the MRF reasoning pipeline inside your own agent.

This is the pattern most developers will actually use in the real world.
"""

from mrfcore.pipeline import ReasoningPipeline


class MyAutonomousAgent:
    def __init__(self, name="ExampleAgent"):
        self.name = name
        self.pipeline = ReasoningPipeline(verbose=False)

    def think(self, query: str):
        """Use the MRF pipeline as the agent's internal reasoning engine."""
        result = self.pipeline.run(query)
        return result

    def act(self, query: str):
        """A stub demonstrating how reasoning informs actions."""
        result = self.think(query)

        if not result["valid"]:
            return {"error": "Reasoning invalid — cannot act safely"}

        # In a real system, this is where tool calls, API requests, or actions would go.
        return {
            "agent": self.name,
            "decision": result["answer"],
            "confidence": result["confidence"],
        }


if __name__ == "__main__":
    agent = MyAutonomousAgent()

    query = "Plan three safe steps an agent should take before modifying system files."

    output = agent.act(query)

    print("\n=== AGENT OUTPUT ===")
    for k, v in output.items():
        print(f"{k}: {v}")
