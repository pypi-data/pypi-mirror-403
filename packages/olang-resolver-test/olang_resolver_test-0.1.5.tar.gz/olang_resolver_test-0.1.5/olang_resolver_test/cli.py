# olang_resolver_test/cli.py
import argparse
import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from .resolver_loader import load_resolver
from .test_suite import TESTS
from .badge import write_badge

def main():
    # Parse CLI args — --version auto-exits, so we never access args.version
    parser = argparse.ArgumentParser(
        prog="olang-test",
        description="O-lang Resolver Conformance Tester"
    )
    parser.add_argument("--json", action="store_true", help="Reserved for future structured output")
    parser.add_argument("--version", action="version", version="olang-resolver-test 0.1.5")
    args = parser.parse_args()  # <-- If --version used, this exits before next line

    # Resolve resolver path
    resolver_path_str = os.getenv("OLANG_RESOLVER")
    if resolver_path_str:
        resolver_dir = Path(resolver_path_str).resolve()
    else:
        resolver_dir = Path.cwd()

    if not resolver_dir.exists():
        print(f"❌ Resolver path does not exist: {resolver_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 Testing resolver at {resolver_dir}")

    try:
        resolver, meta = load_resolver(resolver_dir)
    except Exception as e:
        print(f"❌ Failed to load resolver: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract resolver name
    declaration = meta.get("resolverDeclaration") or meta
    resolver_name = declaration.get("resolverName", "unknown")

    # Map resolver names to their valid test actions
    VALID_ACTIONS = {
        "notify-python": 'Notify user123 "Hello" using notify-python',
        "iot-device-command": "Turn ON device test_device using iot-device-command",
    }

    if resolver_name not in VALID_ACTIONS:
        print(f"❌ Unsupported resolver: {resolver_name}. Supported: {list(VALID_ACTIONS.keys())}", file=sys.stderr)
        sys.exit(1)

    fixture = {"action": VALID_ACTIONS[resolver_name]}

    failed = 0
    results = []

    for name, test in TESTS.items():
        try:
            result = test(resolver, meta, fixture)
            if result is True:
                status = "pass"
                print("✅", name)
            else:
                status = "fail"
                print("❌", name, "→", result)
                failed += 1
        except Exception as e:
            status = "fail"
            print("💥", name, "crashed:", e)
            failed += 1
        results.append({"suite": name, "status": status})

    # Generate conformance.json
    conformance_report = {
        "resolver": resolver_name,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "results": results
    }
    with open(resolver_dir / "conformance.json", "w", encoding="utf-8") as f:
        json.dump(conformance_report, f, indent=2)

    # Generate badge
    passed = failed == 0
    write_badge(resolver_dir, passed, resolver_name)

    print("\n🎉 CERTIFIED" if passed else "\n⚠️ NOT CERTIFIED")
    sys.exit(0 if passed else 1)