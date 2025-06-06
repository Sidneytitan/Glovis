import streamlit as st
import pandas as pd
import requests
import json
import urllib.request
import plotly.express as px
from datetime import date

st.set_page_config(page_title="Dashboard", layout="wide")

# --- Configuração de dados dos fornecedores e logos ---
fornecedores_por_cliente = {
    "Scania": {"Scania": "59104901000761"},
    "Mercedes": {"Mercedes-Benz": "31715616000504", "Mobis": "08585033000314"},
    "Volkswagen": {"Volkswagen": "59104422001806"}
}

logos_cliente = {
    "Mercedes": "https://upload.wikimedia.org/wikipedia/commons/9/90/Mercedes-Logo.svg",
    "Volkswagen": "https://th.bing.com/th/id/OIP.FPiS5vvV-gklhWyf95dUAwHaHZ?r=0&rs=1&pid=ImgDetMain",
    "Scania": "https://upload.wikimedia.org/wikipedia/commons/4/49/Scania_Griffin_Logo.svg",
}

logos_fornecedor = {
    "Mobis": "https://1000marcas.net/wp-content/uploads/2020/11/Mobis-Logo.png",
    "Mercedes-Benz": "https://upload.wikimedia.org/wikipedia/commons/9/90/Mercedes-Logo.svg",
    "Scania": "https://upload.wikimedia.org/wikipedia/commons/4/49/Scania_Griffin_Logo.svg",
    "Volkswagen": "https://th.bing.com/th/id/OIP.FPiS5vvV-gklhWyf95dUAwHaHZ?r=0&rs=1&pid=ImgDetMain"
}

# --- Construção da lista de fornecedores com URLs ---
todos_fornecedores = {}
for cliente, fornecedores in fornecedores_por_cliente.items():
    for fornecedor, cnpj in fornecedores.items():
        url = f"http://app.cargarastreada.com.br/glovis/dashboard-api/?di={{data_inicio}}&df={{data_fim}}&emissor={cnpj}"
        todos_fornecedores[fornecedor] = (cliente, url)
todos_fornecedores = {"Todos": ("Todos", None), **todos_fornecedores}

# --- Interface do usuário ---
col1, col2, col3, col4 = st.columns([1.5, 2, 2, 1.5])

with col1:
    fornecedor = st.selectbox("Selecione o fornecedor:", list(todos_fornecedores.keys()))

with col2:
    data = st.date_input("Selecione o intervalo de datas:", value=[date(2025, 5, 1), date(2025, 5, 30)])
    if isinstance(data, (list, tuple)) and len(data) == 2:
        data_inicio, data_fim = data
    else:
        data_inicio = data_fim = data
    data_inicio_str = data_inicio.strftime("%Y-%m-%d")
    data_fim_str = data_fim.strftime("%Y-%m-%d")

with col3:
    pagina = st.radio("Página", ["Dashboard", "Pedidos", "Estoque"], horizontal=True)

with col4:
    cliente_selecionado = todos_fornecedores[fornecedor][0]
    logo_url = logos_fornecedor.get(fornecedor, logos_cliente.get(cliente_selecionado))
    if logo_url:
        st.image(logo_url, width=80)

st.markdown("---")
st.title(f"{cliente_selecionado} | {pagina}")

# --- Funções auxiliares ---
def get_api_data(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def carregar_geojson():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    with urllib.request.urlopen(url) as response:
        geojson = json.load(response)
    return geojson

# --- Página Dashboard ---
if pagina == "Dashboard":
    st.title("Mapa de Calor - Volume por Estado")

    if fornecedor == "Todos":
        dfs = []
        volumes_por_fornecedor = {}
        for f, (_, url_template) in todos_fornecedores.items():
            if url_template:
                url = url_template.format(data_inicio=data_inicio_str, data_fim=data_fim_str)
                try:
                    dados = get_api_data(url)
                    if dados:
                        df_temp = pd.DataFrame(dados)
                        df_temp["fornecedor"] = f
                        dfs.append(df_temp)
                        volumes_por_fornecedor[f] = df_temp["qtd_volumes"].sum()
                except Exception as e:
                    st.warning(f"Erro ao buscar dados de {f}: {e}")
        df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    else:
        url = todos_fornecedores[fornecedor][1].format(data_inicio=data_inicio_str, data_fim=data_fim_str)
        try:
            dados = get_api_data(url)
            df = pd.DataFrame(dados)
        except Exception as e:
            st.error(f"Erro ao buscar dados: {e}")
            df = pd.DataFrame()

    # --- Processamento e visualização ---
    if not df.empty and "destinatario_uf" in df.columns and "qtd_volumes" in df.columns:
        geojson = carregar_geojson()
        sigla_to_estado = {f["properties"]["sigla"]: f["properties"]["name"] for f in geojson["features"]}
        estados_siglas = list(sigla_to_estado.keys())

        agrupado = df.groupby("destinatario_uf")["qtd_volumes"].sum().reset_index()
        agrupado.columns = ["sigla", "volume"]

        df_completo = pd.DataFrame({"sigla": estados_siglas})
        df_completo = df_completo.merge(agrupado, on="sigla", how="left")
        df_completo["volume"] = df_completo["volume"].fillna(0)
        df_completo["estado"] = df_completo["sigla"].map(sigla_to_estado)

        fig = px.choropleth(
            df_completo,
            geojson=geojson,
            locations="sigla",
            color="volume",
            color_continuous_scale="Reds",
            featureidkey="properties.sigla",
            scope="south america",
            labels={"volume": "Volume"},
            hover_name="estado",
            hover_data={"sigla": False, "volume": True}
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0})
        st.plotly_chart(fig, use_container_width=True)

        # --- Relatório Inteligente ---
        st.subheader("🧠 Relatório Inteligente")
        top_estados = df_completo.sort_values(by="volume", ascending=False).head(5)
        estados_zeros = df_completo[df_completo["volume"] == 0]["estado"].tolist()
        total_volume = df_completo["volume"].sum()
        media_volume = df_completo["volume"].mean()

        st.markdown(f"""
📦 **Volume total transportado:** `{int(total_volume):,}` volumes  
📊 **Média por estado:** `{int(media_volume):,}` volumes

### 🔝 Estados com maior volume:
""")
        for _, row in top_estados.iterrows():
            st.markdown(f"- {row['estado']}: `{int(row['volume']):,}` volumes")

        if estados_zeros:
            st.markdown("### ⚠️ Estados sem movimentação:")
            st.markdown(", ".join(estados_zeros))
        else:
            st.markdown("✅ Todos os estados apresentaram algum volume movimentado.")

        estado_max = df_completo.loc[df_completo["volume"].idxmax()]
        if estado_max["volume"] > 2 * media_volume:
            st.markdown(f"""
💡 **Observação**: O estado **{estado_max["estado"]}** apresentou um volume **muito acima da média**, indicando concentração de entregas ou demanda elevada naquela região.
""")

        # --- Comparativo entre fornecedores ---
        if fornecedor == "Todos" and volumes_por_fornecedor:
            st.subheader("📊 Comparativo entre Fornecedores")
            ranking = sorted(volumes_por_fornecedor.items(), key=lambda x: x[1], reverse=True)
            mais_ativo, maior_volume = ranking[0]
            menos_ativo, menor_volume = ranking[-1]
            dif_pct = (maior_volume - menor_volume) / maior_volume * 100 if maior_volume else 0

            st.markdown(f"""
🏆 **{mais_ativo}** foi o fornecedor com maior volume: `{int(maior_volume):,}` volumes  
📉 **{menos_ativo}** teve o menor volume: `{int(menor_volume):,}` volumes  
📐 Diferença relativa: `{dif_pct:.1f}%`
""")

            if menor_volume < 500:
                st.warning(f"⚠️ O fornecedor **{menos_ativo}** teve um volume muito abaixo do esperado. Pode indicar baixa operação ou falhas no envio.")
    else:
        st.warning("Dados insuficientes para exibir o mapa.")




# --- Outras páginas ---
elif pagina == "Pedidos":
    st.subheader("📄 Lista de Pedidos")

    if fornecedor == "Todos":
        dfs = []
        for f, (_, url_template) in todos_fornecedores.items():
            if url_template:
                url = url_template.format(data_inicio=data_inicio_str, data_fim=data_fim_str)
                try:
                    dados = get_api_data(url)
                    if dados:
                        df_temp = pd.DataFrame(dados)
                        df_temp["fornecedor"] = f
                        dfs.append(df_temp)
                except Exception as e:
                    st.warning(f"Erro ao buscar dados de {f}: {e}")
        df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    else:
        url = todos_fornecedores[fornecedor][1].format(data_inicio=data_inicio_str, data_fim=data_fim_str)
        try:
            dados = get_api_data(url)
            df = pd.DataFrame(dados)
        except Exception as e:
            st.error(f"Erro ao buscar dados: {e}")
            df = pd.DataFrame()

    if not df.empty:
        # Aplica máscara na coluna cte_chave
        if 'cte_chave' in df.columns:
            df["cte_chave"] = df["cte_chave"].astype(str).apply(lambda x: x[28:34] if len(x) >= 34 else "")

        st.dataframe(df)
    else:
        st.info("Nenhum dado disponível para exibir.")

