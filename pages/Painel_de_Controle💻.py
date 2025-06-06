import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="Gerenciador de Tabelas", layout="wide")
st.title("📊 Gerenciador de Tabelas com Excel + SQLite")

# Caminho do banco de dados
db_path = "logistica_interna.db"

# Conexão com o banco
conn = sqlite3.connect(db_path)

# Upload do arquivo
uploaded_file = st.file_uploader("📁 Envie seu arquivo Excel", type=["xlsx"])

# Escolha da operação
operacao = st.radio("Escolha uma operação:", ["Criar nova tabela", "Atualizar tabela existente", "Excluir tabela"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, engine='openpyxl')

        # Converter colunas do tipo Timestamp para string
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].astype(str)

        st.success("✅ Arquivo carregado com sucesso!")
        st.dataframe(df)

        if operacao == "Criar nova tabela":
            nome_tabela = st.text_input("Digite o nome da nova tabela:")

            if st.button("Criar Tabela"):
                if nome_tabela:
                    try:
                        df.columns = [col.strip().replace(" ", "_").lower() for col in df.columns]  # padronizar nomes
                        df.to_sql(nome_tabela, conn, if_exists="fail", index=False)
                        st.success(f"✅ Tabela '{nome_tabela}' criada com sucesso!")
                    except Exception as e:
                        st.error(f"❌ Erro ao criar a tabela: {e}")
                else:
                    st.warning("⚠️ Digite um nome para a tabela!")

        elif operacao == "Atualizar tabela existente":
            tabelas_existentes = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)["name"].tolist()
            tabela_escolhida = st.selectbox("Escolha a tabela para atualizar:", tabelas_existentes)

            if st.button("Atualizar Tabela"):
                try:
                    df.columns = [col.strip().replace(" ", "_").lower() for col in df.columns]  # padronizar nomes
                    placeholders = ", ".join(["?"] * len(df.columns))
                    colunas_sql = ", ".join([f'"{col}"' for col in df.columns])
                    insert_query = f'INSERT INTO "{tabela_escolhida}" ({colunas_sql}) VALUES ({placeholders})'

                    cursor = conn.cursor()
                    cursor.executemany(insert_query, df.values.tolist())
                    conn.commit()
                    st.success(f"✅ Dados inseridos na tabela '{tabela_escolhida}' com sucesso!")
                except Exception as e:
                    st.error(f"❌ Erro ao atualizar a tabela: {e}")

        elif operacao == "Excluir tabela":
            tabelas_existentes = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)["name"].tolist()
            tabela_escolhida = st.selectbox("Escolha a tabela para excluir:", tabelas_existentes)

            if st.button("Excluir Tabela SQL"):
                try:
                    cursor = conn.cursor()
                    cursor.execute(f'DROP TABLE IF EXISTS "{tabela_escolhida}"')
                    conn.commit()
                    st.success(f"✅ Tabela '{tabela_escolhida}' excluída com sucesso!")
                except Exception as e:
                    st.error(f"❌ Erro ao excluir a tabela: {e}")

    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {e}")

# Visualizar tabelas existentes
st.subheader("📚 Visualizar Tabelas Existentes no Banco de Dados")

tabelas = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)

if not tabelas.empty:
    tabela_selecionada = st.selectbox("Escolha uma tabela para visualizar os dados:", tabelas["name"])
    if tabela_selecionada:
        df_tabela = pd.read_sql(f'SELECT * FROM "{tabela_selecionada}"', conn)
        st.write(f"📄 Dados da tabela: `{tabela_selecionada}`")
        st.dataframe(df_tabela)

        # Adicionar botão para excluir a tabela selecionada
        if st.button("🗑️ Excluir Tabela SQL"):
            try:
                cursor = conn.cursor()
                cursor.execute(f'DROP TABLE IF EXISTS "{tabela_selecionada}"')
                conn.commit()
                st.success(f"✅ Tabela '{tabela_selecionada}' excluída com sucesso!")
            except Exception as e:
                st.error(f"❌ Erro ao excluir a tabela: {e}")
else:
    st.info("Nenhuma tabela encontrada no banco de dados.")

# Fechar a conexão
conn.close()

