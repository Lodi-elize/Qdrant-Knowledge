import os

import pytest
from fastapi.testclient import TestClient

os.environ["APP_VECTOR_BACKEND"] = "memory"
os.environ["APP_MODEL_PROVIDER"] = "local"
os.environ["APP_ADMIN_SECRET"] = "test-secret"

from app.main import create_app  # noqa: E402
from app.services.container import reset_services_for_tests  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    reset_services_for_tests()
    return TestClient(create_app())

