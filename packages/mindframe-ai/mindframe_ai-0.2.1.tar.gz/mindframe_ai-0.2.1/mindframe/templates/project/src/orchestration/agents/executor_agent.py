from .base_agent import BaseAgent

class ExecutorAgent(BaseAgent):
    def run(self, goal: str):
        print(f"Executing step: {goal}")
        return "Done"
