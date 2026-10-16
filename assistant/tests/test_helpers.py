import main


def reset():
    main._last_analyzed.clear()
    main._recent_analyses.clear()


def firing(name="DemoAppHighErrorRate", fp="abc"):
    return {"status": "firing", "labels": {"alertname": name}, "fingerprint": fp}


def test_ignores_watchdog_and_resolved():
    reset()
    assert main.claim_alert(firing("Watchdog"), 0)[0] is False
    assert main.claim_alert({**firing(), "status": "resolved"}, 0)[0] is False


def test_cooldown():
    reset()
    assert main.claim_alert(firing(), 0)[0] is True
    assert main.claim_alert(firing(), 60) == (False, "cooldown")
    assert main.claim_alert(firing(), main.COOLDOWN_MINUTES * 60 + 1)[0] is True


def test_hourly_budget():
    reset()
    for i in range(main.MAX_ANALYSES_PER_HOUR):
        assert main.claim_alert(firing(fp=str(i)), 0)[0] is True
    assert main.claim_alert(firing(fp="extra"), 0) == (False, "hourly budget reached")


def test_alert_expr():
    url = "http://prom:9090/graph?g0.expr=up+%3D%3D+0&g0.tab=1"
    assert main.alert_expr({"generatorURL": url}) == "up == 0"
    assert main.alert_expr({}) is None


def test_split_message():
    text = "\n".join(["x" * 100] * 50)
    chunks = main.split_message(text, 1900)
    assert all(len(c) <= 1900 for c in chunks)
    assert "".join(c.replace("\n", "") for c in chunks) == text.replace("\n", "")


def test_label_escaping():
    assert main._label_value('a"b') == 'a\\"b'


def test_openai_body_uses_reasoning_params(monkeypatch):
    monkeypatch.setattr(main, "LLM_BASE_URL", "https://api.openai.com/v1")
    body = main.llm_request_body("hi")
    assert "max_completion_tokens" in body and "temperature" not in body


def test_other_provider_body(monkeypatch):
    monkeypatch.setattr(main, "LLM_BASE_URL", "https://api.groq.com/openai/v1")
    body = main.llm_request_body("hi")
    assert body["max_tokens"] == 700


def test_estimate_cost(monkeypatch):
    monkeypatch.setattr(main, "LLM_INPUT_PRICE_PER_M", 0.25)
    monkeypatch.setattr(main, "LLM_OUTPUT_PRICE_PER_M", 2.00)
    # 4000 input + 1000 output tokens = 0.001 + 0.002 USD
    assert abs(main.estimate_cost(4000, 1000) - 0.003) < 1e-12


def test_metrics_endpoint():
    from fastapi.testclient import TestClient

    body = TestClient(main.app).get("/metrics").text
    assert 'ai_assistant_analyses_total{result="success"} 0.0' in body
    assert "ai_assistant_llm_cost_usd_total" in body
