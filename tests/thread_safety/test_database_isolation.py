import random
import threading
import time

from appworld.apps.lib.models.db import Database

from .conftest import create_mock_engine, mock_tracker


class TestDatabase(Database):
    """Concrete subclass for testing (mirrors app-specific Database subclasses)."""
    pass


class TestDatabaseB(Database):
    """Second subclass to test cross-subclass isolation."""
    pass


def test_database_engine_thread_isolation():
    """Two threads setting Database.engine get independent values."""
    results = {}

    def set_and_read(thread_name, engine):
        TestDatabase.set(engine, mock_tracker(thread_name))
        time.sleep(0.1)
        results[thread_name] = TestDatabase.engine

    engine_a = create_mock_engine("iso_a")
    engine_b = create_mock_engine("iso_b")

    t1 = threading.Thread(target=set_and_read, args=("t1", engine_a))
    t2 = threading.Thread(target=set_and_read, args=("t2", engine_b))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert results["t1"] is engine_a
    assert results["t2"] is engine_b


def test_database_subclass_isolation():
    """TestDatabase and TestDatabaseB maintain separate state on the same thread."""
    engine_a = create_mock_engine("sub_a")
    engine_b = create_mock_engine("sub_b")

    TestDatabase.set(engine_a, mock_tracker("sub_a"))
    TestDatabaseB.set(engine_b, mock_tracker("sub_b"))

    assert TestDatabase.engine is engine_a
    assert TestDatabaseB.engine is engine_b


def test_database_state_invisible_across_threads():
    """Thread 2 should not see thread 1's database state."""
    event = threading.Event()
    results = {}

    def thread_1():
        TestDatabase.set(create_mock_engine("visible"), mock_tracker("vis"))
        event.wait(timeout=5)

    def thread_2():
        time.sleep(0.05)
        results["engine"] = TestDatabase.engine
        event.set()

    t1 = threading.Thread(target=thread_1)
    t2 = threading.Thread(target=thread_2)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert results["engine"] is None


def test_database_all_properties_thread_local():
    """All Database properties are correctly thread-local."""
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


def test_many_concurrent_threads():
    """10 threads each set and verify their own Database state."""
    results = {}
    errors = []

    def worker(thread_id):
        engine = create_mock_engine(f"stress_{thread_id}")
        TestDatabase.set(engine, mock_tracker(f"stress_{thread_id}"))
        time.sleep(random.uniform(0.01, 0.1))
        if TestDatabase.engine is not engine:
            errors.append(f"Thread {thread_id} saw wrong engine")
        results[thread_id] = TestDatabase.engine

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    assert len(set(id(v) for v in results.values())) == 10
