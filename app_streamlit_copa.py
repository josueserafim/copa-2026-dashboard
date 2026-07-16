import streamlit as st
import pandas as pd
from google.cloud import bigquery
import plotly.graph_objects as go
import plotly.express as px

# ==========================
# CONFIGURAÇÃO STREAMLIT
# ==========================
st.set_page_config(
    page_title="Copa 2026 - Análise de Impacto",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Theme
st.markdown("""
    <style>
    .main {
        background-color: #0a0e27;
        color: #ffffff;
    }
    .metric-card {
        background-color: #1a1f3a;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #3d4d7a;
    }
    .title-section {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================
# CACHE E CONEXÃO BQ
# ==========================
@st.cache_resource
def conectar_bigquery():
    """Conecta ao BigQuery usando Secrets do Streamlit"""
    try:
        # Tenta ler do Streamlit Secrets
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            return bigquery.Client.from_service_account_info(creds_dict)
        else:
            st.error("Secrets não configuradas! Adicione as credenciais do Google Cloud nos Secrets.")
            return None
    except Exception as e:
        st.error(f"Erro ao conectar BigQuery: {e}")
        return None

@st.cache_data(ttl=3600)
def carregar_dados_impacto(_client):
    """Carrega dados de impacto por jogo"""
    if _client is None:
        return pd.DataFrame()
    
    try:
        query = """
        SELECT 
            data_jogo,
            hora_jogo,
            confronto,
            time_1,
            time_2,
            fase,
            tipo,
            eh_brasil,
            usuarios_jogo,
            usuarios_controle,
            variacao_pct
        FROM `analytics-bigquery-321918.ionica_gold.v_copa_impacto_por_jogo`
        ORDER BY data_jogo
        """
        return _client.query(query).to_dataframe()
    except Exception as e:
        st.warning(f"Erro ao carregar impacto: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def carregar_dados_serie_temporal(_client):
    """Carrega série temporal"""
    if _client is None:
        return pd.DataFrame()
    
    try:
        query = """
        SELECT 
            data,
            sessoes,
            usuarios,
            duracao_media_minutos
        FROM `analytics-bigquery-321918.ionica_gold.v_copa_serie_temporal`
        ORDER BY data
        """
        return _client.query(query).to_dataframe()
    except Exception as e:
        st.warning(f"Erro ao carregar série temporal: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def carregar_dados_comparacao(_client):
    """Carrega comparação Brasil vs Outros"""
    if _client is None:
        return pd.DataFrame()
    
    try:
        query = """
        SELECT 
            tipo_jogo,
            total_jogos,
            impacto_medio_pct,
            desvio_padrao,
            melhor_resultado,
            pior_resultado
        FROM `analytics-bigquery-321918.ionica_gold.v_copa_brasil_vs_outros`
        """
        return _client.query(query).to_dataframe()
    except Exception as e:
        st.warning(f"Erro ao carregar comparação: {e}")
        return pd.DataFrame()

# ==========================
# LAYOUT PRINCIPAL
# ==========================
# Header
st.markdown("""
    <div class="title-section">
        <h1>COPA 2026 - ANÁLISE DE IMPACTO</h1>
        <p style="font-size: 16px; color: #e0e0e0;">
            Dashboard de Inteligência Artificial | Iônica - Editora FTD
        </p>
    </div>
""", unsafe_allow_html=True)

# Conectar
client = conectar_bigquery()

if client:
    # Carregar dados
    df_impacto = carregar_dados_impacto(client)
    df_serie = carregar_dados_serie_temporal(client)
    df_comparacao = carregar_dados_comparacao(client)
    
    # ==========================
    # KPI CARDS
    # ==========================
    if not df_impacto.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            impacto_medio = df_impacto['variacao_pct'].mean()
            st.metric(
                "Impacto Médio",
                f"{impacto_medio:.1f}%",
                delta=f"{impacto_medio:.1f}%",
                delta_color="inverse"
            )
        
        with col2:
            total_jogos = len(df_impacto)
            st.metric(
                "Total de Jogos",
                f"{total_jogos}",
                delta="Analisados"
            )
        
        with col3:
            jogos_brasil = df_impacto[df_impacto['eh_brasil'] == True].shape[0]
            st.metric(
                "Jogos do Brasil",
                f"{jogos_brasil}",
                delta=f"{(jogos_brasil/total_jogos*100):.0f}%"
            )
        
        with col4:
            if not df_comparacao.empty:
                impacto_brasil = df_comparacao[df_comparacao['tipo_jogo'] == 'Brasil Joga']['impacto_medio_pct'].values
                impacto_outros = df_comparacao[df_comparacao['tipo_jogo'] == 'Outros Países']['impacto_medio_pct'].values
                
                if len(impacto_brasil) > 0 and len(impacto_outros) > 0:
                    diferenca = abs(impacto_brasil[0] - impacto_outros[0])
                    st.metric(
                        "Diferença Brasil vs Outros",
                        f"{diferenca:.1f}%",
                        delta=f"Brasil: {impacto_brasil[0]:.1f}%"
                    )
        
        # ==========================
        # SIDEBAR - FILTROS
        # ==========================
        st.sidebar.markdown("## FILTROS")
        
        # Filtro de Fase
        fases_disponiveis = ['Todos'] + sorted(df_impacto['fase'].unique().tolist())
        fase_selecionada = st.sidebar.selectbox("Fase:", fases_disponiveis)
        
        # Filtro de Tipo
        tipos_disponiveis = ['Todos'] + sorted(df_impacto['tipo'].unique().tolist())
        tipo_selecionado = st.sidebar.selectbox("Tipo:", tipos_disponiveis)
        
        # Aplicar filtros
        df_filtrado = df_impacto.copy()
        if fase_selecionada != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['fase'] == fase_selecionada]
        if tipo_selecionado != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['tipo'] == tipo_selecionado]
        
        # ==========================
        # ABAS
        # ==========================
        tab1, tab2, tab3, tab4 = st.tabs(
            ["Impacto por Jogo", "Série Temporal", "Comparativo", "Dados Detalhados"]
        )
        
        with tab1:
            st.markdown("### Impacto dos Jogos na Plataforma")
            
            # Top 15 maiores impactos
            df_top = df_filtrado.nlargest(15, 'variacao_pct')
            
            if not df_top.empty:
                # Gráfico Plotly interativo
                fig = px.bar(
                    df_top,
                    x='variacao_pct',
                    y='confronto',
                    orientation='h',
                    color='variacao_pct',
                    color_continuous_scale='RdYlGn',
                    labels={'variacao_pct': 'Variação (%)', 'confronto': 'Jogo'},
                    title='Top 15 Jogos com Maior Impacto'
                )
                fig.update_layout(
                    height=600,
                    template='plotly_dark',
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados para exibir com os filtros selecionados")
            
            # Estatísticas
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Pior Impacto",
                    f"{df_filtrado['variacao_pct'].max():.1f}%",
                    f"{df_filtrado.loc[df_filtrado['variacao_pct'].idxmax(), 'confronto']}"
                )
            
            with col2:
                st.metric(
                    "Melhor Impacto",
                    f"{df_filtrado['variacao_pct'].min():.1f}%",
                    f"{df_filtrado.loc[df_filtrado['variacao_pct'].idxmin(), 'confronto']}"
                )
            
            with col3:
                st.metric(
                    "Desvio Padrão",
                    f"{df_filtrado['variacao_pct'].std():.1f}%"
                )
        
        with tab2:
            st.markdown("### Evolução de Usuários - Série Temporal")
            
            if not df_serie.empty:
                # Gráfico Plotly com linha
                fig = px.line(
                    df_serie,
                    x='data',
                    y='usuarios',
                    title='Número de Usuários ao Longo do Tempo',
                    labels={'data': 'Data', 'usuarios': 'Usuários'}
                )
                fig.update_layout(
                    height=500,
                    template='plotly_dark',
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados de série temporal disponíveis")
        
        with tab3:
            st.markdown("### Brasil vs Outros Países")
            
            # Gráfico Plotly de barras comparativo
            if not df_comparacao.empty:
                fig = px.bar(
                    df_comparacao,
                    x='tipo_jogo',
                    y='impacto_medio_pct',
                    color='tipo_jogo',
                    color_discrete_map={'Brasil Joga': '#FFD700', 'Outros Países': '#4169E1'},
                    title='Comparação: Impacto Médio Brasil vs Outros Países',
                    labels={'tipo_jogo': 'Tipo de Jogo', 'impacto_medio_pct': 'Impacto Médio (%)'}
                )
                fig.update_layout(
                    height=400,
                    template='plotly_dark',
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Tabela comparativa
            st.dataframe(
                df_comparacao.style.format({
                    'impacto_medio_pct': '{:.1f}%',
                    'desvio_padrao': '{:.1f}%',
                    'melhor_resultado': '{:.1f}%',
                    'pior_resultado': '{:.1f}%'
                }),
                use_container_width=True
            )
        
        with tab4:
            st.markdown("### Dados Detalhados")
            
            # Tabela completa
            df_exibicao = df_filtrado[[
                'data_jogo', 'hora_jogo', 'confronto', 'fase', 'tipo',
                'usuarios_jogo', 'usuarios_controle', 'variacao_pct'
            ]].sort_values('data_jogo')
            
            st.dataframe(
                df_exibicao.style.format({
                    'usuarios_jogo': '{:.0f}',
                    'usuarios_controle': '{:.0f}',
                    'variacao_pct': '{:.1f}%'
                }),
                use_container_width=True,
                height=500
            )
            
            # Download CSV
            csv = df_exibicao.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"copa_2026_analise.csv",
                mime="text/csv"
            )
        
        # ==========================
        # FOOTER
        # ==========================
        st.markdown("---")
        st.markdown("""
            <div style="text-align: center; color: #888888; padding: 20px;">
                <p>Dashboard de Inteligência Artificial | Iônica - Editora FTD</p>
                <p>Dados: 102 jogos da Copa 2026 | Análise de impacto em plataforma educacional</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Sem dados disponíveis no BigQuery")

else:
    st.error("Não foi possível conectar ao BigQuery")
    st.info("Configure as credenciais do Google Cloud nos Secrets do Streamlit Cloud")
