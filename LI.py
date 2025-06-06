import streamlit as st
import pandas as pd
import sqlite3
import json
import urllib.request
import plotly.express as px
import pydeck as pdk

# Caminho do banco de dados e nome da tabela
db_path = "logistica_interna.db"
nome_tabela = "Relatorios_CTEs"

# Mapeamento de UF para Região
uf_para_regiao = {
    'AC': 'Norte', 'AL': 'Nordeste', 'AP': 'Norte', 'AM': 'Norte', 'BA': 'Nordeste', 'CE': 'Nordeste',
    'DF': 'Centro-Oeste', 'ES': 'Sudeste', 'GO': 'Centro-Oeste', 'MA': 'Nordeste', 'MT': 'Centro-Oeste',
    'MS': 'Centro-Oeste', 'MG': 'Sudeste', 'PA': 'Norte', 'PB': 'Nordeste', 'PR': 'Sul', 'PE': 'Nordeste',
    'PI': 'Nordeste', 'RJ': 'Sudeste', 'RN': 'Nordeste', 'RS': 'Sul', 'RO': 'Norte', 'RR': 'Norte',
    'SC': 'Sul', 'SP': 'Sudeste', 'SE': 'Nordeste', 'TO': 'Norte'
}

# Função para carregar dados do SQLite para estados (UF)
def carregar_dados_sqlite_uf(db_path, nome_tabela):
    conn = sqlite3.connect(db_path)
    query = f"""
        SELECT uf_destinatario as uf, SUM(quantidade_de_volumes) as volume
        FROM {nome_tabela}
        GROUP BY uf_destinatario
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Função para carregar geojson dos estados do Brasil
def carregar_geojson():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    with urllib.request.urlopen(url) as response:
        geojson = json.load(response)
    return geojson

# Função para carregar dados por cidade
def carregar_dados_cidade(db_path):
    with sqlite3.connect(db_path) as conn:
        query = "SELECT cidade_destinatario, uf_destinatario, quantidade_de_volumes FROM Relatorios_CTEs"
        df = pd.read_sql_query(query, conn)
    df['quantidade_de_volumes'] = pd.to_numeric(df['quantidade_de_volumes'], errors='coerce').fillna(0).astype(int)
    return df

# Função para adicionar coordenadas de latitude e longitude no dataframe
def adicionar_coordenadas(df, coordinates, lat_offset=0.03, lon_offset=0.03):
    df['latitude'] = df['cidade_destinatario'].map(lambda x: coordinates.get(x.upper(), [None, None])[0])
    df['longitude'] = df['cidade_destinatario'].map(lambda x: coordinates.get(x.upper(), [None, None])[1])
    # Aplica pequeno deslocamento para não cobrir o centro exato da cidade no zoom
    df['latitude'] = df['latitude'].apply(lambda x: x + lat_offset if pd.notnull(x) else x)
    df['longitude'] = df['longitude'].apply(lambda x: x + lon_offset if pd.notnull(x) else x)
    return df.dropna(subset=['latitude', 'longitude'])

# Função para criar mapa pydeck
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

# Coordenadas das cidades
coordinates = {
    'ARACAJU': [-10.9472, -37.0731],
    'ARAPIRACA': [-9.7528, -36.6612],
    'ARCOVERDE': [-8.4196, -37.0561],
    'BARREIRAS': [-12.1447, -44.9927],
    'BLUMENAU': [-26.9199, -49.0661],
    'CAMBE': [-23.2594, -51.0135],
    'CAMPINA GRANDE': [-7.2306, -35.8819],
    'CAMPO MOURAO': [-24.0462, -52.3786],
    'CARUARU': [-8.2821, -35.9765],
    'CASCAVEL': [-24.9556, -53.4551],
    'CAXIAS DO SUL': [-29.1678, -51.1794],
    'CHAPECO': [-27.1006, -52.6153],
    'CONCORDIA': [-27.2333, -52.0322],
    'CURITIBA': [-25.4284, -49.2733],
    'ERECHIM': [-27.6378, -52.2661],
    'FEIRA DE SANTANA': [-12.2669, -38.9667],
    'FLORIANO': [-6.7669, -43.0303],
    'FORTALEZA': [-3.7172, -38.5434],
    'FOZ DO IGUACU': [-25.5469, -54.5882],
    'GARIBALDI': [-29.3109, -51.5228],
    'GUANAMBI': [-14.2083, -42.7819],
    'GUARAPUAVA': [-25.3909, -51.4622],
    'ICARA': [-28.9536, -49.8849],
    'IJUI': [-28.3845, -53.9178],
    'IMPERATRIZ': [-5.5272, -47.4922],
    'INDAIAL': [-26.9043, -49.2328],
    'ITABUNA': [-14.7877, -39.2781],
    'ITAJAI': [-26.9106, -48.6667],
    'JABOATAO DOS GUARARAPES': [-8.1122, -35.0078],
    'JAGUARIAIVA': [-24.1267, -49.7481],
    'JAGUARIBE': [-5.9878, -39.2964],
    'JOAO PESSOA': [-7.1153, -34.861],
    'JOINVILLE': [-26.3044, -48.8456],
    'JUAZEIRO': [-9.4161, -40.5033],
    'JUAZEIRO DO NORTE': [-7.2136, -39.3153],
    'LAGES': [-27.8174, -50.3251],
    'LAJEADO': [-29.4606, -51.9664],
    'LIMEIRA': [-22.5669, -47.4016],
    'LONDRINA': [-23.3103, -51.1628],
    'MACEIO': [-9.6658, -35.735],
    'MAFRA': [-26.1847, -50.6847],
    'MARECHAL CANDIDO RONDON': [-24.5514, -54.0544],
    'MARINGA': [-23.4256, -51.9331],
    'MOSSORO': [-5.1877, -37.3443],
    'NATAL': [-5.7945, -35.211],
    'NOSSA SENHORA DO SOCORRO': [-10.8891, -37.1033],
    'NOVA SANTA RITA': [-29.8000, -51.1000],
    'NOVO HAMBURGO': [-29.6879, -51.1309],
    'PALMARES': [-8.5625, -35.5436],
    'PARANAVAI': [-23.1003, -52.4683],
    'PARNAMIRIM': [-5.9111, -35.2442],
    'PASSO FUNDO': [-28.2606, -52.4064],
    'PATOS': [-7.0256, -37.2761],
    'PELOTAS': [-31.7658, -52.3373],
    'PETROLINA': [-9.3892, -40.5023],
    'PICOS': [-7.0797, -41.4675],
    'PIRACICABA': [-22.7239, -47.6499],
    'PONTA GROSSA': [-25.0918, -50.1587],
    'PORTO ALEGRE': [-30.0346, -51.2177],
    'RECIFE': [-8.0476, -34.877],
    'RIO BRANCO': [-9.9748, -67.8243],
    'RIO DE JANEIRO': [-22.9068, -43.1729],
    'SALVADOR': [-12.9714, -38.5014],
    'SANTAREM': [-2.4384, -54.6997],
    'SANTO ANGELO': [-28.3003, -54.2664],
    'SANTO ANDRE': [-23.6638, -46.5387],
    'SAO BERNARDO DO CAMPO': [-23.6913, -46.5646],
    'SAO JOSE DO RIO PRETO': [-20.8194, -49.3796],
    'SAO JOSE DOS CAMPOS': [-23.1896, -45.8845],
    'SAO LEOPOLDO': [-29.7613, -51.1487],
    'SAO LUIS': [-2.5307, -44.3068],
    'SAO PAULO': [-23.5505, -46.6333],
    'SAPIRANGA': [-29.5925, -51.1277],
    'SOROCABA': [-23.5015, -47.4526],
    'TANGARA DA SERRA': [-14.6383, -57.5092],
    'TEIXEIRA DE FREITAS': [-17.5208, -39.7408],
    'UBERABA': [-19.7473, -47.9314],
    'UBERLANDIA': [-18.9186, -48.2777],
    'VARGINHA': [-21.5555, -45.4367],
    'VIAMAO': [-30.076, -51.0704],
    'VITORIA': [-20.3155, -40.3128],
    'VITORIA DA CONQUISTA': [-14.861, -40.8397]
}

def main():
    st.set_page_config(page_title="Dashboard Logística Interna", layout="wide")

    st.title("Dashboard Logística Interna")

    tabs = st.tabs(["Mapa por Estado", "Mapa por Cidade"])

    # --- Aba 1: Mapa por Estado ---

    with tabs[0]:
        st.header("Mapa por Estado e Gráfico por Região")

        df_estado = carregar_dados_sqlite_uf(db_path, nome_tabela)
        geojson = carregar_geojson()

        # Cria coluna de região para o gráfico de barras
        df_estado['regiao'] = df_estado['uf'].map(uf_para_regiao).fillna('Desconhecida')

        # Mapa coroplético por estado
        fig_map = px.choropleth(df_estado,
                                geojson=geojson,
                                locations='uf',
                                featureidkey="properties.sigla",
                                color='volume',
                                color_continuous_scale="Viridis",
                                scope="south america",
                                labels={'volume': 'Volumes'},
                                title="Volumes por Estado")

        fig_map.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig_map, use_container_width=True)

        # Gráfico de barras por região
        fig_bar = px.bar(df_estado.groupby('regiao')['volume'].sum().reset_index(),
                         x='regiao', y='volume',
                         labels={'volume': 'Volumes', 'regiao': 'Região'},
                         title="Volumes por Região")
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- Aba 2: Mapa por Cidade com filtro ---

    with tabs[1]:
        st.header("Mapa por Cidade")

        df_cidade = carregar_dados_cidade(db_path)

        # Filtro de cidades disponíveis
        cidades_disponiveis = df_cidade['cidade_destinatario'].dropna().unique()
        cidades_selecionadas = st.multiselect(
            "Filtrar por Cidade Destinatário",
            options=sorted(cidades_disponiveis),
            default=sorted(cidades_disponiveis)
        )

        # Filtra dataframe
        df_filtrado = df_cidade[df_cidade['cidade_destinatario'].isin(cidades_selecionadas)]

        # Adiciona coordenadas
        df_com_coord = adicionar_coordenadas(df_filtrado, coordinates)

        if not df_com_coord.empty:
            mapa = criar_mapa(df_com_coord)
            st.pydeck_chart(mapa)
        else:
            st.warning("Nenhuma cidade selecionada ou dados insuficientes para exibir o mapa.")

        # Exibe tabela filtrada
        st.subheader("Dados Filtrados")
        st.dataframe(df_filtrado)

if __name__ == "__main__":
    main()


