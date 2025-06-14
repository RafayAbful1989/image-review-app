import streamlit as st
import pandas as pd
import requests
import gdown
import os

# ---------- Download CSV from Google Drive ----------
@st.cache_data
def load_data_from_drive():
    file_id = "1ZbYSbmPOBGoCBFOh1rEIbNdzmKzqp9qX"  # Replace this with your actual file ID
    url = f"https://drive.google.com/uc?id={file_id}"
    output = "data.csv"
    gdown.download(url, output, quiet=False)
    return pd.read_csv(output)

df = load_data_from_drive()

# ---------- Session State ----------
if "index" not in st.session_state:
    st.session_state.index = 0
if "results" not in st.session_state:
    st.session_state.results = []
if "processed_ids" not in st.session_state:
    st.session_state.processed_ids = set()

# ---------- App Layout ----------
st.title("📦 Image Review Tool")

# Filter by Location
location = st.selectbox("📍 Choose a Location:", sorted(df["Location"].dropna().unique()))
filtered_df = df[df["Location"] == location].reset_index(drop=True)

# Pagination
start = st.session_state.index
end = min(start + 10, len(filtered_df))
batch = filtered_df.iloc[start:end]

# ---------- CSS for Button Styling ----------
st.markdown("""
    <style>
    .button-row button {
        width: 100% !important;
        padding: 8px;
        font-weight: 600;
        border-radius: 6px;
        margin: 2px 0;
    }
    .stButton>button {
        height: 40px;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- Helper: Check if URL is a valid image ----------
def is_valid_image(url):
    try:
        response = requests.head(url, timeout=2)
        return response.status_code == 200 and "image" in response.headers.get("Content-Type", "")
    except:
        return False

# ---------- Display Rows ----------
for _, row in batch.iterrows():
    if row["ID"] in st.session_state.processed_ids:
        continue

    st.subheader(f"🆔 ID: {row['ID']}")
    image_cols = st.columns(3)
    img_num = 1
    for i in range(1, 10):
        img_url = row.get(f"Image_URL_{i}")
        if isinstance(img_url, str) and is_valid_image(img_url):
            with image_cols[(img_num - 1) % 3]:
                st.image(img_url, caption=f"Image_URL_{i}", use_container_width=True)
                img_num += 1

    st.markdown("#### Select a Decision:")

    # Button layout (4 + 3)
    row1 = st.columns(4)
    row2 = st.columns(3)

    def record_decision(decision_text):
        if row["ID"] not in st.session_state.processed_ids:
            st.session_state.results.append({
                "ID": row["ID"],
                "Location": row["Location"],
                "Decision": decision_text
            })
            st.session_state.processed_ids.add(row["ID"])
            st.experimental_rerun()

    with row1[0]:
        if st.button("✅ Okay", key=f"{row['ID']}_okay"):
            record_decision("Okay")
    with row1[1]:
        if st.button("📦 Secondary packaging not opened", key=f"{row['ID']}_pack"):
            record_decision("Secondary packaging not opened")
    with row1[2]:
        if st.button("🌑 Dark/Blurry/Random Image", key=f"{row['ID']}_blurry"):
            record_decision("Dark/Blurry/Random Image")
    with row1[3]:
        if st.button("🔒 Brand box with Brand Seal not captured", key=f"{row['ID']}_seal"):
            record_decision("Brand box with Brand Seal not captured")

    with row2[0]:
        if st.button("🏷️ Box Description/MRP tag not captured", key=f"{row['ID']}_mrp"):
            record_decision("Box Description/MRP tag not captured")
    with row2[1]:
        if st.button("📦❌ Brand Box/Product Wrapping not opened", key=f"{row['ID']}_wrap"):
            record_decision("Brand Box/Product wrapping not opened")
    with row2[2]:
        if st.button("🎁📷 Main product and accessories image not captured or partially captured", key=f"{row['ID']}_main"):
            record_decision("Main product and accessories image not captured or partially captured")

# ---------- Navigation ----------
if end < len(filtered_df):
    if st.button("➡️ Next 10"):
        st.session_state.index += 10
        st.rerun()
else:
    st.info("✅ You've reached the end of the list.")

# ---------- Save & Download ----------
if st.button("💾 Download CSV"):
    result_df = pd.DataFrame(st.session_state.results)
    result_df.to_csv("results.csv", index=False)
    st.success("✅ Results saved!")
    with open("results.csv", "rb") as f:
        st.download_button("⬇️ Download Results", f, file_name="review_results.csv")
