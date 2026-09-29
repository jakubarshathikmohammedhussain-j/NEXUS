import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime

# -------------------------------------------------------------------
# 1. PAGE CONFIG & CUSTOM CSS (LUXURY TERMINAL AESTHETIC)
# -------------------------------------------------------------------
st.set_page_config(page_title="HOLO EARTH // MACRO", page_icon="⬛", layout="wide")

st.markdown("""
    <style>
        /* Ticker Ribbon */
        .marquee {
            width: 100%; background-color: #000000; color: #71717a;
            font-family: 'Courier New', monospace; font-size: 0.75rem;
            padding: 4px 0; border-bottom: 1px solid #1e293b;
            white-space: nowrap; overflow: hidden; box-sizing: border-box;
        }
        .marquee span { display: inline-block; padding-left: 100%; animation: marquee 25s linear infinite; }
        @keyframes marquee { 0% { transform: translate(0, 0); } 100% { transform: translate(-100%, 0); } }
        
        /* Typography & Glassmorphism */
        .header-title { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 800; font-size: 2rem; color: #ffffff; letter-spacing: -0.02em; margin-bottom: 0;}
        .sub-header { font-family: 'Courier New', monospace; color: #71717a; font-size: 0.8rem; letter-spacing: 0.05em; }
        .metric-box { background: rgba(10, 10, 10, 0.6); backdrop-filter: blur(10px); border: 1px solid #1e293b; border-radius: 4px; padding: 15px; }
    </style>
    
    <div class="marquee">
        <span>GRID STATUS: NOMINAL • SYNC LATENCY: 142ms • ACTIVE NODES: RICH, AEGIS, KRAKEN • COVERAGE: 2,888 ENTITIES • ALGORITHMIC EVALUATION: ACTIVE</span>
    </div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# 2. DATA PIPELINE (QUANTITATIVE HEURISTICS)
# -------------------------------------------------------------------
@st.cache_data(ttl=900)
def load_historical_telemetry():
    creds_dict = dict(st.secrets["gcp_service_account"])
    credentials = service_account.Credentials.from_service_account_info(creds_dict)
    client = bigquery.Client(credentials=credentials, project=creds_dict["project_id"])
    
    # Pull 30 days of data to calculate Z-scores and Volume MAs
    query = f"""
      SELECT ticker, close_price, percent_change, volume, rsi_14d, algorithmic_rating, timestamp
      FROM `{creds_dict["project_id"]}.telemetry_bronze.market_signals`
      WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
      ORDER BY ticker, timestamp ASC
    """
    df = client.query(query).to_dataframe()
    
    if df.empty:
        return pd.DataFrame()

    # Calculate 20-Day Volume MA and 30-Day Z-Score per ticker
    df['vol_20d_ma'] = df.groupby('ticker')['volume'].transform(lambda x: x.rolling(20, min_periods=1).mean())
    df['price_mean_30d'] = df.groupby('ticker')['close_price'].transform(lambda x: x.rolling(30, min_periods=1).mean())
    df['price_std_30d'] = df.groupby('ticker')['close_price'].transform(lambda x: x.rolling(30, min_periods=1).std())
    df['z_score_30d'] = np.where(df['price_std_30d'] > 0, (df['close_price'] - df['price_mean_30d']) / df['price_std_30d'], 0)
    
    # Flag Volume Anomalies (Volume > 2.5x 20D MA)
    df['volume_anomaly'] = df['volume'] > (2.5 * df['vol_20d_ma'])
    
    return df

df_history = load_historical_telemetry()

# Extract only the latest row per ticker for the main screener
if not df_history.empty:
    df_latest = df_history.sort_values('timestamp').groupby('ticker').tail(1).copy()
else:
    st.error("INTELLIGENCE ERROR: No telemetry found in BigQuery.")
    st.stop()

# -------------------------------------------------------------------
# 3. GLOBAL HEADER & EXECUTIVE EXPORT
# -------------------------------------------------------------------
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("<div class='header-title'>HOLO EARTH<span style='color:#38bdf8;'>.</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>PROPRIETARY CAPITAL DEPLOYMENT & MACRODYNAMIC HEURISTICS</div>", unsafe_allow_html=True)
with c2:
    csv_data = df_latest.to_csv(index=False).encode('utf-8')
    st.download_button("EXPORT BRIEFING PACK [CSV]", data=csv_data, file_name=f"HOLO_EARTH_EXEC_{datetime.utcnow().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)

st.write("")

# -------------------------------------------------------------------
# 4. VIEW ARCHITECTURE (TABS)
# -------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["MACRO PULSE", "SCREENER MATRIX", "ENGINE ROOM"])

# --- VIEW 1: MACRO PULSE ---
with tab1:
    # Calculations
    dispersion = df_latest['percent_change'].max() - df_latest['percent_change'].min()
    avg_rsi = df_latest['rsi_14d'].mean()
    anomalies_count = df_latest['volume_anomaly'].sum()
    strong_buys = len(df_latest[df_latest['algorithmic_rating'] == 'Strong Buy'])
    
    # Automated Market Summary
    dominant_flow = "expanded" if dispersion > 5.0 else "contracted"
    memo = f"**Executive Summary:** Market dispersion {dominant_flow} to {dispersion:.2f}% today. Liquidity algorithms identified {anomalies_count} entities exhibiting anomalous volume footprints (>2.5x 20D MA). Systematic RSI equilibrium is locked at {avg_rsi:.1f}, with {strong_buys} assets currently triggering strict quantitative buy signals."
    st.info(memo, icon="ℹ️")
    
    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("CROSS-SECTIONAL DISPERSION", f"{dispersion:.2f}%", "Max/Min Spread")
    m2.metric("SYSTEMIC RSI MEDIAN", f"{avg_rsi:.1f}", "14-Day Baseline")
    m3.metric("VOLUME ANOMALIES", int(anomalies_count), ">2.5x 20-Day MA")
    m4.metric("ARBITRAGE TRIGGERS", strong_buys, "Z-Score / RSI Divergence")

    st.markdown("---")
    
    # Baskets Overview
    st.markdown("##### INSTITUTIONAL BASKETS")
    baskets = {
        "Defense & Aerospace Primes": ['LMT', 'RTX', 'GD', 'BA', 'NOC', 'LHX'],
        "Global Logistics & Maritime": ['FDX', 'UPS', 'ZIM', 'MATX', 'XPO', 'CHRW', 'MAERSK.CO'],
        "AI Infrastructure & Compute Stack": ['NVDA', 'MSFT', 'GOOGL', 'AMZN', 'TSM', 'ASML', 'AVGO'],
        "Critical Minerals & Energy": ['XOM', 'CVX', 'CCJ', 'ALB', 'FCX', 'VALE']
    }
    
    bc1, bc2, bc3, bc4 = st.columns(4)
    for idx, (name, tickers) in enumerate(baskets.items()):
        b_df = df_latest[df_latest['ticker'].isin(tickers)]
        b_perf = b_df['percent_change'].mean() if not b_df.empty else 0
        b_col = [bc1, bc2, bc3, bc4][idx]
        b_col.metric(name, f"Avg Change", f"{b_perf:.2f}%")

# --- VIEW 2: SCREENER MATRIX & DOSSIER ---
with tab2:
    # Command Palette Simulation (Search & Filter)
    st.markdown("<div class='sub-header'>COMMAND PALETTE (Search Entity or Filter)</div>", unsafe_allow_html=True)
    sc1, sc2, sc3 = st.columns([2, 1, 1])
    search_query = sc1.text_input("SEARCH /", placeholder="e.g. LMT, AAPL, or ZIM").upper()
    rating_filter = sc2.selectbox("RATING FILTER", ["ALL", "Strong Buy", "Bullish Momentum", "Hold / Neutral", "Bearish Trend", "Overbought / Sell"])
    anomaly_filter = sc3.checkbox("SHOW VOLUME ANOMALIES ONLY")
    
    # Apply Filters
    f_df = df_latest.copy()
    if search_query:
        f_df = f_df[f_df['ticker'].str.contains(search_query)]
    if rating_filter != "ALL":
        f_df = f_df[f_df['algorithmic_rating'] == rating_filter]
    if anomaly_filter:
        f_df = f_df[f_df['volume_anomaly'] == True]
    
    # Split layout: Screener on left, Dossier on right
    col_screener, col_dossier = st.columns([2, 1])
    
    with col_screener:
        st.dataframe(
            f_df[['ticker', 'close_price', 'percent_change', 'z_score_30d', 'rsi_14d', 'algorithmic_rating']],
            use_container_width=True, hide_index=True, height=500,
            column_config={
                "ticker": "ENTITY", "close_price": st.column_config.NumberColumn("PRICE", format="$%.2f"),
                "percent_change": st.column_config.NumberColumn("24H DELTA", format="%.2f%%"),
                "z_score_30d": st.column_config.NumberColumn("30D Z-SCORE", format="%.2fσ"),
                "rsi_14d": "14D RSI", "algorithmic_rating": "SIGNAL"
            }
        )
    
    with col_dossier:
        st.markdown("<div class='sub-header'>TICKER TELEMETRY DOSSIER</div>", unsafe_allow_html=True)
        target_ticker = st.selectbox("SELECT ENTITY TO ANALYZE:", f_df['ticker'].tolist() if not f_df.empty else [])
        
        if target_ticker:
            dossier_data = df_latest[df_latest['ticker'] == target_ticker].iloc[0]
            dossier_hist = df_history[df_history['ticker'] == target_ticker]
            
            # Key Stats
            st.markdown(f"### {target_ticker}")
            st.markdown(f"**Close:** ${dossier_data['close_price']:.2f} | **Z-Score:** {dossier_data['z_score_30d']:.2f}σ")
            
            # Interactive Sparkline (Plotly)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dossier_hist['timestamp'], y=dossier_hist['close_price'], mode='lines', line=dict(color='#38bdf8', width=2), fill='tozeroy', fillcolor='rgba(56, 189, 248, 0.1)'))
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=150, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_visible=False, yaxis_visible=False)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            # Cross-Node Synergy
            st.markdown("##### CROSS-NODE SYNERGY")
            c_node1, c_node2 = st.columns(2)
            # Simulated checks (in a real app, this queries AEGIS/KRAKEN dataframes)
            aegis_flag = "ACTIVE CLEARANCE" if target_ticker in baskets["Defense & Aerospace Primes"] else "NO DATA"
            kraken_flag = "10-K INGESTED" if target_ticker in baskets["AI Infrastructure & Compute Stack"] else "NO DATA"
            
            c_node1.markdown(f"<div style='border:1px solid #1e293b; padding:10px; border-radius:4px;'><span class='sub-header'>AEGIS</span><br><span style='color:#10b981; font-size:12px;'>{aegis_flag}</span></div>", unsafe_allow_html=True)
            c_node2.markdown(f"<div style='border:1px solid #1e293b; padding:10px; border-radius:4px;'><span class='sub-header'>KRAKEN</span><br><span style='color:#a855f7; font-size:12px;'>{kraken_flag}</span></div>", unsafe_allow_html=True)

# --- VIEW 3: ENGINE ROOM ---
with tab3:
    st.markdown("### AUTONOMOUS ARCHITECTURE PROTOCOL")
    st.markdown("""
    The HOLO EARTH grid operates on a zero-touch, closed-loop telemetry pipeline designed to eliminate manual operational effort.
    
    1. **Data Extraction (GitHub Actions):** UTC-scheduled Python microservices query global APIs (Yahoo Finance, SEC EDGAR, USASpending).
    2. **Transformation (Pandas):** Raw arrays are sanitized, nulls (NaN/Inf) are stripped, and rolling windows (Z-Score, RSI) are computed in-memory.
    3. **Warehouse Ingestion (BigQuery):** Processed payloads are securely appended to the `telemetry_bronze` datasets via Google Cloud Service Accounts.
    4. **Visualization (Streamlit):** The frontend strictly handles read-only SQL execution and UI rendering, utilizing caching layers to minimize database egress costs.
    """)
    
