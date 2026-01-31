import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.inference.inference_engine import run_inference

st.set_page_config(page_title="Mindframe Playground", page_icon="🧠", layout="wide")

st.title("🧠 Mindframe AI Playground")
st.markdown("---")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask your AI anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Thinking..."):
            # This is where your Mindframe logic lives
            response = run_inference(prompt)
            if not response:
                response = "Inference logic not implemented yet. Update `src/inference/inference_engine.py` to get started!"
            
            message_placeholder.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    st.info("Edit your model settings in `config/model_config.yaml` to customize behavior.")
    
    if st.button("Clear History"):
        st.session_state.messages = []
        st.rerun()
