from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest
from src.api.deps import get_current_active_user, get_current_user
from src.core.security import hash_password
from src.main import app
from src.models.user import User


@pytest.fixture(autouse=True)
def default_mock_current_user(request):
    """
    Provide an active default mock user for legacy test endpoints that call
    create_property, unless test explicitly tests authentication logic.
    """
    # If the test is in test_auth.py, do not override globally to allow testing 401 unauth
    if "test_auth" in request.node.nodeid:
        yield
        return

    dummy_user = User(
        id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        email="test.default@space247.vn",
        hashed_password=hash_password("Pass123!"),
        full_name="Default Test User",
        role="user",
        is_active=True,
    )

    apps_to_override = [app]
    try:
        from tests import test_health, test_semantic_search
        if hasattr(test_health, "app"):
            apps_to_override.append(test_health.app)
        if hasattr(test_semantic_search, "app"):
            apps_to_override.append(test_semantic_search.app)
    except Exception:
        pass

    for a in apps_to_override:
        a.dependency_overrides[get_current_active_user] = lambda: dummy_user
        a.dependency_overrides[get_current_user] = lambda: dummy_user

    yield dummy_user

    for a in apps_to_override:
        a.dependency_overrides.pop(get_current_active_user, None)
        a.dependency_overrides.pop(get_current_user, None)
