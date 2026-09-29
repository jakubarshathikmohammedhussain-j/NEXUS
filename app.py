import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime

# -------------------------------------------------------------------
# 1. PAGE CONFIG & AGGRESSIVE CSS OVERRIDES
# -------------------------------------------------------------------
st.set_page_config(page_title="HOLO EARTH // MACRO", page_icon="⬛", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        /* Hide Streamlit Defaults */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container {padding-top: 1rem; max-width: 1600px;}
        
        /* Ticker Ribbon */
        .marquee {
            width: 100%; background-color: #000000; color: #71717a;
            font-family: 'Courier New', monospace; font-size: 0.75rem;
            padding: 6px 0; border-bottom: 1px solid #1e293b;
            white-space: nowrap; overflow: hidden; box-sizing: border-box;
            margin-top: -15px; margin-bottom: 20px;
        }
        .marquee span { display: inline-block; padding-left: 100%; animation: marquee 20s linear infinite; }
        @keyframes marquee { 0% { transform: translate(0, 0); } 100% { transform: translate(-100%, 0); } }
        
        /* Custom Glassmorphism KPI Cards */
        .kpi-card {
            background: linear-gradient(145deg, #0a0a0a 0%, #050505 100%);
            border: 1px solid #1e293b;
            border-top: 1px solid #38bdf8;
            border-radius: 4px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            transition: all 0.3s ease;
        }
        .kpi-card:hover { border-top: 1px solid #10b981; transform: translateY(-2px); }
        .kpi-title { font-family: 'Courier New', monospace; color: #a1a1aa; font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 5px; }
        .kpi-val { font-family: 'Helvetica Neue', sans-serif; font-weight: 700; font-size: 2.2rem; color: #ffffff; line-height: 1.1; }
        .kpi-sub { font-family: 'Courier New', monospace; color: #52525b; font-size: 0.65rem; margin-top: 5px; }
        
        /* Typography */
        .brand-title { font-family: 'Helvetica Neue', sans-serif; font-weight: 900; font-size: 2.5rem; color: #ffffff; letter-spacing: -0.04em; line-height: 1; }
        .brand-dot { color: #38bdf8; }
        .brand-sub { font-family: 'Courier New', monospace; color: #71717a; font-size: 0.75rem; letter-spacing: 0.05em; margin-top: 5px; }
        
        /* Tab Styling Override */
        .stTabs [data-baseweb="tab-list"] { gap: 20px; border-bottom: 1px solid #1e293b; }
        .stTabs [data-baseweb="tab"] { color: #71717a; font-family: 'Courier New', monospace; font-size: 0.85rem; letter-spacing: 0.05em; }
        .stTabs [aria-selected="true"] { color: #ffffff !important; border-bottom-color: #38bdf8 !important; }
    </style>
    
    <div class="marquee">
        <span>[HOLOSPHERE LIVE] GRID STATUS: NOMINAL • LATENCY: 42ms • COVERAGE: 2,888 ENTITIES • ALGORITHMIC EVALUATION: ACTIVE • NEXT SYNC: 08:00 UTC</span>
    </div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# 2. DATA PIPELINE (QUANTITATIVE ENGINE)
# -------------------------------------------------------------------
@st.cache_data(ttl=900)
def load_historical_telemetry():
    creds_dict = dict(st.secrets["gcp_service_account"])
    credentials = service_account.Credentials.from_service_account_info(creds_dict)
    client = bigquery.Client(credentials=credentials, project=creds_dict["project_id"])
    
    query = f"""
      SELECT ticker, close_price, percent_change, volume, rsi_14d, algorithmic_rating, timestamp
      FROM `{creds_dict["project_id"]}.telemetry_bronze.market_signals`
      WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 45 DAY)
      ORDER BY ticker, timestamp ASC
    """
    df = client.query(query).to_dataframe()
    if df.empty: return pd.DataFrame()

    df['vol_20d_ma'] = df.groupby('ticker')['volume'].transform(lambda x: x.rolling(20, min_periods=1).mean())
    df['price_mean_30d'] = df.groupby('ticker')['close_price'].transform(lambda x: x.rolling(30, min_periods=1).mean())
    df['price_std_30d'] = df.groupby('ticker')['close_price'].transform(lambda x: x.rolling(30, min_periods=1).std())
    df['z_score_30d'] = np.where(df['price_std_30d'] > 0, (df['close_price'] - df['price_mean_30d']) / df['price_std_30d'], 0)
    df['volume_anomaly'] = df['volume'] > (2.5 * df['vol_20d_ma'])
    
    return df

df_history = load_historical_telemetry()

if not df_history.empty:
    df_latest = df_history.sort_values('timestamp').groupby('ticker').tail(1).copy()
else:
    st.error("INTELLIGENCE ERROR: No telemetry found in BigQuery.")
    st.stop()

# -------------------------------------------------------------------
# 3. GLOBAL HEADER
# -------------------------------------------------------------------
c1, c2 = st.columns([4, 1])
with c1:
    st.markdown("<div class='brand-title'>HOLO EARTH<span class='brand-dot'>.</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='brand-sub'>PROPRIETARY CAPITAL DEPLOYMENT & MACRODYNAMIC HEURISTICS</div>", unsafe_allow_html=True)
with c2:
    st.write("") # Padding
    csv_data = df_latest.to_csv(index=False).encode('utf-8')
    st.download_button("EXPORT BRIEFING [CSV]", data=csv_data, file_name=f"HOLO_EARTH_{datetime.utcnow().strftime('%Y%m%d')}.csv", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------------------------
# 4. ARCHITECTURE TABS
# -------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["[01] MACRO PULSE", "[02] SCREENER MATRIX", "[03] SYSTEM TOPOLOGY"])

# --- VIEW 1: MACRO PULSE ---
with tab1:
    # Calculations
    dispersion = df_latest['percent_change'].max() - df_latest['percent_change'].min()
    avg_rsi = df_latest['rsi_14d'].mean()
    anomalies_count = df_latest['volume_anomaly'].sum()
    strong_buys = len(df_latest[df_latest['algorithmic_rating'] == 'Strong Buy'])
    
    # Custom HTML KPI Cards
    kpi_html = f"""
    <div style="display: flex; justify-content: space-between; gap: 15px; margin-bottom: 25px;">
        <div class="kpi-card" style="flex: 1;">
            <div class="kpi-title">CROSS-SECTIONAL DISPERSION</div>
            <div class="kpi-val">{dispersion:.2f}%</div>
            <div class="kpi-sub">SPREAD BETWEEN MAX/MIN DELTA</div>
        </div>
        <div class="kpi-card" style="flex: 1; border-top-color: #10b981;">
            <div class="kpi-title">SYSTEMIC RSI MEDIAN</div>
            <div class="kpi-val">{avg_rsi:.1f}</div>
            <div class="kpi-sub">14-DAY OSCILLATOR BASELINE</div>
        </div>
        <div class="kpi-card" style="flex: 1; border-top-color: #f59e0b;">
            <div class="kpi-title">LIQUIDITY ANOMALIES</div>
            <div class="kpi-val">{anomalies_count}</div>
            <div class="kpi-sub">ENTITIES > 2.5X 20D VOLUME MA</div>
        </div>
        <div class="kpi-card" style="flex: 1; border-top-color: #a855f7;">
            <div class="kpi-title">ARBITRAGE TRIGGERS</div>
            <div class="kpi-val">{strong_buys}</div>
            <div class="kpi-sub">STRICT 'STRONG BUY' SIGNALS</div>
        </div>
    </div>
    """
    st.markdown(kpi_html, unsafe_allow_html=True)
    
    # Plotly Arbitrage Matrix
    st.markdown("<div class='brand-sub' style='color:#38bdf8; margin-bottom: 10px;'>QUANTITATIVE ARBITRAGE MATRIX (RSI VS Z-SCORE)</div>", unsafe_allow_html=True)
    
    fig = px.scatter(
        df_latest, x="rsi_14d", y="z_score_30d", 
        color="algorithmic_rating", hover_name="ticker",
        color_discrete_map={
            "Strong Buy": "#10b981", "Bullish Momentum": "#38bdf8", 
            "Hold / Neutral": "#71717a", "Bearish Trend": "#f43f5e", "Overbought / Sell": "#7f1d1d"
        },
        height=400
    )
    fig.update_traces(marker=dict(size=6, opacity=0.7, line=dict(width=0)))
    fig.update_layout(
        plot_bgcolor="#050505", paper_bgcolor="#050505",
        xaxis=dict(title="14-Day RSI (Momentum)", showgrid=True, gridcolor="#18181b", zerolinecolor="#27272a"),
        yaxis=dict(title="30-Day Z-Score (Mean Reversion)", showgrid=True, gridcolor="#18181b", zerolinecolor="#27272a"),
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(family="Courier New", size=10, color="#a1a1aa"))
    )
    # Add target zones
    fig.add_shape(type="rect", x0=0, y0=-4, x1=35, y1=-1.5, fillcolor="rgba(16, 185, 129, 0.1)", line_width=0, layer="below")
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# --- VIEW 2: SCREENER MATRIX ---
with tab2:
    sc1, sc2, sc3 = st.columns([2, 1, 1])
    search_query = sc1.text_input("COMMAND PALETTE / SEARCH ENTITY:", placeholder="e.g. NVDA, LMT").upper()
    rating_filter = sc2.selectbox("SIGNAL FILTER:", ["ALL", "Strong Buy", "Bullish Momentum", "Hold / Neutral", "Bearish Trend", "Overbought / Sell"])
    anomaly_filter = sc3.checkbox("VOLUME ANOMALIES ONLY")
    
    f_df = df_latest.copy()
    if search_query: f_df = f_df[f_df['ticker'].str.contains(search_query)]
    if rating_filter != "ALL": f_df = f_df[f_df['algorithmic_rating'] == rating_filter]
    if anomaly_filter: f_df = f_df[f_df['volume_anomaly'] == True]
    
    col_screener, col_dossier = st.columns([2.5, 1.5])
    
    with col_screener:
        st.dataframe(
            f_df[['ticker', 'close_price', 'percent_change', 'z_score_30d', 'rsi_14d', 'algorithmic_rating']],
            use_container_width=True, hide_index=True, height=550,
            column_config={
                "ticker": "ENTITY", "close_price": st.column_config.NumberColumn("PRICE", format="$%.2f"),
                "percent_change": st.column_config.NumberColumn("24H DELTA", format="%.2f%%"),
                "z_score_30d": st.column_config.NumberColumn("30D Z-SCORE", format="%.2fσ"),
                "rsi_14d": st.column_config.NumberColumn("14D RSI", format="%.1f"),
                "algorithmic_rating": "SYSTEM SIGNAL"
            }
        )
    
    with col_dossier:
        st.markdown("<div class='brand-sub' style='color:#38bdf8;'>TICKER TELEMETRY DOSSIER</div>", unsafe_allow_html=True)
        target_ticker = st.selectbox("ENGAGE TARGET:", f_df['ticker'].tolist() if not f_df.empty else [], label_visibility="collapsed")
        
        if target_ticker:
            d_data = df_latest[df_latest['ticker'] == target_ticker].iloc[0]
            d_hist = df_history[df_history['ticker'] == target_ticker]
            
            dossier_html = f"""
            <div style="background: #0a0a0a; border: 1px solid #1e293b; padding: 20px; border-radius: 4px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 1px solid #1e293b; padding-bottom: 10px; margin-bottom: 15px;">
                    <div style="font-family: 'Helvetica Neue', sans-serif; font-size: 2rem; font-weight: 800; color: #fff;">{target_ticker}</div>
                    <div style="font-family: monospace; font-size: 1.2rem; color: #38bdf8;">${d_data['close_price']:.2f}</div>
                </div>
                <div style="font-family: monospace; font-size: 0.8rem; color: #a1a1aa; line-height: 1.8;">
                    <div style="display: flex; justify-content: space-between;"><span>24H DELTA:</span> <span style="color: {'#10b981' if d_data['percent_change'] > 0 else '#f43f5e'};">{d_data['percent_change']:.2f}%</span></div>
                    <div style="display: flex; justify-content: space-between;"><span>Z-SCORE:</span> <span>{d_data['z_score_30d']:.2f}σ</span></div>
                    <div style="display: flex; justify-content: space-between;"><span>RSI (14D):</span> <span>{d_data['rsi_14d']:.1f}</span></div>
                    <div style="display: flex; justify-content: space-between;"><span>VOLUME:</span> <span>{d_data['volume']:,.0f}</span></div>
                    <div style="display: flex; justify-content: space-between; border-top: 1px dashed #27272a; margin-top: 5px; padding-top: 5px;">
                        <span>SIGNAL:</span> <span style="color: #38bdf8; font-weight: bold;">{d_data['algorithmic_rating']}</span>
                    </div>
                </div>
            </div>
            """
            st.markdown(dossier_html, unsafe_allow_html=True)
            
            # Trajectory Sparkline
            if len(d_hist) > 1:
                fig_line = go.Figure()
                fig_line.add_trace(go.Scatter(x=d_hist['timestamp'], y=d_hist['close_price'], mode='lines', line=dict(color='#38bdf8', width=2), fill='tozeroy', fillcolor='rgba(56, 189, 248, 0.1)'))
                fig_line.update_layout(height=180, margin=dict(l=0, r=0, t=20, b=0), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", xaxis=dict(showgrid=False, visible=False), yaxis=dict(showgrid=True, gridcolor="#18181b", tickfont=dict(color="#71717a", family="monospace")))
                st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})

# --- VIEW 3: ENGINE ROOM ---
with tab3:
    st.markdown("""
    <div style="max-width: 800px; font-family: 'Helvetica Neue', sans-serif;">
        <h3 style="color: #fff; font-weight: 800;">AUTONOMOUS ARCHITECTURE PROTOCOL</h3>
        <p style="color: #a1a1aa; font-size: 0.95rem; line-height: 1.6;">
            HOLO EARTH operates on a zero-touch, closed-loop telemetry pipeline designed to eliminate manual operational drag.
        </p>
        <div style="border-left: 2px solid #38bdf8; padding-left: 20px; margin-top: 20px; color: #d4d4d8;">
            <p><b>1. Extraction (GitHub Actions):</b> CRON-scheduled Python microservices query global endpoints (Yahoo Finance, SEC EDGAR, USASpending).</p>
            <p><b>2. Transformation (Pandas/NumPy):</b> Arrays are sanitized of nulls (NaN/Inf), and rolling statistics (Z-Score, RSI, Vol-MA) are computed in-memory.</p>
            <p><b>3. Ingestion (Google BigQuery):</b> Payloads append to <code>telemetry_bronze</code> via secure GCP Service Accounts.</p>
            <p><b>4. Visualization (Streamlit):</b> UI executes read-only SQL queries with 15-minute caching layers to minimize egress cost while maintaining operational latency.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
