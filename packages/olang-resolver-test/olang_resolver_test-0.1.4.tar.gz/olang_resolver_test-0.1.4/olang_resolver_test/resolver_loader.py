from pathlib import Path
import importlib.util
import sys
import json

def load_resolver(resolver_dir: Path):
    resolver_py = resolver_dir / "resolver.py"
    resolver_json = resolver_dir / "resolver.json"

    if not resolver_py.exists():
        raise FileNotFoundError("resolver.py not found")

    spec = importlib.util.spec_from_file_location("olang_resolver", resolver_py)
    module = importlib.util.module_from_spec(spec)
    sys.modules["olang_resolver"] = module
    spec.loader.exec_module(module)

    if not hasattr(module, "resolve"):
        raise AttributeError("resolver.py must export resolve(input)")

    meta = {}
    if resolver_json.exists():
        meta = json.loads(resolver_json.read_text())
    else:
        meta = {
            "resolverName": getattr(module, "resolverName", "unknown"),
            "version": getattr(module, "version", "0.0.0"),
            "resolverDeclaration": module,
        }

    return module.resolve, meta
