# Versão de teste - sem BigQuery
import streamlit as st

st.set_page_config(page_title="Copa 2026", layout="wide")

st.markdown("# COPA 2026 - ANÁLISE DE IMPACTO")
st.markdown("Dashboard de Inteligência Artificial | Iônica")

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Impacto Médio", "5.8%")
col2.metric("Total de Jogos", "102")
col3.metric("Jogos Brasil", "5")
col4.metric("Diferença", "2.1%")

st.success("App está funcionando!")
