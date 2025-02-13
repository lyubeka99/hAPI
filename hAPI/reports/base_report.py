class BaseReport:
    def __init__(self, results):
        self.results = results

    def generate(self):
        raise NotImplementedError("Subclasses must implement the generate() method.")