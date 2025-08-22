import streamlit as st
import pandas as pd
import logging

# Setup logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("preprocess")

@st.cache_data
def load_data(nrows=5000000):
    logger.info(f"Loading CSV dataset (first {nrows} rows only)...")
    df = pd.read_csv(
        "./data/.airline.csv.shuffle",  # <- raw CSV
        nrows=nrows,
        encoding="latin1",
        low_memory=False,
        on_bad_lines="skip"
    )

    logger.info(f"CSV loaded: {df.shape[0]} rows, {df.shape[1]} columns")

    # Keep only relevant columns
    keep_cols = ["Year","Month","DayofMonth","ArrDelay","DepDelay","UniqueCarrier","Origin","Dest","FlightNum"]
    df = df[keep_cols].copy()

    # Fill missing values
    df["ArrDelay"] = df["ArrDelay"].fillna(0)
    df["DepDelay"] = df["DepDelay"].fillna(0)

    # Ensure correct types
    df["ArrDelay"] = df["ArrDelay"].astype(float)
    df["DepDelay"] = df["DepDelay"].astype(float)
    df["Year"] = df["Year"].astype(int)
    df["Month"] = df["Month"].astype(int)
    df["DayofMonth"] = df["DayofMonth"].astype(int)

    # Create Late column
    df["Late"] = df["ArrDelay"] > 15

    # Create Date column safely
    df["Date"] = pd.to_datetime(
        dict(year=df["Year"], month=df["Month"], day=df["DayofMonth"]),
        errors="coerce"
    )

    # Log preview
    logger.info(f"Columns: {list(df.columns)}")
    logger.info(f"First row: {df.iloc[0].to_dict()}")

    # Save preprocessed CSV
    preprocessed_path = "./data/.airline_preprocessed.csv"
    df.to_csv(preprocessed_path, index=False, encoding="utf-8")
    logger.info(f"Preprocessed CSV saved to {preprocessed_path}")

    return df

load_data()