"""Check that every installed distribution carries an allowed licence (PKG-09, D-12).

Repo-only CI tool, standard library only. pip-licenses is not used because it mishandles
SPDX ``OR`` expressions. For each installed distribution the licence is read, in order, from:

1. a reviewed per-package override in ``tools/licence-allowlist.json``;
2. the ``License-Expression`` metadata field (PEP 639);
3. the ``License`` field, when it is a known alias or parses as an SPDX expression;
4. the ``License ::`` trove classifiers, mapped to SPDX ids (several combine with ``OR``).

The expression is then evaluated against the allow-list: ``OR`` passes when any alternative
is allowed, ``AND`` only when every part is, and ``X WITH Y`` counts as ``X``.

Exit codes: 0 when every distribution is allowed, 1 when any is not, 2 when the allow-list
file cannot be used.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "tools" / "licence-allowlist.json"

# Values some build tools write into the License field when there is no real licence.
_PLACEHOLDERS = {"unknown", "none", "noassertion", ""}

_TOKEN = re.compile(r"\s*(\(|\)|[A-Za-z0-9.+:-]+)")


def normalise(name: str) -> str:
    """Return the PEP 503 normalised form of a distribution name."""
    return re.sub(r"[-_.]+", "-", name).lower()


# --- SPDX expressions --------------------------------------------------------------------


def _tokenise(expr: str) -> list[str]:
    tokens = []
    pos = 0
    text = expr.strip()
    while pos < len(text):
        match = _TOKEN.match(text, pos)
        if match is None:
            raise ValueError(f"unexpected character {text[pos]!r} in licence expression")
        tokens.append(match.group(1))
        pos = match.end()
        while pos < len(text) and text[pos].isspace():
            pos += 1
    if not tokens:
        raise ValueError("empty licence expression")
    return tokens


class _Parser:
    """Recursive-descent parser: ``AND`` binds tighter than ``OR``; ``WITH`` tightest."""

    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def take(self) -> str:
        token = self.peek()
        if token is None:
            raise ValueError("licence expression ends too early")
        self.pos += 1
        return token

    def parse(self):
        node = self.or_expr()
        if self.peek() is not None:
            raise ValueError(f"unexpected {self.peek()!r} in licence expression")
        return node

    def or_expr(self):
        parts = [self.and_expr()]
        while (self.peek() or "").upper() == "OR":
            self.take()
            parts.append(self.and_expr())
        return ("OR", parts) if len(parts) > 1 else parts[0]

    def and_expr(self):
        parts = [self.with_expr()]
        while (self.peek() or "").upper() == "AND":
            self.take()
            parts.append(self.with_expr())
        return ("AND", parts) if len(parts) > 1 else parts[0]

    def with_expr(self):
        node = self.atom()
        if (self.peek() or "").upper() == "WITH":
            self.take()
            exception = self.take()
            if exception in ("(", ")") or exception.upper() in ("AND", "OR", "WITH"):
                raise ValueError("WITH must be followed by an exception id")
            # The exception widens the grant; the base licence decides.
        return node

    def atom(self):
        token = self.take()
        if token == "(":
            node = self.or_expr()
            if self.take() != ")":
                raise ValueError("unbalanced parentheses in licence expression")
            return node
        if token == ")" or token.upper() in ("AND", "OR", "WITH"):
            raise ValueError(f"unexpected {token!r} in licence expression")
        return ("ID", token)


def parse_expression(expr: str):
    """Parse an SPDX licence expression into a small tree, or raise ``ValueError``."""
    return _Parser(_tokenise(expr)).parse()


def _identifiers(node) -> list[str]:
    if node[0] == "ID":
        return [node[1]]
    return [ident for part in node[1] for ident in _identifiers(part)]


def _allowed(node, allowed: set[str]) -> bool:
    kind, value = node
    if kind == "ID":
        if value.lower().startswith("licenseref-"):
            return False
        return value.lower() in allowed
    if kind == "OR":
        return any(_allowed(part, allowed) for part in value)
    return all(_allowed(part, allowed) for part in value)


def evaluate_expression(expr: str, allowed) -> bool:
    """Return True when the SPDX expression ``expr`` is satisfied by ``allowed`` ids.

    Identifiers compare case-insensitively, ``LicenseRef-*`` is never allowed, and an
    expression that does not parse is not allowed.
    """
    try:
        tree = parse_expression(expr)
    except ValueError:
        return False
    return _allowed(tree, {ident.lower() for ident in allowed})


# --- Reading a distribution's licence -----------------------------------------------------


@dataclass(frozen=True)
class Violation:
    name: str
    version: str
    licence: str | None
    source: str
    reason: str

    def line(self) -> str:
        shown = self.licence if self.licence is not None else "no usable licence metadata"
        return f"VIOLATION {self.name} {self.version}: {self.reason} ({shown}; from {self.source})"


def _alias(value: str, config: dict) -> str | None:
    aliases = {key.lower(): spdx for key, spdx in config.get("aliases", {}).items()}
    return aliases.get(value.strip().lower())


def _licence_field(value: str, config: dict) -> str | None:
    """Return an SPDX expression for a ``License`` field value, or None if it is free text."""
    value = (value or "").strip()
    if value.lower() in _PLACEHOLDERS:
        return None
    alias = _alias(value, config)
    if alias is not None:
        return alias
    try:
        tree = parse_expression(value)
    except ValueError:
        return None
    if any(ident.lower() in _PLACEHOLDERS for ident in _identifiers(tree)):
        return None
    return value


def _classifier_licence(classifiers: list[str], config: dict) -> tuple[str | None, str]:
    mapping = config.get("classifier_map", {})
    mapped, unmapped = [], []
    for classifier in classifiers:
        parts = [part.strip() for part in classifier.split("::")]
        if len(parts) < 3 or parts[0] != "License":
            continue  # "License :: OSI Approved" alone names no licence
        name = parts[-1]
        if name in mapping:
            if mapping[name] not in mapped:
                mapped.append(mapping[name])
        else:
            unmapped.append(name)
    if mapped:
        expr = " OR ".join(mapped)
        return expr, "classifier"
    if unmapped:
        return None, "classifier (unmapped: " + "; ".join(unmapped) + ")"
    return None, "none"


def licence_of(dist, config: dict) -> tuple[str | None, str]:
    """Return ``(spdx_expression_or_None, source)`` for an installed distribution."""
    meta = dist.metadata
    override = config.get("overrides", {}).get(normalise(meta["Name"] or ""))
    if override is not None:
        return override["licence"], "reviewed override"
    expression = (meta.get("License-Expression") or "").strip()
    if expression:
        return expression, "License-Expression"
    field = _licence_field(meta.get("License") or "", config)
    if field is not None:
        return field, "License"
    classifiers = [c for c in (meta.get_all("Classifier") or []) if c.startswith("License ::")]
    return _classifier_licence(classifiers, config)


def check_distributions(dists, config: dict) -> list[Violation]:
    """Return one violation per distribution whose licence is unknown or not allowed."""
    allowed = config["allowed"]
    violations = []
    for dist in dists:
        meta = dist.metadata
        name = meta["Name"] or "<unnamed>"
        version = meta["Version"] or "<unknown>"
        licence, source = licence_of(dist, config)
        if licence is None:
            violations.append(Violation(name, version, None, source, "licence unknown"))
        elif not evaluate_expression(licence, allowed):
            violations.append(Violation(name, version, licence, source, "licence not allowed"))
    return sorted(violations, key=lambda v: (normalise(v.name), v.version))


def load_config(path: Path) -> dict:
    """Load and sanity-check the allow-list file, raising ``ValueError`` on any problem."""
    try:
        config = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"licence allow-list not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"licence allow-list is not valid JSON: {path}: {exc}") from None
    if config.get("schema_version") != 1:
        raise ValueError(f"licence allow-list has an unsupported schema_version: {path}")
    if not isinstance(config.get("allowed"), list) or not config["allowed"]:
        raise ValueError(f"licence allow-list has no 'allowed' list: {path}")
    for name, entry in config.get("overrides", {}).items():
        for field in ("licence", "reason", "reviewed_on"):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                raise ValueError(f"override for {name!r} needs a non-empty {field!r}")
    return config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
    except ValueError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    dists = list(importlib.metadata.distributions())
    violations = check_distributions(dists, config)
    for violation in violations:
        print(violation.line())
    if violations:
        print(f"{len(violations)} of {len(dists)} distributions failed the licence check.")
        return 1
    print(f"Licence check passed: all {len(dists)} installed distributions are allowed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
