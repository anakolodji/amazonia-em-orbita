import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# Imports do projeto

# Simulação de dados — substitua pelo seu DataFrame real
data = pd.DataFrame({
    'municipio': ['Manaus', 'Boa Vista', 'Tabatinga', 'Uarini', 'Tefé'],
    'estado': ['AM', 'RR', 'AM', 'AM', 'AM'],
    'casos': [320, 180, 500, 80, 250],
    'obitos': [2, 1, 3, 0, 1],
    'risco_inundacao': [1, 0, 1, 1, 0],
    'risco_predito_heuristica': ['Alto', 'Médio', 'Alto', 'Baixo', 'Médio'],
    'latitude': [-3.1, 2.8, -4.2, -2.9, -3.4],
    'longitude': [-60.0, -60.7, -69.9, -64.5, -64.7]
})

# Título da aplicação
st.title("Amazônia em Órbita")

# Filtro de risco
risco_opcao = st.selectbox("Filtrar por nível de risco:", ["Todos", "Alto", "Médio", "Baixo"])
if risco_opcao != "Todos":
    data = data[data['risco_predito_heuristica'] == risco_opcao]

# Filtro de estado
estado_opcao = st.selectbox("Filtrar por estado:", ["Todos"] + sorted(data['estado'].unique().tolist()))
if estado_opcao != "Todos":
    data = data[data['estado'] == estado_opcao]

# Criar o mapa com Folium
m = folium.Map(location=[-3.5, -63.0], zoom_start=5)
cluster = MarkerCluster().add_to(m)

# Adiciona os pontos no mapa
for _, row in data.iterrows():
    cor = {
        "Alto": "red",
        "Médio": "orange",
        "Baixo": "green"
    }.get(row['risco_predito_heuristica'], "blue")

    popup_info = f"""
    <strong>{row['municipio']} ({row['estado']})</strong><br>
    Casos: {row['casos']}<br>
    Óbitos: {row['obitos']}<br>
    Risco de Inundação: {'Sim' if row['risco_inundacao'] else 'Não'}<br>
    Nível de Risco: {row['risco_predito_heuristica']}
    """
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=popup_info,
        icon=folium.Icon(color=cor)
    ).add_to(cluster)

# Exibir o mapa na interface
st_folium(m, width=700, height=500)

# Mostrar tabela abaixo
st.subheader("📊 Tabela de Municípios Monitorados")
st.dataframe(data)
