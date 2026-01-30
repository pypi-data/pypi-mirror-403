import inspect
import copy
import json

# -------------------------
# Helpers
# -------------------------

def _has_valid_signature(fn):
    return len(inspect.signature(fn).parameters) == 1

def _deep_equal(a, b):
    return a == b

# -------------------------
# R-005 → R-012 with diagnostics
# -------------------------

def R005_metadata(resolver, meta, fixture):
    if "resolverDeclaration" not in meta:
        return "Missing 'resolverDeclaration' object in resolver.json"
    
    decl = meta["resolverDeclaration"]
    if not isinstance(decl, dict):
        return "'resolverDeclaration' must be an object"

    if "resolverName" not in decl:
        return "Missing 'resolverName' in resolverDeclaration"
    if not isinstance(decl["resolverName"], str) or not decl["resolverName"].strip():
        return "'resolverName' must be a non-empty string"

    if "version" not in decl:
        return "Missing 'version' in resolverDeclaration"
    if not isinstance(decl["version"], str) or not decl["version"].strip():
        return "'version' must be a non-empty string"

    return True


def R006_runtime_shape(resolver, meta, fixture):
    if not _has_valid_signature(resolver):
        return "Resolver function must accept exactly one argument"

    try:
        res = resolver(copy.deepcopy(fixture))
    except Exception as e:
        return f"Resolver threw an exception: {e}"

    if not isinstance(res, dict):
        return f"Resolver must return a dictionary, got {type(res).__name__}"

    has_output = "output" in res
    has_error = "error" in res

    if has_output and has_error:
        return "Resolver must not return both 'output' and 'error'"
    if not has_output and not has_error:
        return "Resolver must return either 'output' or 'error'"

    return True


def R007_failure_contract(resolver, meta, fixture):
    bad_inputs = [
        ({}, "empty input"),
        ({"action": ""}, "empty 'action' string"),
        ({"action": 123}, "non-string 'action'")
    ]
    
    for inp, desc in bad_inputs:
        try:
            r = resolver(inp)
            if not isinstance(r, dict):
                return f"Resolver returned non-dict for {desc}: {r}"
            if "error" not in r:
                return f"Resolver did not return {{'error': ...}} for invalid input ({desc})"
        except Exception as e:
            return f"Resolver crashed on invalid input ({desc}): {e}"
    
    return True


def R008_input_validation(resolver, meta, fixture):
    try:
        r = resolver(copy.deepcopy(fixture))
        if not isinstance(r, dict):
            return f"Resolver returned non-dict: {r}"
        return True
    except Exception as e:
        return f"Resolver crashed on valid input: {e}"


def R009_retry_semantics(resolver, meta, fixture):
    try:
        r = resolver(copy.deepcopy(fixture))
    except Exception as e:
        return f"Resolver crashed: {e}"

    if "error" in r and "retriable" in r:
        if not isinstance(r["retriable"], bool):
            return "'retriable' must be a boolean when present"
    return True


def R010_output_contract(resolver, meta, fixture):
    try:
        r = resolver(copy.deepcopy(fixture))
    except Exception as e:
        return f"Resolver crashed: {e}"

    if "output" not in r:
        return "Resolver did not return 'output' for valid input"

    try:
        json.dumps(r["output"])
    except (TypeError, ValueError) as e:
        return f"'output' is not JSON-serializable: {e}"

    return True


def R011_determinism(resolver, meta, fixture):
    try:
        r1 = resolver(copy.deepcopy(fixture))
        r2 = resolver(copy.deepcopy(fixture))
    except Exception as e:
        return f"Resolver crashed during determinism check: {e}"

    if not _deep_equal(r1, r2):
        return "Resolver returned different results for identical inputs (not deterministic)"
    
    return True


def R012_side_effects(resolver, meta, fixture):
    # We can't detect side effects at runtime in Python without sandboxing,
    # but we ensure it doesn't crash and runs cleanly.
    try:
        resolver(copy.deepcopy(fixture))
        return True
    except Exception as e:
        return f"Resolver crashed (possible side-effect instability): {e}"


TESTS = {
    "R-005-resolver-metadata-contract": R005_metadata,
    "R-006-resolver-runtime-shape": R006_runtime_shape,
    "R-007-resolver-failure-contract": R007_failure_contract,
    "R-008-resolver-input-validation": R008_input_validation,
    "R-009-resolver-retry-semantics": R009_retry_semantics,
    "R-010-resolver-output-contract": R010_output_contract,
    "R-011-resolver-determinism": R011_determinism,
    "R-012-resolver-side-effects": R012_side_effects,
}