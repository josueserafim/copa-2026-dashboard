import streamlit as st

st.set_page_config(page_title="Copa 2026", layout="wide")

st.title("COPA 2026 - ANÁLISE DE IMPACTO")
st.markdown("Dashboard de Inteligência Artificial | Iônica - Editora FTD")

st.divider()

# KPI Cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Impacto Médio", "5.8%", "+5.8%")

with col2:
    st.metric("Total de Jogos", "102", "Analisados")

with col3:
    st.metric("Jogos do Brasil", "5", "+5%")

with col4:
    st.metric("Diferença Brasil vs Outros", "2.1%", "Brasil: 3.8%")

st.divider()

# Abas
tab1, tab2, tab3, tab4 = st.tabs(["Impacto por Jogo", "Série Temporal", "Comparativo", "Dados"])

with tab1:
    st.subheader("Top 15 Jogos com Maior Impacto")
    st.info("Dados de demonstração - conecte ao BigQuery para dados reais")
    
    # Dados de exemplo
    example_data = {
        "Jogo": [
            "Brasil vs Japan",
            "Argentina vs Austria", 
            "Sweden vs Tunisia",
            "Portugal vs Spain",
            "United States vs Belgium"
        ],
        "Impacto %": [98.13, 97.57, 97.57, 167.87, 167.87]
    }
    
    st.bar_chart(data=example_data, x="Jogo", y="Impacto %", height=400)

with tab2:
    st.subheader("Evolução de Usuários - Série Temporal")
    st.info("Dados de demonstração - conecte ao BigQuery para dados reais")

with tab3:
    st.subheader("Brasil vs Outros Países")
    
    comparison_data = {
        "Tipo": ["Brasil Joga", "Outros Países"],
        "Impacto Médio %": [3.8, 6.0],
        "Total de Jogos": [5, 97]
    }
    
    st.bar_chart(data=comparison_data, x="Tipo", y="Impacto Médio %", height=400)

with tab4:
    st.subheader("Dados Detalhados")
    st.info("Dados de demonstração - conecte ao BigQuery para dados reais")
    
    st.write("App funcionando! Próximo passo: configurar credenciais do BigQuery")

st.divider()
st.markdown("Dashboard de Inteligência Artificial | Iônica - Editora FTD")
