from appworld.apps.lib.models.db import CachedDBHandler, ModelHashHandler, set_bridge_id, cleanup_bridge

from .conftest import create_mock_engine, mock_tracker


def test_cached_db_handler_bridge_isolation():
    """Each bridge_id has its own cache."""
    set_bridge_id("bridge_ch_a")
    engine_a = create_mock_engine("ch_a")
    CachedDBHandler.set("path_a", engine_a, mock_tracker("ch_a"))
    assert CachedDBHandler.has("path_a")

    set_bridge_id("bridge_ch_b")
    engine_b = create_mock_engine("ch_b")
    CachedDBHandler.set("path_b", engine_b, mock_tracker("ch_b"))
    assert CachedDBHandler.has("path_b")
    assert not CachedDBHandler.has("path_a")

    set_bridge_id("bridge_ch_a")
    assert CachedDBHandler.has("path_a")
    assert not CachedDBHandler.has("path_b")

    cleanup_bridge("bridge_ch_a")
    cleanup_bridge("bridge_ch_b")


def test_cached_db_handler_reset_isolation():
    """Resetting one bridge's cache doesn't affect another."""
    set_bridge_id("bridge_rs_a")
    CachedDBHandler.set("reset_a", create_mock_engine("rs_a"), mock_tracker("rs_a"))

    set_bridge_id("bridge_rs_b")
    CachedDBHandler.set("reset_b", create_mock_engine("rs_b"), mock_tracker("rs_b"))

    set_bridge_id("bridge_rs_a")
    CachedDBHandler.reset()
    assert CachedDBHandler.is_empty()

    set_bridge_id("bridge_rs_b")
    assert CachedDBHandler.has("reset_b")

    cleanup_bridge("bridge_rs_a")
    cleanup_bridge("bridge_rs_b")


def test_model_hash_handler_bridge_isolation():
    """Each bridge_id has its own hash data."""
    set_bridge_id("bridge_mh_a")
    data_a = ModelHashHandler._get_data()
    data_a["home"]["supervisor"]["hash_1"] = 42

    set_bridge_id("bridge_mh_b")
    data_b = ModelHashHandler._get_data()
    assert data_b["home"]["supervisor"]["hash_1"] == 0

    set_bridge_id("bridge_mh_a")
    assert ModelHashHandler._get_data()["home"]["supervisor"]["hash_1"] == 42

    cleanup_bridge("bridge_mh_a")
    cleanup_bridge("bridge_mh_b")
