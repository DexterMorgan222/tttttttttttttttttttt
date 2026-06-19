import random
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
        header { display: none !important; }
        body { background-color: #121212; color: #e0e0e0; display: flex; flex-direction: column; height: 100vh; }
        #chatContainer { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; }
        .message { max-width: 75%; padding: 12px 16px; border-radius: 18px; font-size: 15px; line-height: 1.5; word-wrap: break-word; }
        .user-message { background-color: #2b2b2b; color: #ffffff; align-self: flex-end; border-bottom-right-radius: 4px; }
        .ai-message { background-color: #1f1f1f; color: #e0e0e0; align-self: flex-start; border-bottom-left-radius: 4px; border: 1px solid #2d2d2d; }
        .message-image { max-width: 100%; max-height: 200px; border-radius: 8px; margin-bottom: 8px; display: block; }
        .bottom-panel { background-color: #1a1a1a; padding: 15px; border-top: 1px solid #2d2d2d; display: flex; flex-direction: column; gap: 10px; }
        .input-container { display: flex; align-items: center; background-color: #252525; border-radius: 25px; padding: 5px 15px; border: 1px solid #333; }
        #clipBtn { background: none; border: none; font-size: 22px; color: #888; cursor: pointer; margin-right: 10px; }
        #chatInput { flex: 1; background: none; border: none; color: #ffffff; font-size: 15px; outline: none; padding: 10px 0; }
        #sendBtn { background-color: #4A90E2; color: white; border: none; padding: 8px 20px; border-radius: 20px; font-weight: 600; cursor: pointer; }
        #previewContainer { display: none; align-self: flex-start; position: relative; margin-left: 15px; margin-bottom: 5px; }
        #imagePreview { max-width: 90px; max-height: 90px; border-radius: 8px; border: 2px solid #4A90E2; }
        #cancelImgBtn { position: absolute; top: -6px; right: -6px; background-color: #ff3b30; color: white; border: none; border-radius: 50%; width: 20px; height: 20px; cursor: pointer; font-size: 11px; }
    </style>
</head>
<body>
    <div id="chatContainer">
        <div class="message ai-message">Система yortAI готова. Введите ваш запрос или прикрепите изображение.</div>
    </div>
    <div class="bottom-panel">
        <div id="previewContainer"><img id="imagePreview" src="" alt="Превью"><button id="cancelImgBtn" type="button">X</button></div>
        <div class="input-container">
            <input type="file" id="fileElement" accept="image/*" style="display: none;">
            <button id="clipBtn" type="button">📎</button>
            <input type="text" id="chatInput" placeholder="Спроси ИИ..." autocomplete="off">
            <button id="sendBtn" type="button">ИДТИ</button>
        </div>
    </div>
    <script>
        let imgB64 = null, imgMime = "image/jpeg", imgSrc = null;
        const fileEl = document.getElementById('fileElement'), clipBt = document.getElementById('clipBtn');
        const prevCont = document.getElementById('previewContainer'), imgPrev = document.getElementById('imagePreview');
        const cancBt = document.getElementById('cancelImgBtn'), chatIn = document.getElementById('chatInput');
        const sendBt = document.getElementById('sendBtn'), chatCont = document.getElementById('chatContainer');

        clipBt.onclick = () => fileEl.click();
        fileEl.onchange = function() {
            const file = this.files[0];
            if (file) {
                imgMime = file.type;
                const r = new FileReader();
                r.onload = (e) => {
                    imgSrc = e.target.result;
                    imgB64 = e.target.result.split(',')[1];
                    imgPrev.src = e.target.result;
                    prevCont.style.display = 'block';
                };
                r.readAsDataURL(file);
            }
        };
        cancBt.onclick = () => { imgB64 = null; imgSrc = null; fileEl.value = ''; prevCont.style.display = 'none'; };

        async function send() {
            const text = chatIn.value.trim();
            if (!text && !imgB64) return;
            append('user', text, imgSrc);
            
            // Передаем правильные имена полей для Pydantic-модели бэкенда
            const p = { message: text, image: imgB64, mimeType: imgMime };
            
            chatIn.value = ''; imgB64 = null; imgSrc = null; fileEl.value = ''; prevCont.style.display = 'none';
            const loadDiv = document.createElement('div');
            loadDiv.className = 'message ai-message'; loadDiv.innerText = 'yortAI думает...';
            chatCont.appendChild(loadDiv); chatCont.scrollTop = chatCont.scrollHeight;
            try {
                const res = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(p) });
                const d = await res.json();
                loadDiv.innerText = d.content;
            } catch {
                loadDiv.innerText = "Ошибка бэкенда.";
            }
            chatCont.scrollTop = chatCont.scrollHeight;
        }
        sendBt.onclick = send;
        chatIn.onkeydown = (e) => { if (e.key === 'Enter') send(); };

        function append(sender, t, src) {
            const d = document.createElement('div');
            d.className = 'message ' + (sender === 'user' ? 'user-message' : 'ai-message');
            if (src) { const i = document.createElement('img'); i.src = src; i.className = 'message-image'; d.appendChild(i); }
            if (t) { const s = document.createElement('span'); s.innerText = t; d.appendChild(s); }
            chatCont.appendChild(d); chatCont.scrollTop = chatCont.scrollHeight;
        }
    </script>
</body>
</html>"""

class ChatRequest(BaseModel):
    message: str
    image: Optional[str] = None
    mimeType: Optional[str] = "image/jpeg"

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return HTML_CONTENT

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    api_keys = [
        "AIzaSyA9G33A-dn6Drlaamh98hqENNBbTlvIiMk",
        "AIzaSyBFDKq0ywvBsHycEuUZGfYDzDvvaIH1GOM"
    ]
    
    selected_key = random.choice(api_keys)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={selected_key}"
    
    parts = []
    if request.message:
        parts.append({"text": request.message})
    if request.image:
        parts.append({
            "inlineData": {
                "mimeType": request.mimeType if request.mimeType else "image/jpeg",
                "data": request.image
            }
        })
        
    if not parts:
        raise HTTPException(status_code=400, detail="Запрос пустой")

    payload = {
        "contents": [{
            "parts": parts
        }]
    }

    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        response_data = response.json()
        
        # Если Google вернул ошибку, выводим её текст прямо в чат для диагностики
        if 'error' in response_data:
            return {"content": f"Ошибка Google API: {response_data['error'].get('message', 'Неизвестная ошибка')}"}
            
        return {"content": response_data['candidates'][0]['content']['parts'][0]['text']}
    except Exception as e:
        print(f"Ошибка при запросе к Gemini API: {e}")
        return {"content": f"Не удалось обработать запрос бэкендом: {str(e)}"}
