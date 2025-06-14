import streamlit as st
import pandas as pd
import gdown

# ---------- Load Data from Google Drive ----------
@st.cache_data
def load_data():
    file_id = "1ZbYSbmPOBGoCBFOh1rEIbNdzmKzqp9qX"  # Replace this with your actual file ID
    url = f"https://drive.google.com/uc?id={file_id}"
    output = "data.csv"
    gdown.download(url, output, quiet=False)
    return pd.read_csv(output)

df = load_data()

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

# ---------- CSS Styling ----------
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        height: 40px;
        font-weight: 600;
        border-radius: 8px;
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- Display Each Row ----------
for _, row in batch.iterrows():
    if row["ID"] in st.session_state.processed_ids:
        continue

    st.subheader(f"🆔 ID: {row['ID']}")
    image_cols = st.columns(3)
    img_index = 0

    for col_name in row.index:
        if col_name.startswith("Image_URL_") and pd.notna(row[col_name]):
            with image_cols[img_index % 3]:
                st.image(row[col_name], caption=col_name, use_container_width=True)
                img_index += 1

    st.markdown("#### Select a Decision:")

    # Button Rows
    row1 = st.columns(4)
    row2 = st.columns(3)

    def record(decision_text):
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
            record("Okay")
    with row1[1]:
        if st.button("📦 Secondary packaging not opened", key=f"{row['ID']}_pack"):
            record("Secondary packaging not opened")
    with row1[2]:
        if st.button("🌑 Dark/Blurry/Random Image", key=f"{row['ID']}_blurry"):
            record("Dark/Blurry/Random Image")
    with row1[3]:
        if st.button("🔒 Brand Seal not captured", key=f"{row['ID']}_seal"):
            record("Brand box with Brand Seal not captured")
    with row2[0]:
        if st.button("🏷️ MRP tag not captured", key=f"{row['ID']}_mrp"):
            record("Box Description/MRP tag not captured")
    with row2[1]:
        if st.button("📦❌ Wrapping not opened", key=f"{row['ID']}_wrap"):
            record("Brand Box/Product wrapping not opened")
    with row2[2]:
        if st.button("🎁📷 Main image not captured", key=f"{row['ID']}_main"):
            record("Main product and accessories image not captured or partially captured")

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
