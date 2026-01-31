"""Hashing module config."""

from typing import Literal, NotRequired, TypedDict


class BcryptConfig(TypedDict):
    """Bcrypt hasher config."""

    rounds: NotRequired[int]
    prefix: NotRequired[Literal["2a", "2b"]]


class Argon2Config(TypedDict):
    """Argon2 hasher config."""

    time_cost: NotRequired[int]
    memory_cost: NotRequired[int]
    parallelism: NotRequired[int]
    hash_len: NotRequired[int]
    salt_len: NotRequired[int]


class HashingConfig(TypedDict):
    """Hasher config."""

    driver: Literal["argon2", "bcrypt"]
    argon: NotRequired[Argon2Config]
    bcrypt: NotRequired[BcryptConfig]
