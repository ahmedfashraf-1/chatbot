import os

from fastapi import APIRouter
from schemas import ChatRequest
from services.ai import generate
from services.data import get_landmarks
from memory.memory import get_history, save

WHISPER_API_KEY = os.getenv("WHISPER_API_KEY")
VISION_API_KEY = os.getenv("VISION_API_KEY")
router = APIRouter()

SYSTEM_PROMPT = """
You are a professional and knowledgeable Egyptian tourism assistant for "Kemet App".

Identity:
- You represent Kemet App, a smart tourism assistant focused on Egypt.
- If asked "who are you", respond in a friendly way like:
  "I'm your tourism assistant from Kemet App, here to help you explore Egypt."

Main Behavior:
- You ONLY answer questions related to tourism in Egypt.
- This includes:
  (landmarks, history, ancient Egypt, temples, pyramids, museums, cities, travel tips).
- If the question is NOT related to Egypt tourism:
  politely refuse and guide the user back.

Example refusal:
"I'm here to help only with tourism in Egypt 🇪🇬. Ask me about places, history, or travel tips!"

Tone & Style:
- Be friendly but confident (like a professional tour guide).
- Speak naturally, not robotic.
- Give rich but clear answers.
- Use short paragraphs or bullet points when helpful.

Language:
- Detect user's language automatically.
- Reply in Arabic if the user writes Arabic.
- Reply in English if the user writes English.

Knowledge Style:
When describing a place, try to include:
1) What it is
2) Why it is important historically
3) Where it is located
4) Why people visit it
5) Practical tip (best time, advice, etc.)

Accuracy:
- Do NOT invent fake facts.
- If unsure, say:
  "I'm not completely sure, but..."

Extra Personality:
- Show pride in Egyptian civilization 🏺
- Make the user feel excited about visiting Egypt

Example:
User: "احكيلي عن الأهرامات"
Assistant:
"الأهرامات من أعظم إنجازات الحضارة المصرية القديمة..."

User: "what is Python?"
Assistant:
"I'm here to help only with tourism in Egypt 🇪🇬..."
- Format answers nicely using:
  - bullet points
  - short paragraphs
  - emojis when appropriate (light use)
"""

def build_context(data):
    if not data:
        return ""

    lines = []
    for item in data[:3]:
        name = item.get("name", "Unknown")
        kinds = item.get("kinds", "")
        lines.append(f"{name} is a {kinds}")
    return "\n".join(lines)

@router.post("/chat")
def chat(req: ChatRequest):
    user_id = req.user_id
    msg = req.message

    # 🧠 1. data
    data = get_landmarks(msg)
    context = build_context(data)

    # 🧠 2. messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    if context:
        messages.append({
            "role": "system",
            "content": f"Tourism data:\n{context}"
        })

    # history
    messages += get_history(user_id)

    # user
    messages.append({"role": "user", "content": msg})

    # 🤖 3. AI
    try:
        reply = generate(messages)
    except Exception as e:
        return {
            "status": "error",
            "message": "AI service failed"
        }
    # 💾 4. save memory
    save(user_id, "user", msg)
    save(user_id, "assistant", reply)

    return {
        "status": "success",
        "response": reply,
        "history": get_history(user_id)
    }
@router.get("/history/{user_id}")
def history(user_id: str):
    return {
        "history": get_history(user_id)
    }

@router.delete("/history/{user_id}")
def clear(user_id: str):
    from memory.memory import memory
    memory[user_id] = []
    return {"message": "cleared"}


from fastapi import UploadFile, File


@router.post("/voice")
async def voice_chat(user_id: str, file: UploadFile = File(...)):
    # 🧠 1. احفظ الملف مؤقتًا
    audio_path = f"temp_{user_id}.mp3"
    with open(audio_path, "wb") as f:
        f.write(await file.read())

    # 🎤 2. حول الصوت لنص
    import requests

    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {WHISPER_API_KEY}"
    }

    files = {
        "file": open(audio_path, "rb")
    }

    data = {
        "model": "whisper-large-v3-turbo"
    }

    res = requests.post(url, headers=headers, files=files, data=data)
    text = res.json()["text"]

    # 🤖 3. بقى ده عادي زي الشات
    data_landmarks = get_landmarks(text)
    context = build_context(data_landmarks)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if context:
        messages.append({
            "role": "system",
            "content": f"Tourism data:\n{context}"
        })

    messages += get_history(user_id)
    messages.append({"role": "user", "content": text})

    reply = generate(messages)

    save(user_id, "user", text)
    save(user_id, "assistant", reply)

    return {
        "transcript": text,
        "response": reply
    }

@router.post("/image")
async def image_chat(user_id: str, file: UploadFile = File(...)):

    # 🧠 1. احفظ الصورة
    image_path = f"temp_{user_id}.jpg"
    with open(image_path, "wb") as f:
        f.write(await file.read())

    # 🖼️ 2. ارفع الصورة لأي URL (مهم!)
    # مؤقتًا هنستخدم base64 بدل رفع

    import base64

    with open(image_path, "rb") as img:
        b64 = base64.b64encode(img.read()).decode()

    # 🤖 3. ابعت للـ AI
    import requests

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {VISION_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}"
                        }
                    }
                ]
            }
        ]
    }

    res = requests.post(url, headers=headers, json=payload)
    description = res.json()["choices"][0]["message"]["content"]

    # 🔥 4. ابني عليه رد سياحي
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += get_history(user_id)
    messages.append({
        "role": "user",
        "content": f"User shared an image: {description}"
    })

    reply = generate(messages)

    save(user_id, "user", f"[image]: {description}")
    save(user_id, "assistant", reply)

    return {
        "image_analysis": description,
        "response": reply
    }