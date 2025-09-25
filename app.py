import streamlit as st
from openai import OpenAI
from gtts import gTTS
from deep_translator import GoogleTranslator
import speech_recognition as sr
from io import BytesIO
import requests

# =======================
# 🔑 API KEYS
# =======================
OPENAI_API_KEY = "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"
OCR_API_KEY = "K87313976288957"

# ✅ Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# =======================
# 📑 OCR Function
# =======================
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

# =======================
# ✨ Summarization
# =======================
def summarize_text_openai(text):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes documents."},
            {"role": "user", "content": f"Summarize this document in simple language:\n{text}"}
        ],
        max_tokens=250
    )
    return response.choices[0].message.content.strip()

# =======================
# 🌍 Translation
# =======================
def translate_text(text, target_lang="en"):
    if target_lang == "en":
        return text
    return GoogleTranslator(source="auto", target=target_lang).translate(text)

# =======================
# 🔊 Text to Speech
# =======================
def text_to_speech(text, lang="en"):
    tts = gTTS(text=text, lang=lang)
    audio_fp = BytesIO()
    tts.write_to_fp(audio_fp)
    audio_fp.seek(0)
    return audio_fp

# =======================
# 🎙️ Speech to Text
# =======================
def speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎙️ Speak now...")
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "Could not understand audio"
    except sr.RequestError:
        return "Speech recognition service error"

# =======================
# 🎨 Streamlit UI
# =======================
st.set_page_config(page_title="AI Document Platform", layout="wide")
st.title("📄 AI Document Platform")
st.markdown("Upload, Summarize, Translate, and Convert Documents to Speech.")

# File Upload
uploaded_file = st.file_uploader("📤 Upload a document/image (TXT, PDF, DOCX, PNG, JPG)", type=["txt", "pdf", "docx", "png", "jpg", "jpeg"])

if uploaded_file:
    if uploaded_file.type in ["image/png", "image/jpeg"]:
        extracted_text = extract_text_online(uploaded_file)
    else:
        extracted_text = uploaded_file.read().decode("utf-8", errors="ignore")

    st.subheader("📑 Extracted Text")
    st.write(extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text)

    if st.button("✨ Summarize"):
        summary = summarize_text_openai(extracted_text)
        st.subheader("📝 Summary")
        st.write(summary)

        # Translate
        target_lang = st.selectbox("🌍 Translate Summary to:", ["en", "hi", "ml", "ar", "fr"])
        if st.button("🌐 Translate"):
            translated_summary = translate_text(summary, target_lang)
            st.write(translated_summary)

        # Text-to-Speech
        if st.button("🔊 Convert Summary to Speech"):
            audio_file = text_to_speech(summary, lang="en")
            st.audio(audio_file, format="audio/mp3")
