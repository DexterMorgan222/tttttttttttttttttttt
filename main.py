import os
import random
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Весь код твоего интерфейса без верхней плашки yortAI PRO Mobile
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>yortAI Studio Dual</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        header {
            display: none !important;
        }

        body {
            background-color: #121212;
            color: #e0e0e0;
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        #chatContainer {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .message {
            max-width: 75%;
            padding: 12px 16px;
            border-radius: 18px;
            font-size: 15px;
            line-height: 1.5;
            word-wrap: break-word;
        }

        .user-message {
            background-color: #2b2b2b;
            color: #ffffff;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }

        .ai-message {
            background-color: #1f1f1f;
            color: #e0e0e0;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
            border: 1px solid #2d2d2d;
        }

        .message-image {
            max-width: 100%;
            max-height: 200px;
            border-radius: 8px;
            margin-bottom: 8px;
            display: block;
        }

        .bottom-panel {
            background-color: #1a1a1a;
            padding: 15px;
            border-top: 1px solid #2d2d2d;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .input-container {
            display: flex;
            align-items: center;
            background-color: #252525;
            border-radius: 25px;
            padding: 5px 15px;
            border: 1px solid #333;
        }

        #clipBtn {
            background: none;
            border: none;
            font-size: 22px;
            color: #888;
            cursor: pointer;
            margin-right: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        #chatInput {
            flex: 1;
            background: none;
            border: none;
            color: #ffffff;
            font-size: 15px;
            outline: none;
            padding: 10px 0;
        }

        #sendBtn {
            background-color: #4A90E2;
            color: white;
            border: none;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: 600;
            cursor: pointer;
        }

        #previewContainer {
            display: none;
            align-self: flex-start;
            position: relative;
            margin-left: 15px;
            margin-bottom: 5px;
        }

        #imagePreview {
            max-width: 90px;
            max-height: 90px;
            border-radius: 8px;
            border: 2px solid #4A90E2;
            display: block;
        }

        #cancelImgBtn {
            position: absolute;
            top: -6px;
            right: -6px;
            background-color: #ff3b30;
            color: white;
            border: none;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            cursor: pointer;
            font-size: 11px;
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: center;
        }
    </style>
</head>
<body>

    <div id="chatContainer">
        <div class="message ai-message">
            Система готова. Напишите текстовый вопрос или нажмите на скрепку 📎, чтобы прикрепить изображение для анализа.
        </div>
    </div>

    <div class="bottom-panel">
        <div id="previewContainer">
            <img id="imagePreview" src="" alt="Превью">
            <button id="cancelImgBtn" type="button">X</button>
        </div>

        <div class="input-container">
            <input type="file" id="fileElement" accept="image/*" style="display: none;">
            <button id="clipBtn" type="button">📎</button>
            <input type="text" id="chatInput" placeholder="Спроси ИИ или отправь картинку..." autocomplete="off">
            <button id="sendBtn" type="button">ИДТИ</button>
        </div>
    </div>

    <script>
        let attachedImageBase64 = null;
        let attachedMimeType = "image/jpeg";
        let attachedImageSrc = null;

        const fileElement = document.getElementById('fileElement');
        const clipBtn = document.getElementById('clipBtn');
        const previewContainer = document.getElementById('previewContainer');
        const imagePreview = document.getElementById('imagePreview');
        const cancelImgBtn = document.getElementById('cancelImgBtn');
        const chatInput = document.getElementById('chatInput');
        const sendBtn = document.getElementById('sendBtn');
        const chatContainer = document.getElementById('chatContainer');

        if (clipBtn && fileElement && sendBtn) {
            
            clipBtn.onclick = function() {
                fileElement.click();
            };

            fileElement.onchange = function() {
                const file = this.files[0];
                if (file) {
                    attachedMimeType = file.type;
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        attachedImageSrc = e.target.result;
                        attachedImageBase64 = e.target.result.split(',')[1];
                        
                        imagePreview.src = e.target.result;
                        previewContainer.style.display = 'block';
                        clipBtn.style.color = '#4A90E2';
                    };
                    reader.readAsDataURL(file);
                }
            };

            cancelImgBtn.onclick = function() {
                attachedImageBase64 = null;
                attachedImageSrc = null;
                fileElement.value = '';
                previewContainer.style.display = 'none';
                clipBtn.style.color = '#888';
            };

            async function sendMessage() {
                const text = chatInput.value.trim();
                if (!text && !attachedImageBase64) return;
                
                appendMessage('user', text, attachedImageSrc);
                
                const payload = {
                    message: text,
                    image: attachedImageBase64,
                    mimeType: attachedMimeType
                };
                
                chatInput.value = '';
                attachedImageBase64 = null;
                attachedImageSrc = null;
                fileElement.value = '';
                previewContainer.style.display = 'none';
                clipBtn.style.color = '#888';

                const aiLoadingDiv = document.createElement('div');
                aiLoadingDiv.classList.add('message', 'ai-message');
                aiLoadingDiv.innerText = 'yortAI думает...';
                chatContainer.appendChild(aiLoadingDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;

                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    
                    const data = await response.json();
                    aiLoadingDiv.innerText = data.content;
                    
                } catch (e) {
                    console.error("Ошибка запроса:", e);
                    aiLoadingDiv.innerText = "Не удалось получить ответ от yortAI. Backend недоступен.";
                }
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }

            sendBtn.onclick = sendMessage;
            chatInput.onkeydown = function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            };
        }

        function appendMessage(sender, text, imgSrc = null) {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message', sender === 'user' ? 'user-message' : 'ai-message');
            
            if (imgSrc) {
                const imgElement = document.createElement('img');
                imgElement.src = imgSrc;
                imgElement.classList.add('message-image');
                messageDiv.appendChild(imgElement);
            }
            
            if (text) {
                const textSpan = document.createElement('span');
                textSpan.innerText = text;
                messageDiv.appendChild(textSpan);
            }
            
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    </script>
</body>
</html>
"""

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
    
    # Переключили на стабильную стабильную версию 1.5-flash для серверов Render
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
        
        # Проверяем, вернул ли Google ошибку в ответе (например, проблемы с ключом или лимитами)
        if 'error' in response_data:
            print(f"Ошибка от Google API: {response_data['error']}")
            return {"content": f"Google API Error: {response_data['error'].get('message', 'Unknown error')}"}
            
        ai_text = response_data['candidates'][0]['content']['parts'][0]['text']
        return {"content": ai_text}
        
    except Exception as e:
        print(f"Ошибка бэкенда: {e}")
        return {"content": "Ошибка при генерации ответа. Пожалуйста, попробуйте еще раз через минуту."}
