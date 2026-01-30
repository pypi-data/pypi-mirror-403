import json
from pathlib import Path

class ConformanceReport:
    def __init__(self):
        self.results = {}

    def record(self, test_id, passed):
        self.results[test_id] = {
            "status": "pass" if passed else "fail"
        }

    def write(self, resolver_dir: Path):
        path = resolver_dir / "conformance.json"
        with open(path, "w") as f:
            json.dump(self.results, f, indent=2)
