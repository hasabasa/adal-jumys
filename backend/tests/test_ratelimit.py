from app.main import app as fastapi_app
from app.services.ratelimit import InMemoryLimiter, get_limiter


def test_register_rate_limited(client):
    """Тіркелу лимиті: бір IP-ден 5 сұраныс өтеді, 6-сы 429 алады."""
    limiter = InMemoryLimiter()
    fastapi_app.dependency_overrides[get_limiter] = lambda: limiter
    try:
        statuses = []
        for i in range(6):
            response = client.post(
                "/auth/register",
                json={
                    "email": f"limit{i}@t.kz",
                    "password": "sekret123",
                    "pseudonym": f"limituser_{i}",
                    "role": "worker",
                },
            )
            statuses.append(response.status_code)
        assert statuses[:5] == [201] * 5
        assert statuses[5] == 429
    finally:
        fastapi_app.dependency_overrides.pop(get_limiter)


def test_limiter_disabled_in_tests_by_default(client, register):
    """Әдепкі тест-ортада NoopLimiter: 6+ тіркелу еркін өтеді."""
    for i in range(7):
        register(f"free{i}@t.kz", f"freeuser_{i}")
