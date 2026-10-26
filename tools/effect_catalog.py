"""Get effect names and aliases from the real engine AST, without importing heavy video libraries."""
import ast
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1] / "scripts" / "fx.py"

def read_registry(path=ENGINE):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    names = []
    aliases = {}
    looks = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                if (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name)
                    and dec.func.id == "effect" and dec.args
                    and isinstance(dec.args[0], ast.Constant) and isinstance(dec.args[0].value, str)):
                    names.append(dec.args[0].value)
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "ALIASES":
                    aliases = ast.literal_eval(node.value)
                if isinstance(t, ast.Name) and t.id == "LOOK_NAMES":
                    looks = ast.literal_eval(node.value)
    if len(names) != len(set(names)):
        raise ValueError("Duplicate effect registrations")
    if not names:
        raise ValueError("No registered effects in renderer")
    missing = [v for v in aliases.values() if v not in names]
    missing += [v[0] for v in looks.values() if v[0] not in names]
    if missing:
        raise ValueError(f"Invalid aliases/looks: {missing}")
    return names, aliases, looks
