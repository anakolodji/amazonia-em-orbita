from __future__ import annotations

from pathlib import Path

import cv2
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from orbital.image_analysis import analyze_image_array, load_image_from_bytes, load_image_from_file
from orbital.llm_client import LLMAPIError, LLMClient
from orbital.priority_index import apply_priority_index
from orbital.report_generator import build_llm_messages, generate_humanitarian_report


PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMMUNITIES_PATH = PROJECT_ROOT / "data" / "communities_orbital.csv"
SAMPLE_IMAGE_DIR = PROJECT_ROOT / "data" / "sample_images"


def main() -> None:
    st.set_page_config(page_title="Amazônia em Órbita", layout="wide")
    _inject_styles()

    communities = _load_communities()
    image_bgr, image_label = _image_source_controls()
    analysis = analyze_image_array(image_bgr)

    linked_community = st.sidebar.selectbox(
        "Cena orbital vinculada",
        communities["community"].tolist(),
        index=0,
    )

    scenario = _apply_image_to_community(communities, linked_community, analysis)
    prioritized = apply_priority_index(scenario)

    priority_filter = st.sidebar.multiselect(
        "Prioridade",
        ["Alta", "Média", "Baixa"],
        default=["Alta", "Média", "Baixa"],
    )
    visible = prioritized[prioritized["priority"].isin(priority_filter)]

    st.title("Amazônia em Órbita")
    st.caption(
        "Sistema inteligente para priorização de áreas vulneráveis usando imagens de satélite, "
        "risco ambiental e geração automática de relatórios humanitários."
    )

    overview_tab, image_tab, priority_tab, report_tab = st.tabs(
        ["Visão geral", "Análise orbital", "Priorização humanitária", "Relatório IA"]
    )

    with overview_tab:
        _render_overview(visible, prioritized)

    with image_tab:
        _render_image_analysis(image_bgr, image_label, linked_community, analysis)

    with priority_tab:
        _render_priority_table(visible)

    with report_tab:
        _render_report(prioritized, linked_community, analysis)


@st.cache_data
def _load_communities() -> pd.DataFrame:
    df = pd.read_csv(COMMUNITIES_PATH)
    score_columns = [
        "environmental_risk",
        "rainfall_intensity",
        "logistic_isolation",
        "sanitary_cases",
        "orbital_area_affected",
    ]
    df[score_columns] = df[score_columns].astype(float)
    return df


def _image_source_controls() -> tuple:
    st.sidebar.header("Análise orbital")
    sample_images = sorted(SAMPLE_IMAGE_DIR.glob("*.png")) + sorted(SAMPLE_IMAGE_DIR.glob("*.jpg"))

    source = st.sidebar.radio("Origem da imagem", ["Amostra", "Upload"], horizontal=True)
    if source == "Upload":
        uploaded = st.sidebar.file_uploader("Imagem orbital", type=["png", "jpg", "jpeg"])
        if uploaded is not None:
            return load_image_from_bytes(uploaded.getvalue()), uploaded.name

    if not sample_images:
        st.error("Nenhuma imagem orbital de amostra foi encontrada.")
        st.stop()

    selected = st.sidebar.selectbox(
        "Imagem orbital",
        sample_images,
        format_func=lambda path: path.stem.replace("_", " ").title(),
    )
    return load_image_from_file(selected), selected.name


def _apply_image_to_community(communities: pd.DataFrame, community: str, analysis) -> pd.DataFrame:
    scenario = communities.copy()
    mask = scenario["community"] == community
    scenario.loc[mask, "orbital_area_affected"] = analysis.affected_area_percent
    scenario.loc[mask, "environmental_risk"] = scenario.loc[mask, "environmental_risk"].map(
        lambda value: max(float(value), analysis.environmental_risk)
    )
    return scenario


def _render_overview(visible: pd.DataFrame, prioritized: pd.DataFrame) -> None:
    high_priority = int((prioritized["priority"] == "Alta").sum())
    avg_ipho = prioritized["IPHO"].mean()
    monitored_people = int(prioritized["monitored_population"].sum())
    last_contact = pd.to_datetime(prioritized["last_contact"]).max().strftime("%d/%m/%Y")

    metric_cols = st.columns(4)
    _metric_card(metric_cols[0], "Comunidades monitoradas", len(prioritized), f"{monitored_people:,} pessoas")
    _metric_card(metric_cols[1], "IPHO médio", f"{avg_ipho:.1f}", "escala 0-100")
    _metric_card(metric_cols[2], "Prioridade alta", high_priority, "áreas críticas")
    _metric_card(metric_cols[3], "Última análise", last_contact, "ciclo orbital")

    map_col, chart_col = st.columns([1.45, 0.75])
    with map_col:
        st.subheader("Mapa operacional")
        st_folium(_build_map(visible), height=520, use_container_width=True, returned_objects=[])

    with chart_col:
        st.subheader("Distribuição IPHO")
        distribution = (
            prioritized["priority"]
            .value_counts()
            .reindex(["Alta", "Média", "Baixa"], fill_value=0)
            .rename_axis("Prioridade")
            .reset_index(name="Comunidades")
        )
        st.bar_chart(distribution, x="Prioridade", y="Comunidades", color="#146b54")
        st.dataframe(
            prioritized[["community", "IPHO", "priority"]].rename(
                columns={"community": "Comunidade", "priority": "Prioridade"}
            ),
            hide_index=True,
            use_container_width=True,
        )


def _render_image_analysis(image_bgr, image_label: str, linked_community: str, analysis) -> None:
    st.subheader(f"Cena orbital vinculada a {linked_community}")

    image_cols = st.columns(2)
    with image_cols[0]:
        st.image(cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB), caption=f"Original: {image_label}")
    with image_cols[1]:
        st.image(analysis.processed_image_rgb, caption="Processamento: água, vegetação e solo exposto")

    metric_cols = st.columns(5)
    _metric_card(metric_cols[0], "Água detectada", f"{analysis.water_percent:.1f}%", "máscara orbital")
    _metric_card(metric_cols[1], "Vegetação", f"{analysis.vegetation_percent:.1f}%", "cobertura estimada")
    _metric_card(metric_cols[2], "Solo exposto", f"{analysis.exposed_soil_percent:.1f}%", "alteração visual")
    _metric_card(metric_cols[3], "Área afetada", f"{analysis.affected_area_percent:.1f}%", "entrada do IPHO")
    _metric_card(metric_cols[4], "Risco ambiental", f"{analysis.environmental_risk:.1f}", "escala 0-100")

    encoded = _encode_png(analysis.processed_image_rgb)
    st.download_button(
        "Baixar imagem processada",
        data=encoded,
        file_name="amazonia_em_orbita_processada.png",
        mime="image/png",
    )


def _render_priority_table(visible: pd.DataFrame) -> None:
    st.subheader("IPHO - Índice de Prioridade Humanitária Orbital")
    table = visible[
        [
            "community",
            "environmental_risk",
            "rainfall_intensity",
            "logistic_isolation",
            "sanitary_cases",
            "sanitary_case_score",
            "orbital_area_affected",
            "IPHO",
            "priority",
        ]
    ].rename(
        columns={
            "community": "Comunidade",
            "environmental_risk": "Risco ambiental",
            "rainfall_intensity": "Intensidade de chuva",
            "logistic_isolation": "Isolamento",
            "sanitary_cases": "Casos sanitários",
            "sanitary_case_score": "Risco sanitário",
            "orbital_area_affected": "Área afetada",
            "priority": "Prioridade",
        }
    )
    st.dataframe(table, hide_index=True, use_container_width=True)


def _render_report(prioritized: pd.DataFrame, linked_community: str, analysis) -> None:
    st.subheader("Relatório humanitário automatizado")
    llm_client = LLMClient()
    llm_enabled = st.toggle("Usar API LLM", value=True)
    status_label = "API LLM configurada" if llm_client.is_configured else "Fallback local"
    st.caption(f"Modo: {status_label}")

    selected = st.selectbox(
        "Comunidade",
        prioritized["community"].tolist(),
        index=int(prioritized.index[prioritized["community"] == linked_community][0])
        if linked_community in prioritized["community"].values
        else 0,
    )
    row = prioritized[prioritized["community"] == selected].iloc[0].to_dict()

    if st.button("Gerar relatório humanitário", type="primary"):
        fallback_report = generate_humanitarian_report(row, analysis.as_dict())
        st.session_state["orbital_report_source"] = "Fallback local"

        if llm_enabled and llm_client.is_configured:
            try:
                with st.spinner("Gerando relatório com API LLM..."):
                    st.session_state["orbital_report"] = llm_client.generate_text(
                        build_llm_messages(row, analysis.as_dict())
                    )
                st.session_state["orbital_report_source"] = "API LLM"
            except LLMAPIError as exc:
                st.session_state["orbital_report"] = fallback_report
                st.warning(f"API LLM indisponível. Relatório local gerado. Detalhe: {exc}")
        else:
            st.session_state["orbital_report"] = fallback_report
            if llm_enabled:
                st.info("Configure LLM_API_KEY e LLM_MODEL para gerar com API LLM.")

    if "orbital_report" in st.session_state:
        st.caption(f"Fonte: {st.session_state.get('orbital_report_source', 'Fallback local')}")
        st.text_area("Saída", st.session_state["orbital_report"], height=330)
        st.download_button(
            "Baixar relatório",
            data=st.session_state["orbital_report"].encode("utf-8"),
            file_name=f"relatorio_{selected.lower().replace(' ', '_')}.txt",
            mime="text/plain",
        )


def _build_map(df: pd.DataFrame) -> folium.Map:
    map_object = folium.Map(location=[1.7, -64.2], zoom_start=6, tiles="CartoDB positron", control_scale=True)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satélite",
        overlay=False,
        control=True,
    ).add_to(map_object)

    for _, row in df.iterrows():
        color = _priority_color(row["priority"])
        popup = (
            f"<strong>{row['community']}</strong><br>"
            f"IPHO: {row['IPHO']:.1f}<br>"
            f"Prioridade: {row['priority']}<br>"
            f"Chuva: {row['rainfall_intensity']:.1f}/100<br>"
            f"Casos sanitários: {int(row['sanitary_cases'])}<br>"
            f"Área afetada: {row['orbital_area_affected']:.1f}%"
        )
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=7 + row["IPHO"] / 16,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.72,
            popup=popup,
        ).add_to(map_object)

    folium.LayerControl(collapsed=True).add_to(map_object)
    map_object.get_root().html.add_child(folium.Element(_legend_html()))
    return map_object


def _priority_color(priority: str) -> str:
    return {"Alta": "#b91c1c", "Média": "#d97706", "Baixa": "#146b54"}.get(priority, "#2563eb")


def _legend_html() -> str:
    return """
    <div style="
        position: fixed;
        bottom: 28px;
        left: 28px;
        z-index: 9999;
        background: #ffffff;
        border: 1px solid #d9ded6;
        border-radius: 8px;
        box-shadow: 0 8px 22px rgba(23, 33, 29, 0.14);
        padding: 12px 14px;
        color: #17211d;
        font-family: Arial, sans-serif;
        font-size: 13px;
        line-height: 1.35;">
        <strong style="display:block;margin-bottom:8px;">Prioridade IPHO</strong>
        <div><span style="display:inline-block;width:11px;height:11px;background:#b91c1c;border-radius:50%;margin-right:7px;"></span>Alta</div>
        <div><span style="display:inline-block;width:11px;height:11px;background:#d97706;border-radius:50%;margin-right:7px;"></span>Média</div>
        <div><span style="display:inline-block;width:11px;height:11px;background:#146b54;border-radius:50%;margin-right:7px;"></span>Baixa</div>
    </div>
    """


def _metric_card(container, label: str, value, detail: str) -> None:
    container.markdown(
        f"""
        <div class="metric-card">
            <span>{label}</span>
            <strong>{value}</strong>
            <small>{detail}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _encode_png(image_rgb) -> bytes:
    success, encoded = cv2.imencode(".png", cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR))
    if not success:
        raise ValueError("Não foi possível codificar a imagem processada.")
    return encoded.tobytes()


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: #f6f7f3;
            color: #17211d;
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1280px;
        }
        h1, h2, h3, p, span, label {
            letter-spacing: 0;
        }
        .metric-card {
            min-height: 122px;
            border: 1px solid #d9ded6;
            border-top: 4px solid #146b54;
            border-radius: 8px;
            background: #ffffff;
            padding: 16px 16px 14px;
            box-shadow: 0 8px 22px rgba(23, 33, 29, 0.06);
        }
        .metric-card span {
            display: block;
            color: #56635b;
            font-size: 0.82rem;
            line-height: 1.25;
        }
        .metric-card strong {
            display: block;
            color: #17211d;
            font-size: clamp(1.25rem, 2.2vw, 2rem);
            line-height: 1.1;
            margin-top: 8px;
            word-break: break-word;
        }
        .metric-card small {
            display: block;
            color: #6f786f;
            font-size: 0.78rem;
            line-height: 1.3;
            margin-top: 10px;
        }
        div[data-testid="stTabs"] button {
            border-radius: 8px 8px 0 0;
        }
        div[data-testid="stDownloadButton"] button,
        div[data-testid="stButton"] button {
            border-radius: 8px;
            min-height: 42px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
