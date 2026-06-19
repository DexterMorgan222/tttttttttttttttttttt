import os
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Разрешаем CORS, чтобы запросы летали и с компов, и со смартфонов
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Твой рабочий API-ключ Gemini
GEMINI_API_KEY = "AQ.Ab8RN6IHiR3VPDQ4hDYaGsUoD_cq32o398LweCXKUmzInJUipg"

def fetch_gemini_multimodal(prompt: str, image_base64: str = None, mime_type: str = "image/jpeg") -> str:
    # Используем прямую отправку через эндпоинт v1beta к модели gemini-2.5-flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    parts = []
    
    # Если прикреплена картинка
    if image_base64:
        parts.append({
            "inlineData": {
                "mimeType": mime_type,
                "data": image_base64
            }
        })
    
    # Текстовый запрос
    parts.append({"text": prompt if prompt else "Опиши это изображение."})
    
    payload = {
        "contents": [{
            "parts": parts
        }],
        "systemInstruction": {
            "parts": [
                {"text": "Ты — yortAI, продвинутый текстовый и визуальный ИИ-ассистент. Отвечай четко, коротко и по делу."}
            ]
        },
        "generationConfig": {
            "maxOutputTokens": 1500,
            "temperature": 0.7
        }
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            res_json = response.json()
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"[ОШИБКА GOOGLE]: {response.text}")
            return f"Ошибка Gemini API (Код {response.status_code})."
    except Exception as e:
        return f"Не удалось связаться с сервером Google: {str(e)}"

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    nocache_headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    try:
        data = await request.json()
        prompt = data.get("message", "").strip()
        image_data = data.get("image", None)
        mime_type = data.get("mimeType", "image/jpeg")
        
        if not prompt and not image_data:
            return JSONResponse({"type": "text", "content": "Вы отправили пустое сообщение."}, headers=nocache_headers)

        ai_response = fetch_gemini_multimodal(prompt, image_data, mime_type)
        return JSONResponse({"type": "text", "content": ai_response}, headers=nocache_headers)
    except Exception as e:
        return JSONResponse({"type": "text", "content": f"Внутренний сбой бэкенда: {str(e)}"}, headers=nocache_headers)

@app.get("/", response_class=HTMLResponse)
async def get_index():
    # Заголовки, которые заставят любой Safari подчиниться и сбросить кэш
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
            # Жестко вырезаем шапку и скрываем ее стилями прямо перед отправкой в браузер
            html_content = html_content.replace("<header>", "<header style='display:none !important;'>")
            return HTMLResponse(content=html_content, headers=headers)
    return HTMLResponse(content="Файл index.html не найден!", headers=headers)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)