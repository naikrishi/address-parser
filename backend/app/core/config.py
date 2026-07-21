import os


def get_database_url() -> str:
    """Return the database URL from environment with a safe local default."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://app:app@127.0.0.1:5432/address_parser",
    )
