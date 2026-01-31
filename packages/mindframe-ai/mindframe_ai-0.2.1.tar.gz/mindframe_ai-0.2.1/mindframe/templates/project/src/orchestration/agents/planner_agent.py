from .base_agent import BaseAgent

class PlannerAgent(BaseAgent):
    def run(self, goal: str):
        print(f"Planning for goal: {goal}")
        return ["step1", "step2"]
