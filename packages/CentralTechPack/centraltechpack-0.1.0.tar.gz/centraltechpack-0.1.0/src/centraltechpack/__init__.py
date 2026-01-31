"""
le __init__.py permet de rendre les fonctions de chargement de datasets accessibles directement depuis le package centraltechpack.
autrement dit , ca permet de choisir ce que notre package montre au monde exterieur.

"""
from .datasets.loader import list_datasets,load_dataset,export_dataset

__all__=['list_datasets','load_dataset','export_dataset']
__version__='0.1.0'


