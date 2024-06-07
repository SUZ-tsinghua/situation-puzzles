import streamlit as st
st.set_page_config(
    page_title="海龟汤 Demo",
    page_icon=":robot:",
    layout='centered',
    initial_sidebar_state='expanded',
)

import demo_tool_m

# Set the title of the demo
st.title("海龟汤 Demo")

with st.sidebar:
    top_p = st.slider(
        'top_p', 0.0, 1.0, 0.8, step=0.01
    )
    temperature = st.slider(
        'temperature', 0.0, 1.5, 0.95, step=0.01
    )

# 输入框
prompt_text = st.chat_input(
    '来玩一把海龟汤吧!',
    key='chat_input',
)

demo_tool_m.main(
            prompt_text=prompt_text,
            top_p=top_p,
            temperature=temperature,
        )