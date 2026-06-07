import numpy as np

from orbital.image_analysis import analyze_image_array
from orbital.llm_client import LLMAPIError, LLMClient, LLMConfig
from orbital.priority_index import (
    PriorityInputs,
    apply_priority_index,
    calculate_ipho,
    classify_priority,
    sanitary_cases_to_score,
)
from orbital.report_generator import build_llm_messages, generate_humanitarian_report
from orbital.app import _build_map


def test_calculate_ipho_uses_defined_weights():
    score = calculate_ipho(
        PriorityInputs(
            environmental_risk=82,
            sanitary_cases=132,
            logistic_isolation=90,
            rainfall_intensity=78,
            orbital_area_affected=66,
        )
    )

    assert score == 81.5
    assert classify_priority(score) == "Alta"
    assert sanitary_cases_to_score(132) == 82.5


def test_apply_priority_index_orders_highest_priority_first():
    result = apply_priority_index(
        [
            {
                "community": "Maturacá",
                "environmental_risk": 42,
                "sanitary_cases": 52,
                "logistic_isolation": 55,
                "rainfall_intensity": 45,
                "orbital_area_affected": 34,
            },
            {
                "community": "Surucucu",
                "environmental_risk": 82,
                "sanitary_cases": 132,
                "logistic_isolation": 90,
                "rainfall_intensity": 78,
                "orbital_area_affected": 66,
            },
        ]
    )

    assert result.iloc[0]["community"] == "Surucucu"
    assert result.iloc[0]["priority"] == "Alta"


def test_analyze_image_array_detects_water_and_vegetation():
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    image[:, :50] = (190, 90, 20)
    image[:, 50:] = (45, 130, 45)

    analysis = analyze_image_array(image)

    assert analysis.water_percent > 40
    assert analysis.vegetation_percent > 40
    assert analysis.affected_area_percent > 40


def test_generate_humanitarian_report_contains_priority_context():
    report = generate_humanitarian_report(
        {
            "community": "Surucucu",
            "territory": "Terra Indígena Yanomami",
            "priority": "Alta",
            "IPHO": 81.5,
            "environmental_risk": 82,
            "rainfall_intensity": 78,
            "logistic_isolation": 90,
            "sanitary_cases": 132,
            "sanitary_case_score": 82.5,
            "orbital_area_affected": 66,
        }
    )

    assert "Surucucu" in report
    assert "Nível de prioridade" in report
    assert "Justificativa" in report
    assert "Recomendações" in report
    assert "Próximos passos" in report
    assert "IPHO 81.5/100" in report
    assert "132 casos sanitários" in report


def test_build_llm_messages_contains_required_context():
    messages = build_llm_messages(
        {
            "community": "Surucucu",
            "territory": "Terra Indígena Yanomami",
            "priority": "Alta",
            "IPHO": 81.5,
            "environmental_risk": 82,
            "rainfall_intensity": 78,
            "logistic_isolation": 90,
            "sanitary_cases": 132,
            "sanitary_case_score": 82.5,
            "orbital_area_affected": 66,
        }
    )

    prompt = messages[1]["content"]

    assert messages[0]["role"] == "system"
    assert "Resumo da situação" in prompt
    assert "Casos sanitários simulados: 132" in prompt
    assert "Área afetada por imagem orbital: 66.0%" in prompt


def test_llm_client_calls_chat_completions_payload():
    fake_http = FakeHTTPClient(
        {
            "choices": [
                {
                    "message": {
                        "content": "Resumo da situação:\nRelatório gerado pela API LLM."
                    }
                }
            ]
        }
    )
    client = LLMClient(
        config=LLMConfig(
            api_key="test-key",
            model="test-model",
            api_url="https://example.com/v1/chat/completions",
        ),
        http_client=fake_http,
    )

    text = client.generate_text([{"role": "user", "content": "gere relatório"}])

    assert "API LLM" in text
    assert fake_http.last_payload["model"] == "test-model"
    assert fake_http.last_payload["messages"][0]["content"] == "gere relatório"
    assert fake_http.last_headers["Authorization"] == "Bearer test-key"


def test_llm_client_requires_configuration():
    client = LLMClient(config=LLMConfig(api_key=None, model=None))

    try:
        client.generate_text([{"role": "user", "content": "teste"}])
    except LLMAPIError as exc:
        assert "não configurada" in str(exc)
    else:
        raise AssertionError("LLMAPIError não foi levantado")


def test_map_includes_priority_legend():
    prioritized = apply_priority_index(
        [
            {
                "community": "Surucucu",
                "latitude": 2.8333,
                "longitude": -63.6667,
                "environmental_risk": 82,
                "rainfall_intensity": 78,
                "logistic_isolation": 90,
                "sanitary_cases": 132,
                "orbital_area_affected": 66,
            }
        ]
    )

    html = _build_map(prioritized).get_root().render()

    assert "Prioridade IPHO" in html
    assert "Alta" in html
    assert "Média" in html
    assert "Baixa" in html


class FakeHTTPClient:
    def __init__(self, payload):
        self.payload = payload
        self.last_headers = None
        self.last_payload = None

    def post(self, url, headers, json, timeout):
        self.last_url = url
        self.last_headers = headers
        self.last_payload = json
        self.last_timeout = timeout
        return FakeResponse(self.payload)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload
