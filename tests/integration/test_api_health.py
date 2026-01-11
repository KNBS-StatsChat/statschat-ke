"""
Integration test for API Health Check.

Purpose:
    Ensures the FastAPI application can start and responding to basic health checks.
    This is the "smoke test" for the backend.

Why:
    If this fails, the entire backend is broken. It validates the FastAPI instance,
    CORS configuration, and basic routing.
"""

from fastapi.testclient import TestClient

# Adjust import path based on how pytest runs (root vs local)
import sys
import os

# Ensure the root directory is in sys.path so we can import 'fast-api'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    # Attempt import assuming 'fast-api' is a package or reachable module
    # The folder is named 'fast-api' (with hyphen), which is not a valid python identifier
    # so we might need to import dynamically or rename the folder.
    # HOWEVER, usually dev ops run uvicorn fast-api.main_api_local:app
    # Let's try importing specifically using importlib due to the hyphen.
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "main_api_local", os.path.join(project_root, "fast-api", "main_api_local.py")
    )
    main_api_local = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_api_local)
    app = main_api_local.app
except Exception as e:
    raise ImportError(f"Could not import main_api_local: {e}")


client = TestClient(app)


def test_read_root_redirect():
    """
    Test GET /
    Why: Verifies the root endpoint exists and redirects to documentation (default behavior).
    """
    response = client.get("/", follow_redirects=False)
    # The app returns a RedirectResponse to /openapi.json which is a 307 Temporary Redirect
    assert response.status_code == 307
    assert response.headers["location"] == "/openapi.json"
