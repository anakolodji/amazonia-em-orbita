from datetime import date
from urllib.parse import parse_qs, urlparse

import cv2
import numpy as np

from orbital.image_analysis import analyze_image_array
from orbital.llm_client import LLMAPIError, LLMClient, LLMConfig
from orbital.mission_agents import build_agent_decisions
from orbital.ml_risk_model import blend_ipho_with_ml, predict_ml_risk_score
from orbital.nasa_gibs import (
    GIBS_LAYER_OPTIONS,
    GIBS_REGION_OPTIONS,
    build_gibs_wms_url,
    fetch_gibs_scene,
)
from orbital.priority_index import (
    PriorityInputs,
    apply_priority_index,
    calculate_ipho,
    classify_priority,
    sanitary_cases_to_score,
)
from orbital.rag import retrieve_humanitarian_context
from orbital.report_generator import (
    REQUIRED_REPORT_SECTIONS,
    build_llm_messages,
    generate_humanitarian_report,
)
from orbital.sensor_stream import load_sensor_readings, summarize_sensor_risk
from orbital.yolo_detector import detect_orbital_objects
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
    assert result.iloc[0]["priority_validated"] == "Alta"
    assert result.iloc[0]["ml_risk_score"] > 50
    assert result.iloc[0]["IPHO_validated"] > 70


def test_predictive_model_blends_with_explainable_ipho():
    ml_score = predict_ml_risk_score(
        {
            "environmental_risk": 82,
            "sanitary_case_score": 82.5,
            "logistic_isolation": 90,
            "rainfall_intensity": 78,
            "orbital_area_affected": 66,
        }
    )

    assert ml_score > 70
    assert blend_ipho_with_ml(81.5, ml_score) > 78


def test_analyze_image_array_detects_water_and_vegetation():
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    image[:, :50] = (190, 90, 20)
    image[:, 50:] = (45, 130, 45)

    analysis = analyze_image_array(image)

    assert analysis.water_percent > 40
    assert analysis.vegetation_percent > 40
    assert analysis.affected_area_percent > 40
    assert analysis.segmentation_confidence > 80
    assert "k-means" in analysis.analysis_method


def test_yolo_ready_detector_returns_contour_detections():
    image = np.zeros((120, 120, 3), dtype=np.uint8)
    image[:60, :] = (190, 90, 20)
    image[60:, :] = (45, 130, 45)
    analysis = analyze_image_array(image)

    detections = detect_orbital_objects(analysis)
    labels = {detection.label for detection in detections}

    assert "água superficial" in labels
    assert "vegetação densa" in labels
    assert all(detection.model.startswith("YOLO-ready") for detection in detections)


def test_rag_retrieves_humanitarian_protocol_context():
    snippets = retrieve_humanitarian_context(
        "prioridade alta chuva isolamento casos sanitarios água segura liderança local",
        top_k=2,
    )

    assert snippets
    assert any("Prioridade alta" in snippet.text for snippet in snippets)


def test_build_gibs_wms_url_uses_nasa_parameters():
    url = build_gibs_wms_url(
        layer=GIBS_LAYER_OPTIONS["MODIS Terra True Color"],
        image_date=date(2025, 6, 1),
        bbox=GIBS_REGION_OPTIONS["Yanomami / Roraima"].bbox,
    )
    params = parse_qs(urlparse(url).query)

    assert "gibs.earthdata.nasa.gov" in url
    assert params["SERVICE"] == ["WMS"]
    assert params["REQUEST"] == ["GetMap"]
    assert params["LAYERS"] == ["MODIS_Terra_CorrectedReflectance_TrueColor"]
    assert params["TIME"] == ["2025-06-01"]


def test_fetch_gibs_scene_decodes_image_with_fake_http():
    image = np.zeros((12, 12, 3), dtype=np.uint8)
    image[:, :] = (190, 90, 20)
    success, encoded = cv2.imencode(".jpg", image)
    assert success

    scene = fetch_gibs_scene(
        layer=GIBS_LAYER_OPTIONS["MODIS Terra True Color"],
        region=GIBS_REGION_OPTIONS["Yanomami / Roraima"],
        image_date=date(2025, 6, 1),
        http_client=FakeGetHTTPClient(encoded.tobytes()),
    )

    assert scene.image_bgr.shape[:2] == (12, 12)
    assert "MODIS Terra True Color" in scene.label
    assert "gibs.earthdata.nasa.gov" in scene.source_url


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
    assert "Contexto RAG recuperado" in report


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
    assert "Contexto RAG local recuperado" in prompt


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
    assert fake_http.last_payload["max_tokens"] == 2048
    assert fake_http.last_payload["stream"] is False
    assert fake_http.last_payload["messages"][0]["content"] == "gere relatório"
    assert fake_http.last_headers["Authorization"] == "Bearer test-key"
    assert fake_http.last_stream is False


def test_llm_client_accumulates_streaming_chunks():
    fake_http = FakeHTTPClient(
        stream_lines=[
            'data: {"choices":[{"delta":{"content":"Resumo "}}]}',
            'data: {"choices":[{"delta":{"content":"completo "}}]}',
            'data: {"choices":[{"delta":{"content":"gerado."}}]}',
            "data: [DONE]",
        ]
    )
    client = LLMClient(
        config=LLMConfig(
            api_key="test-key",
            model="test-model",
            api_url="https://example.com/v1/chat/completions",
            stream=True,
        ),
        http_client=fake_http,
    )

    text = client.generate_text([{"role": "user", "content": "gere relatório"}])

    assert text == "Resumo completo gerado."
    assert fake_http.last_payload["stream"] is True
    assert fake_http.last_stream is True


def test_llm_client_parses_event_stream_body_even_without_stream_flag():
    fake_http = FakeHTTPClient(
        text=(
            'data: {"choices":[{"delta":{"content":"Primeira parte "}}]}\n\n'
            'data: {"choices":[{"delta":{"content":"segunda parte."}}]}\n\n'
            "data: [DONE]\n"
        ),
        headers={"content-type": "text/event-stream"},
        json_error=True,
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

    assert text == "Primeira parte segunda parte."


def test_llm_client_continues_truncated_response():
    fake_http = FakeHTTPClient(
        payloads=[
            {
                "choices": [
                    {
                        "finish_reason": "length",
                        "message": {
                            "content": "Resumo da situação:\nA comunidade fica na Terra Ind"
                        },
                    }
                ]
            },
            {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": (
                                "ígena Yanomami.\n\n"
                                "Nível de prioridade:\nAlta.\n\n"
                                "Justificativa:\nIPHO elevado por risco ambiental e isolamento.\n\n"
                                "Recomendações:\nPriorizar equipe de saúde e insumos.\n\n"
                                "Próximos passos:\nValidar rota e acionar liderança local."
                            )
                        },
                    }
                ]
            },
        ]
    )
    client = LLMClient(
        config=LLMConfig(
            api_key="test-key",
            model="test-model",
            api_url="https://example.com/v1/chat/completions",
        ),
        http_client=fake_http,
    )

    text = client.generate_text(
        [{"role": "user", "content": "gere relatório"}],
        required_markers=REQUIRED_REPORT_SECTIONS,
        min_chars=120,
    )

    assert "Terra Indígena Yanomami" in text
    assert "Próximos passos" in text
    assert len(fake_http.requests) == 2
    assert "resposta anterior foi interrompida" in fake_http.requests[1]["messages"][-1][
        "content"
    ]


def test_llm_config_defaults_low_reasoning_for_google(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "gemini-test")
    monkeypatch.setenv(
        "LLM_API_URL",
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
    )
    monkeypatch.delenv("LLM_REASONING_EFFORT", raising=False)

    config = LLMConfig.from_env()

    assert config.reasoning_effort == "low"
    assert config.max_tokens == 2048


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


def test_sensor_stream_loads_realtime_jsonl(tmp_path):
    sensor_file = tmp_path / "sensores.jsonl"
    sensor_file.write_text(
        "\n".join(
            [
                '{"temperatura": 26.5, "umidade": 78.0, "chuva": 64.0, "timestamp": "2026-06-16T12:00:00"}',
                '{"temperatura": 31.0, "umidade": 40.0, "chuva": 10.0, "timestamp": "2026-06-16T12:00:05"}',
            ]
        ),
        encoding="utf-8",
    )

    readings = load_sensor_readings(sensor_file)
    summary = summarize_sensor_risk(readings)

    assert len(readings) == 2
    assert readings.iloc[0]["risk_label"] in {"Alto", "Médio", "Baixo"}
    assert summary.total_readings == 2
    assert summary.latest_score >= 0


def test_agent_orchestration_contains_space_ai_and_edge_layers():
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

    decisions = build_agent_decisions(
        prioritized,
        {
            "water_percent": 19.1,
            "vegetation_percent": 71.9,
            "exposed_soil_percent": 8.9,
            "affected_area_percent": 28.7,
            "environmental_risk": 82.0,
            "segmentation_confidence": 99.0,
        },
        llm_configured=True,
        nasa_source_enabled=True,
    )
    agents = {decision.agent for decision in decisions}

    assert "Agente orbital" in agents
    assert "Agente preditivo ML" in agents
    assert "Agente IoT/sensores" in agents
    assert "Agente cloud/distribuído" in agents


class FakeHTTPClient:
    def __init__(
        self,
        payload=None,
        payloads=None,
        stream_lines=None,
        text="",
        headers=None,
        json_error=False,
    ):
        self.payload = payload
        self.payloads = list(payloads or [])
        self.stream_lines = stream_lines or []
        self.text = text
        self.headers = headers or {}
        self.json_error = json_error
        self.requests = []
        self.last_headers = None
        self.last_payload = None
        self.last_stream = None

    def post(self, url, headers, json, timeout, stream=False):
        self.last_url = url
        self.last_headers = headers
        self.last_payload = json
        self.last_timeout = timeout
        self.last_stream = stream
        self.requests.append(json)
        payload = self.payloads.pop(0) if self.payloads else self.payload
        return FakeResponse(
            payload,
            stream_lines=self.stream_lines,
            text=self.text,
            headers=self.headers,
            json_error=self.json_error,
        )


class FakeResponse:
    def __init__(self, payload, stream_lines=None, text="", headers=None, json_error=False):
        self.payload = payload
        self.stream_lines = stream_lines or []
        self.text = text
        self.headers = headers or {}
        self.json_error = json_error

    def raise_for_status(self):
        return None

    def json(self):
        if self.json_error:
            raise ValueError("not json")
        return self.payload

    def iter_lines(self, decode_unicode=False):
        for line in self.stream_lines:
            if decode_unicode:
                yield line
            else:
                yield line.encode("utf-8")


class FakeGetHTTPClient:
    def __init__(self, content: bytes):
        self.content = content
        self.last_url = None
        self.last_timeout = None

    def get(self, url, timeout):
        self.last_url = url
        self.last_timeout = timeout
        return FakeGetResponse(self.content)


class FakeGetResponse:
    headers = {"content-type": "image/jpeg"}

    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self):
        return None
