import requests
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

HTML_CONTENT = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>yortAI Studio Dual</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: sans-serif; }
        body { background-color: #121212; color: #e0e0e0; display: flex; flex-direction: column; height: 100vh; }
        #chatContainer { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; }
        .message { max-width: 75%; padding: 12px 16px; border-radius: 18px; font-size: 15px; line-height: 1.5; word-wrap: break-word; }
        .user-message { background-color: #2b2b2b; color: #ffffff; align-self: flex-end; border-bottom-right-radius: 4px; }
        .ai-message { background-color: #1f1f1f; color: #e0e0e0; align-self: flex-start; border-bottom-left-radius: 4px; border: 1px solid #2d2d2d; }
        .bottom-panel { background-color: #1a1a1a; padding: 15px; border-top: 1px solid #2d2d2d; display: flex; flex-direction: column; gap: 10px; }
        .input-container { display: flex; align-items: center; background-color: #252525; border-radius: 25px; padding: 5px 15px; border: 1px solid #333; }
        #chatInput { flex: 1; background: none; border: none; color: #ffffff; font-size: 15px; outline: none; padding: 10px 0; }
        #sendBtn { background-color: #4A90E2; color: white; border: none; padding: 8px 20px; border-radius: 20px; font-weight: 600; cursor: pointer; }
    </style>
</head>
<body>
    <div id="chatContainer">
        <div class="message ai-message">Система yortAI готова. Подключен стабильный безлимитный ИИ-канал.</div>
    </div>
    <div class="bottom-panel">
        <div class="input-container">
            <input type="text" id="chatInput" placeholder="Спроси ИИ..." autocomplete="off">
            <button id="sendBtn" type="button">ИДТИ</button>
        </div>
    </div>
    <script>
        const chatIn = document.getElementById('chatInput');
        const sendBt = document.getElementById('sendBtn');
        const chatCont = document.getElementById('chatContainer');

        async function send() {
            const text = chatIn.value.trim();
            if (!text) return;
            append('user', text);
            
            chatIn.value = '';
            const loadDiv = document.createElement('div');
            loadDiv.className = 'message ai-message'; loadDiv.innerText = 'yortAI думает...';
            chatCont.appendChild(loadDiv); chatCont.scrollTop = chatCont.scrollHeight;
            
            try {
                const res = await fetch('/api/chat', { 
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' }, 
                    body: JSON.stringify({ message: text }) 
                });
                const d = await res.json();
                loadDiv.innerText = d.content;
            } catch {
                loadDiv.innerText = "Ошибка соединения с сервером.";
            }
            chatCont.scrollTop = chatCont.scrollHeight;
        }
        sendBt.onclick = send;
        chatIn.onkeydown = (e) => { if (e.key === 'Enter') send(); };

        function append(sender, t) {
            const d = document.createElement('div');
            d.className = 'message ' + (sender === 'user' ? 'user-message' : 'ai-message');
            const s = document.createElement('span'); s.innerText = t; d.appendChild(s);
            chatCont.appendChild(d); chatCont.scrollTop = chatCont.scrollHeight;
        }
    </script>
</body>
</html>"""

class ChatRequest(BaseModel):
    message: str

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return HTML_CONTENT

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    if not request.message:
        raise HTTPException(status_code=400, detail="Пустой запрос")

    init_url = "https://duckduckgo.com/duckchat/v1/status"
    headers = {"x-vqd-accept": "1", "User-Agent": "Mozilla/5.0"}
    
    try:
        init_res = requests.get(init_url, headers=headers)
        vqd_token = init_res.headers.get("x-vqd-token")
        
        if not vqd_token:
            return {"content": "Не удалось запустить ИИ-сессию. Попробуйте еще раз."}
            
        chat_url = "https://duckduckgo.com/duckchat/v1/chat"
        chat_headers = {
            "x-vqd-token": vqd_token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": request.message}]
        }
        
        response = requests.post(chat_url, json=payload, headers=chat_headers)
        
        lines = response.text.split("\n")
        full_text = ""
        for line in lines:
            if line.startswith("data:"):
                data_content = line[5:].strip()
                if data_content == "[DONE]":
                    break
                try:
                    js = json.loads(data_content)
                    if "message" in js:
                        full_text += js["message"]
                except:
                    continue
                    
        if not full_text:
            return {"content": "ИИ временно не ответил. Напишите запрос повторно."}
            
        return {"content": full_text.strip()}
        
    except Exception as e:
        return {"content": f"Ошибка шлюза: {str(e)}"}
