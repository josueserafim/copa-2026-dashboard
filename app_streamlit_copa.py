import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from google.cloud import bigquery
from datetime import datetime
import os
import json

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
    """Conecta ao BigQuery usando credentials.json local ou Secrets"""
    try:
        # Tenta ler credentials.json da pasta local PRIMEIRO
        if os.path.exists('credentials.json'):
            st.info("Usando credentials.json local")
            return bigquery.Client.from_service_account_json('credentials.json')
        # Se não houver arquivo local, tenta Streamlit Secrets
        elif "gcp_service_account" in st.secrets:
            st.info("Usando Secrets do Streamlit Cloud")
            creds_dict = dict(st.secrets["gcp_service_account"])
            return bigquery.Client.from_service_account_info(creds_dict)
        else:
            # Fallback: tenta usar credenciais do ambiente
            st.info("Usando credenciais do ambiente")
            return bigquery.Client(project="analytics-bigquery-321918")
    except Exception as e:
        st.error(f"Erro ao conectar BigQuery: {e}")
        st.warning("Certifique-se de que credentials.json está na mesma pasta do script!")
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
            duracao_media_minutos,
            jogos_do_dia,
            fases,
            tem_jogo_brasil,
            quantidade_jogos_dia
        FROM `analytics-bigquery-321918.ionica_gold.v_copa_serie_temporal`
        ORDER BY data DESC
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

@st.cache_data(ttl=3600)
def carregar_dados_fase(_client):
    """Carrega resumo por fase"""
    if _client is None:
        return pd.DataFrame()
    
    try:
        query = """
        SELECT 
            fase,
            total_jogos,
            impacto_medio_pct,
            melhor_impacto,
            pior_impacto,
            variacao_stddev
        FROM `analytics-bigquery-321918.ionica_gold.v_copa_resumo_por_fase`
        ORDER BY impacto_medio_pct DESC
        """
        return _client.query(query).to_dataframe()
    except Exception as e:
        st.warning(f"Erro ao carregar fase: {e}")
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
    try:
        df_impacto = carregar_dados_impacto(client)
        df_serie = carregar_dados_serie_temporal(client)
        df_comparacao = carregar_dados_comparacao(client)
        df_fase = carregar_dados_fase(client)
        
        if df_impacto.empty:
            st.warning("Sem dados disponíveis no BigQuery")
        else:
            # ==========================
            # KPI CARDS (TOP)
            # ==========================
            st.markdown("### Indicadores Principais")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                impacto_medio = df_impacto['variacao_pct'].mean()
                st.metric("Impacto Médio", f"{impacto_medio:.1f}%")
                if impacto_medio < 0:
                    st.caption("Queda média de acessos durante os jogos")
                elif impacto_medio > 0:
                    st.caption("Aumento médio de acessos durante os jogos")
                else:
                    st.caption("Sem variação média")
            
            with col2:
                total_jogos = len(df_impacto)
                st.metric("Total de Jogos", f"{total_jogos}")
                st.caption("Analisados")
            
            with col3:
                jogos_brasil = df_impacto[df_impacto['eh_brasil'] == True].shape[0]
                st.metric("Jogos do Brasil", f"{jogos_brasil}")
                st.caption(f"{(jogos_brasil/total_jogos*100):.0f}% do total")
            
            with col4:
                if not df_comparacao.empty:
                    impacto_brasil = df_comparacao[df_comparacao['tipo_jogo'] == 'Brasil Joga']['impacto_medio_pct'].values
                    impacto_outros = df_comparacao[df_comparacao['tipo_jogo'] == 'Outros Países']['impacto_medio_pct'].values
                    
                    if len(impacto_brasil) > 0 and len(impacto_outros) > 0:
                        diferenca = abs(impacto_brasil[0] - impacto_outros[0])
                        st.metric(
                            "Diferença Brasil vs Outros",
                            f"{diferenca:.1f}%"
                        )
            
            # Explicação dos KPIs (Dropdown)
            with st.expander("Como ler os indicadores", expanded=False):
                st.markdown("""
                **Impacto Médio:** Variação percentual média dos acessos durante todos os jogos analisados. 
                - Valores NEGATIVOS = Menos usuários durante os jogos (esperado - competição com transmissão)
                - Valores POSITIVOS = Mais usuários durante os jogos (conteúdo Copa atraindo)

                **Total de Jogos:** Quantidade total de partidas da Copa 2026 que tiveram seus dados analisados.

                **Jogos do Brasil:** Número de partidas que o Brasil participou e foram monitoradas.

                **Diferença Brasil vs Outros:** Comparação do impacto médio entre jogos com Brasil e jogos entre outros países.
                """)
            
            st.divider()
            
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
            # TABS
            # ==========================
            tab1, tab2, tab3, tab4 = st.tabs(
                ["Impacto por Jogo", "Série Temporal", "Comparativo", "Dados Detalhados"]
            )
            
            with tab1:
                st.markdown("### Impacto dos Jogos na Plataforma")
                
                # Gráfico de Barras - Top 15
                df_top = df_filtrado.nlargest(15, 'variacao_pct')
                
                fig_barras = px.bar(
                    df_top,
                    x='variacao_pct',
                    y='confronto',
                    orientation='h',
                    color='eh_brasil',
                    color_discrete_map={True: '#FFD700', False: '#3498DB'},
                    hover_data=['data_jogo', 'hora_jogo', 'fase', 'usuarios_jogo', 'usuarios_controle'],
                    title="Top 15 Jogos com Maior Impacto",
                    labels={
                        'variacao_pct': 'Variação (%)',
                        'confronto': 'Confronto',
                        'eh_brasil': 'Brasil'
                    }
                )
                
                fig_barras.update_layout(
                    height=500,
                    template='plotly_dark',
                    hovermode='y unified',
                    margin=dict(l=150)
                )
                
                st.plotly_chart(fig_barras, use_container_width=True)
                
                # Explicação do gráfico (Dropdown)
                with st.expander("Como ler este gráfico", expanded=False):
                    st.markdown("""
                    **Eixo Horizontal (Variação %):** Mostra a variação percentual de usuários durante o jogo.
                    - Valores NEGATIVOS = MENOS acessos durante o jogo (esperado - concorrência com transmissão)
                    - Valores POSITIVOS = MAIS acessos durante o jogo (conteúdo Copa atraindo usuários)

                    **Cores:** 
                    - Amarelo = Jogos com Brasil
                    - Azul = Jogos entre outros países

                    **Barra mais longa para a esquerda (negativa):** Maior queda de usuários durante o jogo.
                    **Barra mais longa para a direita (positiva):** Maior aumento de usuários durante o jogo.

                    **Interatividade:** Passe o mouse sobre as barras para ver data, hora, fase e número de usuários.
                    """)
                
                # Estatísticas
                st.markdown("### Estatísticas do Período")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    linha_min = df_filtrado.loc[df_filtrado['variacao_pct'].idxmin()]
                    st.metric("Maior Queda", f"{linha_min['variacao_pct']:.1f}%")
                    st.caption(linha_min['confronto'])
                
                with col2:
                    linha_max = df_filtrado.loc[df_filtrado['variacao_pct'].idxmax()]
                    st.metric("Maior Aumento", f"{linha_max['variacao_pct']:.1f}%")
                    st.caption(linha_max['confronto'])
                
                with col3:
                    st.metric(
                        "Desvio Padrão",
                        f"{df_filtrado['variacao_pct'].std():.1f}%"
                    )
                
                with st.expander("O que significam essas métricas", expanded=False):
                    st.markdown("""
                    **Maior Queda:** O jogo que MAIS diminuiu os acessos à plataforma (competição com transmissão do jogo).

                    **Maior Aumento:** O jogo que MAIS aumentou os acessos (conteúdo Copa-relacionado atraindo usuários).

                    **Desvio Padrão:** Mede a variabilidade dos impactos. 
                    - Valores altos = impactos muito diferentes entre jogos
                    - Valores baixos = impactos mais consistentes
                    """)
            
            with tab2:
                st.markdown("### Evolução de Usuários - Série Temporal")
                
                if not df_serie.empty:
                    # Gráfico de Linha
                    fig_linha = px.line(
                        df_serie,
                        x='data',
                        y='usuarios',
                        color='tem_jogo_brasil',
                        hover_data=['usuarios', 'jogos_do_dia'],
                        title="Acesso Diário à Plataforma",
                        labels={
                            'data': 'Data',
                            'usuarios': 'Usuários',
                            'tem_jogo_brasil': 'Brasil Jogando'
                        }
                    )
                    
                    fig_linha.update_layout(
                        height=500,
                        template='plotly_dark',
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig_linha, use_container_width=True)
                    
                    with st.expander("Como ler este gráfico", expanded=False):
                        st.markdown("""
                        **Eixo Horizontal (Data):** Período de análise da Copa 2026.

                        **Eixo Vertical (Usuários):** Número de usuários acessando a plataforma naquele dia.

                        **Cores da linha:** Diferentes cores indicam dias com (azul claro) e sem (azul escuro) jogos do Brasil.

                        **Picos e quedas:** 
                        - Picos = dias com mais acesso
                        - Quedas = dias com menos acesso (geralmente durante/após jogos)

                        **Tendência geral:** A linha mostra se o engajamento está crescendo, caindo ou se mantendo estável ao longo do tempo.
                        """)
                else:
                    st.info("Sem dados de série temporal disponíveis")
            
            with tab3:
                st.markdown("### Brasil vs Outros Países")
                
                if not df_comparacao.empty:
                    # Gráfico Comparativo
                    fig_comparacao = px.bar(
                        df_comparacao,
                        x='tipo_jogo',
                        y='impacto_medio_pct',
                        color='tipo_jogo',
                        color_discrete_map={'Brasil Joga': '#FFD700', 'Outros Países': '#3498DB'},
                        hover_data=['total_jogos', 'desvio_padrao', 'melhor_resultado', 'pior_resultado'],
                        title="Comparação: Impacto Médio Brasil vs Outros",
                        labels={
                            'tipo_jogo': 'Tipo',
                            'impacto_medio_pct': 'Impacto Médio (%)'
                        }
                    )
                    
                    fig_comparacao.update_layout(
                        height=400,
                        template='plotly_dark',
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig_comparacao, use_container_width=True)
                    
                    with st.expander("Como ler este gráfico", expanded=False):
                        st.markdown("""
                        **Comparação direta:** Mostra qual tipo de jogo (Brasil ou Outros) tem maior impacto médio nos acessos.

                        **Barra mais baixa (mais negativa):** Maior queda de acessos durante estes jogos.

                        **Número de jogos:** Passe o mouse para ver quantos jogos de cada tipo foram analisados.

                        **Interpretação:** 
                        - Se Brasil tem queda MAIOR = jogos do Brasil afastam mais usuários (mais audiência de TV)
                        - Se Outros tem queda MAIOR = outros jogos afastam mais usuários
                        """)
                    
                    # Tabela comparativa
                    st.markdown("### Detalhes da Comparação")
                    st.dataframe(
                        df_comparacao.style.format({'impacto_medio_pct': '{:.1f}%', 'desvio_padrao': '{:.1f}%'}),
                        use_container_width=True
                    )
                else:
                    st.info("Sem dados de comparação disponíveis")
            
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
                
                with st.expander("Explicação das colunas", expanded=False):
                    st.markdown("""
                    **Data/Hora do Jogo:** Quando a partida ocorreu.

                    **Confronto:** Qual foi o jogo (times envolvidos).

                    **Fase:** Etapa da Copa (Grupos, Oitavas, Quartas, etc).

                    **Tipo:** Se foi jogo do Brasil ou de Outros Países.

                    **Usuários Jogo:** Quantidade de usuários durante o dia do jogo.

                    **Usuários Controle:** Usuários no mesmo dia da semana da semana anterior (baseline).

                    **Variação %:** Percentual de diferença entre dia do jogo e baseline.
                    - Negativo = Menos usuários durante o jogo
                    - Positivo = Mais usuários durante o jogo
                    """)
                
                # Download CSV
                csv = df_exibicao.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"copa_2026_analise_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
            # ==========================
            # FOOTER
            # ==========================
            st.markdown("---")
            st.markdown("""
                <div style="text-align: center; color: #888888; padding: 20px;">
                    <p>Dashboard de Inteligência Artificial | Iônica - Editora FTD</p>
                    <p>Última atualização: """ + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + """</p>
                    <p>Dados: 104 jogos da Copa 2026 | Análise de impacto em plataforma educacional</p>
                </div>
            """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        st.info("Verifique se as views existem no BigQuery")

else:
    st.error("Não foi possível conectar ao BigQuery")
    st.warning("Certifique-se de que:")
    st.warning("1. credentials.json está na mesma pasta que este script")
    st.warning("2. OU as credenciais estão configuradas nos Secrets do Streamlit Cloud")
