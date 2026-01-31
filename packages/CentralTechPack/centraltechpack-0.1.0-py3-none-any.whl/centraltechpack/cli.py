import argparse
import json
from pathlib import Path
from .datasets.loader import list_datasets, load_dataset, export_dataset
"""
Bash cmd contrôle et synthase rédaction , forme d'écriture

"""
def main():
    parser = argparse.ArgumentParser(prog="centraltechpack", description="CentralTechPack CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List available datasets")

    p_load = sub.add_parser("load", help="Load a dataset and print as JSON")
    p_load.add_argument("name", help="Dataset name")

    p_exp = sub.add_parser("export", help="Export dataset file to a path")
    p_exp.add_argument("name", help="Dataset name")
    'commande '
    p_exp.add_argument("--out", required=True, help="Output path, e.g. ./medicine.csv")

    args = parser.parse_args()

    if args.cmd == "list":
        print(json.dumps(list_datasets(), indent=2, ensure_ascii=False))
    elif args.cmd == "load":
        data = load_dataset(args.name)
        print(json.dumps(data[:50], indent=2, ensure_ascii=False))  # show first 50 rows
    elif args.cmd == "export":
        out = export_dataset(args.name, Path(args.out))
        print(str(out))
