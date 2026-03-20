import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from datetime import datetime
from streamlit_autorefresh import st_autorefresh # IMPORTANTE: pip install streamlit-autorefresh

# 1. Configuração de Página
st.set_page_config(page_title="BI Trading Bot Pro", layout="wide", initial_sidebar_state="expanded")

# --- NOVIDADE: AUTO-REFRESH REAL ---
# Atualiza a página inteira a cada 30 segundos automaticamente
st_autorefresh(interval=30 * 1000, key="datarefresh")

# 2. Conexão e Carga de Dados
DB_URL = st.secrets["DB_URL"]

@st.cache_data(ttl=30)
def load_data():
    try:
        conn = psycopg2.connect(DB_URL)
        query = "SELECT * FROM trades ORDER BY timestamp DESC"
        df = pd.read_sql(query, conn)
        conn.close()
        
        # --- LIMPEZA DE DADOS (IMPEDIR ERRO NP) ---
        cols_num = ['price', 'amount', 'profit_loss', 'volume_ratio']
        for col in cols_num:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
        return df
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=30)
def load_rejections():
    try:
        conn = psycopg2.connect(DB_URL)
        df_rej = pd.read_sql("SELECT * FROM rejections ORDER BY timestamp DESC LIMIT 20", conn)
        conn.close()
        
        if 'volume_ratio' in df_rej.columns:
            df_rej['volume_ratio'] = pd.to_numeric(df_rej['volume_ratio'], errors='coerce').fillna(0.0)
            
        return df_rej
    except:
        return pd.DataFrame()

df = load_data()
df_rej = load_rejections()

# --- SIDEBAR (FILTROS) ---
st.sidebar.title("🤖 Bot Control")
st.sidebar.write(f"🕒 Status: Online")
st.sidebar.caption(f"Último Sync: {datetime.now().strftime('%H:%M:%S')}")

if not df.empty:
    lista_moedas = ["Todas"] + sorted(list(df['symbol'].unique()))
    moeda_sel = st.sidebar.selectbox("Escolha o Ativo:", lista_moedas)
    modo_sel = st.sidebar.radio("Modo de Operação:", ["Todos", "SIMULADO", "REAL"])

    df_f = df.copy()
    if moeda_sel != "Todas":
        df_f = df_f[df_f['symbol'] == moeda_sel]
    if modo_sel != "Todos":
        # Ajuste para captar BUY_SIMULADO ou SIMULADO
        df_f = df_f[df_f['mode'].str.contains(modo_sel, na=False)]
else:
    df_f = df

# --- DASHBOARD PRINCIPAL ---
st.title("📊 BI Trading Bot - Analytics Pro")

if not df_f.empty:
    # --- CÁLCULOS DE BI ---
    df_f['timestamp'] = pd.to_datetime(df_f['timestamp'])
    df_bench = df_f.sort_values('timestamp')
    
    # Prevenção para caso a coluna price venha vazia
    preco_inicial = df_bench.iloc[0]['price'] if not df_bench.empty else 0
    preco_atual = df_bench.iloc[-1]['price'] if not df_bench.empty else 0
    retorno_mercado = ((preco_atual - preco_inicial) / preco_inicial) * 100 if preco_inicial > 0 else 0
    
    lucro_total = df_f['profit_loss'].sum()
    
    # Win Rate corrigido: Considera apenas trades finalizados (SELL)
    vendas_count = len(df_f[df_f['type'].str.contains('SELL')])
    wins_count = len(df_f[(df_f['type'].str.contains('SELL')) & (df_f['profit_loss'] > 0)])
    win_rate = (wins_count / vendas_count * 100) if vendas_count > 0 else 0

    # Lógica de Saldo Estimado
    num_posicoes_abertas = len(df_f[df_f['type'].str.contains('BUY')]) - vendas_count
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
    c1.metric("Lucro Total", f"${lucro_total:.2f}", delta=f"{lucro_total:.4f}")
    c2.metric("Mkt Perf.", f"{retorno_mercado:.2f}%")
    c3.metric("Win Rate", f"{win_rate:.1f}%")
    c4.metric("Avg. Vol Ratio", f"{df_f['volume_ratio'].mean():.2f}x")

    st.divider()
    
    # --- LINHA 1: EVOLUÇÃO E VOLUME ---
    col_left, col_right = st.columns(2)
    with col_left:
        # Gráfico acumulado apenas de trades fechados (mais real)
        df_sell_only = df_bench[df_bench['type'].str.contains('SELL')].copy()
        df_sell_only['Acumulado'] = df_sell_only['profit_loss'].cumsum()
        
        fig_evolucao = px.area(df_sell_only, x='timestamp', y='Acumulado', title="💰 Curva de Patrimônio ($)", template="plotly_dark")
        fig_evolucao.update_traces(line_color='#00FFCC', fillcolor='rgba(0, 255, 204, 0.2)')
        st.plotly_chart(fig_evolucao, use_container_width=True)
        
    with col_right:
        fig_scatter = px.scatter(df_f, x='volume_ratio', y='profit_loss', color='symbol', size='amount', title="📈 Eficiência: Volume vs Resultado", template="plotly_dark")
        st.plotly_chart(fig_scatter, use_container_width=True)

    # --- LINHA 2: RANKING E TEMPO DE ESPERA ---
    col_rank, col_wait = st.columns(2)
    with col_rank:
        st.subheader("🏆 Ranking de Lucratividade")
        ranking_df = df_f.groupby('symbol')['profit_loss'].sum().reset_index().sort_values(by='profit_loss', ascending=False)
        fig_ranking = px.bar(ranking_df, x='symbol', y='profit_loss', color='profit_loss', color_continuous_scale='GnBu', template="plotly_dark")
        st.plotly_chart(fig_ranking, use_container_width=True)

    with col_wait:
        st.subheader("🕒 Tempo de Hold por Moeda")
        buy_data = df_f[df_f['type'].str.contains('BUY')][['trade_id', 'timestamp', 'symbol']]
        sell_data = df_f[df_f['type'].str.contains('SELL')][['trade_id', 'timestamp']]
        trades_completos = pd.merge(buy_data, sell_data, on='trade_id', suffixes=('_in', '_out'))
        if not trades_completos.empty:
            trades_completos['espera_min'] = (pd.to_datetime(trades_completos['timestamp_out']) - pd.to_datetime(trades_completos['timestamp_in'])).dt.total_seconds() / 60
            wait_df = trades_completos.groupby('symbol')['espera_min'].mean().reset_index()
            fig_wait = px.bar(wait_df, x='symbol', y='espera_min', template="plotly_dark")
            fig_wait.update_traces(marker_color='#FFA500')
            st.plotly_chart(fig_wait, use_container_width=True)
        else:
            st.info("Aguardando fechamento de trades para calcular Hold Time.")

    # --- LINHA 3: EFICIÊNCIA E REJEIÇÕES ---
    col_hour, col_rej = st.columns(2)
    
    with col_hour:
        st.subheader("⏰ Distribuição de Lucro (Hora)")
        df_f['hour'] = df_f['timestamp'].dt.hour
        hour_df = df_f.groupby('hour')['profit_loss'].sum().reset_index().sort_values('hour')
        fig_hour = px.bar(hour_df, x='hour', y='profit_loss', color='profit_loss', color_continuous_scale='Bluered', template="plotly_dark")
        fig_hour.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=1))
        st.plotly_chart(fig_hour, use_container_width=True)

    with col_rej:
        st.subheader("🚫 Radar de Rejeições (Filtro 1.3x)")
        if not df_rej.empty:
            st.dataframe(df_rej[['timestamp', 'symbol', 'volume_ratio']], use_container_width=True)
            avg_rej = df_rej['volume_ratio'].mean()
            st.caption(f"Volume Médio das Rejeições: {avg_rej:.2f}x")
        else:
            st.info("Nenhuma rejeição registrada.")

    with st.expander("📝 Log Detalhado de Operações"):
        st.dataframe(df_f.sort_values('timestamp', ascending=False), use_container_width=True)
else:
    st.info("🛰️ Conectado ao Neon. Aguardando a primeira operação do bot...")

st.caption(f"Status: Sincronizado | Horário Brasília: {datetime.now().strftime('%H:%M:%S')}")
