import streamlit as st
import pandas as pd
import sqlite3
import json
from itertools import combinations
from streamlit_modal import Modal

# Configuração da página
st.set_page_config(page_title="Kanban - Site Carga Rastreada", layout="wide")
st.title("🚚 Planejamento de pedidos After-Sales")

PASSWORD = "123"

# Conectar ao banco de dados SQLite
conn = sqlite3.connect("logistica_interna.db")
cursor = conn.cursor()

# Criar tabela garantindo que 'cte' não seja duplicado
cursor.execute("""
CREATE TABLE IF NOT EXISTS `Site Carga Rastreada` (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cte TEXT UNIQUE,  -- Evita inserções duplicadas
    nf TEXT,
    emissor TEXT,
    status TEXT
);
""")
conn.commit()

# Verificar se a tabela tem colunas definidas antes de prosseguir
cursor.execute("PRAGMA table_info(`Site Carga Rastreada`);")
table_info = cursor.fetchall()
if not table_info:
    st.error("Erro: A tabela não contém colunas. Verifique o banco de dados.")
    st.stop()

columns = [col[1] for col in table_info]

# Carregar dados da tabela
try:
    df = pd.read_sql("SELECT * FROM `Site Carga Rastreada`", conn)
    df.columns = df.columns.str.strip()  # Remove espaços extras
    df.fillna("Não informado", inplace=True)  # Evita valores nulos

    # Agrupar dados por CTe e organizar informações de NF separadamente
    df_grouped = df.groupby(["cte", "nf"]).agg({
        **{col: "first" for col in df.columns if col not in ["cte", "nf"]}
    }).reset_index()

except Exception as e:
    st.error(f"Erro ao carregar a tabela: {e}")
    df_grouped = pd.DataFrame()

# Função para carregar estado salvo do Kanban
def load_kanban():
    try:
        with open("kanban_state.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "Em Coleta": df_grouped.to_dict(orient="records"),
            "Em Triagem": [],
            "Aguardando Coleta": [],
            "Em Rota de Entrega": [],
            "Entrega Concluída": []
        }

# Função para salvar estado do Kanban
def save_kanban():
    with open("kanban_state.json", "w") as f:
        json.dump(st.session_state.kanban, f)

# Inicializar estado
if "kanban" not in st.session_state:
    st.session_state.kanban = load_kanban()

# Função para mover cards entre colunas
def move_card(origem, destino, card):
    if card in st.session_state.kanban[origem]:
        st.session_state.kanban[origem].remove(card)
        st.session_state.kanban[destino].append(card)
        save_kanban()
        st.rerun()

def move_card_com_senha(origem, destino, card, senha):
    if senha == PASSWORD:
        move_card(origem, destino, card)
    else:
        st.error("❌ Senha incorreta! Permissão negada.")

# Estilos CSS para cartões
st.markdown("""
<style>
.kanban-column { background-color: #f8f9fb; padding: 15px; border-radius: 12px; height: 85vh; overflow-y: auto; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.07); }
.kanban-card { background: linear-gradient(145deg, #ffffff, #f3f4f7); border-radius: 10px; padding: 16px 18px; margin-bottom: 18px; box-shadow: 0 3px 10px rgba(0,0,0,0.1); }
.card-coleta { border-left: 6px solid #007bff; }
.card-triagem { border-left: 6px solid #17a2b8; }
.card-aguardando { border-left: 6px solid #ffc107; }
.card-rota { border-left: 6px solid #fd7e14; }
.card-concluido { border-left: 6px solid #28a745; }
</style>
""", unsafe_allow_html=True)

# Layout Kanban
col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
status_list = ["Em Coleta", "Em Triagem", "Aguardando Coleta", "Em Rota de Entrega", "Entrega Concluída"]
color_class = {
    "Em Coleta": "card-coleta",
    "Em Triagem": "card-triagem",
    "Aguardando Coleta": "card-aguardando",
    "Em Rota de Entrega": "card-rota",
    "Entrega Concluída": "card-concluido"
}
status_progression = {
    "Em Coleta": "Em Triagem",
    "Em Triagem": "Aguardando Coleta",
    "Aguardando Coleta": "Em Rota de Entrega",
    "Em Rota de Entrega": "Entrega Concluída"
}

for col, status in zip([col1, col2, col3, col4, col5], status_list):
    with col:
        st.subheader(status)
        cards = st.session_state.kanban.get(status, [])
        if not cards:
            st.info("Nenhum cartão aqui.")
            continue

        for card in cards:
            card_html = f"<div class='kanban-card {color_class[status]}'>"
            card_html += f"<strong>CTe:</strong> {card.get('cte', 'Não informado')}<br>"
            card_html += f"<strong>NF:</strong> {card.get('nf', 'Não informado')}<br>"
            for col_name in columns:
                if col_name not in ["cte", "nf"]:
                    card_html += f"<strong>{col_name}:</strong> {card.get(col_name, 'Não informado')}<br>"
            card_html += "</div>"
            st.markdown(card_html, unsafe_allow_html=True)

            # Botão de progressão para a próxima etapa
            if status in status_progression:
                next_status = status_progression[status]
                if st.button(f"🔄 Mover para '{next_status}' [{card.get('cte')}] - NF {card.get('nf')}", key=f"{status}_{card.get('cte')}_to_{next_status}"):
                    move_card(status, next_status, card)

            # Modal de detalhes com NF separadas
            modal = Modal(f"📋 Detalhes do CTe {card.get('cte', 'Não informado')} - NF {card.get('nf', 'Não informado')}", key=f"modal_{card.get('cte')}_{card.get('nf')}", max_width=700)
            open_modal = st.button(f"📋 Ver Detalhes [{card.get('cte', 'Não informado')}] - NF {card.get('nf', 'Não informado')}", key=f"open_modal_{card.get('cte')}_{card.get('nf')}")

            if open_modal:
                modal.open()

            if modal.is_open():
                with modal.container():
                    st.markdown(f"### Detalhes do CTe: {card.get('cte', 'Não informado')} - NF {card.get('nf', 'Não informado')}")
                    for key, value in card.items():
                        st.write(f"**{key}:** {value}")
