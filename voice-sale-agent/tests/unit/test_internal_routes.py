"""验证生产应用不再公开 Python 登录、调试和静态入口。"""

from app.main import create_app


def test_only_health_is_public_and_business_routes_are_internal():
    app = create_app()
    paths = {getattr(route, "path", "") for route in app.routes}

    assert "/health" in paths
    assert "/internal/v1/sessions/start" in paths
    assert "/internal/v1/chat/text" in paths
    assert "/internal/v1/orders/mine" in paths
    assert "/ws/voice" in paths
    assert "/auth/dev-login" not in paths
    assert "/debug/chat/text" not in paths
    assert "/static" not in paths
