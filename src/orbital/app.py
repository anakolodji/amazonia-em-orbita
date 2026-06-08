from __future__ import annotations

from pathlib import Path

import cv2
import altair as alt
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from orbital.image_analysis import analyze_image_array, load_image_from_bytes, load_image_from_file
from orbital.llm_client import LLMAPIError, LLMClient
from orbital.priority_index import apply_priority_index
from orbital.report_generator import (
    REQUIRED_REPORT_SECTIONS,
    build_llm_messages,
    generate_humanitarian_report,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMMUNITIES_PATH = PROJECT_ROOT / "data" / "communities_orbital.csv"
SAMPLE_IMAGE_DIR = PROJECT_ROOT / "data" / "sample_images"
VIEW_OPTIONS = ("Território", "Imagem orbital", "IPHO", "Relatório IA")
PRIORITY_ORDER = ["Alta", "Média", "Baixa"]
PRIORITY_COLORS = {
    "Alta": "#b91c1c",
    "Média": "#d97706",
    "Baixa": "#146b54",
}


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

    _render_sidebar_summary(prioritized, linked_community, analysis)
    _render_page_header(prioritized, linked_community)

    active_view = _render_view_navigation()
    if active_view == "Território":
        _render_overview(visible, prioritized)
    elif active_view == "Imagem orbital":
        _render_image_analysis(image_bgr, image_label, linked_community, analysis)
    elif active_view == "IPHO":
        _render_priority_table(visible)
    else:
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
    st.sidebar.title("Amazônia em Órbita")
    st.sidebar.caption("Monitoramento orbital para priorização humanitária.")
    st.sidebar.divider()
    st.sidebar.subheader("Imagem orbital")
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


def _render_sidebar_summary(prioritized: pd.DataFrame, linked_community: str, analysis) -> None:
    selected = prioritized[prioritized["community"] == linked_community]
    if selected.empty:
        return

    row = selected.iloc[0]
    st.sidebar.divider()
    st.sidebar.subheader("Cena vinculada")
    st.sidebar.markdown(
        f"""
        <div class="sidebar-summary">
            <strong>{linked_community}</strong>
            <span>IPHO {row['IPHO']:.1f} · {row['priority']}</span>
            <small>{analysis.affected_area_percent:.1f}% de área afetada na imagem atual</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _apply_image_to_community(communities: pd.DataFrame, community: str, analysis) -> pd.DataFrame:
    scenario = communities.copy()
    mask = scenario["community"] == community
    scenario.loc[mask, "orbital_area_affected"] = analysis.affected_area_percent
    scenario.loc[mask, "environmental_risk"] = scenario.loc[mask, "environmental_risk"].map(
        lambda value: max(float(value), analysis.environmental_risk)
    )
    return scenario


def _render_page_header(prioritized: pd.DataFrame, linked_community: str) -> None:
    selected = prioritized[prioritized["community"] == linked_community]
    priority = selected.iloc[0]["priority"] if not selected.empty else "Média"
    ipho = selected.iloc[0]["IPHO"] if not selected.empty else prioritized["IPHO"].mean()
    badge_class = f"priority-badge priority-{_priority_slug(priority)}"

    st.markdown(
        f"""
        <section class="app-header">
            <div>
                <span class="eyebrow">Inteligência espacial aplicada à Amazônia</span>
                <h1>Amazônia em Órbita</h1>
                <p>Sistema de apoio à decisão para priorizar comunidades vulneráveis a partir de imagem orbital, chuva, isolamento e casos sanitários.</p>
            </div>
            <div class="header-status">
                <span class="{badge_class}">{priority}</span>
                <strong>{ipho:.1f}</strong>
                <small>IPHO da cena selecionada</small>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_view_navigation() -> str:
    if "orbital_active_view" not in st.session_state:
        st.session_state["orbital_active_view"] = VIEW_OPTIONS[0]

    active_view = st.segmented_control(
        "Visão",
        VIEW_OPTIONS,
        key="orbital_active_view",
        label_visibility="collapsed",
    )

    if active_view not in VIEW_OPTIONS:
        active_view = VIEW_OPTIONS[0]
        st.session_state["orbital_active_view"] = active_view
    return str(active_view)


def _render_overview(visible: pd.DataFrame, prioritized: pd.DataFrame) -> None:
    high_priority = int((prioritized["priority"] == "Alta").sum())
    avg_ipho = prioritized["IPHO"].mean()
    monitored_people = int(prioritized["monitored_population"].sum())
    last_contact = pd.to_datetime(prioritized["last_contact"]).max().strftime("%d/%m/%Y")
    top = prioritized.iloc[0]

    metric_cols = st.columns(4)
    _metric_card(metric_cols[0], "Comunidades monitoradas", len(prioritized), f"{monitored_people:,} pessoas", "blue")
    _metric_card(metric_cols[1], "IPHO médio", f"{avg_ipho:.1f}", "escala 0-100", _score_tone(avg_ipho))
    _metric_card(metric_cols[2], "Prioridade alta", high_priority, "áreas críticas", "critical" if high_priority else "ok")
    _metric_card(metric_cols[3], "Última análise", last_contact, "ciclo orbital", "neutral")

    _insight_strip(top)

    map_col, chart_col = st.columns([1.45, 0.75])
    with map_col:
        st.subheader("Mapa operacional")
        st_folium(_build_map(visible), height=520, use_container_width=True, returned_objects=[])

    with chart_col:
        st.subheader("Distribuição IPHO")
        distribution = (
            prioritized["priority"]
            .value_counts()
            .reindex(PRIORITY_ORDER, fill_value=0)
            .rename_axis("Prioridade")
            .reset_index(name="Comunidades")
        )
        st.altair_chart(_priority_chart(distribution), use_container_width=True)
        st.dataframe(
            prioritized[["community", "IPHO", "priority"]].rename(
                columns={"community": "Comunidade", "priority": "Prioridade"}
            ),
            hide_index=True,
            use_container_width=True,
            column_config={
                "IPHO": st.column_config.ProgressColumn("IPHO", min_value=0, max_value=100, format="%.1f"),
            },
        )


def _render_image_analysis(image_bgr, image_label: str, linked_community: str, analysis) -> None:
    st.subheader(f"Cena orbital vinculada a {linked_community}")

    image_cols = st.columns(2)
    with image_cols[0]:
        st.image(cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB), caption=f"Original: {image_label}")
    with image_cols[1]:
        st.image(analysis.processed_image_rgb, caption="Processamento: água, vegetação e solo exposto")

    metric_cols = st.columns(5)
    _metric_card(metric_cols[0], "Água detectada", f"{analysis.water_percent:.1f}%", "máscara orbital", "blue")
    _metric_card(metric_cols[1], "Vegetação", f"{analysis.vegetation_percent:.1f}%", "cobertura estimada", "ok")
    _metric_card(metric_cols[2], "Solo exposto", f"{analysis.exposed_soil_percent:.1f}%", "alteração visual", "warning")
    _metric_card(metric_cols[3], "Área afetada", f"{analysis.affected_area_percent:.1f}%", "entrada do IPHO", _score_tone(analysis.affected_area_percent))
    _metric_card(metric_cols[4], "Risco ambiental", f"{analysis.environmental_risk:.1f}", "escala 0-100", _score_tone(analysis.environmental_risk))

    st.markdown(
        """
        <div class="overlay-legend">
            <span><i class="swatch swatch-water"></i>Água</span>
            <span><i class="swatch swatch-vegetation"></i>Vegetação</span>
            <span><i class="swatch swatch-soil"></i>Solo exposto</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
    st.dataframe(
        table,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Risco ambiental": st.column_config.ProgressColumn("Risco ambiental", min_value=0, max_value=100, format="%.1f"),
            "Intensidade de chuva": st.column_config.ProgressColumn("Intensidade de chuva", min_value=0, max_value=100, format="%.1f"),
            "Isolamento": st.column_config.ProgressColumn("Isolamento", min_value=0, max_value=100, format="%.1f"),
            "Risco sanitário": st.column_config.ProgressColumn("Risco sanitário", min_value=0, max_value=100, format="%.1f"),
            "Área afetada": st.column_config.ProgressColumn("Área afetada", min_value=0, max_value=100, format="%.1f"),
            "IPHO": st.column_config.ProgressColumn("IPHO", min_value=0, max_value=100, format="%.1f"),
            "Casos sanitários": st.column_config.NumberColumn("Casos sanitários", format="%d"),
        },
    )


def _render_report(prioritized: pd.DataFrame, linked_community: str, analysis) -> None:
    st.subheader("Relatório humanitário automatizado")
    llm_client = LLMClient()
    status_label = "API LLM configurada" if llm_client.is_configured else "Fallback local"

    control_col, report_col = st.columns([0.36, 0.64])
    with control_col:
        st.markdown(
            f"""
            <div class="report-status">
                <span>Modo de geração</span>
                <strong>{status_label}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
        llm_enabled = st.toggle("Usar API LLM", value=True)
        selected = st.selectbox(
            "Comunidade",
            prioritized["community"].tolist(),
            index=int(prioritized.index[prioritized["community"] == linked_community][0])
            if linked_community in prioritized["community"].values
            else 0,
        )

        row = prioritized[prioritized["community"] == selected].iloc[0].to_dict()

        if st.button("Gerar relatório humanitário", type="primary", use_container_width=True):
            fallback_report = generate_humanitarian_report(row, analysis.as_dict())
            st.session_state["orbital_report_source"] = "Fallback local"

            if llm_enabled and llm_client.is_configured:
                try:
                    with st.spinner("Gerando relatório com API LLM..."):
                        st.session_state["orbital_report"] = llm_client.generate_text(
                            build_llm_messages(row, analysis.as_dict()),
                            required_markers=REQUIRED_REPORT_SECTIONS,
                            min_chars=600,
                        )
                    st.session_state["orbital_report_source"] = "API LLM"
                except LLMAPIError as exc:
                    st.session_state["orbital_report"] = fallback_report
                    st.warning(f"API LLM indisponível. Relatório local gerado. Detalhe: {exc}")
            else:
                st.session_state["orbital_report"] = fallback_report
                if llm_enabled:
                    st.info("Configure LLM_API_KEY e LLM_MODEL para gerar com API LLM.")

    with report_col:
        if "orbital_report" in st.session_state:
            st.caption(f"Fonte: {st.session_state.get('orbital_report_source', 'Fallback local')}")
            st.text_area("Saída", st.session_state["orbital_report"], height=380)
            st.download_button(
                "Baixar relatório",
                data=st.session_state["orbital_report"].encode("utf-8"),
                file_name=f"relatorio_{selected.lower().replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        else:
            st.markdown(
                """
                <div class="empty-report">
                    <strong>Relatório ainda não gerado</strong>
                    <span>Selecione a comunidade e gere a síntese para visualizar a saída nesta área.</span>
                </div>
                """,
                unsafe_allow_html=True,
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
    return PRIORITY_COLORS.get(priority, "#2563eb")


def _priority_slug(priority: str) -> str:
    return {"Alta": "high", "Média": "medium", "Baixa": "low"}.get(priority, "medium")


def _score_tone(score: float) -> str:
    if score >= 70:
        return "critical"
    if score >= 40:
        return "warning"
    return "ok"


def _insight_strip(top: pd.Series) -> None:
    st.markdown(
        f"""
        <div class="insight-strip">
            <span class="priority-dot priority-dot-{_priority_slug(top['priority'])}"></span>
            <div>
                <strong>{top['community']} lidera a fila operacional</strong>
                <small>IPHO {top['IPHO']:.1f} · {top['priority']} · {int(top['sanitary_cases'])} casos sanitários · {top['rainfall_intensity']:.1f}/100 chuva</small>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _priority_chart(distribution: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(distribution)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("Prioridade:N", sort=PRIORITY_ORDER, title=None),
            y=alt.Y("Comunidades:Q", title=None, axis=alt.Axis(tickMinStep=1)),
            color=alt.Color(
                "Prioridade:N",
                scale=alt.Scale(domain=PRIORITY_ORDER, range=[PRIORITY_COLORS[item] for item in PRIORITY_ORDER]),
                legend=None,
            ),
            tooltip=["Prioridade", "Comunidades"],
        )
        .properties(height=220)
    )


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


def _metric_card(container, label: str, value, detail: str, tone: str = "neutral") -> None:
    container.markdown(
        f"""
        <div class="metric-card metric-{tone}">
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
            background: #f5f7f4;
            color: #17211d;
        }
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1280px;
        }
        section[data-testid="stSidebar"] {
            background: #eef2ec;
            border-right: 1px solid #d9ded6;
        }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: #17211d;
        }
        h1, h2, h3, p, span, label {
            letter-spacing: 0;
        }
        .stApp,
        .block-container,
        [data-testid="stAppViewContainer"],
        [data-testid="stSidebar"],
        [data-testid="stMarkdownContainer"],
        [data-testid="stCaptionContainer"],
        [data-testid="stWidgetLabel"],
        [data-testid="stWidgetLabel"] p {
            color: #17211d !important;
        }
        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p,
        [data-testid="stCaptionContainer"] span {
            color: #4f5d55 !important;
        }
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] textarea,
        [data-testid="stTextArea"] textarea,
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input {
            background-color: #ffffff !important;
            color: #17211d !important;
            -webkit-text-fill-color: #17211d !important;
            border-color: #cbd3ca !important;
        }
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] svg,
        div[data-baseweb="popover"] *,
        [data-testid="stMultiSelect"] span,
        [data-testid="stFileUploader"] *,
        [data-testid="stTextArea"] textarea::placeholder {
            color: #17211d !important;
            -webkit-text-fill-color: #17211d !important;
        }
        [data-testid="stFileUploader"] section {
            background-color: #ffffff !important;
            border-color: #cbd3ca !important;
        }
        button[data-baseweb="tab"] p {
            color: #4f5d55 !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] p {
            color: #146b54 !important;
            font-weight: 700;
        }
        div[data-testid="stDataFrame"],
        div[data-testid="stDataFrame"] * {
            color: #17211d !important;
        }
        div[data-testid="stButton"] button,
        div[data-testid="stDownloadButton"] button {
            background-color: #ffffff !important;
            color: #17211d !important;
            border: 1px solid #cbd3ca !important;
        }
        div[data-testid="stButton"] button *,
        div[data-testid="stDownloadButton"] button * {
            color: inherit !important;
        }
        div[data-testid="stButton"] button[kind="primary"] {
            background-color: #146b54 !important;
            color: #ffffff !important;
            border-color: #146b54 !important;
        }
        .stAlert,
        .stAlert * {
            color: #17211d !important;
        }
        .app-header {
            display: flex;
            align-items: stretch;
            justify-content: space-between;
            gap: 20px;
            padding: 22px 0 18px;
            border-bottom: 1px solid #d9ded6;
            margin-bottom: 18px;
        }
        .app-header h1 {
            font-size: clamp(2rem, 4vw, 3.6rem);
            line-height: 1;
            margin: 4px 0 10px;
            color: #17211d;
        }
        .app-header p {
            max-width: 780px;
            margin: 0;
            color: #4f5d55;
            font-size: 1rem;
            line-height: 1.45;
        }
        .eyebrow {
            color: #146b54;
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
        }
        .header-status {
            min-width: 180px;
            border: 1px solid #d9ded6;
            border-radius: 8px;
            background: #ffffff;
            padding: 16px;
            align-self: stretch;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .header-status strong {
            display: block;
            font-size: 2.2rem;
            line-height: 1;
            margin-top: 10px;
            color: #17211d;
        }
        .header-status small {
            color: #6f786f;
            margin-top: 8px;
        }
        .priority-badge {
            width: fit-content;
            border-radius: 999px;
            padding: 5px 10px;
            color: #ffffff;
            font-size: 0.76rem;
            font-weight: 700;
        }
        .priority-high { background: #b91c1c; }
        .priority-medium { background: #d97706; }
        .priority-low { background: #146b54; }
        .sidebar-summary {
            border: 1px solid #d9ded6;
            border-radius: 8px;
            background: #ffffff;
            padding: 12px;
        }
        .sidebar-summary strong,
        .sidebar-summary span,
        .sidebar-summary small {
            display: block;
        }
        .sidebar-summary strong {
            color: #17211d;
            font-size: 0.95rem;
        }
        .sidebar-summary span {
            color: #146b54;
            font-weight: 700;
            margin-top: 4px;
        }
        .sidebar-summary small {
            color: #6f786f;
            margin-top: 8px;
            line-height: 1.35;
        }
        .metric-card {
            min-height: 122px;
            border: 1px solid #d9ded6;
            border-top: 4px solid #69766e;
            border-radius: 8px;
            background: #ffffff;
            padding: 16px 16px 14px;
            box-shadow: 0 8px 22px rgba(23, 33, 29, 0.06);
        }
        .metric-critical { border-top-color: #b91c1c; }
        .metric-warning { border-top-color: #d97706; }
        .metric-ok { border-top-color: #146b54; }
        .metric-blue { border-top-color: #2563eb; }
        .metric-neutral { border-top-color: #69766e; }
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
        .insight-strip {
            display: flex;
            align-items: center;
            gap: 12px;
            border: 1px solid #d9ded6;
            border-radius: 8px;
            background: #ffffff;
            padding: 13px 15px;
            margin: 16px 0 18px;
        }
        .insight-strip strong,
        .insight-strip small {
            display: block;
        }
        .insight-strip strong {
            color: #17211d;
        }
        .insight-strip small {
            color: #6f786f;
            margin-top: 3px;
            line-height: 1.35;
        }
        .priority-dot {
            width: 13px;
            height: 13px;
            border-radius: 50%;
            flex: 0 0 auto;
        }
        .priority-dot-high { background: #b91c1c; }
        .priority-dot-medium { background: #d97706; }
        .priority-dot-low { background: #146b54; }
        .overlay-legend {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            border: 1px solid #d9ded6;
            border-radius: 8px;
            background: #ffffff;
            padding: 10px 12px;
            margin: 12px 0 14px;
            width: fit-content;
        }
        .overlay-legend span {
            color: #4f5d55;
            font-size: 0.86rem;
            font-weight: 600;
        }
        .swatch {
            display: inline-block;
            width: 11px;
            height: 11px;
            border-radius: 3px;
            margin-right: 6px;
            vertical-align: -1px;
        }
        .swatch-water { background: #1e68d2; }
        .swatch-vegetation { background: #2e7d32; }
        .swatch-soil { background: #bf7e29; }
        .report-status,
        .empty-report {
            border: 1px solid #d9ded6;
            border-radius: 8px;
            background: #ffffff;
            padding: 14px;
            margin-bottom: 14px;
        }
        .report-status span,
        .report-status strong,
        .empty-report strong,
        .empty-report span {
            display: block;
        }
        .report-status span,
        .empty-report span {
            color: #6f786f;
            font-size: 0.85rem;
            line-height: 1.35;
        }
        .report-status strong,
        .empty-report strong {
            color: #17211d;
            margin-top: 4px;
        }
        .empty-report {
            min-height: 380px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        div[data-testid="stSegmentedControl"] {
            margin-bottom: 20px;
        }
        div[data-testid="stSegmentedControl"] label {
            color: #17211d !important;
        }
        div[data-testid="stSegmentedControl"] button {
            border-radius: 8px !important;
            min-height: 42px;
            color: #17211d !important;
        }
        div[data-testid="stDownloadButton"] button,
        div[data-testid="stButton"] button {
            border-radius: 8px;
            min-height: 42px;
        }
        @media (max-width: 760px) {
            .app-header {
                flex-direction: column;
            }
            .header-status {
                min-width: 0;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
