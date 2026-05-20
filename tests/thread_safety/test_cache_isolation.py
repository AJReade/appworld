import threading
import time

from appworld.apps.lib.models.db import CachedDBHandler, ModelHashHandler

from .conftest import create_mock_engine, mock_tracker


def test_cached_db_handler_thread_isolation():
    """Each thread has its own cache dict."""
    event_1 = threading.Event()
    event_2 = threading.Event()
    results = {}

    def thread_1():
        engine = create_mock_engine("ch_a")
        CachedDBHandler.set("path_a", engine, mock_tracker("ch_a"))
        assert CachedDBHandler.has("path_a")
        results["t1_has_a"] = True
        event_1.set()
        event_2.wait(timeout=5)
        results["t1_has_b"] = CachedDBHandler.has("path_b")

    def thread_2():
        event_1.wait(timeout=5)
        engine = create_mock_engine("ch_b")
        CachedDBHandler.set("path_b", engine, mock_tracker("ch_b"))
        assert CachedDBHandler.has("path_b")
        results["t2_has_b"] = True
        results["t2_has_a"] = CachedDBHandler.has("path_a")
        event_2.set()

    t1 = threading.Thread(target=thread_1)
    t2 = threading.Thread(target=thread_2)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert results["t1_has_a"] is True
    assert results["t1_has_b"] is False
    assert results["t2_has_b"] is True
    assert results["t2_has_a"] is False


def test_cached_db_handler_reset_isolation():
    """Resetting cache on thread 1 does not affect thread 2."""
    event_1 = threading.Event()
    event_2 = threading.Event()
    results = {}

    def thread_1():
        engine = create_mock_engine("rs_a")
        CachedDBHandler.set("reset_a", engine, mock_tracker("rs_a"))
        event_1.set()
        event_2.wait(timeout=5)
        CachedDBHandler.reset()
        results["t1_empty"] = CachedDBHandler.is_empty()

    def thread_2():
        event_1.wait(timeout=5)
        engine = create_mock_engine("rs_b")
        CachedDBHandler.set("reset_b", engine, mock_tracker("rs_b"))
        event_2.set()
        time.sleep(0.2)
        results["t2_has_b"] = CachedDBHandler.has("reset_b")

    t1 = threading.Thread(target=thread_1)
    t2 = threading.Thread(target=thread_2)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert results["t1_empty"] is True
    assert results["t2_has_b"] is True


def test_model_hash_handler_thread_isolation():
    """Each thread has its own hash tracking data."""
    results = {}

    def thread_1():
        data = ModelHashHandler._get_data()
        data["home_a"]["supervisor"]["hash_1"] = 42
        results["t1_value"] = data["home_a"]["supervisor"]["hash_1"]

    def thread_2():
        time.sleep(0.05)
        data = ModelHashHandler._get_data()
        results["t2_value"] = data["home_a"]["supervisor"]["hash_1"]

    t1 = threading.Thread(target=thread_1)
    t1.start()
    t1.join()

    t2 = threading.Thread(target=thread_2)
    t2.start()
    t2.join()

    assert results["t1_value"] == 42
    assert results["t2_value"] == 0  # Counter default
