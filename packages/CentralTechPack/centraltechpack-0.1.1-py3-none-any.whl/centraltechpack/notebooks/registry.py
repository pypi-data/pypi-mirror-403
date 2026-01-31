from dataclasses import dataclass

@dataclass(frozen=True)
class NotebookInfo:
    name: str
    relpath: str
    description: str

NOTEBOOKS = {
    "ml_engineer_cheatsheet": NotebookInfo(
        name="ml_engineer_cheatsheet",
        relpath="notebooks/content/ml_engineer_cheatsheet.ipynb",
        description="Expert DS/ML Engineer commands & workflow cheat sheet (Markdown)."
    )
}
