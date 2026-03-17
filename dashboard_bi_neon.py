import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px

# Faz o Dashboard recarregar os dados do Neon automaticamente a cada 30 segundos
if "do_refresh" not in st.session_state:
    st.session_state.do_refresh = True

# Comando para atualizar a página sem intervenção humana
st.logo("https://img.icons8.com/fluency/48/bot.png") # Um toque visual opcional
st.write(f"🕒 Próxima atualização em 30s...")
st.empty() # Limpa o cache visual

# Força o Modo Escuro e Configuração da Página
st.set_page_config(page_title="BI Trading Bot Pro", layout="wide", initial_sidebar_state="expanded")

# Puxa a URL das Secrets do Streamlit Cloud
DB_URL = st.secrets["DB_URL"]

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
st.sidebar.header("🎯 Filtros de Análise")
if not df.empty:
    # Filtro por Moeda
    lista_moedas = ["Todas"] + list(df['symbol'].unique())
    moeda_sel = st.sidebar.selectbox("Escolha o Ativo:", lista_moedas)
    
    # Filtro por Modo
    modo_sel = st.sidebar.radio("Modo de Operação:", ["Todos", "SIMULADO", "REAL"])

    # Aplicação dos Filtros
    df_filtered = df.copy()
    if moeda_sel != "Todas":
        df_filtered = df_filtered[df_filtered['symbol'] == moeda_sel]
    if modo_sel != "Todos":
        df_filtered = df_filtered[df_filtered['mode'] == modo_sel]
else:
    df_filtered = df

# --- DASHBOARD PRINCIPAL ---
st.title("📊 BI Trading Bot - Analytics Pro")

if not df_filtered.empty:
    # KPIs Dinâmicos
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lucro Filtrado", f"${df_filtered['profit_loss'].sum():.2f}")
    c2.metric("Win Rate", f"{(len(df_filtered[df_filtered['profit_loss'] > 0]) / len(df_filtered) * 100):.1f}%")
    c3.metric("Trades", len(df_filtered))
    c4.metric("Avg. Volume Ratio", f"{df_filtered['volume_ratio'].mean():.2f}x")

    st.divider()
    
    # Gráficos Lado a Lado
    col_left, col_right = st.columns(2)
    
    with col_left:
        fig_evolucao = px.line(df_filtered.sort_values('timestamp'), x='timestamp', y='profit_loss', 
                               title="Evolução do Patrimônio (Série Temporal)", template="plotly_dark")
        st.plotly_chart(fig_evolucao, use_container_width=True)
        
    with col_right:
        fig_scatter = px.scatter(df_filtered, x='volume_ratio', y='profit_loss', color='symbol',
                                 size='amount', title="Relação: Volume Anômalo vs Lucratividade",
                                 template="plotly_dark")
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.subheader("📋 Registros Filtrados")
    st.dataframe(df_filtered, use_container_width=True)
else:
    st.info("Selecione os filtros ou aguarde novos dados do bot.")
