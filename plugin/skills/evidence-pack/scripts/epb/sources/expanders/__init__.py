"""Expander seam (PF-11, D-14). Interface stub; implemented in the GREEN step."""

REGISTRY: list = []


def register(expander):
    raise NotImplementedError


def expanders_for(mime):
    raise NotImplementedError
