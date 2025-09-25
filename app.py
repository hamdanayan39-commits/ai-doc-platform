import os
import base64
import requests
import openai
from deep_translator import GoogleTranslator
from gtts import gTTS
import streamlit as st
from io import BytesIO
import speech_recognition as sr

# ===============================
# 1️⃣ API KEYS
# ===============================
OPENAI_API_KEY = "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"
OCR_API_KEY = "K87313976288957"

openai.api_key = OPENAI_API_KEY

# ===============================
# 2️⃣ OCR & Summarization
# ===============================
def extract_text_online(file):
    r = requests.post(
        "https://api.ocr.space/parse/image",
        files={"file": file},
        data={"apikey": OCR_API_KEY, "language": "eng"}
    )
    result = r.json()
    try:
        return result["ParsedResults"][0]["ParsedText"]
    except:
        return ""

def summarize_text_openai(text):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes text."},
            {"role": "user", "content": f"Summarize this document in simple language:\n{text}"}
        ],
        max_tokens=250
    )
    return response.choices[0].message.content.strip()

def translate_text(text, target_lang="en"):
    if target_lang == "en":
        return text
    return GoogleTranslator(source="auto", target=target_lang).translate(text)

def text_to_speech(text, lang="en"):
    tts = gTTS(text=text, lang=lang)
    audio_fp = BytesIO()
    tts.write_to_fp(audio_fp)
    audio_fp.seek(0)
    audio_base64 = base64.b64encode(audio_fp.read()).decode("utf-8")
    return audio_base64

# ===============================
# 3️⃣ Voice Command Input
# ===============================
def voice_command_input(prompt="Say a command:"):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info(prompt)
        audio_data = recognizer.listen(source, timeout=5)
        try:
            command_text = recognizer.recognize_google(audio_data)
            return command_text.lower()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            st.error("Speech recognition service failed.")
            return ""

# ===============================
# 4️⃣ Streamlit App UI
# ===============================
st.title("📄 AI Voice-Controlled Document Analyzer")

# File Upload Section
uploaded_file = st.file_uploader("Upload PDF/DOCX/Image", type=["pdf","docx","png","jpg","jpeg","tiff"])
lang = st.selectbox("Select Language", ["en","hi","ml","ar","fr"])

# Process uploaded files
if uploaded_file is not None:
    extracted_text = extract_text_online(uploaded_file)
    if extracted_text.strip():
        summary = summarize_text_openai(extracted_text)
        translated = translate_text(summary, lang)
        st.subheader("Summary")
        st.write(translated)
        audio_base64 = text_to_speech(translated, lang)
        st.audio(base64.b64decode(audio_base64))
    else:
        st.warning("⚠️ No text could be extracted from the uploaded file.")

# Voice Command Section
if st.button("🎙️ Use Voice Command"):
    command = voice_command_input()
    if command:
        st.success(f"Command detected: {command}")
        if "upload" in command:
            st.info("Please upload a file above to process it.")
    else:
        st.warning("No voice command detected.")
