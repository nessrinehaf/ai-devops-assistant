from main import app


def client():
    return app.test_client()


def test_index():
    r = client().get("/")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_healthz():
    assert client().get("/healthz").status_code == 200


def test_error_returns_500():
    assert client().get("/error").status_code == 500


def test_metrics_exposed():
    c = client()
    c.get("/")
    r = c.get("/metrics")
    assert r.status_code == 200
    assert b"http_requests_total" in r.data
