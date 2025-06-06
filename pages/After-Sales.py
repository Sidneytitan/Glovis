import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Visualizar Tabela", layout="wide")
st.title("📊 Visualizar Tabela do Banco de Dados SQLite")

# Caminho do banco de dados
db_path = "logistica_interna.db"

# Conexão com o banco
conn = sqlite3.connect(db_path)

# Listar todas as tabelas
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

        df_tabela['emissao_cte'] = pd.to_datetime(df_tabela['emissao_cte'], errors='coerce')
        df_tabela['prev.entrega'] = pd.to_datetime(df_tabela['prev.entrega'], errors='coerce')
        df_tabela['dt.entrega'] = pd.to_datetime(df_tabela['dt.entrega'], errors='coerce')

        df_tabela = df_tabela[df_tabela['hub'].isin(hub_selecionado)]

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

            # Adicionar transportadora do usuário
            df_hub = pd.read_sql(f'SELECT danfe_dest_cidade, transportadora FROM "{tabela_hub}"', conn)
            cidade_transportadora_dict = dict(zip(df_hub['danfe_dest_cidade'], df_hub['transportadora']))
            df_tabela['transportadora_usuario'] = df_tabela['cidade'].map(cidade_transportadora_dict)

            # Filtro por Emissor ANTES do filtro por status
            emissores_disponiveis = df_tabela['emissor'].dropna().unique().tolist()
            emissor_selecionado = st.multiselect("Filtrar por Emissor", emissores_disponiveis, default=emissores_disponiveis)
            df_tabela = df_tabela[df_tabela['emissor'].isin(emissor_selecionado)]

            # Filtro por Status do Pedido
            status_options = ["Em Trânsito 🚚", "Em Trânsito (ATRASADO) 🚚❌", "No Prazo ✅", "Antecipado ✅", "Atrasado❌"]
            status_selecionado = st.multiselect("Filtrar por Status do Pedido", status_options, default=status_options)
            df_tabela = df_tabela[df_tabela['status_pedido'].isin(status_selecionado)]

            def calcular_dias_restantes(row):
                if "Atrasado❌" in row['status_pedido']:
                    return -(datetime.now().date() - row['prev.entrega'].date()).days
                elif "Em Trânsito" in row['status_pedido']:
                    return (row['prev.entrega'].date() - datetime.now().date()).days
                return row['diferença_dias']

            df_tabela['diferença_dias'] = df_tabela.apply(calcular_dias_restantes, axis=1)
            df_tabela['diferença_dias'] = df_tabela['diferença_dias'].astype('Int64')

            total_pedidos = len(df_tabela)
            em_transito = len(df_tabela[df_tabela['status_pedido'].str.contains("Em Trânsito")])
            no_prazo = len(df_tabela[df_tabela['status_pedido'] == "No Prazo ✅"])
            antecipado = len(df_tabela[df_tabela['status_pedido'] == "Antecipado ✅"])
            atrasado = len(df_tabela[df_tabela['status_pedido'] == "Atrasado❌"])
            em_transito_atrasado = len(df_tabela[df_tabela['status_pedido'] == "Em Trânsito (ATRASADO) 🚚❌"])

            pct_em_transito = (em_transito / total_pedidos) * 100 if total_pedidos > 0 else 0
            pct_no_prazo = (no_prazo / total_pedidos) * 100 if total_pedidos > 0 else 0
            pct_antecipado = (antecipado / total_pedidos) * 100 if total_pedidos > 0 else 0
            pct_atrasado = (atrasado / total_pedidos) * 100 if total_pedidos > 0 else 0
            pct_em_transito_atrasado = (em_transito_atrasado / total_pedidos) * 100 if total_pedidos > 0 else 0

            total_volumes = df_tabela['qtd.vols'].sum()
            qtd_vols_em_transito = df_tabela[df_tabela['status_pedido'].str.contains("Em Trânsito")]['qtd.vols'].sum()
            qtd_vols_no_prazo_antecipado = df_tabela[df_tabela['status_pedido'].isin(["No Prazo ✅", "Antecipado ✅"])]['qtd.vols'].sum()
            qtd_vols_atrasado = df_tabela[df_tabela['status_pedido'] == "Atrasado❌"]['qtd.vols'].sum()

            pct_vols_em_transito = (qtd_vols_em_transito / total_volumes) * 100 if total_volumes > 0 else 0
            pct_vols_no_prazo_antecipado = (qtd_vols_no_prazo_antecipado / total_volumes) * 100 if total_volumes > 0 else 0
            pct_vols_atrasado = (qtd_vols_atrasado / total_volumes) * 100 if total_volumes > 0 else 0

            col1, col8, col2, col3, col4, col5, col6, col7 = st.columns(8)

            col1.metric("Em Trânsito 🚚", em_transito, delta=f"{pct_em_transito:.2f}%")
            col8.metric("Em Trânsito (ATRASADO) 🚚❌", em_transito_atrasado, delta=f"{pct_em_transito_atrasado:.2f}%", delta_color="inverse")
            col2.metric("No Prazo ✅", no_prazo, delta=f"{pct_no_prazo:.2f}%")
            col3.metric("Antecipado ✅", antecipado, delta=f"{pct_antecipado:.2f}%")
            col4.metric("Atrasado ❌", atrasado, delta=f"{pct_atrasado:.2f}%", delta_color="inverse")

            col5.metric("Volume Em Trânsito 🚚", qtd_vols_em_transito, delta=f"{pct_vols_em_transito:.2f}%")
            col6.metric("Volume Entregue ✅", qtd_vols_no_prazo_antecipado, delta=f"{pct_vols_no_prazo_antecipado:.2f}%")
            col7.metric("Volume Em Atraso ❌", qtd_vols_atrasado, delta=f"{pct_vols_atrasado:.2f}%", delta_color="inverse")

            def color_status(val):
                color = {
                    "Atrasado❌": "red",
                    "Antecipado ✅": "green",
                    "No Prazo ✅": "blue",
                    "Em Trânsito 🚚": "orange",
                    "Em Trânsito (ATRASADO) 🚚❌": "darkred"
                }.get(val, "")
                return f"color: {color}"

            st.dataframe(df_tabela.style.applymap(color_status, subset=['status_pedido']))
