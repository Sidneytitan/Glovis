import streamlit as st
import requests

# Função para obter dados da API
def get_api_data(url):
    response = requests.get(url)
    return response.json()

# Aplicação Streamlit
def main():
    st.title("Visualizador de Dados da API")

    # Entrada para a URL da API
    api_url = st.text_input("Digite a URL da API:")

    if api_url:
        try:
            data = get_api_data(api_url)
            st.write(data)
        except Exception as e:
            st.error(f"Erro ao buscar dados: {e}")

if __name__ == "__main__":
    main()
