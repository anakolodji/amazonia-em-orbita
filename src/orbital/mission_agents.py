from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import pandas as pd


@dataclass(frozen=True)
class AgentDecision:
    agent: str
    layer: str
    status: str
    evidence: str
    next_action: str

    def as_dict(self) -> dict[str, str]:
        return {
            "Agente": self.agent,
            "Camada": self.layer,
            "Status": self.status,
            "Evidência": self.evidence,
            "Ação recomendada": self.next_action,
        }


def build_agent_decisions(
    prioritized: pd.DataFrame,
    image_metrics: Mapping[str, float],
    *,
    llm_configured: bool = False,
    nasa_source_enabled: bool = False,
) -> list[AgentDecision]:
    top = prioritized.iloc[0]
    high_priority = int((prioritized["priority_validated"] == "Alta").sum())
    confidence = float(image_metrics.get("segmentation_confidence", 0.0))

    return [
        AgentDecision(
            agent="Agente orbital",
            layer="Dados espaciais",
            status="Fonte NASA ativa" if nasa_source_enabled else "Amostra local ou upload",
            evidence=f"Fonte analisada com confiança visual {confidence:.1f}/100",
            next_action="Usar NASA GIBS quando houver rede; manter fallback local para demo.",
        ),
        AgentDecision(
            agent="Agente de visão computacional",
            layer="Edge/Fog",
            status="HSV + k-means + YOLO-ready",
            evidence=(
                f"Água {image_metrics['water_percent']:.1f}%, vegetação "
                f"{image_metrics['vegetation_percent']:.1f}%, solo exposto "
                f"{image_metrics['exposed_soil_percent']:.1f}%"
            ),
            next_action="Usar fallback YOLO-ready para localizar áreas relevantes por contorno.",
        ),
        AgentDecision(
            agent="Agente IPHO",
            layer="Analytics",
            status="Priorização calculada",
            evidence=(
                f"{top['community']} lidera com IPHO validado "
                f"{top['IPHO_validated']:.1f}/100"
            ),
            next_action="Ordenar fila operacional por prioridade validada.",
        ),
        AgentDecision(
            agent="Agente preditivo ML",
            layer="Machine Learning",
            status="Score auxiliar ativo",
            evidence=f"Risco ML máximo {prioritized['ml_risk_score'].max():.1f}/100",
            next_action="Comparar score ML com IPHO explicável antes do acionamento.",
        ),
        AgentDecision(
            agent="Agente generativo",
            layer="IA Generativa",
            status="API LLM configurada" if llm_configured else "Fallback local",
            evidence="Relatório estruturado em cinco seções obrigatórias com contexto RAG local.",
            next_action="Recuperar protocolos humanitários antes de gerar a síntese.",
        ),
        AgentDecision(
            agent="Agente IoT/sensores",
            layer="Borda",
            status="Tempo real disponível",
            evidence="API Flask e JSONL alimentam a visão de sensores em tempo real.",
            next_action="Substituir simulador por ESP32 em piloto de campo.",
        ),
        AgentDecision(
            agent="Agente cloud/distribuído",
            layer="Cloud",
            status="Arquitetura preparada",
            evidence=f"{len(prioritized)} comunidades podem ser processadas em lote.",
            next_action="Escalar ingestão, cache orbital e geração de relatórios em jobs.",
        ),
    ]


def decisions_to_frame(decisions: list[AgentDecision]) -> pd.DataFrame:
    return pd.DataFrame([decision.as_dict() for decision in decisions])
