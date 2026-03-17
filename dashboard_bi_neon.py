import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px

# 1. Configuração de Página (Deve ser o primeiro comando Streamlit)
st.set_page_config(page_title="BI Trading Bot Pro", layout="wide", initial_sidebar_state="expanded")

# 2. Sistema de Auto-Refresh (30 segundos)
if "do_refresh" not in st.session_state:
    st.session_state.do_refresh = True
st.sidebar.write(f"🕒 Atualização automática: Ativa (30s)")

# 3. Conexão e Carga de Dados
DB_URL = st.secrets["DB_URL"]

@st.cache_data(ttl=30)
def load_data():
    try:
        conn = psycopg2.connect(DB_URL)
        query = "SELECT * FROM trades ORDER BY timestamp DESC"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro na conexão Neon: {e}")
        return pd.DataFrame()

df = load_data()

# --- SIDEBAR (FILTROS) ---
st.sidebar.logo("https://img.icons8.com/fluency/48/bot.png")
st.sidebar.header("🎯 Filtros de Análise")

if not df.empty:
    lista_moedas = ["Todas"] + list(df['symbol'].unique())
    moeda_sel = st.sidebar.selectbox("Escolha o Ativo:", lista_moedas)
    modo_sel = st.sidebar.radio("Modo de Operação:", ["Todos", "SIMULADO", "REAL"])

    # Aplicação dos Filtros
    df_f = df.copy()
    if moeda_sel != "Todas":
        df_f = df_f[df_f['symbol'] == moeda_sel]
    if modo_sel != "Todos":
        df_f = df_f[df_f['mode'] == modo_sel]
else:
    df_f = df

# --- DASHBOARD PRINCIPAL ---
st.title("📊 BI Trading Bot - Analytics Pro")

if not df_f.empty:
    # --- CÁLCULO DE BENCHMARK ---
    df_bench = df_f.sort_values('timestamp')
    preco_inicial = df_bench.iloc[0]['price']
    preco_atual = df_bench.iloc[-1]['price']
    retorno_mercado = ((preco_atual - preco_inicial) / preco_inicial) * 100
    lucro_total = df_f['profit_loss'].sum()

    # --- KPIs Dinâmicos ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lucro Total", f"${lucro_total:.2f}", delta=f"{lucro_total:.2f}")
    
    # KPI de Benchmark com cor dinâmica
    c2.metric("Market Performance", f"{retorno_mercado:.2f}%", 
              help="Variação do preço do ativo desde a primeira operação registrada.")
    
    c3.metric("Win Rate", f"{(len(df_f[df_f['profit_loss'] > 0]) / len(df_f) * 100):.1f}%")
    c4.metric("Avg. Vol Ratio", f"{df_f['volume_ratio'].mean():.2f}x")

    st.divider()
    
    # --- GRÁFICOS ---
    col_left, col_right = st.columns(2)
    
    with col_left:
        # Evolução do Patrimônio
        df_bench['Acumulado'] = df_bench['profit_loss'].cumsum()
        fig_evolucao = px.line(df_bench, x='timestamp', y='Acumulado', 
                               title="💰 Evolução do Lucro Acumulado ($)", 
                               template="plotly_dark", markers=True)
        fig_evolucao.update_traces(line_color='#00ffcc')
        st.plotly_chart(fig_evolucao, use_container_width=True)
        
    with col_right:
        # Scatter Plot de Volume
        fig_scatter = px.scatter(df_f, x='volume_ratio', y='profit_loss', color='symbol',
                                 size='amount', title="📈 Volume Anômalo vs Resultado ($)",
                                 template="plotly_dark", hover_data=['price'])
        st.plotly_chart(fig_scatter, use_container_width=True)

    # --- TABELA DE DADOS ---
    with st.expander("📝 Visualizar Histórico Completo de Trades"):
        st.dataframe(df_f, use_container_width=True)
else:
    st.info("Aguardando novos dados do bot para gerar o dashboard...")

# Rodapé técnico
st.caption(f"Conectado ao Neon PostgreSQL | Última atualização: {datetime.now().strftime('%H:%M:%S')}")
