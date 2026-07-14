"""Deterministic random-number helpers."""

from __future__ import annotations

import hashlib

import numpy as np
from faker import Faker


def stable_seed(root_seed: int, namespace: str) -> int:
    """Derive a stable 32-bit seed for a named generator stage."""
    digest = hashlib.sha256(f"{root_seed}:{namespace}".encode()).digest()
    return int.from_bytes(digest[:4], "little")


def rng_for(root_seed: int, namespace: str) -> np.random.Generator:
    return np.random.default_rng(stable_seed(root_seed, namespace))


def faker_for(root_seed: int, namespace: str) -> Faker:
    fake = Faker("en_US")
    fake.seed_instance(stable_seed(root_seed, namespace))
    return fake
