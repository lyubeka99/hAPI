import os
from jinja2 import Environment, FileSystemLoader
from hAPI.reports.base_report import BaseReport

class HTMLReport(BaseReport):
    """Generates an HTML report containing the results from all modules chosen by the user."""

    def __init__(self, results):
        super().__init__(self,results)
        self.env = Environment(loader=FileSystemLoader(os.path.dirname(__file__), "../templates"))
    
    def generate(self):
        template = self.env.get_template("base_template.html")
        return template.render(modules=self.results)