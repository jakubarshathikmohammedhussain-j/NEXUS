import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime

# -------------------------------------------------------------------
# 1. PAGE CONFIG & V4 CYBERNETIC CSS (HEX GRID & ANIMATIONS)
# -------------------------------------------------------------------
st.set_page_config(page_title="HOLO EARTH // OMEGA", page_icon="⬛", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        /* Hide Default Streamlit Elements */
        #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
        .block-container {padding-top: 1rem; max-width: 1600px; z-index: 10;}
        
        /* The Living Hex-Grid Background */
        .stApp {
            background-color: #030303;
            background-image: 
                linear-gradient(rgba(20, 20, 20, 0.8) 1px, transparent 1px),
                linear-gradient(90deg, rgba(20, 20, 20, 0.8) 1px, transparent 1px);
            background-size: 30px 30px;
            background-position: center center;
        }

        /* Glitch & Target Lock Animations */
        @keyframes targetLock {
            0% { transform: scale(1.1); opacity: 0; box-shadow: 0 0 0 rgba(56,189,248,0); }
            50% { box-shadow: 0 0 20px rgba(56,189,248,0.5); }
            100% { transform: scale(1); opacity: 1; box-shadow: 0 0 0 rgba(56,189,248,0); }
        }
        .dossier-lock { animation: targetLock 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
        
        /* Glowing Glassmorphism KPIs */
        .kpi-card {
            background: rgba(5, 5, 5, 0.85); backdrop-filter: blur(10px);
            border: 1px solid #1e293b; border-radius: 4px; padding: 20px;
            transition: all 0.3s ease; position: relative; overflow: hidden;
        }
        .kpi-card::before { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 2px; }
        .kpi-card:hover { transform: translateY(-3px); box-shadow: 0 10px 30px rgba(0,0,0,0.8); }
        .glow-blue::before { background: #38bdf8; box-shadow: 0 0 15px #38bdf8; }
        .glow-emerald::before { background: #10b981; box-shadow: 0 0 15px #10b981; }
        .glow-amber::before { background: #f59e0b; box-shadow: 0 0 15px #f59e0b; }
        .glow-purple::before { background: #a855f7; box-shadow: 0 0 15px #a855f7; }
        
        .kpi-title { font-family: 'Courier New', monospace; color: #a1a1aa; font-size: 0.75rem; letter-spacing: 0.1em; }
        .kpi-val { font-family: 'Helvetica Neue', sans-serif; font-weight: 900; font-size: 2.5rem; color: #ffffff; line-height: 1.1; }
        .kpi-sub { font-family: 'Courier New', monospace; color: #52525b; font-size: 0.65rem; margin-top: 5px; text-transform: uppercase; }
        
        /* Ticker Ribbon */
        .marquee {
            width: 100%; background-color: #000; color: #38bdf8; font-family: 'Courier New', monospace; font-size: 0.75rem; font-weight: bold;
            padding: 6px 0; border-bottom: 1px solid #1e293b; white-space: nowrap; overflow: hidden; margin-top: -15px; margin-bottom: 20px;
        }
        .marquee span { display: inline-block; padding-left: 100%; animation: marquee 20s linear infinite; }
        @keyframes marquee { 0% { transform: translate(0, 0); } 100% { transform: translate(-100%, 0); } }
        
        .brand-title { font-family: 'Helvetica Neue', sans-serif; font-weight: 900; font-size: 2.8rem; color: #ffffff; letter-spacing: -0.05em; line-height: 1; }
        .brand-dot { color: #38bdf8; text-shadow: 0 0 15px #38bdf8; }
        .brand-sub { font-family: 'Courier New', monospace; color: #71717a; font-size: 0.75rem; letter-spacing: 0.1em; margin-top: 5px; text-transform: uppercase;}
    </style>
    
    <div class="marquee">
        <span>[O.M.E.G.A. PROTOCOL ENGAGED] SYSTEM TOPOLOGY ACTIVE • RENDERING 3D MACRO SURFACE • SCANNING 2,888 ENTITIES • GOD VIEW CLUSTERING ONLINE </span>
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
if not df_history.empty: df_latest = df_history.sort_values('timestamp').groupby('ticker').tail(1).copy()
else: st.error("INTELLIGENCE ERROR: No telemetry found."); st.stop()

# -------------------------------------------------------------------
# 3. GLOBAL HEADER
# -------------------------------------------------------------------
c1, c2 = st.columns([4, 1])
with c1:
    st.markdown("<div class='brand-title'>HOLO EARTH<span class='brand-dot'>.</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='brand-sub'>PROPRIETARY CAPITAL DEPLOYMENT & MACRODYNAMIC HEURISTICS</div>", unsafe_allow_html=True)
with c2:
    st.write("") 
    st.download_button("EXPORT SYSTEM DOSSIER [CSV]", data=df_latest.to_csv(index=False).encode('utf-8'), file_name=f"OMEGA_EXPORT_{datetime.utcnow().strftime('%Y%m%d')}.csv", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------------------------
# 4. ARCHITECTURE TABS (ADDED GOD VIEW)
# -------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["[01] O.M.E.G.A. TOPOLOGY", "[02] SIGNAL MATRIX", "[03] GOD VIEW", "[04] ARCHITECTURE"])

# --- VIEW 1: O.M.E.G.A. TOPOLOGY (3D MACRO) ---
with tab1:
    dispersion = df_latest['percent_change'].max() - df_latest['percent_change'].min()
    avg_rsi = df_latest['rsi_14d'].mean()
    anomalies_count = df_latest['volume_anomaly'].sum()
    strong_buys = len(df_latest[df_latest['algorithmic_rating'] == 'Strong Buy'])
    
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; gap: 15px; margin-bottom: 25px;">
        <div class="kpi-card glow-blue" style="flex: 1;"><div class="kpi-title">GLOBAL DISPERSION</div><div class="kpi-val">{dispersion:.2f}%</div><div class="kpi-sub">MAX/MIN DELTA SPREAD</div></div>
        <div class="kpi-card glow-emerald" style="flex: 1;"><div class="kpi-title">SYSTEMIC RSI</div><div class="kpi-val">{avg_rsi:.1f}</div><div class="kpi-sub">14-DAY OSCILLATOR MEDIAN</div></div>
        <div class="kpi-card glow-amber" style="flex: 1;"><div class="kpi-title">CAPITAL ANOMALIES</div><div class="kpi-val">{anomalies_count}</div><div class="kpi-sub">ENTITIES > 2.5X VOLUME MA</div></div>
        <div class="kpi-card glow-purple" style="flex: 1;"><div class="kpi-title">ARBITRAGE VECTORS</div><div class="kpi-val">{strong_buys}</div><div class="kpi-sub">QUANTITATIVE BUY TRIGGERS</div></div>
    </div>
    """, unsafe_allow_html=True)
    
    df_3d = df_latest[df_latest['volume'] > 0].copy()
    df_3d['log_volume'] = np.log10(df_3d['volume'])
    
    fig_3d = px.scatter_3d(
        df_3d, x="rsi_14d", y="z_score_30d", z="log_volume", color="algorithmic_rating", hover_name="ticker",
        color_discrete_map={"Strong Buy": "#10b981", "Bullish Momentum": "#38bdf8", "Hold / Neutral": "#71717a", "Bearish Trend": "#f43f5e", "Overbought / Sell": "#7f1d1d"},
        height=650
    )
    fig_3d.update_traces(marker=dict(size=4, opacity=0.8, line=dict(width=0)))
    fig_3d.update_layout(
        scene=dict(
            xaxis=dict(title="MOMENTUM (RSI)", backgroundcolor="rgba(0,0,0,0)", gridcolor="#18181b"),
            yaxis=dict(title="REVERSION (Z-SCORE)", backgroundcolor="rgba(0,0,0,0)", gridcolor="#18181b"),
            zaxis=dict(title="LIQUIDITY (LOG VOL)", backgroundcolor="rgba(0,0,0,0)", gridcolor="#18181b"),
            bgcolor="rgba(0,0,0,0)"
        ),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(family="Courier New", color="#a1a1aa"))
    )
    st.plotly_chart(fig_3d, use_container_width=True)

# --- VIEW 2: SIGNAL MATRIX & RADAR DOSSIER ---
with tab2:
    sc1, sc2, sc3 = st.columns([2, 1, 1])
    search_query = sc1.text_input("COMMAND PALETTE / SEARCH:", placeholder="> ENGAGE TARGET (e.g. NVDA)_").upper()
    rating_filter = sc2.selectbox("SYSTEM SIGNAL:", ["ALL", "Strong Buy", "Bullish Momentum", "Hold / Neutral", "Bearish Trend", "Overbought / Sell"])
    anomaly_filter = sc3.checkbox("VOLUME ANOMALIES ONLY")
    
    f_df = df_latest.copy()
    if search_query: f_df = f_df[f_df['ticker'].str.contains(search_query)]
    if rating_filter != "ALL": f_df = f_df[f_df['algorithmic_rating'] == rating_filter]
    if anomaly_filter: f_df = f_df[f_df['volume_anomaly'] == True]
    
    col_screener, col_dossier = st.columns([2.5, 1.5])
    
    with col_screener:
        st.dataframe(
            f_df[['ticker', 'close_price', 'percent_change', 'z_score_30d', 'rsi_14d', 'algorithmic_rating']],
            use_container_width=True, hide_index=True, height=650,
            column_config={
                "ticker": "ENTITY", "close_price": st.column_config.NumberColumn("PRICE", format="$%.2f"),
                "percent_change": st.column_config.NumberColumn("24H DELTA", format="%.2f%%"),
                "z_score_30d": st.column_config.NumberColumn("Z-SCORE", format="%.2fσ"),
                "rsi_14d": st.column_config.NumberColumn("RSI", format="%.1f"),
                "algorithmic_rating": "SIGNAL"
            }
        )
    
    with col_dossier:
        st.markdown("<div class='brand-sub' style='color:#38bdf8;'>TICKER TELEMETRY DOSSIER</div>", unsafe_allow_html=True)
        target_ticker = st.selectbox("ENGAGE TARGET:", f_df['ticker'].tolist() if not f_df.empty else [], label_visibility="collapsed")
        
        if target_ticker:
            d_data = df_latest[df_latest['ticker'] == target_ticker].iloc[0]
            d_hist = df_history[df_history['ticker'] == target_ticker]
            
            # CSS Wrapper for Target Lock Animation
            st.markdown("<div class='dossier-lock'>", unsafe_allow_html=True)
            
            # Radar Data Normalization
            rad_mom = min(100, max(0, d_data['rsi_14d']))
            rad_vol = min(100, max(0, abs(d_data['percent_change']) * 10)) 
            rad_rev = min(100, max(0, abs(d_data['z_score_30d']) * 25)) 
            rad_liq = min(100, max(0, (d_data['volume'] / (df_latest['volume'].mean() + 1)) * 50))
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=[rad_mom, rad_rev, rad_vol, rad_liq, rad_mom],
                theta=['MOMENTUM', 'REVERSION', 'VOLATILITY', 'LIQUIDITY', 'MOMENTUM'],
                fill='toself', fillcolor='rgba(56, 189, 248, 0.3)', line=dict(color='#38bdf8', width=2)
            ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=False, range=[0, 100]), 
                    angularaxis=dict(color="#a1a1aa", tickfont=dict(family="Courier New", size=10)), 
                    bgcolor="rgba(0,0,0,0)"
                ),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=30, r=30, t=30, b=30), height=250, showlegend=False
            )

            st.markdown(f"""
            <div style="background: rgba(5,5,5,0.8); border: 1px solid #1e293b; padding: 20px; border-radius: 4px; border-top: 1px solid #38bdf8;">
                <div style="display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 1px dashed #1e293b; padding-bottom: 10px;">
                    <div style="font-family: 'Helvetica Neue', sans-serif; font-size: 2.5rem; font-weight: 900; color: #fff; letter-spacing: -1px;">{target_ticker}</div>
                    <div style="font-family: Courier New, monospace; font-size: 1.5rem; color: #38bdf8;">${d_data['close_price']:.2f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.plotly_chart(fig_radar, use_container_width=True, config={'displayModeBar': False})
            
            if len(d_hist) > 1:
                fig_line = go.Figure()
                fig_line.add_trace(go.Scatter(x=d_hist['timestamp'], y=d_hist['close_price'], mode='lines', line=dict(color='#10b981', width=2), fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.1)'))
                fig_line.update_layout(height=120, margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", xaxis=dict(visible=False), yaxis=dict(showgrid=False, tickfont=dict(color="#71717a", family="monospace")))
                st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})
                
            st.markdown("</div>", unsafe_allow_html=True) # End Animation Wrapper

# --- VIEW 3: GOD VIEW HEATMAP (NEW) ---
with tab3:
    st.markdown("<div class='brand-sub' style='color:#10b981; margin-bottom: 15px;'>GLOBAL MARKET BREADTH CLUSTERING</div>", unsafe_allow_html=True)
    
    # Create the Treemap
    df_tree = df_latest[df_latest['volume'] > 0].copy()
    df_tree['macro_grid'] = 'GLOBAL GRID' # Root node
    
    # Cap outliers so the colors don't wash out
    color_scale_max = 5.0
    df_tree['perf_capped'] = df_tree['percent_change'].clip(lower=-color_scale_max, upper=color_scale_max)
    
    fig_tree = px.treemap(
        df_tree, 
        path=['macro_grid', 'algorithmic_rating', 'ticker'], 
        values='volume',
        color='perf_capped',
        color_continuous_scale=['#f43f5e', '#000000', '#10b981'],
        color_continuous_midpoint=0,
        height=750
    )
    
    fig_tree.update_layout(
        margin=dict(t=10, l=10, r=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_colorbar=dict(title="24H Delta %", tickfont=dict(color="#a1a1aa", family="monospace"))
    )
    fig_tree.update_traces(
        marker=dict(line=dict(color='#1e293b', width=1)),
        textfont=dict(family="Helvetica Neue", color="#ffffff", size=14)
    )
    
    st.plotly_chart(fig_tree, use_container_width=True)

# --- VIEW 4: ENGINE ROOM ---
with tab4:
    st.markdown("""
    <div style="max-width: 900px; font-family: 'Helvetica Neue', sans-serif; background: rgba(5,5,5,0.8); border: 1px solid #1e293b; padding: 40px; border-radius: 4px; backdrop-filter: blur(10px);">
        <h2 style="color: #fff; font-weight: 900; letter-spacing: -0.02em; border-bottom: 1px solid #27272a; padding-bottom: 15px;">O.M.E.G.A. ARCHITECTURE PROTOCOL</h2>
        <p style="color: #a1a1aa; font-size: 1rem; line-height: 1.6; margin-top: 20px;">
            HOLO EARTH operates on a highly classified, zero-touch telemetry pipeline. The system is designed to entirely bypass manual operational drag, delivering sovereign-grade macroeconomic synthesis directly to command.
        </p>
        <div style="border-left: 3px solid #38bdf8; padding-left: 25px; margin-top: 30px; color: #d4d4d8; background: linear-gradient(90deg, rgba(56,189,248,0.05) 0%, rgba(0,0,0,0) 100%); padding-top: 10px; padding-bottom: 10px;">
            <p><b style="color: #38bdf8; font-family: Courier New, monospace;">[NODE 1] EXTRACTION:</b> CRON-scheduled Python microservices autonomously query global endpoints.</p>
            <p><b style="color: #10b981; font-family: Courier New, monospace;">[NODE 2] TRANSFORMATION:</b> Raw data arrays are sanitized. Rolling statistics (Z-Score, RSI, Volatility) are computed in-memory via multi-threaded Pandas matrices.</p>
            <p><b style="color: #f59e0b; font-family: Courier New, monospace;">[NODE 3] INGESTION:</b> Processed payloads are securely appended to the <code>telemetry_bronze</code> BigQuery warehouse via IAM Service Accounts.</p>
            <p><b style="color: #a855f7; font-family: Courier New, monospace;">[NODE 4] VISUALIZATION:</b> O.M.E.G.A. UI executes cached, read-only SQL queries to map 3D market topography and Treemap clustering with sub-second latency.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
