# O-Lang Resolver Test Suite

Language-agnostic conformance and certification tests for **O-Lang resolvers**.

O-Lang resolvers are executable contracts: small, deterministic units that perform actions described in O-Lang.  
This test suite ensures that resolvers behave **consistently, predictably, and safely** across **all programming languages that understand JSON**.

---

## TL;DR

- One contract
- One test suite
- Any programming language
- Deterministic, auditable resolvers

If your resolver passes these tests, it is **O-Lang compliant**.

---

## What This Test Suite Does

The O-Lang Resolver Test Suite validates that a resolver:

- Declares required metadata (`resolverName`, `version`)
- Exposes a valid `resolve(input)` entry point
- Accepts structured JSON input
- Returns a strictly shaped response:
  - `{ "output": ... }` **or**
  - `{ "error": ... }`
- Fails explicitly and predictably
- Behaves deterministically (same input → same output)

The **same tests** apply whether your resolver is written in:

- Python
- JavaScript (Node.js)
- Go
- Rust
- Java
- Or **any language capable of JSON I/O**

---

## Why This Exists

Most systems don’t fail because of syntax errors.  
They fail because **contracts are unclear**.

Without resolver conformance testing:

- Every resolver invents its own response format
- Error handling becomes inconsistent
- Cross-language execution breaks silently
- Tooling cannot reason about behavior

O-Lang solves this by enforcing resolver contracts with a shared, language-agnostic test suite.

---

## Documentation & Guide

For a full walkthrough covering:

- Resolver contracts
- Test philosophy
- Python and JavaScript examples
- Cross-language guarantees

Read the official Medium article:

👉 **How to Test O-Lang Resolvers in Python and JavaScript**  
https://medium.com/@o-lang/how-to-test-o-lang-resolvers-in-python-and-javascript-07e6fab4385f

---

## Typical Resolver Structure

```text
resolver-your-action/
├── resolver.py        # or index.js, main.go, etc.
├── resolver.json
└── tests/
    ├── R-005-resolver-metadata-contract.json
    ├── R-006-resolver-runtime-shape.json
    ├── R-007-resolver-failure-contract.json
    └── ...