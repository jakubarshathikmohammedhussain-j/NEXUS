import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

# 1. Page Configuration (Luxury Minimalist Identity)
st.set_page_config(
    page_title="HOLO EARTH.",
    page_icon="⬛",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Minimalist Typography Setup
st.markdown("""
    <style>
        .mono-text { font-family: 'Courier New', Courier, monospace; color: #71717a; font-size: 0.8rem; letter-spacing: 0.05em; }
    </style>
""", unsafe_allow_html=True)

# 2. BigQuery Data Engine
@st.cache_data(ttl=600) # Caches data for 10 minutes to minimize BigQuery costs
def load_telemetry():
    # Streamlit natively manages nested secrets mapping
    creds_dict = dict(st.secrets["gcp_service_account"])
    credentials = service_account.Credentials.from_service_account_info(creds_dict)
    client = bigquery.Client(credentials=credentials, project=creds_dict["project_id"])
    
    query = f"""
      WITH RankedSignals AS (
        SELECT 
          ticker, close_price, percent_change, volume, rsi_14d, algorithmic_rating, timestamp,
          ROW_NUMBER() OVER(PARTITION BY ticker ORDER BY timestamp DESC) as rn
        FROM `{creds_dict["project_id"]}.telemetry_bronze.market_signals`
      )
      SELECT ticker, close_price, percent_change, volume, rsi_14d, algorithmic_rating, timestamp
      FROM RankedSignals
      WHERE rn = 1
      ORDER BY ABS(percent_change) DESC
      LIMIT 1000
    """
    df = client.query(query).to_dataframe()
    return df

try:
    df = load_telemetry()
except Exception as e:
    st.error(f"INTELLIGENCE ERROR: {e}")
    st.stop()

# 3. Header & Export Briefing Pack
col_logo, col_export = st.columns([3, 1])
with col_logo:
    st.title("HOLO EARTH.")
    st.markdown("<p class='mono-text'>PROPRIETARY CAPITAL DEPLOYMENT & MACRODYNAMIC HEURISTICS</p>", unsafe_allow_html=True)
with col_export:
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="EXPORT BRIEFING PACK [CSV]",
        data=csv,
        file_name='HOLO_EARTH_RICH_EXEC_SUMMARY.csv',
        mime='text/csv',
        use_container_width=True
    )

st.divider()

# 4. Quantitative Metric Tiles
if not df.empty:
    dispersion = df['percent_change'].max() - df['percent_change'].min()
    avg_rsi = df['rsi_14d'].mean()
    strong_buys = len(df[df['algorithmic_rating'] == 'Strong Buy'])
    anomalies = len(df[df['percent_change'].abs() > 5.0])
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("MARKET DISPERSION", f"{dispersion:.2f}%", "Max/Min Delta Spread")
    m2.metric("SYSTEMIC RSI MEDIAN", f"{avg_rsi:.1f}", "14-Day Baseline")
    m3.metric("STRONG BUY TRIGGERS", strong_buys, "Oversold Under <35 RSI")
    m4.metric("VOLATILITY ANOMALIES", anomalies, "Movements > 5.0%")

st.divider()

# 5. Baskets & Filters
THEMATIC_BASKETS = {
    "ALL ENTITIES": [],
    "DEFENSE PRIMES": ['LMT', 'RTX', 'GD', 'BA', 'NOC', 'LHX'],
    "LOGISTICS & FREIGHT": ['FDX', 'UPS', 'ZIM', 'MATX', 'XPO', 'CHRW'],
    "AI & COMPUTE": ['NVDA', 'MSFT', 'GOOGL', 'AMZN', 'TSM', 'ASML', 'AVGO'],
    "CRITICAL ENERGY": ['XOM', 'CVX', 'CCJ', 'ALB', 'FCX', 'VALE']
}

f1, f2, f3 = st.columns([2, 1, 1])
with f1:
    selected_basket = st.selectbox("THEMATIC BASKET", options=list(THEMATIC_BASKETS.keys()))
with f2:
    rating_filter = st.selectbox("ALGORITHMIC SIGNAL", options=["ALL", "Strong Buy", "Bullish Momentum", "Hold / Neutral", "Bearish Trend", "Overbought / Sell"])
with f3:
    search_query = st.text_input("SEARCH ENTITY...", "")

# Apply Filters
filtered_df = df.copy()
if selected_basket != "ALL ENTITIES":
    filtered_df = filtered_df[filtered_df['ticker'].isin(THEMATIC_BASKETS[selected_basket])]
if rating_filter != "ALL":
    filtered_df = filtered_df[filtered_df['algorithmic_rating'] == rating_filter]
if search_query:
    filtered_df = filtered_df[filtered_df['ticker'].str.contains(search_query.upper())]

# 6. Screener Matrix Data Table
st.markdown("<p class='mono-text'>LIVE TELEMETRY MATRIX</p>", unsafe_allow_html=True)
st.dataframe(
    filtered_df[['ticker', 'close_price', 'percent_change', 'rsi_14d', 'algorithmic_rating', 'volume']],
    use_container_width=True,
    hide_index=True,
    column_config={
        "ticker": st.column_config.TextColumn("ENTITY"),
        "close_price": st.column_config.NumberColumn("PRICE", format="$%.2f"),
        "percent_change": st.column_config.NumberColumn("24H DELTA (%)", format="%.2f%%"),
        "rsi_14d": st.column_config.NumberColumn("14D RSI", format="%.2f"),
        "algorithmic_rating": st.column_config.TextColumn("RATING"),
        "volume": st.column_config.NumberColumn("VOLUME")
    }
)
