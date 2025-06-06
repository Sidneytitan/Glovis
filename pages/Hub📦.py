import streamlit as st

# Clientes com logos oficiais via URL e informações básicas
clientes = {
    "Mercedes": {
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/9/90/Mercedes-Logo.svg",
        "info": "Informações da Mercedes: histórico, produtos, contato."
    },
    "Volkswagen": {
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/6/6e/Volkswagen_logo_2019.svg",
        "info": "Informações da Volkswagen: dados financeiros, modelos, suporte."
    },
    "Scania": {
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/4/49/Scania_Griffin_Logo.svg",
        "info": "Informações da Scania: frota, serviços, assistência técnica."
    }
}

def main():
    st.sidebar.title("Clientes")
    cliente_selecionado = st.sidebar.selectbox("Escolha o Cliente", list(clientes.keys()))

    cliente = clientes[cliente_selecionado]

    # Mostrar logo
    st.image(cliente["logo_url"], width=250)

    # Título e informações
    st.title(f"Bem-vindo à página do {cliente_selecionado}")
    st.write(cliente["info"])

    # Conteúdo extra personalizado para cada cliente (exemplo)
    st.markdown("---")
    st.subheader("Conteúdo personalizado")
    if cliente_selecionado == "Mercedes":
        st.write("Aqui você pode mostrar os dados específicos da Mercedes.")
    elif cliente_selecionado == "Volkswagen":
        st.write("Informações especiais e novidades da Volkswagen.")
    elif cliente_selecionado == "Scania":
        st.write("Detalhes e estatísticas da Scania.")

if __name__ == "__main__":
    main()
