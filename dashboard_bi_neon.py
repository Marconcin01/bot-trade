import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from datetime import datetime

# 1. Configuração de Página
st.set_page_config(page_title="BI Trading Bot Pro", layout="wide", initial_sidebar_state="expanded")

# 2. Conexão e Carga de Dados
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
        return pd.DataFrame()

df = load_data()

# --- SIDEBAR (FILTROS) ---
st.sidebar.title("🤖 Bot Control")
st.sidebar.write(f"🕒 Refresh: 30s")

if not df.empty:
    lista_moedas = ["Todas"] + list(df['symbol'].unique())
    moeda_sel = st.sidebar.selectbox("Escolha o Ativo:", lista_moedas)
    modo_sel = st.sidebar.radio("Modo de Operação:", ["Todos", "SIMULADO", "REAL"])

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
    # --- CÁLCULOS DE BI ---
    df_bench = df_f.sort_values('timestamp')
    preco_inicial = df_bench.iloc[0]['price']
    preco_atual = df_bench.iloc[-1]['price']
    retorno_mercado = ((preco_atual - preco_inicial) / preco_inicial) * 100
    lucro_total = df_f['profit_loss'].sum()
    win_rate = (len(df_f[df_f['profit_loss'] > 0]) / len(df_f) * 100)

    # Lógica de Saldo Estimado
    compras = df_f[df_f['type'].str.contains('BUY')]
    vendas = df_f[df_f['type'].str.contains('SELL')]
    num_posicoes_abertas = len(compras) - len(vendas)
    SALDO_INICIAL = 100.0
    VALOR_POR_TRADE = 10.0
    saldo_usdt_estimado = SALDO_INICIAL - (num_posicoes_abertas * VALOR_POR_TRADE) + lucro_total

    # --- ALERTA DE META ---
    META_LUCRO = 10.0
    if lucro_total >= META_LUCRO:
        st.balloons()
        st.success(f"🏆 META ATINGIDA! Você ultrapassou ${META_LUCRO:.2f} de lucro acumulado!")

    # --- KPIs Dinâmicos ---
    c_saldo, c1, c2, c3, c4 = st.columns(5)
    c_saldo.metric("Saldo Estimado", f"${saldo_usdt_estimado:.2f}")
    c1.metric("Lucro Total", f"${lucro_total:.2f}", delta=f"{lucro_total:.2f}")
    c2.metric("Market Performance", f"{retorno_mercado:.2f}%")
    c3.metric("Win Rate", f"{win_rate:.1f}%")
    c4.metric("Avg. Vol Ratio", f"{df_f['volume_ratio'].mean():.2f}x")

    st.divider()
    
    # --- GRÁFICOS DE PERFORMANCE ---
    col_left, col_right = st.columns(2)
    with col_left:
        df_bench['Acumulado'] = df_bench['profit_loss'].cumsum()
        fig_evolucao = px.line(df_bench, x='timestamp', y='Acumulado', title="💰 Evolução do Lucro ($)", template="plotly_dark")
        fig_evolucao.update_traces(line_color='#00FFCC')
        st.plotly_chart(fig_evolucao, use_container_width=True)
        
    with col_right:
        fig_scatter = px.scatter(df_f, x='volume_ratio', y='profit_loss', color='symbol', size='amount', title="📈 Volume vs Resultado ($)", template="plotly_dark")
        st.plotly_chart(fig_scatter, use_container_width=True)

    # --- NOVO: RANKING E TEMPO DE ESPERA ---
    col_rank, col_wait = st.columns(2)
    
    with col_rank:
        st.subheader("🏆 Ranking por Ativo")
        ranking_df = df.groupby('symbol')['profit_loss'].sum().reset_index().sort_values(by='profit_loss', ascending=False)
        fig_ranking = px.bar(ranking_df, x='symbol', y='profit_loss', color='profit_loss', color_continuous_scale='GnBu', template="plotly_dark")
        st.plotly_chart(fig_ranking, use_container_width=True)

    with col_wait:
        st.subheader("🕒 Tempo Médio de Espera (Min)")
        # Lógica para calcular a duração entre BUY e SELL com o mesmo ID
        buy_data = df[df['type'].str.contains('BUY')][['trade_id', 'timestamp', 'symbol']]
        sell_data = df[df['type'].str.contains('SELL')][['trade_id', 'timestamp']]
        
        trades_completos = pd.merge(buy_data, sell_data, on='trade_id', suffixes=('_in', '_out'))
        if not trades_completos.empty:
            trades_completos['timestamp_in'] = pd.to_datetime(trades_completos['timestamp_in'])
            trades_completos['timestamp_out'] = pd.to_datetime(trades_completos['timestamp_out'])
            trades_completos['espera_min'] = (trades_completos['timestamp_out'] - trades_completos['timestamp_in']).dt.total_seconds() / 60
            
            wait_df = trades_completos.groupby('symbol')['espera_min'].mean().reset_index()
            fig_wait = px.bar(wait_df, x='symbol', y='espera_min', title="Hold Time Médio por Moeda", template="plotly_dark")
            fig_wait.update_traces(marker_color='#FFA500')
            st.plotly_chart(fig_wait, use_container_width=True)
        else:
            st.info("Aguardando o fechamento do primeiro trade para calcular o tempo de espera.")

    with st.expander("📝 Visualizar Histórico Completo"):
        st.dataframe(df_f, use_container_width=True)
else:
    st.info("Aguardando dados para gerar o dashboard...")

st.caption(f"Última atualização: {datetime.now().strftime('%H:%M:%S')} | Conectado ao Neon Cloud")
