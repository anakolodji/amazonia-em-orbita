from __future__ import annotations

from typing import Mapping

from orbital.priority_index import sanitary_cases_to_score

REQUIRED_REPORT_SECTIONS = (
    "Resumo da situação",
    "Nível de prioridade",
    "Justificativa",
    "Recomendações",
    "Próximos passos",
)


def generate_humanitarian_report(
    community: Mapping[str, object],
    image_metrics: Mapping[str, float] | None = None,
) -> str:
    context = build_report_context(community, image_metrics)
    action_window = {
        "Alta": "nas próximas 48 horas",
        "Média": "nos próximos 5 dias",
        "Baixa": "no próximo ciclo de monitoramento",
    }.get(context["priority"], "no próximo ciclo de monitoramento")
    recommendations = _recommendations(context["priority"])
    next_steps = _next_steps(context["priority"])

    return (
        f"Relatório humanitário automatizado - {context['name']}\n\n"
        "Resumo da situação:\n"
        f"A comunidade {context['name']}, no território {context['territory']}, apresenta sinais combinados de "
        f"vulnerabilidade ambiental, sanitária e logística. A cena orbital indica {context['affected']:.1f}% "
        f"de área afetada e a base simulada registra {context['sanitary_cases']:.0f} casos sanitários no ciclo atual.\n\n"
        "Nível de prioridade:\n"
        f"{context['priority']} - IPHO {context['ipho']:.1f}/100.\n\n"
        "Justificativa:\n"
        f"A classificação combina risco ambiental ({context['environmental']:.1f}), intensidade de chuva "
        f"({context['rainfall']:.1f}), isolamento logístico ({context['isolation']:.1f}), risco sanitário derivado dos "
        f"casos ({context['sanitary']:.1f}) e área afetada por imagem orbital ({context['affected']:.1f}%).\n\n"
        "Recomendações:\n"
        f"A resposta deve ser planejada {action_window}. {recommendations}\n\n"
        "Próximos passos:\n"
        f"{next_steps}"
    )


def build_report_context(
    community: Mapping[str, object],
    image_metrics: Mapping[str, float] | None = None,
) -> dict[str, float | str]:
    name = str(community["community"])
    territory = str(community.get("territory", "Amazônia Legal"))
    priority = str(community["priority"])
    ipho = float(community["IPHO"])
    environmental = float(community["environmental_risk"])
    rainfall = float(community["rainfall_intensity"])
    isolation = float(community["logistic_isolation"])
    sanitary_cases = float(community["sanitary_cases"])
    sanitary = float(community.get("sanitary_case_score", sanitary_cases_to_score(sanitary_cases)))
    affected = float(community["orbital_area_affected"])

    if image_metrics:
        affected = float(image_metrics.get("affected_area_percent", affected))
        environmental = max(environmental, float(image_metrics.get("environmental_risk", environmental)))

    return {
        "name": name,
        "territory": territory,
        "priority": priority,
        "ipho": ipho,
        "environmental": environmental,
        "rainfall": rainfall,
        "isolation": isolation,
        "sanitary_cases": sanitary_cases,
        "sanitary": sanitary,
        "affected": affected,
    }


def build_llm_messages(
    community: Mapping[str, object],
    image_metrics: Mapping[str, float] | None = None,
) -> list[dict[str, str]]:
    context = build_report_context(community, image_metrics)
    sections = "\n".join(f"- {section}" for section in REQUIRED_REPORT_SECTIONS)
    return [
        {
            "role": "system",
            "content": (
                "Você é uma analista humanitária especializada em Amazônia, dados orbitais, "
                "risco ambiental e priorização de resposta. Escreva em português do Brasil, "
                "com tom técnico, claro e acionável. Não invente dados fora do contexto enviado."
            ),
        },
        {
            "role": "user",
            "content": (
                "Gere um relatório humanitário automatizado para equipes de campo.\n\n"
                "Use exatamente estas seções:\n"
                f"{sections}\n\n"
                "Contexto quantitativo:\n"
                f"- Comunidade: {context['name']}\n"
                f"- Território: {context['territory']}\n"
                f"- Prioridade: {context['priority']}\n"
                f"- IPHO: {context['ipho']:.1f}/100\n"
                f"- Risco ambiental: {context['environmental']:.1f}/100\n"
                f"- Intensidade de chuva: {context['rainfall']:.1f}/100\n"
                f"- Isolamento logístico: {context['isolation']:.1f}/100\n"
                f"- Casos sanitários simulados: {context['sanitary_cases']:.0f}\n"
                f"- Risco sanitário normalizado: {context['sanitary']:.1f}/100\n"
                f"- Área afetada por imagem orbital: {context['affected']:.1f}%\n\n"
                "Regras: seja objetivo, explique a justificativa do IPHO, cite recomendações "
                "práticas e conclua com próximos passos verificáveis."
            ),
        },
    ]


def _recommendations(priority: str) -> str:
    if priority == "Alta":
        return (
            "Recomenda-se priorizar envio de equipe médica, insumos antimaláricos, kits de água "
            "segura, comunicação com lideranças locais e acompanhamento orbital diário."
        )
    if priority == "Média":
        return (
            "Recomenda-se manter pré-posicionamento de insumos, confirmar rotas de acesso e repetir "
            "a análise orbital antes de deslocar equipes."
        )
    return (
        "Recomenda-se manter vigilância remota, registrar sinais ambientais e reservar acionamento "
        "presencial para mudança relevante no IPHO."
    )


def _next_steps(priority: str) -> str:
    if priority == "Alta":
        return (
            "validar a condição em campo, acionar rota logística prioritária, atualizar a imagem "
            "orbital após novo ciclo de chuva e registrar a decisão tomada."
        )
    if priority == "Média":
        return (
            "confirmar dados com lideranças locais, revisar a rota de acesso, repetir a análise "
            "orbital e manter equipe de resposta em prontidão."
        )
    return (
        "manter monitoramento remoto, atualizar os casos sanitários simulados e reprocessar a "
        "imagem orbital no próximo ciclo."
    )
