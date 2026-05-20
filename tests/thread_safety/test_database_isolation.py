import random
import threading
import time

from appworld.apps.lib.models.db import Database, set_bridge_id, cleanup_bridge

from .conftest import create_mock_engine, mock_tracker


class TestDatabase(Database):
    pass


class TestDatabaseB(Database):
    pass


def test_database_engine_bridge_isolation():
    """Two bridge_ids get independent Database state."""
    engine_a = create_mock_engine("iso_a")
    engine_b = create_mock_engine("iso_b")

    set_bridge_id("bridge_a")
    TestDatabase.set(engine_a, mock_tracker("a"))

    set_bridge_id("bridge_b")
    TestDatabase.set(engine_b, mock_tracker("b"))

    set_bridge_id("bridge_a")
    assert TestDatabase.engine is engine_a

    set_bridge_id("bridge_b")
    assert TestDatabase.engine is engine_b

    cleanup_bridge("bridge_a")
    cleanup_bridge("bridge_b")


def test_database_subclass_isolation():
    """TestDatabase and TestDatabaseB maintain separate state for the same bridge."""
    set_bridge_id("bridge_sub")
    engine_a = create_mock_engine("sub_a")
    engine_b = create_mock_engine("sub_b")

    TestDatabase.set(engine_a, mock_tracker("sub_a"))
    TestDatabaseB.set(engine_b, mock_tracker("sub_b"))

    assert TestDatabase.engine is engine_a
    assert TestDatabaseB.engine is engine_b

    cleanup_bridge("bridge_sub")


def test_database_state_invisible_across_bridges():
    """Bridge B should not see bridge A's state."""
    set_bridge_id("bridge_vis_a")
    TestDatabase.set(create_mock_engine("vis"), mock_tracker("vis"))

    set_bridge_id("bridge_vis_b")
    assert TestDatabase.engine is None

    cleanup_bridge("bridge_vis_a")
    cleanup_bridge("bridge_vis_b")


def test_database_all_properties():
    """All Database properties work correctly."""
    set_bridge_id("bridge_props")
    engine = create_mock_engine("props")
    tracker = mock_tracker("props")
    TestDatabase.set(engine, tracker)

    assert TestDatabase.engine is engine
    assert TestDatabase.tracker is tracker
    assert TestDatabase.url is not None
    assert TestDatabase.path is not None
    assert TestDatabase.home_path is not None
    assert TestDatabase.storage_type is not None
    assert TestDatabase.connection is not None

    cleanup_bridge("bridge_props")


def test_concurrent_bridges_on_threads():
    """Multiple threads with different bridge_ids get isolated state."""
    results = {}
    errors = []

    def worker(bridge_id):
        set_bridge_id(bridge_id)
        engine = create_mock_engine(f"conc_{bridge_id}")
        TestDatabase.set(engine, mock_tracker(bridge_id))
        time.sleep(random.uniform(0.01, 0.1))
        set_bridge_id(bridge_id)  # re-set in case thread changed (mimics Pythonx pattern)
        if TestDatabase.engine is not engine:
            errors.append(f"Bridge {bridge_id} saw wrong engine")
        results[bridge_id] = TestDatabase.engine

    threads = [
        threading.Thread(target=worker, args=(f"bridge_{i}",))
        for i in range(10)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    assert len(set(id(v) for v in results.values())) == 10

    for i in range(10):
        cleanup_bridge(f"bridge_{i}")
