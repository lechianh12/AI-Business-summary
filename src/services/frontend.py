import sys
import time

import requests
import streamlit as st

sys.path.append("D:/Work/KV/project/AI-Business-summary")

from src.models.schema import RETAILER_OPTIONS, SCREEN_OPTIONS, TIME_PERIOD_OPTIONS

API_URL = "http://127.0.0.1:8000/api/response"

# UI Design
st.set_page_config(page_title="Business Summary AI", page_icon="📊", layout="wide")

# Sidebar
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/a/a7/React-icon.svg", width=100
    )
    st.markdown("## Select Retailer, Screen, and Time Period")
    retailer_id = st.selectbox(
        "Select Retailer ID", options=list(RETAILER_OPTIONS.keys())
    )
    screen = st.selectbox("Select Screen", options=list(SCREEN_OPTIONS.keys()))
    time_period = st.selectbox(
        "Select Time Period", options=list(TIME_PERIOD_OPTIONS.keys())
    )

# Main Content
st.title("💬 AI Business Summary")
st.markdown("Select the retailer, screen, and time period to get the business summary.")

# Button to submit the request
if st.button("🚀 Get Summary"):
    # Create a single expander for the entire response
    with st.expander("📊 Business Summary", expanded=True):
        # Create a placeholder inside the expander for streaming content
        response_container = st.container()

        with st.spinner("Generating..."):
            params = {
                "retailer_id": retailer_id,
                "screen": screen,
                "time_period": time_period,
            }

            # Create status placeholder
            status = st.empty()

            try:
                # Set a timeout to ensure we don't wait forever
                with requests.get(
                    API_URL, params=params, stream=True, timeout=60
                ) as response:
                    if response.status_code == 200:
                        # Initialize variables for tracking
                        full_response = ""
                        response_placeholder = response_container.empty()
                        start_time = time.time()
                        buffer = ""
                        chunk_size = 1  # Process smaller chunks for smoother updates
                        chunk_count = 0

                        # Stream the response
                        for chunk in response.iter_content(
                            chunk_size=chunk_size, decode_unicode=True
                        ):
                            if chunk:
                                full_response += chunk
                                # Update display with every received chunk
                                response_placeholder.markdown(full_response)

                        # Final update (optional, as it's updated in the loop)
                        # response_placeholder.markdown(full_response)

                    else:
                        status.error(f"Error: {response.text}")
            except requests.exceptions.RequestException as e:
                status.error(f"Connection error: {str(e)}")
