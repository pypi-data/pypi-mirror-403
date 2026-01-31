from dataclasses import dataclass
"c'est la partie regristre  du dataset       "
@dataclass(frozen=True)
class DatasetInfo:
    name: str
    relpath: str   # path inside package
    description: str


#On crée un dictionnaire dans lequel on met cette structure de donnée 
#Il s'agit de notre registre de chemin des datasets
REGISTRY = {
    "medicine": DatasetInfo(
        name="medicine",
        relpath="datasets/data/medicine/diabete.csv",
        description="Sample medicine dataset for trainings."
    ),
    "astro": DatasetInfo(
        name="astro",
        relpath="datasets/data/astro/astro.csv",
        description="Sample astronomy dataset for trainings."
    ),
    "misc": DatasetInfo(
        name="misc",
        relpath="datasets/data/misc/misc.csv",
        description="Misc dataset for demos."
    ),
}
print(REGISTRY.values())