"""The D-09 workspace upgrade. Interface only; implemented in plan 01-12 GREEN."""

from collections.abc import Callable

UPGRADE_STEPS: dict[int, Callable[[dict], None]] = {}


def needs_upgrade(state_dict) -> bool:
    raise NotImplementedError


def run_upgrade(case_root, ctx, snapshot) -> dict:
    raise NotImplementedError
