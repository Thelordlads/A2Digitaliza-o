import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Download dos Dados Filtrados")

st.write("Selecione as colunas que deseja baixar e clique no botão abaixo para baixar o CSV.")

# Recupera os dados filtrados do session_state
if 'dados_filtrados' in st.session_state:
    dados_filtrados = st.session_state['dados_filtrados']
    colunas = list(dados_filtrados.columns)
    colunas_selecionadas = st.multiselect(
        "Escolha as colunas para exportar:",
        colunas,
        default=colunas
    )
    if colunas_selecionadas:
        dados_exportar = dados_filtrados[colunas_selecionadas]
        csv = dados_exportar.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Baixar CSV dos Dados Filtrados",
            data=csv,
            file_name='dados_filtrados.csv',
            mime='text/csv'
        )
        st.dataframe(dados_exportar)
    else:
        st.info("Selecione ao menos uma coluna para exportar.")
else:
    st.warning("Nenhum dado filtrado encontrado. Volte à página principal, aplique os filtros e tente novamente.")