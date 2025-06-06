import sqlite3
import pandas as pd
import streamlit as st
import pydeck as pdk

# === Funções auxiliares ===

def carregar_dados(db_path):
    with sqlite3.connect(db_path) as conn:
        query = "SELECT cidade_destinatario, uf_destinatario, quantidade_de_volumes FROM Relatorios_CTEs"
        df = pd.read_sql_query(query, conn)
    df['quantidade_de_volumes'] = pd.to_numeric(df['quantidade_de_volumes'], errors='coerce').fillna(0).astype(int)
    return df

def adicionar_coordenadas(df, coordinates, lat_offset=0.03, lon_offset=0.03):
    df['latitude'] = df['cidade_destinatario'].map(lambda x: coordinates.get(x, [None, None])[0])
    df['longitude'] = df['cidade_destinatario'].map(lambda x: coordinates.get(x, [None, None])[1])
    # Aplica pequeno deslocamento para não cobrir o centro exato da cidade no zoom
    df['latitude'] = df['latitude'].apply(lambda x: x + lat_offset if pd.notnull(x) else x)
    df['longitude'] = df['longitude'].apply(lambda x: x + lon_offset if pd.notnull(x) else x)
    return df.dropna(subset=['latitude', 'longitude'])

def criar_mapa(df):
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        df,
        get_position='[longitude, latitude]',
        get_radius='quantidade_de_volumes * 100',
        get_fill_color='[255, 75, 75]',
        pickable=True,
        auto_highlight=True,
    )
    view_state = pdk.ViewState(
        latitude=df['latitude'].mean(),
        longitude=df['longitude'].mean(),
        zoom=5,
        pitch=30,
    )
    tooltip = {
        "html": "<b>{cidade_destinatario} - {uf_destinatario}</b><br>Volumes: {quantidade_de_volumes}",
        "style": {"color": "white"}
    }
    return pdk.Deck(layers=[scatter_layer], initial_view_state=view_state, tooltip=tooltip)

# === Coordenadas das cidades ===
coordinates = {
    'São Paulo': [-23.550520, -46.633308],
    'Rio de Janeiro': [-22.906847, -43.172896],
    'Belo Horizonte': [-19.916681, -43.934493],
    'Salvador': [-12.97563, -38.49096],
    'Fortaleza': [-3.71722, -38.54306],
    'Manaus': [-3.10194, -60.025],
    'Brasília': [-15.77972, -47.92972],
    'Curitiba': [-25.42778, -49.27306],
    'Recife': [-8.05389, -34.88111],
    'Goiânia': [-16.67861, -49.25389],
    'Belém': [-1.45583, -48.50444],
    'Porto Alegre': [-30.03283, -51.23019],
    'Guarulhos': [-23.46278, -46.53333],
    'Maceió': [-9.66583, -35.73528],
    'Campinas': [-22.90556, -47.06083],
    'São Luís': [-2.52972, -44.30278],
    'Campo Grande': [-20.44278, -54.64639],
    'Natal': [-5.795, -35.20944],
    'Teresina': [-5.08917, -42.80194],
    'Nova Iguaçu': [-22.75917, -43.45111],
    'ARACAJU': [-10.9472, -37.0731],
    'ARAPIRACA': [-9.75487, -36.6616],
    'ARCOVERDE': [-8.4187, -37.0531],
    'BARREIRAS': [-12.1446, -44.9968],
    'BLUMENAU': [-26.9194, -49.0661],
    'CAMBE': [-23.2766, -51.2798],
    'CAMPINA GRANDE': [-7.2306, -35.8811],
    'CAMPO MOURAO': [-24.0463, -52.3787],
    'CARUARU': [-8.2822, -35.9753],
    'CASCAVEL': [-24.9578, -53.459],
    'CAXIAS DO SUL': [-29.1678, -51.1794],
    'CHAPECO': [-27.1004, -52.6152],
    'CONCORDIA': [-27.2349, -52.026],
    'ERECHIM': [-27.6346, -52.2735],
    'FEIRA DE SANTANA': [-12.2664, -38.9663],
    'FLORIANO': [-6.7694, -43.025],
}

# === Execução ===
st.title("Mapa de Volumes por Cidade")

df = carregar_dados("logistica_interna.db")

df_grouped = df.groupby(['cidade_destinatario', 'uf_destinatario'], as_index=False).sum()
st.subheader("Volumes agrupados por cidade:")
st.dataframe(df_grouped)

df_com_coords = adicionar_coordenadas(df_grouped, coordinates)

if df_com_coords.empty:
    st.warning("Nenhuma cidade do banco tem coordenadas definidas. Adicione mais coordenadas ao dicionário.")
else:
    st.subheader("Distribuição geográfica (pontos vermelhos):")
    mapa = criar_mapa(df_com_coords)
    st.pydeck_chart(mapa)
