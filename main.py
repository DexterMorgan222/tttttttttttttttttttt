import os
import requests
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
        <div class="message ai-message">Система yortAI готова. Подключена модель Gemini 2.5 Flash.</div>
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
                loadDiv.innerText = "Ошибка соединения с бэкендом сервером.";
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
    # Безопасно вытаскиваем секретный ключ из переменных среды Render
    selected_key = os.getenv("GEMINI_KEY")
    
    if not selected_key:
        return {"content": "Ошибка настройки: В панели управления Render не задана переменная GEMINI_KEY."}
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={selected_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": request.message}]
        }]
    }

    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        response_data = response.json()
        
        if 'error' in response_data:
            return {"content": f"Ошибка от Google API: {response_data['error'].get('message', 'Неизвестная ошибка')}"}
            
        return {"content": response_data['candidates'][0]['content']['parts'][0]['text']}
    except Exception as e:
        return {"content": f"Ошибка на стороне сервера: {str(e)}"}
