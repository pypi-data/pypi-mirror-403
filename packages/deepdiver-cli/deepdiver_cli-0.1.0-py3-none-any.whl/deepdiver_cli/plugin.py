import importlib
from typing import Optional



def create_plugin(path: Optional[str] = None):
    if not path:
        return None
    obj = load_object(path)
    return obj() if callable(obj) else obj


def load_object(path: str):
    # path like "pkg.module:Obj"
    mod, _, attr = path.partition(":")
    if not mod or not attr:
        raise ValueError("Invalid path, expected 'pkg.module:Obj'")
    m = importlib.import_module(mod)
    return getattr(m, attr)