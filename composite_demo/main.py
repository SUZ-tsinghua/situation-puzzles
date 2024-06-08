import streamlit as st
st.set_page_config(
    page_title="海龟汤 Demo",
    page_icon=":robot:",
    layout='centered',
    initial_sidebar_state='expanded',
)

import demo_tool_m
from enum import Enum

# Set the title of the demo
st.title("海龟汤 Demo")

class Mode(str, Enum):
    AI_AS_HOST, AI_VS_AI = 'AI as Host', 'AI vs AI'

with st.sidebar:
    top_p = st.slider(
        'top_p', 0.0, 1.0, 0.8, step=0.01
    )
    temperature = st.slider(
        'temperature', 0.0, 1.5, 0.95, step=0.01
    )

tab = st.radio(
    'Mode',
    [mode.value for mode in Mode],
    horizontal=True,
    label_visibility='hidden',
)

match tab:
    case Mode.AI_AS_HOST:
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
    case Mode.AI_VS_AI:
        with st.sidebar:
            cols = st.columns(1)
            generate_bttn = cols[0].button("生成一轮（仅限AI vs AI）", use_container_width=True)
        if generate_bttn:
            demo_tool_m.main(
                    prompt_text="1",
                    top_p=top_p,
                    temperature=temperature,
                )
