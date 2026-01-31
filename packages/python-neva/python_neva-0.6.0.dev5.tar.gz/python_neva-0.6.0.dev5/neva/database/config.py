"""Database configs."""

from typing import Literal, NotRequired, TypedDict


class SQLiteCredentials(TypedDict):
    """SQLite credentials."""

    file_path: str
    journal_mode: NotRequired[str]
    journal_size_limit: NotRequired[int]
    foreign_keys: NotRequired[bool]


class PostgresCredentials(TypedDict):
    """Postgres credentials."""

    user: str
    password: str
    host: str
    port: int
    database: str
    minsize: NotRequired[int]
    maxsize: NotRequired[int]
    max_queries: NotRequired[int]
    max_inactive_connection_lifetime: NotRequired[float]
    schema: NotRequired[str]
    ssl: NotRequired[bool]


class SQLiteConnection(TypedDict):
    """SQLite connection config."""

    engine: Literal["tortoise.backends.sqlite"]
    credentials: SQLiteCredentials


class PostgresConnection(TypedDict):
    """Postgres connection config."""

    engine: Literal["tortoise.backends.asyncpg"]
    credentials: PostgresCredentials


DBConnection = SQLiteConnection | PostgresConnection


class DBApp(TypedDict):
    """DB application config."""

    models: list[str]
    default_connection: str


class DatabaseConfig(TypedDict):
    """Database config."""

    connections: dict[str, DBConnection]
    apps: dict[str, DBApp]
