import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import json
import logging
import plotly.express as px

from app import cache, config

# --------------------------
# Logging
# --------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("main")

# --------------------------
# Page load timer
# --------------------------
start_time = time.time()

# --------------------------
# Load dataset
# --------------------------
@st.cache_data
def load_data(nrows=None):
    logger.info("Loading preprocessed CSV...")
    df = pd.read_csv(config.DATASET_PATH, nrows=nrows, encoding="utf-8")
    logger.info(f"Loaded {df.shape[0]} rows, {df.shape[1]} columns")

    # Convert month numbers to month names
    df["MonthName"] = pd.to_datetime(df["Month"], format="%m").dt.strftime("%B")

    # Force chronological order for months
    month_order = ["January","February","March","April","May","June",
                   "July","August","September","October","November","December"]
    df["MonthName"] = pd.Categorical(df["MonthName"], categories=month_order, ordered=True)

    return df

df = load_data()

# --------------------------
# Aggregations
# --------------------------
def avg_delay_per_airline(df):
    return df.groupby("UniqueCarrier")["ArrDelay"].mean().reset_index()

def flights_per_airport(df):
    return df.groupby("Origin")["FlightNum"].count().reset_index().rename(columns={"FlightNum": "NumFlights"})

# --------------------------
# Cache wrapper (Redis)
# --------------------------
def get_or_compute(key, compute_func, df):
    cached = cache.get_cache(key)
    if cached:
        logger.info(f"Returned cached data for key={key}")
        return pd.DataFrame(json.loads(cached)), True
    else:
        logger.info(f"Computing data for key={key} from CSV")
        start = time.time()
        result = compute_func(df)
        elapsed = time.time() - start
        cache.set_cache(key, result.to_json(orient="records"))
        logger.info(f"Computed and cached key={key} in {elapsed:.2f} seconds")
        return result, False

# --------------------------
# Streamlit UI
# --------------------------
st.set_page_config(page_title="Airline Dashboard", layout="wide")
st.title("✈️ Airline On-Time Performance Dashboard")
st.write("Interactive dashboard with Redis caching")

# --------------------------
# Sidebar Filters
# --------------------------
st.sidebar.header("🔎 Filters")
years = st.sidebar.multiselect(
    "Select Year(s)", sorted(df["Year"].dropna().unique()), default=sorted(df["Year"].dropna().unique())
)
months = st.sidebar.multiselect(
    "Select Month(s)", df["MonthName"].dropna().unique(), default=df["MonthName"].dropna().unique()
)
airlines = st.sidebar.multiselect(
    "Select Airline(s)", sorted(df["UniqueCarrier"].dropna().unique()), default=sorted(df["UniqueCarrier"].dropna().unique())
)
airports = st.sidebar.multiselect(
    "Select Origin Airport(s)", sorted(df["Origin"].dropna().unique()), default=sorted(df["Origin"].dropna().unique())
)

# Filter dataset
df_filtered = df.copy()
if years: df_filtered = df_filtered[df_filtered["Year"].isin(years)]
if months: df_filtered = df_filtered[df_filtered["MonthName"].isin(months)]
if airlines: df_filtered = df_filtered[df_filtered["UniqueCarrier"].isin(airlines)]
if airports: df_filtered = df_filtered[df_filtered["Origin"].isin(airports)]

# --------------------------
# Page load time display
# --------------------------
elapsed_total = time.time() - start_time
st.info(f"Page loaded in {elapsed_total:.2f} seconds")

# --------------------------
# KPIs
# --------------------------
st.subheader("📊 Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Flights", f"{len(df_filtered):,}")
col2.metric("Late Flights", f"{df_filtered['Late'].sum():,}")
col3.metric("Pct Delayed", f"{100*df_filtered['Late'].mean():.1f}%")

# --------------------------
# Tabs for Charts
# --------------------------
tab1, tab2 = st.tabs(["📈 Late Flights", "🏆 Airports"])

# --- Tab 1: Late flights per month
with tab1:
    late_by_month = df_filtered.groupby(["Year", "MonthName"])["Late"].sum().reset_index()
    fig1 = px.line(late_by_month, x="MonthName", y="Late", color="Year", markers=True,
                   title="Late Flights per Month")
    st.plotly_chart(fig1, use_container_width=True)
    st.download_button(
        "Download Filtered Data (CSV)", df_filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_flights.csv"
    )

# --- Tab 2: Top and least delayed airports
with tab2:
    late_by_airport = df_filtered.groupby("Origin")["Late"].sum().reset_index().sort_values("Late", ascending=False)
    col1, col2 = st.columns(2)
    with col1:
        fig2 = px.bar(late_by_airport.head(10), x="Origin", y="Late", title="Top 10 Airports with Most Delays")
        st.plotly_chart(fig2, use_container_width=True)
    with col2:
        fig3 = px.bar(late_by_airport.tail(10), x="Origin", y="Late", title="Top 10 Airports with Least Delays")
        st.plotly_chart(fig3, use_container_width=True)

# --------------------------
# Aggregations with Redis
# --------------------------
st.header("📊 Extra Analyses")

# Avg delay per airline
key_avg_delay = f"avg_delay_airline_{'_'.join(map(str, years))}"
result_delay, _ = get_or_compute(key_avg_delay, avg_delay_per_airline, df_filtered)
st.subheader("Average Delay per Airline")
selected_airline = st.selectbox("Filter Airline", result_delay["UniqueCarrier"].unique())
st.dataframe(result_delay[result_delay["UniqueCarrier"] == selected_airline])

# Flights per airport
key_flights = f"flights_per_airport_{'_'.join(map(str, years))}"
result_flights, _ = get_or_compute(key_flights, flights_per_airport, df_filtered)
st.subheader("Flights per Airport")
st.dataframe(result_flights.sort_values("NumFlights", ascending=False).head(20))


st.sidebar.header("⚠️ Cache Control")
if st.sidebar.button("Clear Redis Cache"):
    cache.clear_cache()
    st.sidebar.success("✅ Redis cache cleared!")
