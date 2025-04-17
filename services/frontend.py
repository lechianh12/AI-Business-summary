import streamlit as st
import requests
import sys
import os
sys.path.append('/home/le-chi-anh/AI-Business-summary/scriptss/')

from scriptss.schema import RETAILER_OPTIONS, SCREEN_OPTIONS, TIME_PERIOD_OPTIONS


API_URL = "http://127.0.0.1:8000/api/response"

# UI Design
st.set_page_config(page_title="Business Summary AI", page_icon="📊", layout="wide")

# Sidebar
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/a/a7/React-icon.svg", width=100
    )
    st.markdown("## Select Retailer, Screen, and Time Period")
    retailer_id = st.selectbox("Select Retailer ID", options=list(RETAILER_OPTIONS.keys()))  
    screen = st.selectbox("Select Screen", options=list(SCREEN_OPTIONS.keys()))  
    time_period = st.selectbox("Select Time Period", options=list(TIME_PERIOD_OPTIONS.keys()))  

# Main Content
st.title("💬 AI Business Summary")
st.markdown("Select the retailer, screen, and time period to get the business summary.")

# Placeholder to update text incrementally
output_placeholder = st.empty()

# Button to submit the request
if st.button("🚀 Get Summary"):
    with st.spinner("🤖 Generating..."):
        params = {
            "retailer_id": retailer_id,
            "screen": SCREEN_OPTIONS,  
            "time_period": TIME_PERIOD_OPTIONS
        }
        response = requests.get(API_URL, params=params, stream=True)

        if response.status_code == 200:
            # Đọc phản hồi từ API từng phần
            output_text = ""
            for chunk in response.iter_content(chunk_size=10, decode_unicode=True):
                output_text += chunk
                output_placeholder.text(output_text)  # Cập nhật dần dần trong Streamlit

            # Tách thành 2 phần: Insights và Rủi ro & bất thường
            insights_start = output_text.find("<Insights>") + len("<Insights>")
            insights_end = output_text.find("</Insights>")
            risks_start = output_text.find("<Rủi ro & bất thường>") + len("<Rủi ro & bất thường>")
            risks_end = output_text.find("</Rủi ro & bất thường>")

            # Tạo expander cho phần Insights
            if insights_start != -1 and insights_end != -1:
                insights_text = output_text[insights_start:insights_end]
                with st.expander("🔍 Insights"):
                    st.markdown(insights_text)

            # Tạo expander cho phần Rủi ro & bất thường
            if risks_start != -1 and risks_end != -1:
                risks_text = output_text[risks_start:risks_end]
                with st.expander("⚠️ Rủi ro & Bất thường"):
                    st.markdown(risks_text)

        else:
            st.error(f"❌ Error: {response.text}")
