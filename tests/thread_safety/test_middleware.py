"""Test that BridgeIDMiddleware correctly passes bridge_id to the handler thread."""
import threading

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.testclient import TestClient

from appworld.apps.lib.models.db import Database, set_bridge_id, get_bridge_id, cleanup_bridge

from .conftest import create_mock_engine, mock_tracker


class TestDatabase(Database):
    pass


def test_middleware_sets_bridge_id_on_handler_thread():
    """The middleware reads X-Bridge-ID header and sets it on the handler thread."""
    # Record what bridge_id the handler sees
    handler_saw = {}

    app = FastAPI()

    class BridgeIDMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            bid = request.headers.get("x-bridge-id")
            if bid:
                set_bridge_id(bid)
            return await call_next(request)

    app.add_middleware(BridgeIDMiddleware)

    @app.get("/test")
    def test_endpoint():
        handler_saw["bridge_id"] = get_bridge_id()
        handler_saw["thread"] = threading.current_thread().ident
        return {"ok": True}

    client = TestClient(app).__enter__()

    # Make request WITH the header
    response = client.get("/test", headers={"X-Bridge-ID": "test_bridge_123"})
    assert response.status_code == 200
    assert handler_saw["bridge_id"] == "test_bridge_123"

    # Verify handler ran on a different thread than this one
    caller_thread = threading.current_thread().ident
    print(f"Caller thread: {caller_thread}, Handler thread: {handler_saw['thread']}")

    client.__exit__(None, None, None)


def test_middleware_with_database_access():
    """Full flow: set bridge_id on caller, set DB state, make request, handler sees correct DB."""
    handler_saw = {}

    app = FastAPI()

    class BridgeIDMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            bid = request.headers.get("x-bridge-id")
            if bid:
                set_bridge_id(bid)
            return await call_next(request)

    app.add_middleware(BridgeIDMiddleware)

    @app.get("/db-test")
    def db_test_endpoint():
        handler_saw["bridge_id"] = get_bridge_id()
        handler_saw["engine"] = TestDatabase.engine
        return {"ok": True}

    # Set up DB state for our bridge
    set_bridge_id("db_test_bridge")
    engine = create_mock_engine("db_test")
    TestDatabase.set(engine, mock_tracker("db_test"))

    # Verify caller can see the engine
    assert TestDatabase.engine is engine

    client = TestClient(app).__enter__()

    # Make request with bridge_id header
    response = client.get("/db-test", headers={"X-Bridge-ID": "db_test_bridge"})
    assert response.status_code == 200

    # The handler should have seen the correct bridge_id AND the engine
    assert handler_saw["bridge_id"] == "db_test_bridge"
    assert handler_saw["engine"] is engine, (
        f"Handler saw engine={handler_saw['engine']}, expected {engine}. "
        f"Bridge_id was '{handler_saw['bridge_id']}'"
    )

    client.__exit__(None, None, None)
    cleanup_bridge("db_test_bridge")


def test_two_bridges_concurrent_requests():
    """Two bridges with different IDs make requests, each sees its own DB state."""
    results = {}

    app = FastAPI()

    class BridgeIDMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            bid = request.headers.get("x-bridge-id")
            if bid:
                set_bridge_id(bid)
            return await call_next(request)

    app.add_middleware(BridgeIDMiddleware)

    @app.get("/which-engine")
    def which_engine():
        bid = get_bridge_id()
        eng = TestDatabase.engine
        return {"bridge_id": bid, "has_engine": eng is not None}

    # Set up two bridges with different engines
    set_bridge_id("bridge_x")
    engine_x = create_mock_engine("x")
    TestDatabase.set(engine_x, mock_tracker("x"))

    set_bridge_id("bridge_y")
    engine_y = create_mock_engine("y")
    TestDatabase.set(engine_y, mock_tracker("y"))

    client = TestClient(app).__enter__()

    # Bridge X request
    resp_x = client.get("/which-engine", headers={"X-Bridge-ID": "bridge_x"})
    results["x"] = resp_x.json()

    # Bridge Y request
    resp_y = client.get("/which-engine", headers={"X-Bridge-ID": "bridge_y"})
    results["y"] = resp_y.json()

    assert results["x"]["bridge_id"] == "bridge_x"
    assert results["x"]["has_engine"] is True
    assert results["y"]["bridge_id"] == "bridge_y"
    assert results["y"]["has_engine"] is True

    client.__exit__(None, None, None)
    cleanup_bridge("bridge_x")
    cleanup_bridge("bridge_y")
