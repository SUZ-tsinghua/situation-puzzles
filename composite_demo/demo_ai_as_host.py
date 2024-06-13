from io import BytesIO
import json
from pydoc import cli
import PIL
import requests
import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from openai import OpenAI
from tool_registry import get_image_from_dalle
from conversation import Conversation, Role

# 创建 OpenAI client
client = OpenAI(api_key='sk-proj-VUixgiopd34tsCI6w0UfT3BlbkFJZA2JN6Fn9ehr5wpw3bTE')

initialized = False

tools = [
    {
            "type": "function",
            "function": {
                "name": "get_image_from_dalle",
                "description": "在以下情况下，你可以调用这个工具来生成一张图片：1. 游戏的最开始，你需要一张图片来向用户展示汤面。2.当用户索要图片提示时，你需要生成一张能够提供足够提示的图片。首先，搜索你的记忆，找到玩家没猜到的\"核心设定\"的部分。随机抽取一个未猜到的\“核心设定\",随机给出其中的一个词，名词或者动词都可以。基于这个词生成一张图片 3.谜底揭晓时，你需要提供一张能以足够准确度展示谜底的图片。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "style": {
                            "type": "string",
                            "description": "图片整体风格",
                        },
                        "hue": {
                            "type": "string",
                            "description": "图片整体色调",
                        },
                        "image_content": {
                            "type": "string",
                            "description": "图片描述，要足够细致",
                        },
                    },
                    "required": ["style", "hue", "image_content"],
                },
            },
        }
]

# 读入 system prompt
with open('./ai_host_prompt.txt', 'r', encoding='utf-8') as file:
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
                    tools=[tools[0]],
                    tool_choice="auto",
                    temperature=temperature,
                    top_p=top_p
                )

        response_message = response.choices[0].message
        messages.append(response_message)
        print(response_message)
        tool_calls = response_message.tool_calls
        content = response_message.content

        if tool_calls:
            print("received a tool call request", tool_calls)
            

            with markdown_placeholder:
                # with st.spinner(f'Calling tools ...'):
                available_functions = {
                        "get_image_from_dalle": get_image_from_dalle
                    }
                print (f"toolcall is {tool_calls}")
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_to_call = available_functions[function_name]
                    function_args = json.loads(tool_call.function.arguments)
                    if function_name == "get_image_from_dalle":
                        with st.spinner(f'Generating Image ...'):
                            style = function_args.get("style", "")
                            hue = function_args.get("hue", "")
                            image_content = function_args.get("image_content", "")
                            prompt = "图片风格是:" + style + "图片色调是:" + hue + "图像内容是:" + image_content
                            function_response = function_to_call(client, prompt)
                            image_url = function_response.data[0].url
                        st.image(image_url, use_column_width=True)

                        print("display!!!")
                        response = requests.get(image_url)
                        img = PIL.Image.open(BytesIO(response.content))
                    
                        messages.append(
                                {
                                    "tool_call_id": tool_call.id,
                                    "role": "tool",
                                    "name": function_name,
                                    "content": "this is a picture tool",
                                }
                            )  
                        append_conversation(Conversation(
                                                Role.TOOL,
                                                "this is a picture tool",
                                                tool = "function_name",
                                                image=img
                                            ), st.session_state.tool_history, markdown_placeholder)
        if content:
            # 如果有图片内容的话，需要新建一个对话框
            if tool_calls:
                placeholder = st.container()
                message_placeholder = placeholder.chat_message(name="assistant", avatar="assistant")
                markdown_placeholder = message_placeholder.empty()

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

        # # TODO: 展示图片示例，后面需要删掉
        # placeholder = st.container()
        # message_placeholder = placeholder.chat_message(name="assistant", avatar="assistant")
        # markdown_placeholder = message_placeholder.empty()

        # with markdown_placeholder:
        #     with st.spinner(f'Generating Image ...'):
        #         response = client.images.generate(
        #                     model="dall-e-2",
        #                     prompt="a white siamese cat",
        #                     size="256x256",
        #                     quality="standard",
        #                     n=1,
        #                     )
        #     image_url = response.data[0].url
        #     st.image(image_url, use_column_width=True)
    
        initialized = True
        
    else:
        if 'tool_history' not in st.session_state:
            initialized = False
            main(
                    prompt_text=prompt_text,
                    top_p=top_p,
                    temperature=temperature,
                )
            return
            # st.session_state.tool_history = []
            # st.session_state.messages = [{"role": "system", "content": system_prompt}]
            # history: list[Conversation] = st.session_state.tool_history
            # messages: list[dict] = st.session_state.messages

        history: list[Conversation] = st.session_state.tool_history
        messages: list[dict] = st.session_state.messages

        # show 之前所有的对话内容
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
            with markdown_placeholder:
                with st.spinner(f'Generating Text ...'):
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        tools=[tools[0]],
                        tool_choice="auto",
                        temperature=temperature,
                        top_p=top_p
                    )

            response_message = response.choices[0].message
            messages.append(response_message)
            print(response_message)
            tool_calls = response_message.tool_calls
            content = response_message.content

            if tool_calls:
                print("received a tool call request", tool_calls)

                with markdown_placeholder:
                    # with st.spinner(f'Calling tools ...'):
                    available_functions = {
                            "get_image_from_dalle": get_image_from_dalle
                        }
                    print (f"toolcall is {tool_calls}")
                    for tool_call in tool_calls:
                        function_name = tool_call.function.name
                        function_to_call = available_functions[function_name]
                        function_args = json.loads(tool_call.function.arguments)
                        if function_name == "get_image_from_dalle":
                            with st.spinner(f'Generating Image ...'):
                                style = function_args.get("style", "")
                                hue = function_args.get("hue", "")
                                image_content = function_args.get("image_content", "")
                                prompt = "图片风格是:" + style + "图片色调是:" + hue + "图像内容是:" + image_content
                                function_response = function_to_call(client, prompt)
                                image_url = function_response.data[0].url
                                print("image_url:", image_url)
                            st.image(image_url, use_column_width=True)

                            print("display!!!")
                            response = requests.get(image_url)
                            img = PIL.Image.open(BytesIO(response.content))
                            messages.append(
                                    {
                                        "tool_call_id": tool_call.id,
                                        "role": "tool",
                                        "name": function_name,
                                        "content": "this is a picture tool",
                                    }
                                )  
                            append_conversation(Conversation(
                                                    Role.TOOL,
                                                    "this is a picture tool",
                                                    tool = function_name,
                                                    image=img
                                                ), st.session_state.tool_history, markdown_placeholder)

            if content:
                # 如果有图片内容的话，需要新建一个对话框
                if tool_calls:
                    placeholder = st.container()
                    message_placeholder = placeholder.chat_message(name="assistant", avatar="assistant")
                    markdown_placeholder = message_placeholder.empty()

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