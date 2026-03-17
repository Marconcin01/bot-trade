import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from datetime import datetime

# Configuração Pro
st.set_page_config(page_title="BI Trading Bot - Benchmark", layout="wide")
DB_URL = st.secrets["DB_URL"]

@st.cache_data(ttl=30)
def load_data():
    try:
        conn = psycopg2.connect(DB_URL)
        query = "SELECT * FROM trades ORDER BY timestamp DESC"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

df = load_data()

# --- SIDEBAR ---
st.sidebar.header("🎯 Filtros")
moeda_sel = st.sidebar.selectbox("Escolha o Ativo:", ["Todas"] + list(df['symbol'].unique()) if not df.empty else ["Aguardando..."])

# --- DASHBOARD ---
st.title("📊 BI Trading: Bot vs. Mercado (Buy & Hold)")

if not df.empty:
    # Lógica de Benchmark
    df_bench = df.sort_values('timestamp')
    if moeda_sel != "Todas":
        df_bench = df_bench[df_bench['symbol'] == moeda_sel]
    
    # Preço inicial (Primeira compra) vs Preço final (Último trade)
    preco_inicial = df_bench.iloc[0]['price']
    preco_atual = df_bench.iloc[-1]['price']
    retorno_mercado = ((preco_atual - preco_inicial) / preco_inicial) * 100
    lucro_bot = df_bench['profit_loss'].sum()

    # --- KPIs de Comparação ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Lucro do Bot ($)", f"${lucro_bot:.2f}", delta=f"{lucro_bot:.2f}")
    c2.metric("Variação do Ativo (%)", f"{retorno_mercado:.2f}%", help="Quanto a moeda subiu/desceu desde o seu primeiro trade.")
    
    status_bot = "🔥 Superando o Mercado" if lucro_bot > (retorno_mercado/100) else "📉 Abaixo do Benchmark"
    c3.subheader(f"Status: {status_bot}")

    st.divider()

    # --- Gráfico de Comparação ---
    df_bench['Acumulado_Bot'] = df_bench['profit_loss'].cumsum()
    df_bench['Performance_Ativo'] = ((df_bench['price'] - preco_inicial) / preco_inicial) * 100
    
    st.subheader(f"📈 Curva de Performance: {moeda_sel}")
    fig = px.line(df_bench, x='timestamp', y=['Acumulado_Bot', 'Performance_Ativo'],
                  labels={'value': 'Resultado', 'variable': 'Métrica'},
                  template="plotly_dark", title="Lucro do Bot ($) vs Variação do Ativo (%)")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df_bench[['timestamp', 'symbol', 'price', 'profit_loss', 'Acumulado_Bot']], use_container_width=True)

else:
    st.warning("Aguardando mais dados de trades para calcular o Benchmark...")
