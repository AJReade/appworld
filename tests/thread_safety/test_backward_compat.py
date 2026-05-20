from appworld.apps.lib.models.db import Database, CachedDBHandler, ModelHashHandler

from .conftest import create_mock_engine, mock_tracker


class CompatDatabase(Database):
    """Subclass for backward compat testing."""
    pass


def test_single_thread_database_operations():
    """All Database operations work identically on a single thread."""
    engine = create_mock_engine("compat")
    tracker = mock_tracker("compat")

    CompatDatabase.set(engine, tracker)
    assert CompatDatabase.engine is engine
    assert CompatDatabase.tracker is tracker
    assert CompatDatabase.connection is not None
    assert CompatDatabase.url is not None
    assert CompatDatabase.storage_type is not None
    assert CompatDatabase.connection_is_open()


def test_single_thread_cached_db_handler():
    """CachedDBHandler works identically on a single thread."""
    engine = create_mock_engine("compat_ch")
    tracker = mock_tracker("compat_ch")

    CachedDBHandler.set("compat_path", engine, tracker)
    assert CachedDBHandler.has("compat_path")
    assert CachedDBHandler.get("compat_path") == (engine, tracker)
    assert not CachedDBHandler.is_empty()

    CachedDBHandler.reset()
    assert CachedDBHandler.is_empty()


def test_single_thread_model_hash_handler():
    """ModelHashHandler works identically on a single thread."""
    ModelHashHandler.reset()
    data = ModelHashHandler._get_data()
    assert data == {}

    data["home"]["supervisor"]["hash_1"] = 10
    assert ModelHashHandler._get_data()["home"]["supervisor"]["hash_1"] == 10

    ModelHashHandler.reset()
    assert ModelHashHandler._get_data()["home"]["supervisor"]["hash_1"] == 0  # Counter default


def test_database_set_idempotent():
    """Setting the same engine twice is a no-op."""
    engine = create_mock_engine("idemp")
    tracker = mock_tracker("idemp")

    CompatDatabase.set(engine, tracker)
    url_1 = CompatDatabase.url

    CompatDatabase.set(engine, tracker)
    url_2 = CompatDatabase.url

    assert url_1 == url_2
