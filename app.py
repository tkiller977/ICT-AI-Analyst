# ==========================================================
# ICT AI Analyst - Advanced Streamlit Dashboard
# ==========================================================
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="ICT AI Analyst", layout="wide")

# ----------------------------------------------------------
# FUNCTIONS
# ----------------------------------------------------------
def get_data(symbol, tf="1h", period="60d"):
    data = yf.download(symbol, interval=tf, period=period, progress=False)
    data.dropna(inplace=True)
    data.reset_index(inplace=True)
    data.rename(columns={"Datetime": "Time"}, inplace=True)
    return data

def find_swings(df, lookback=3):
    df['Swing_High'] = df['High'][(df['High'] > df['High'].shift(1)) & (df['High'] > df['High'].shift(-1))]
    df['Swing_Low']  = df['Low'][(df['Low'] < df['Low'].shift(1)) & (df['Low'] < df['Low'].shift(-1))]
    return df

def detect_structure(df):
    structure = []
    trend = None
    last_high = last_low = None
    
    for i in range(len(df)):
        close = df['Close'].iloc[i]
        if pd.notna(df['Swing_High'].iloc[i]):
            if last_high and close > last_high:
                structure.append(("BOS", df['Time'].iloc[i]))
                trend = "bullish"
            last_high = df['Swing_High'].iloc[i]
        if pd.notna(df['Swing_Low'].iloc[i]):
            if last_low and close < last_low:
                structure.append(("CHOCH", df['Time'].iloc[i]))
                trend = "bearish"
            last_low = df['Swing_Low'].iloc[i]
    return structure, trend

def find_order_blocks(df, lookback=3):
    ob_list = []
    for i in range(lookback, len(df)-1):
        # Bullish OB (last bearish candle before bullish move)
        if df['Close'].iloc[i] < df['Open'].iloc[i] and df['Close'].iloc[i+1] > df['Open'].iloc[i+1]:
            ob_list.append(("Bullish OB", df['Low'].iloc[i], df['High'].iloc[i]))
        # Bearish OB (last bullish candle before bearish move)
        if df['Close'].iloc[i] > df['Open'].iloc[i] and df['Close'].iloc[i+1] < df['Open'].iloc[i+1]:
            ob_list.append(("Bearish OB", df['Low'].iloc[i], df['High'].iloc[i]))
    return ob_list

def find_fvg(df):
    fvg_list = []
    for i in range(2, len(df)):
        # Bullish FVG
        if df['Low'].iloc[i] > df['Close'].iloc[i-2]:
            fvg_list.append(("Bullish FVG", df['Close'].iloc[i-2], df['Low'].iloc[i]))
        # Bearish FVG
        if df['High'].iloc[i] < df['Close'].iloc[i-2]:
            fvg_list.append(("Bearish FVG", df['High'].iloc[i], df['Close'].iloc[i-2]))
    return fvg_list

def generate_alerts(trend, ob_list, fvg_list):
    alerts = []
    if trend == "bullish":
        for ob in ob_list:
            if ob[0] == "Bullish OB":
                alerts.append(f"Buy Alert: Price may react at OB {ob[1]:.2f}-{ob[2]:.2f}")
        for fvg in fvg_list:
            if fvg[0] == "Bullish FVG":
                alerts.append(f"Buy Alert: Price may fill FVG {fvg[1]:.2f}-{fvg[2]:.2f}")
    elif trend == "bearish":
        for ob in ob_list:
            if ob[0] == "Bearish OB":
                alerts.append(f"Sell Alert: Price may react at OB {ob[1]:.2f}-{ob[2]:.2f}")
        for fvg in fvg_list:
            if fvg[0] == "Bearish FVG":
                alerts.append(f"Sell Alert: Price may fill FVG {fvg[1]:.2f}-{fvg[2]:.2f}")
    return alerts

def analyze(symbol):
    df = get_data(symbol)
    df = find_swings(df)
    structure, trend = detect_structure(df)
    ob_list = find_order_blocks(df)
    fvg_list = find_fvg(df)
    alerts = generate_alerts(trend, ob_list, fvg_list)

    # Plot chart
    fig, ax = plt.subplots(figsize=(14,6))
    ax.plot(df["Time"], df["Close"], label="Close", color="blue")
    ax.scatter(df["Time"], df["Swing_High"], color="red", label="Swing High", marker="^")
    ax.scatter(df["Time"], df["Swing_Low"], color="green", label="Swing Low", marker="v")
    
    # Plot OBs
    for ob in ob_list:
        ax.axhspan(ob[1], ob[2], alpha=0.3, color="green" if "Bullish" in ob[0] else "red", label=ob[0])
    # Plot FVGs
    for fvg in fvg_list:
        ax.axhspan(fvg[1], fvg[2], alpha=0.2, color="lime" if "Bullish" in fvg[0] else "pink", label=fvg[0])

    ax.set_title(f"{symbol} - Market Structure + OB/FVG")
    ax.legend(loc="upper left", bbox_to_anchor=(1,1))
    ax.grid(True)
    st.pyplot(fig)

    # Display trend
    if trend == "bullish":
        st.success("🟢 Trend Bias: Bullish — look for Buy setups near OB or FVG.")
    elif trend == "bearish":
        st.error("🔴 Trend Bias: Bearish — look for Sell setups after liquidity sweeps.")
    else:
        st.info("⚪ No clear structure — wait for confirmation.")

    # Display alerts
    if alerts:
        st.markdown("### ⚡ AI-Generated Alerts")
        for alert in alerts:
            st.info(alert)

# ----------------------------------------------------------
# STREAMLIT UI
# ----------------------------------------------------------
st.title("📈 ICT AI Analyst - Advanced Version")
st.write("An AI-powered stock market analyzer that reads ICT-style structure + OB + FVG for smarter signals.")

symbol = st.text_input("Enter Stock Symbol (e.g., AAPL, TSLA, MSFT):", "AAPL")

if st.button("Analyze"):
    analyze(symbol)