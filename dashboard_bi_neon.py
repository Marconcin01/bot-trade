import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="BI Trading Bot - Neon Cloud", layout="wide")

DB_URL = st.secrets["DB_URL"]

def load_data():
    try:
        conn = psycopg2.connect(DB_URL)
        # Buscamos todos os trades ordenados pelos mais recentes
        query = "SELECT * FROM trades ORDER BY timestamp DESC"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao conectar ao Banco de Dados Neon: {e}")
        return pd.DataFrame()

st.title("📊 Dashboard de BI - Bot de Trading (Cloud)")
st.markdown("Dados extraídos em tempo real do banco de dados **PostgreSQL (Neon)**.")

df = load_data()

if not df.empty:
    # --- KPIs Principais ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_profit = df['profit_loss'].sum()
        st.metric("Lucro Total", f"${total_profit:.2f}", delta=f"{total_profit:.2f}")
    
    with col2:
        win_rate = (len(df[df['profit_loss'] > 0]) / len(df)) * 100 if len(df) > 0 else 0
        st.metric("Win Rate", f"{win_rate:.1f}%")
        
    with col3:
        total_trades = len(df)
        st.metric("Total de Trades", total_trades)

    # --- Gráficos de BI ---
    st.divider()
    c1, c2 = st.columns(2)
    
    with c1:
        # Performance por Moeda
        fig_symbol = px.bar(df.groupby('symbol')['profit_loss'].sum().reset_index(), 
                            x='symbol', y='profit_loss', color='symbol',
                            title="Lucro Acumulado por Ativo")
        st.plotly_chart(fig_symbol, use_container_width=True)
        
    with c2:
        # Análise de Volume Institucional vs Lucro
        fig_vol = px.scatter(df, x='volume_ratio', y='profit_loss', color='symbol',
                             size='amount', hover_data=['type'],
                             title="Volume Institucional vs Resultado")
        st.plotly_chart(fig_vol, use_container_width=True)

    # --- Tabela de Dados Brutos ---
    st.subheader("📝 Histórico Completo (Vindo do Neon)")
    st.dataframe(df, use_container_width=True)

else:
    st.warning("⚠️ Nenhuma operação encontrada no banco de dados. O bot precisa realizar o primeiro trade para popular o Neon!")
