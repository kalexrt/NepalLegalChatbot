import streamlit as st
from uuid import uuid4
import asyncio
import random
import ast
from datetime import datetime
from nepal_constitution_ai.config.db_session import get_session
from nepal_constitution_ai.utils.utils import is_valid_uuid
from nepal_constitution_ai.chat.controller import create_chat_session, user_input
from nepal_constitution_ai.chat.services import get_chat_history_service
from nepal_constitution_ai.user.services import user_create
from nepal_constitution_ai.chat.model import ChatMessageModel
from streamlit_local_storage import LocalStorage

async def create_new_chat_session(db, localS):
    new_user_id = uuid4()
    await user_create(user_id=new_user_id, db=db)
    new_chat_session = await create_chat_session(
    db=db, created_by=new_user_id
    )
    chat_session_id = new_chat_session.chat_session_id
    user_id = new_chat_session.created_by
    localS.setItem("chat_session", {"id": str(chat_session_id), "user_id":str(user_id)})
    
    return chat_session_id

def load_chat_session(db):
    localS = LocalStorage()

    try:
        chat_session = localS.getItem("chat_session")
        if chat_session is None:
            return asyncio.run(create_new_chat_session(db=db, localS=localS))

        chat_session_id = chat_session.get("id")
        user_id = chat_session.get("user_id")

        if not is_valid_uuid(chat_session_id) or not is_valid_uuid(user_id):
            return asyncio.run(create_new_chat_session(db=db, localS=localS))
        
        return chat_session_id
    
    except:
        localS.deleteAll()
        return asyncio.run(create_new_chat_session(db=db, localS=localS))



def load_chat_history(chat_session_id, db):

    chat_history = get_chat_history_service(session_id=chat_session_id, db=db, fetch_all=True)

    return chat_history

processing_messages = ["Thinking", "Cooking", "Going brrr", "Spinning the wheel", "Beep boop boop"]

with get_session() as db:
    chat_session_id = load_chat_session(db=db)
    chat_history = load_chat_history(chat_session_id=chat_session_id, db=db)
    # Show title and description.
    st.title("💬 Nepal Law Chatbot")
    st.write(
        "This is a conversational chatbot where you can ask "
        "questions regarding the Laws, Constitution, Rules and Regulations of Nepal."
    )
 
    if st.button("Reset Conversation"):
        localS = LocalStorage()
        localS.deleteAll()
        chat_history = []
    

    # Initialize chat history.
    st.session_state.messages = chat_history

    # Display the existing chat messages via `st.chat_message`.
    for message in st.session_state.messages:
        if message.message_by == "user":
            with st.chat_message("user"):
                message = message.content
                st.markdown(message, unsafe_allow_html=True)
        else:
            with st.chat_message("assistant"):
                message = message.content
                message = ast.literal_eval(message)
                if message.get("source","") == "" and message.get("link","") == "":
                    st.markdown(message.get("answer", ""))
                else:
                    try:
                        link_title = message.get('source', "").split("from", 1)[1].strip()
                    except:
                        link_title = "Click Here"

                    formatted_response = f"""
                        {message.get('answer', "")}

                        **Source:** {message.get('source', "")}

                        **Link:** [{link_title}]({message.get('link', "")})
                        """
                    st.markdown(formatted_response, unsafe_allow_html=True)

    # Create a chat input field to allow the user to enter a message. This will display
    # automatically at the bottom of the page.
    input_field = st.chat_input("Ask a question")
    if prompt := input_field:

        # Store and display the current prompt.
        new_message = ChatMessageModel(content=prompt, chat_session_id=chat_session_id, message_by="user", message_time=datetime.now())
        st.session_state.messages.append(new_message)
        with st.chat_message("user"):
            st.markdown(prompt)
        # Generate a response using the OpenAI API.
        random_processing_message = processing_messages[random.randint(0, len(processing_messages)-1)]
        with st.spinner(f'{random_processing_message}...'):
            output = user_input(db=db, user="", query=prompt, chat_session_id=chat_session_id)
        # Stream the response to the chat using `st.write_stream`, then store it in 
        # session state.
        with st.chat_message("assistant"):
            response = st.markdown(output, unsafe_allow_html=True)
        new_message = ChatMessageModel(content=output, chat_session_id=chat_session_id, message_by="llm", message_time=datetime.now())
        st.session_state.messages.append(new_message)
    
