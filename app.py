import streamlit as st
import pandas as pd
from datetime import datetime

# ----------------- PAGE CONFIG -----------------
st.set_page_config(page_title="🔒 Simple Fraud Detection Agent", page_icon="🔒", layout="wide")

# ----------------- THEME / STYLES -----------------
st.markdown("""
<style>
/* Background & fonts */
html, body, [class*="css"]  {
  font-family: "Inter", system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial;
}
.main {
  background: linear-gradient(135deg, #e8f0fe, #ffffff);
}

/* Cards */
.card {
  padding: 20px;
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
  border: 1px solid #eef2ff;
  margin-bottom: 20px;
}

/* Buttons */
.stButton > button {
  background: linear-gradient(90deg, #0d47a1, #1976d2);
  color: #fff;
  border-radius: 12px;
  padding: 10px 18px;
  font-weight: 700;
  border: none;
  transition: transform .15s ease;
}
.stButton > button:hover { transform: scale(1.03); }

/* Headers */
h1, h2, h3 { color: #0d47a1; }

/* Dataframe tweaks */
[data-testid="stDataFrame"] div  {
  font-size: 14px !important;
}
</style>
""", unsafe_allow_html=True)

# ----------------- HEADER -----------------
st.markdown("<h1 style='text-align:center;'>🔒 Simple Fraud Detection Agent</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:16px;'>Analyze transactions and flag potential risks using transparent rules. Great for demos & education.</p>", unsafe_allow_html=True)

# ----------------- SESSION: HISTORY -----------------
if "history" not in st.session_state:
    st.session_state.history = []

# ----------------- RULES ENGINE -----------------
RISKY_MCC = {"Crypto", "Gambling", "Betting", "Gift_Cards"}
HIGH_AMOUNT_NGN = 500_000
HIGH_AMOUNT_USD = 1_000

def ngn_to_usd(ngn: float, rate: float = 1600.0) -> float:
    """Very rough demo conversion so mixed currencies can be scored comparably."""
    return ngn / rate

def usd_to_ngn(usd: float, rate: float = 1600.0) -> float:
    return usd * rate

def score_transaction(
    amount: float,
    currency: str,
    country: str,
    usual_country: str,
    merchant_category: str,
    channel: str,           # Online / POS / ATM
    hour: int,              # 0-23
    card_present: bool,
    device_id: str = "",
) -> tuple[int, list[str]]:
    """
    Returns: (risk_score (0-100), reasons[])
    Rule-of-thumb scoring, transparent & explainable for demos.
    """
    score = 0
    reasons = []

    # Normalize amount to USD for comparison (demo only)
    amount_usd = amount if currency.upper() == "USD" else ngn_to_usd(amount)

    # High amount
    if currency.upper() == "NGN" and amount > HIGH_AMOUNT_NGN:
        score += 30; reasons.append(f"High amount in NGN (>₦{HIGH_AMOUNT_NGN:,})")
    if currency.upper() == "USD" and amount > HIGH_AMOUNT_USD:
        score += 30; reasons.append(f"High amount in USD (>${HIGH_AMOUNT_USD:,})")

    # Cross-border use
    if usual_country and country and usual_country.strip().upper() != country.strip().upper():
        score += 25; reasons.append(f"Different country than usual (Usual: {usual_country}, Current: {country})")

    # Nighttime usage
    if hour in [0,1,2,3,4,5]:
        score += 15; reasons.append("Nighttime transaction (00:00–05:59)")

    # Risky merchants
    if merchant_category in RISKY_MCC:
        score += 20; reasons.append(f"Risky merchant category: {merchant_category}")

    # Online + card not present + large amount
    if channel == "Online" and not card_present and amount_usd >= 300:
        score += 20; reasons.append("Card-not-present high amount online")

    # New/unknown device (demo): if device differs from last device we saw in this session
    last_device = st.session_state.get("last_device_id")
    if device_id and last_device and device_id != last_device:
        score += 10; reasons.append("New device used vs previous session device")
    if device_id:
        st.session_state["last_device_id"] = device_id

    # Cap score to 100
    score = min(score, 100)
    return score, reasons

def label_from_score(score: int) -> tuple[str, str]:
    if score < 40:
        return f"✅ Low Risk ({score}%)", "green"
    elif score < 70:
        return f"⚠️ Medium Risk ({score}%)", "orange"
    else:
        return f"❌ High Risk ({score}%)", "red"

# ----------------- MANUAL CHECK (FORM) -----------------
with st.container():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📝 Manual Transaction Check")

    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        amount = st.number_input("Amount", min_value=0.0, step=1.0, value=0.0)
        currency = st.selectbox("Currency", ["NGN", "USD"])
        channel = st.selectbox("Channel", ["Online", "POS", "ATM"])
    with c2:
        country = st.text_input("Transaction Country (e.g., NG, US, GB)", value="NG")
        usual_country = st.text_input("Usual Country (optional)", value="NG")
        hour = st.slider("Hour of day (0–23)", min_value=0, max_value=23, value=datetime.now().hour)
    with c3:
        merchant_category = st.selectbox("Merchant Category", ["Groceries", "Fuel", "Electronics", "Travel", "Crypto", "Gambling", "Betting", "Gift_Cards", "Other"])
        card_present = st.checkbox("Card Present (chip/swipe/tap)?", value=True)
        device_id = st.text_input("Device ID (optional)", value="")

    colA, colB = st.columns([1,1])
    with colA:
        run_manual = st.button("🔎 Analyze Transaction")
    with colB:
        if st.button("🗑 Clear History"):
            st.session_state.history = []
            st.success("History cleared.")

    if run_manual:
        score, reasons = score_transaction(
            amount, currency, country, usual_country, merchant_category, channel, hour, card_present, device_id
        )
        label, color = label_from_score(score)
        st.markdown(f"<h4 style='color:{color}; margin-top:8px;'>{label}</h4>", unsafe_allow_html=True)

        if reasons:
            with st.expander("Why was this flagged? (explanations)"):
                for r in reasons:
                    st.write("•", r)
        else:
            st.info("No specific risk conditions were triggered.")

        # Save to history
        st.session_state.history.append({
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Amount": amount,
            "Currency": currency,
            "Country": country,
            "Usual_Country": usual_country,
            "Merchant_Category": merchant_category,
            "Channel": channel,
            "Hour": hour,
            "Card_Present": card_present,
            "Device_ID": device_id,
            "Risk_Score": score,
            "Result": label
        })

    st.markdown("</div>", unsafe_allow_html=True)

# ----------------- HISTORY -----------------
if st.session_state.history:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📜 Analysis History")
    hist_df = pd.DataFrame(st.session_state.history)
    st.dataframe(hist_df, use_container_width=True)
    st.download_button("⬇️ Download History CSV", data=hist_df.to_csv(index=False), file_name="fraud_history.csv", mime="text/csv")
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------- BULK CHECK (CSV) -----------------
with st.container():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📂 Bulk Fraud Detection (CSV Upload)")

    st.caption("CSV columns expected: Transaction_ID, Amount, Currency (NGN/USD), Country, Usual_Country, Merchant_Category, Channel (Online/POS/ATM), Hour (0–23), Card_Present (True/False), Device_ID, Card_ID, Email")

    uploaded_file = st.file_uploader("Upload transactions CSV", type="csv")

    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        required_cols = {"Amount","Currency","Country","Usual_Country","Merchant_Category","Channel","Hour","Card_Present"}
        if not required_cols.issubset(set(df.columns)):
            st.error(f"Missing required columns. Please include at least: {', '.join(sorted(required_cols))}")
        else:
            scores, labels, reasons_list = [], [], []
            for _, row in df.iterrows():
                score, reasons = score_transaction(
                    amount=float(row["Amount"]),
                    currency=str(row["Currency"]),
                    country=str(row["Country"]),
                    usual_country=str(row.get("Usual_Country", "")),
                    merchant_category=str(row["Merchant_Category"]),
                    channel=str(row["Channel"]),
                    hour=int(row["Hour"]),
                    card_present=bool(row["Card_Present"]),
                    device_id=str(row.get("Device_ID", "")),
                )
                label, _ = label_from_score(score)
                scores.append(score)
                labels.append(label)
                reasons_list.append("; ".join(reasons))

            df["Risk_Score"] = scores
            df["Result"] = labels
            df["Reasons"] = reasons_list

            # Simple velocity flag (same Card_ID multiple times) if present
            if "Card_ID" in df.columns:
                counts = df["Card_ID"].value_counts()
                df["Velocity_Flag"] = df["Card_ID"].map(lambda cid: "High velocity" if counts.get(cid, 0) >= 2 else "")
            else:
                df["Velocity_Flag"] = ""

            def highlight(val):
                if isinstance(val, str):
                    if "High Risk" in val:   return "background-color:#ffcdd2; color:#b71c1c;"
                    if "Medium Risk" in val: return "background-color:#fff9c4; color:#e65100;"
                    if "Low Risk" in val:    return "background-color:#c8e6c9; color:#1b5e20;"
                return ""

            st.write("🔎 Results")
            st.dataframe(df.style.applymap(highlight, subset=["Result"]), use_container_width=True)
            st.download_button("⬇️ Download Results CSV", data=df.to_csv(index=False), file_name="fraud_results.csv", mime="text/csv")

    st.markdown("</div>", unsafe_allow_html=True)

# ----------------- DISCLAIMER -----------------
st.caption("This demo uses simple, transparent rules for educational purposes and is not a substitute for production-grade fraud systems.")
