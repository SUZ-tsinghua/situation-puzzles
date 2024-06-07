import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from openai import OpenAI
from conversation import Conversation, Role

# 创建 OpenAI client
client = OpenAI(api_key='sk-proj-VUixgiopd34tsCI6w0UfT3BlbkFJZA2JN6Fn9ehr5wpw3bTE')

initialized = False

# 读入 system prompt
with open('./prompt.txt', 'r', encoding='utf-8') as file:
    system_prompt = file.read()

# Append a conversation into history, while show it in a new markdown block
def append_conversation(
    conversation: Conversation,
    history: list[Conversation],
    placeholder: DeltaGenerator | None=None,
) -> None:
    history.append(conversation)
    conversation.show(placeholder)

def main(top_p: float, temperature: float, prompt_text: str):

    # initialize
    global initialized
    if not initialized:
        st.session_state.tool_history = []
        st.session_state.messages = [{"role": "system", "content": system_prompt}]
        history: list[Conversation] = st.session_state.tool_history
        messages: list[dict] = st.session_state.messages

        # 创建一个对话框
        placeholder = st.container()
        message_placeholder = placeholder.chat_message(name="assistant", avatar="assistant")
        markdown_placeholder = message_placeholder.empty()

        # 调用 OpenAI API
        # TODO: 加个 tool
        with markdown_placeholder:
            with st.spinner(f'Generating Text ...'):
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=temperature,
                    top_p=top_p
                )

        response_message = response.choices[0].message

        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": response_message.content,
                            }
                        )
        append_conversation(Conversation(
                                Role.ASSISTANT,
                                response_message.content,
                            ), st.session_state.tool_history, markdown_placeholder)
        
        # TODO: 展示图片示例，后面需要删掉
        placeholder = st.container()
        message_placeholder = placeholder.chat_message(name="assistant", avatar="assistant")
        markdown_placeholder = message_placeholder.empty()

        with markdown_placeholder:
            with st.spinner(f'Generating Image ...'):
                response = client.images.generate(
                            model="dall-e-2",
                            prompt="a white siamese cat",
                            size="256x256",
                            quality="standard",
                            n=1,
                            )
            image_url = response.data[0].url
            st.image(image_url, use_column_width=True)
    
        initialized = True
    
    else:
        history: list[Conversation] = st.session_state.tool_history
        messages: list[dict] = st.session_state.messages

        # show 之前所有的对话内容
        # TODO: 需要把生成的图片也加入到 history 中，否则无法正常展示图片
        for conversation in history:
            conversation.show()

        if prompt_text:
            prompt_text = prompt_text.strip()
            append_conversation(Conversation(Role.USER, prompt_text), history)
            
            placeholder = st.container()
            message_placeholder = placeholder.chat_message(name="assistant", avatar="assistant")
            markdown_placeholder = message_placeholder.empty()

            messages.append({"role": "user", "content": prompt_text})

            print(messages)
            # TODO: 这里也需要加 tool
            with markdown_placeholder:
                with st.spinner(f'Generating Text ...'):
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        temperature=temperature,
                        top_p=top_p
                    )

            response_message = response.choices[0].message

            messages.append(
                                {
                                    "role": "assistant",
                                    "content": response_message.content,
                                }
                            )
            append_conversation(Conversation(
                                    Role.ASSISTANT,
                                    response_message.content,
                                ), history, markdown_placeholder)