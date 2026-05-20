import threading

from sqlmodel import create_engine

from appworld.apps.lib.models.db import DBChangesTracker


def create_mock_engine(name: str):
    """Create a named in-memory SQLite engine for testing.

    Name format includes a / to satisfy _get_engine_to_details assertion.
    """
    return create_engine(
        f"sqlite:///file:{name}/test.db?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False},
    )


def mock_tracker(name: str = "default") -> DBChangesTracker:
    """Create a DBChangesTracker backed by a mock engine."""
    engine = create_mock_engine(f"tracker_{name}")
    return DBChangesTracker(engine)
