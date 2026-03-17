# 🚀 Crypto Trading Bot & Real-Time BI Dashboard

Este projeto é um ecossistema completo de trading automatizado e Business Intelligence. O sistema integra a captura de dados em tempo real da **Binance**, processamento de indicadores técnicos, persistência em um banco de dados relacional na nuvem e visualização avançada de KPIs através de um dashboard interativo.

## 🛠️ Stack Tecnológica

* **Linguagem:** Python 3.14
* **Integração de Exchange:** CCXT Library (Binance Spot)
* **Banco de Dados:** PostgreSQL (Hospedado via Neon.tech / AWS São Paulo)
* **Dashboard de BI:** Streamlit Cloud
* **Visualização de Dados:** Plotly Express
* **Notificações:** WhatsApp API via CallMeBot

## 🧠 Inteligência da Estratégia

O bot utiliza filtros técnicos rigorosos para garantir entradas de alta probabilidade:
* **Filtro de Tendência:** Média Móvel Simples (SMA 200) no gráfico de 1h para garantir operações a favor da tendência principal.
* **Indicador de Momento:** RSI (Índice de Força Relativa) configurado para identificar zonas de sobrevenda (abaixo de 30).
* **Volume Institucional:** Filtro de anomalia que exige um volume 1.5x superior à média móvel de volume (SMA 20), identificando a presença de grandes players.
* **Gestão de Risco:** Saídas automatizadas via **Trailing Stop** dinâmico e **Breakeven** para proteção do capital.

## 📊 Pipeline de BI (Cloud Dashboard)

Os dados de cada operação são enviados instantaneamente para o PostgreSQL no Neon. O Dashboard consome esses dados com as seguintes funcionalidades:
* **Auto-Refresh:** Atualização automática dos KPIs a cada 30 segundos.
* **Filtros Dinâmicos:** Seleção por ativo (SOL, ADA, XRP) e modo de operação (Simulado/Real) através de uma barra lateral.
* **Modo Dark:** Interface otimizada para monitoramento contínuo.
* **Análise de Performance:** Correlação entre anomalias de volume e lucratividade por operação.

## 📁 Estrutura do Repositório

* `binance_bot_final(1).py`: Script principal do robô de trading.
* `dashboard_bi_neon.py`: Código-fonte do Dashboard de BI em Streamlit.
* `requirements.txt`: Lista de dependências para deploy em nuvem.

---
*Desenvolvido como projeto de portfólio para demonstrar competências em Engenharia de Dados, Business Intelligence e automação com Python.*
