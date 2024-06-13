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

# 读入 system prompt
with open('./ai_host_prompt.txt', 'r', encoding='utf-8') as file:
    system_prompt = file.read()
with open('./ai_player_prompt.txt', 'r', encoding='utf-8') as file:
    system_prompt_player = file.read()

# Append a conversation into history, while show it in a new markdown block
def append_conversation(
    conversation: Conversation,
    history: list[Conversation],
    placeholder: DeltaGenerator | None=None,
    show: bool = True,
) -> None:
    history.append(conversation)
    if show:
        conversation.show(placeholder)

def main(top_p: float, temperature: float, prompt_text: str):

    # initialize
    global initialized
    if not initialized:
        st.session_state.player_history = []
        st.session_state.player_messages = [{"role": "system", "content": system_prompt_player}]
        player_history: list[Conversation] = st.session_state.player_history
        player_messages: list[dict] = st.session_state.player_messages
        
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
        messages.append(response_message)
        player_messages.append(response_message)
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
                        player_messages.append(
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
                        append_conversation(Conversation(
                                                Role.TOOL,
                                                "this is a picture tool",
                                                tool = "function_name",
                                                image=img
                                            ), st.session_state.player_history, markdown_placeholder, show=False)
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
            st.session_state.player_messages.append(
                {
                    "role": "assistant",
                    "content": response_message.content,
                }
            )
            
            append_conversation(Conversation(
                                    Role.ASSISTANT,
                                    response_message.content,
                                ), st.session_state.tool_history, markdown_placeholder)
            append_conversation(Conversation(
                                    Role.ASSISTANT,
                                    response_message.content,
                                ), st.session_state.player_history, markdown_placeholder, show=False)

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
        if 'player_history' not in st.session_state:
            initialized = False
            main(
                    prompt_text="1",
                    top_p=top_p,
                    temperature=temperature,
                )
            return
            # st.session_state.player_history = []
            # st.session_state.player_messages = [{"role": "system", "content": system_prompt_player}]
            # player_history: list[Conversation] = st.session_state.player_history
            # player_messages: list[dict] = st.session_state.player_messages
            
            # st.session_state.tool_history = []
            # st.session_state.messages = [{"role": "system", "content": system_prompt}]
            # history: list[Conversation] = st.session_state.tool_history
            # messages: list[dict] = st.session_state.messages

        player_history: list[Conversation] = st.session_state.player_history
        player_messages: list[dict] = st.session_state.player_messages

        tool_history: list[Conversation] = st.session_state.tool_history
        messages: list[dict] = st.session_state.messages

        # show 之前所有的对话内容
        for conversation in tool_history:
            conversation.show()
            
        # 创建一个对话框
        placeholder = st.container()
        message_placeholder = placeholder.chat_message(name="user", avatar="user")
        markdown_placeholder = message_placeholder.empty()

        # 调用 OpenAI API
        # TODO: 加个 tool
        with markdown_placeholder:
            with st.spinner(f'Generating Text ...'):
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=player_messages,
                    temperature=temperature,
                    top_p=top_p
                )

        response_message = response.choices[0].message
        messages.append(response_message)
        player_messages.append(response_message)
        print(response_message)

        if response_message.content:
            response_message = response_message.content.strip()
            append_conversation(Conversation(Role.USER, response_message), player_history, show=False)
            append_conversation(Conversation(Role.USER, response_message), tool_history, markdown_placeholder)
            
            placeholder = st.container()
            message_placeholder = placeholder.chat_message(name="assistant", avatar="assistant")
            markdown_placeholder = message_placeholder.empty()

            player_messages.append({"role": "user", "content": response_message})
            messages.append({"role": "user", "content": response_message})

            print(messages)
            with markdown_placeholder:
                with st.spinner(f'Generating Text ...'):
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        temperature=temperature,
                        top_p=top_p
                    )

            response_message = response.choices[0].message
            messages.append(response_message)
            player_messages.append(response_message)
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
                            player_messages.append(
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
                            append_conversation(Conversation(
                                                    Role.TOOL,
                                                    "this is a picture tool",
                                                    tool = function_name,
                                                    image=img
                                                ), st.session_state.player_history, markdown_placeholder, show=False)

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
                st.session_state.player_messages.append(
                    {
                        "role": "assistant",
                        "content": response_message.content,
                    }
                )
                append_conversation(Conversation(
                                        Role.ASSISTANT,
                                        response_message.content,
                                    ), st.session_state.tool_history, markdown_placeholder)
                append_conversation(Conversation(
                                        Role.ASSISTANT,
                                        response_message.content,
                                    ), st.session_state.player_history, markdown_placeholder, show=False)