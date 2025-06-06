import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

# Configuração da página
st.set_page_config(page_title="Visualizar Tabela", layout="wide")
st.title("📊 Visualizar Tabela do Banco de Dados SQLite")

# Caminho do banco de dados
db_path = "logistica_interna.db"
conn = sqlite3.connect(db_path)

# Carregar tabelas
tabelas = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
if not tabelas.empty:
    tabela_site = "Site Carga Rastreada"
    tabela_hub = "Hub_Mercedes_Benz"

    if tabela_site in tabelas["name"].values and tabela_hub in tabelas["name"].values:
        datas_disponiveis = pd.read_sql(f'SELECT DISTINCT emissao_cte FROM "{tabela_site}" ORDER BY emissao_cte', conn)
        datas_disponiveis['emissao_cte'] = pd.to_datetime(datas_disponiveis['emissao_cte'])

        data_inicio, data_fim = st.date_input(
            "Selecione o intervalo de datas de emissão do CTE",
            value=(datas_disponiveis['emissao_cte'].min(), datas_disponiveis['emissao_cte'].max()),
            min_value=datas_disponiveis['emissao_cte'].min(),
            max_value=datas_disponiveis['emissao_cte'].max()
        )
        data_inicio_str = data_inicio.strftime('%Y-%m-%d')
        data_fim_str = data_fim.strftime('%Y-%m-%d')

        nf_input = st.text_input("Digite o número da NF para buscar", "")
        cte_input = st.text_input("Digite o número do CTE para buscar", "")

        hubs_disponiveis = pd.read_sql(f'SELECT DISTINCT hub FROM "{tabela_hub}"', conn)
        hub_selecionado = st.multiselect("Filtrar por Hub", hubs_disponiveis['hub'].tolist(), default=hubs_disponiveis['hub'].tolist())

        query = f'''
            SELECT 
                s.*, 
                h.hub, 
                h.transportadora
            FROM "{tabela_site}" s
            LEFT JOIN "{tabela_hub}" h 
                ON s.cidade = h.danfe_dest_cidade
            WHERE s.emissao_cte BETWEEN "{data_inicio_str}" AND "{data_fim_str}"
        '''
        if nf_input:
            query += f' AND s.nf LIKE "%{nf_input}%"'
        if cte_input:
            query += f' AND s.cte LIKE "%{cte_input}%"'

        df_tabela = pd.read_sql(query, conn)

        # Ajuste datas
        df_tabela['emissao_cte'] = pd.to_datetime(df_tabela['emissao_cte'], errors='coerce')
        df_tabela['prev.entrega'] = pd.to_datetime(df_tabela['prev.entrega'], errors='coerce')
        df_tabela['dt.entrega'] = pd.to_datetime(df_tabela['dt.entrega'], errors='coerce')

        df_tabela = df_tabela[df_tabela['hub'].isin(hub_selecionado)]

        # Calcular status (igual ao seu código)
        if 'prev.entrega' in df_tabela.columns and 'dt.entrega' in df_tabela.columns:
            df_tabela['diferença_dias'] = (df_tabela['prev.entrega'] - df_tabela['dt.entrega']).dt.days

            def calcular_status(row):
                if pd.isna(row['prev.entrega']):
                    return "Em Trânsito 🚚"
                elif pd.isna(row['dt.entrega']):
                    if datetime.now().date() > row['prev.entrega'].date():
                        return "Em Trânsito (ATRASADO) 🚚❌"
                    else:
                        return "Em Trânsito 🚚"
                elif row['diferença_dias'] < 0:
                    return "Atrasado❌"
                elif row['diferença_dias'] > 0:
                    return "Antecipado ✅"
                else:
                    return "No Prazo ✅"
            df_tabela['status_pedido'] = df_tabela.apply(calcular_status, axis=1)

        # Filtros adicionais
        emissores_disponiveis = df_tabela['emissor'].dropna().unique().tolist()
        emissor_selecionado = st.multiselect("Filtrar por Emissor", emissores_disponiveis, default=emissores_disponiveis)
        df_tabela = df_tabela[df_tabela['emissor'].isin(emissor_selecionado)]

        status_options = ["Em Trânsito 🚚", "Em Trânsito (ATRASADO) 🚚❌", "No Prazo ✅", "Antecipado ✅", "Atrasado❌"]
        status_selecionado = st.multiselect("Filtrar por Status do Pedido", status_options, default=status_options)
        df_tabela = df_tabela[df_tabela['status_pedido'].isin(status_selecionado)]

        # Configurar AgGrid para melhor UX
        gb = GridOptionsBuilder.from_dataframe(df_tabela)

        # Coluna status com cores customizadas via JS
        cellstyle_jscode = JsCode("""
        function(params) {
            if (params.value == "Atrasado❌") {
                return {'color': 'white', 'backgroundColor': 'red'};
            } else if (params.value == "Antecipado ✅") {
                return {'color': 'white', 'backgroundColor': 'green'};
            } else if (params.value == "No Prazo ✅") {
                return {'color': 'white', 'backgroundColor': 'blue'};
            } else if (params.value == "Em Trânsito 🚚") {
                return {'color': 'black', 'backgroundColor': 'orange'};
            } else if (params.value == "Em Trânsito (ATRASADO) 🚚❌") {
                return {'color': 'white', 'backgroundColor': 'darkred'};
            } else {
                return {};
            }
        };
        """)

        gb.configure_column("status_pedido", cellStyle=cellstyle_jscode)

        # Permitir filtros, ordenação, busca global
        gb.configure_default_column(filter=True, sortable=True, resizable=True)
        gb.configure_grid_options(domLayout='normal', pagination=True, paginationPageSize=20)

        gridOptions = gb.build()

        st.markdown("### Resultado da Consulta")
        AgGrid(df_tabela, gridOptions=gridOptions, enable_enterprise_modules=False, allow_unsafe_jscode=True, height=500, fit_columns_on_grid_load=True)

else:
    st.warning("Nenhuma tabela encontrada no banco de dados.")
