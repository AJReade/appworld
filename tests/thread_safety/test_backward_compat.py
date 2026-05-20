from appworld.apps.lib.models.db import Database, CachedDBHandler, ModelHashHandler, set_bridge_id, cleanup_bridge

from .conftest import create_mock_engine, mock_tracker


class CompatDatabase(Database):
    pass


def test_single_bridge_database_operations():
    """All Database operations work on a single bridge."""
    set_bridge_id("bridge_compat")
    engine = create_mock_engine("compat")
    tracker = mock_tracker("compat")

    CompatDatabase.set(engine, tracker)
    assert CompatDatabase.engine is engine
    assert CompatDatabase.tracker is tracker
    assert CompatDatabase.connection is not None
    assert CompatDatabase.url is not None
    assert CompatDatabase.storage_type is not None
    assert CompatDatabase.connection_is_open()

    cleanup_bridge("bridge_compat")


def test_single_bridge_cached_db_handler():
    """CachedDBHandler works on a single bridge."""
    set_bridge_id("bridge_compat_ch")
    engine = create_mock_engine("compat_ch")
    tracker = mock_tracker("compat_ch")

    CachedDBHandler.set("compat_path", engine, tracker)
    assert CachedDBHandler.has("compat_path")
    assert CachedDBHandler.get("compat_path") == (engine, tracker)
    assert not CachedDBHandler.is_empty()

    CachedDBHandler.reset()
    assert CachedDBHandler.is_empty()

    cleanup_bridge("bridge_compat_ch")


def test_single_bridge_model_hash_handler():
    """ModelHashHandler works on a single bridge."""
    set_bridge_id("bridge_compat_mh")
    ModelHashHandler.reset()
    data = ModelHashHandler._get_data()
    data["home"]["supervisor"]["hash_1"] = 10
    assert ModelHashHandler._get_data()["home"]["supervisor"]["hash_1"] == 10

    ModelHashHandler.reset()
    assert ModelHashHandler._get_data()["home"]["supervisor"]["hash_1"] == 0

    cleanup_bridge("bridge_compat_mh")


def test_database_set_idempotent():
    """Setting the same engine twice is a no-op."""
    set_bridge_id("bridge_idemp")
    engine = create_mock_engine("idemp")
    tracker = mock_tracker("idemp")

    CompatDatabase.set(engine, tracker)
    url_1 = CompatDatabase.url

    CompatDatabase.set(engine, tracker)
    url_2 = CompatDatabase.url

    assert url_1 == url_2

    cleanup_bridge("bridge_idemp")


def test_cleanup_bridge_removes_all_state():
    """cleanup_bridge removes all entries for a bridge_id."""
    set_bridge_id("bridge_cleanup")
    CompatDatabase.set(create_mock_engine("cleanup"), mock_tracker("cleanup"))
    CachedDBHandler.set("cleanup_path", create_mock_engine("cleanup_ch"), mock_tracker("cleanup_ch"))

    assert CompatDatabase.engine is not None
    assert CachedDBHandler.has("cleanup_path")

    cleanup_bridge("bridge_cleanup")

    set_bridge_id("bridge_cleanup")
    assert CompatDatabase.engine is None
    assert CachedDBHandler.is_empty()
