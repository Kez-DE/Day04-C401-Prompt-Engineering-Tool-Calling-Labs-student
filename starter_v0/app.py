import streamlit as st
import json
from pathlib import Path

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from chat import run_model_tool_loop, trim_history

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

st.set_page_config(page_title="Research Agent UI", page_icon="🤖", layout="centered")

st.title("🤖 Research Agent")
st.caption("A tool-calling AI agent that explores the web, social media, and internal policies.")

# Sidebar Settings
with st.sidebar:
    st.header("⚙️ Settings")
    provider_choice = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"], index=0)
    version_choice = st.text_input("Artifact Version", value="v3")
    history_window = st.slider("History Window", min_value=1, max_value=10, value=5)
    max_tool_rounds = st.slider("Max Tool Rounds", min_value=1, max_value=10, value=4)
    
    if st.button("Clear History"):
        st.session_state.messages = []
        st.rerun()

# Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

# Load core artifacts
system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
tool_declarations = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
openai_tools = to_openai_tools(tool_declarations)
provider = make_provider(provider_choice)

# Display chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.markdown(msg["content"])
            
            # Display tool results if they exist in the metadata
            if "tool_events" in msg and msg["tool_events"]:
                with st.expander("🛠️ Tool Executions"):
                    for event in msg["tool_events"]:
                        st.markdown(f"**Tool:** `{event['tool']}`")
                        st.json(event["args"])
                        st.markdown("**Result:**")
                        st.json(event["result"])

# Chat input
if prompt := st.chat_input("Ask something (e.g., 'Phân tích repo GitHub...' hoặc 'Lấy tin tức hôm nay')"):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        status_container = st.empty()
        status_container.info("🧠 Thinking and selecting tools...")
        
        # Prepare context
        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
        messages = [
            {"role": "system", "content": system_prompt},
            *trim_history(history, history_window),
            {"role": "user", "content": prompt}
        ]
        
        try:
            result = run_model_tool_loop(
                provider=provider,
                messages=messages,
                tools=openai_tools,
                model=getattr(provider, "default_model", None),
                max_tool_rounds=max_tool_rounds,
            )
            
            assistant_text = result.get("assistant_text", "")
            tool_events = result.get("tool_events", [])
            
            status_container.empty()
            
            # Display final text
            if assistant_text:
                st.markdown(assistant_text)
                
            # Display tools in UI right away
            if tool_events:
                with st.expander(f"🛠️ Ran {len(tool_events)} Tool Calls"):
                    for event in tool_events:
                        st.markdown(f"**Tool:** `{event['tool']}`")
                        st.json(event["args"])
                        st.markdown("**Result:**")
                        st.json(event["result"])
                        
            # Save to history
            st.session_state.messages.append({
                "role": "assistant", 
                "content": assistant_text,
                "tool_events": tool_events
            })
            
        except Exception as exc:
            error_msg = f"**Error:** {type(exc).__name__}: {str(exc)}"
            status_container.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
