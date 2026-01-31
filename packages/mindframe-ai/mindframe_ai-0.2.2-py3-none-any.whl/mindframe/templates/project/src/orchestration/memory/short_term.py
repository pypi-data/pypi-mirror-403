class ShortTermMemory:
    def __init__(self):
        self.log = []
    def add(self, msg: str):
        self.log.append(msg)
