import requests
import streamlit as st

# API Endpoint
API_URL = "http://127.0.0.1:7000/hello"


def upload_and_get_response(prompt, files):
    files_to_send = [("files", (file.name, file, file.type)) for file in files]

    response = requests.post(API_URL, data={"prompt": prompt}, files=files_to_send)

    if response.status_code == 200:
        return response.json().get("response", "No response received.")
    else:
        return f"❌ Error: {response.text}"


# UI Design
st.set_page_config(page_title="Chatbot API", page_icon="🤖", layout="wide")

# Custom CSS để đặt input chat xuống sát mép dưới và tăng khoảng cách trên
st.markdown(
    """
    <style>
        .chat-input-container {
            position: fixed;
            bottom: -40px;  /* Giảm xuống sát hơn */
            left: 10%;
            width: 80%;
            background: white;
            padding: 5px;  /* Giảm padding để nhỏ gọn hơn */
            box-shadow: 0px -2px 10px rgba(0, 0, 0, 0.1);
            border-top: 1px solid #ddd;
            margin-top: 100px;  /* Tăng khoảng cách từ trên */
        }
        
        .stButton button {
            margin-top: 10px;  /* Tăng khoảng cách giữa nút gửi và input */
        }
    </style>
""",
    unsafe_allow_html=True,
)

# Sidebar
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/a/a7/React-icon.svg", width=100
    )  # Thay thế bằng logo của bạn
    st.markdown("## 📂 Upload Files")
    files = st.file_uploader(
        "Upload PDF, CSV, or TXT files",
        accept_multiple_files=True,
        type=["pdf", "csv", "txt"],
    )

# Main Content
st.title("💬 AI Chatbot API")
st.markdown(
    "Interact with the chatbot by entering a prompt and optionally uploading files."
)

# Chat Container
chat_container = st.container()
response_container = st.container()

# Display Responses
with response_container:
    st.markdown("### 🤖 Chatbot Response:")
    chat_output = st.empty()

# Input Chat Box (cố định sát mép dưới và thêm khoảng cách từ trên)
st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
col1, col2 = st.columns([8, 2])
with col1:
    prompt = st.text_input(
        "Type your message here...",
        placeholder="Type your message here...",
        key="chat_input",
        label_visibility="collapsed",
    )
with col2:
    send_button = st.button("🚀 Send", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# Handle Response
if send_button and prompt:
    with st.spinner("🤖 Thinking..."):
        response = upload_and_get_response(prompt, files)
        chat_output.markdown(f"**Chatbot:** {response}")
