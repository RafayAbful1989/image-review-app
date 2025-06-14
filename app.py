import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# -------------- Google Sheets Setup --------------
@st.cache_resource
def init_gsheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("Image Review Results").sheet1
    return sheet

sheet = init_gsheets()

# -------------- Load Data --------------
@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

df = load_data()

# -------------- Session State Setup --------------
if "index" not in st.session_state:
    st.session_state.index = 0
if "processed_ids" not in st.session_state:
    st.session_state.processed_ids = set()

# -------------- UI Setup --------------
st.title("📦 Image Review Tool")

# Filter by Location
location = st.selectbox("📍 Choose Location:", df["Location"].unique())
filtered_df = df[df["Location"] == location].reset_index(drop=True)

start = st.session_state.index
end = min(start + 10, len(filtered_df))
batch = filtered_df.iloc[start:end]

# -------------- Helper: Send to Sheet --------------
def send_to_sheet(row_id, location, decision):
    sheet.append_row([row_id, location, decision, datetime.now().isoformat()])

# -------------- Helper: Record --------------
def record(row, decision_text):
    if row["ID"] not in st.session_state.processed_ids:
        send_to_sheet(row["ID"], row["Location"], decision_text)
        st.session_state.processed_ids.add(row["ID"])
        st.experimental_rerun()

# -------------- Display Rows --------------
for _, row in batch.iterrows():
    st.subheader(f"🆔 ID: {row['ID']}")

    # Show images if available
    cols = st.columns(3)
    for i in range(1, 10):
        col = cols[(i - 1) % 3]
        url = row.get(f"Image_URL_{i}")
        if isinstance(url, str) and url.startswith("http"):
            with col:
                st.image(url, caption=f"Image_URL_{i}", use_container_width=True)

    # 7 Decision Buttons
    buttons = [
        "Okay",
        "Secondary packaging not opened",
        "Dark/Blurry/Random Image",
        "Brand box with Brand Seal not captured",
        "Box Description/MRP tag not captured",
        "Brand Box/Product wrapping not opened",
        "Main product and accessories image not captured or partially captured"
    ]

    st.markdown("### Your Decision:")
    btn_cols = st.columns(3)
    for i, label in enumerate(buttons):
        with btn_cols[i % 3]:
            if st.button(label, key=f"{row['ID']}_{label}"):
                record(row, label)

    st.markdown("---")

# -------------- Pagination --------------
if end < len(filtered_df):
    if st.button("➡️ Next 10"):
        st.session_state.index += 10
        st.rerun()
else:
    st.success("✅ You've reviewed all items in this location.")
