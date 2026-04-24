import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "llama-3.3-70b-versatile"

def generate(messages):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.4,
        top_p=0.9,
        max_tokens=400,
    )
    return response.choices[0].message.content