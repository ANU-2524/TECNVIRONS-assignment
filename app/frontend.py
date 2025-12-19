import streamlit as st 
import websockets 
import asyncio

st.set_page_config(page_title="AI STREAMING CHAT" , layout="wide")
st.title("AI CHAT - Live Streaming")
user_input = st.text_input("Type your message here !")
st.markdown("#### Chat History...")

if "messages" not in st.session_state : 
    st.session_state.messages  = []

async def send_and_receive(message) :
    url = "ws://127.0.0.1:8000/ws" 
    async with websockets.connect(url) as websocket : 
        await websocket.send(message)
        
        response = ""
        async for chunk in websocket :
            response += chunk 
            yield response 
if st.button("Send") and user_input.strip() != "" :
    st.session_state.messages.append(("user" , user_input))
    placeholder = st.empty()
    final_msg = ""
    async def stream_call() :
        global final_msg 
        async for partial in send_and_receive(user_input) :
            final_msg = partial 
            placeholder.markdown(f"**AI : **{final_msg}")
    asyncio.run(stream_call())
    st.session_state.messages.append(("ai" , final_msg))

for role , msg in st.session_state.messages : 
    if role == "user" :
        st.markdown(f"**You : **{msg}")
    else :
        st.markdown(f"**AI : **{msg}")
    