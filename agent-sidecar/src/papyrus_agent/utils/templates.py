"""Currently Mock only"""

class Template:
    def __init__(self):
        self.template_path: str = "~/papyrus/templates/test.tex"

class TemplateRegistry(): 

    def __init__(self) -> None:
        self.templates: dict[str, Template] = {
            "Default" : Template()
        }

    def get(self, template_id: str) -> Template | None:
        """NotImplemented - Mocked"""
        print(f"currently mocked: {template_id}")
        return self.templates.get("Default")

template_registry = TemplateRegistry()
