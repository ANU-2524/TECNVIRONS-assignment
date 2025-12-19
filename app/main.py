from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from openai import OpenAI
import os
from dotenv import load_dotenv
from app.db import supabase
from datetime import datetime
import uuid

load_dotenv()

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    session_uuid = str(uuid.uuid4())

    # Insert new session record
    supabase.table("sessions").insert({
        "id": session_uuid,
        "user_id": "user_demo"
    }).execute()

    await websocket.accept()

    try:
        while True:
            
            # receive message
            message = await websocket.receive_text()
            supabase.table("session_events").insert({
                "session_id": session_uuid,
                "event_type": "user_message",
                "role": "user",
                "content": message
            }).execute()

            ai_response_full = ""  # store complete response

            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a very intelligent and brilliant assistant."},
                    {"role": "user", "content": message}
                ],
                stream=True
            )

            for chunks in stream:
                if chunks.choices[0].delta.content:
                    token = chunks.choices[0].delta.content
                    ai_response_full += token
                    await websocket.send_text(token)

            supabase.table("session_events").insert({
                "session_id": session_uuid,
                "event_type": "ai_final_message",
                "role": "assistant",
                "content": ai_response_full
            }).execute()

    except WebSocketDisconnect:

        supabase.table("sessions").update({
            "end_time": datetime.utcnow()
        }).eq("id", session_uuid).execute()
