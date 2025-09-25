import os
import base64
import openai
from deep_translator import GoogleTranslator
from gtts import gTTS
import streamlit as st
from io import BytesIO
import pdfplumber
import docx
from PIL import Image
import requests

# ===============================
# 1️⃣ API KEYS
# ===============================
OPENAI_API_KEY = "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"
OCR_API_KEY = "K87313976288957"

openai.api_key = OPENAI_API_KEY

# ===============================
# 2️⃣ OCR & File Text Extraction
# ===============================
def extract_text_file(file):
    if file.type == "application/pdf":
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(file)
        text = "\n".join([p.text for p in doc.paragraphs])
        return text
    elif file.type.startswith("image/"):
        # Use OCR.space API
        r = requests.post(
            "https://api.ocr.space/parse/image",
            files={"file": file},
            data={"apikey": OCR_API_KEY, "language": "eng"}
        )
        result = r.json()
        try:
            return result["ParsedResults"][0]["ParsedText"]
        except:
            return "OCR failed: No text extracted."
    else:
        return ""

# ===============================
# 3️⃣ Summarization + Translation + Speech
# ===============================
def summarize_text_openai(text):
    if not text.strip():
        return "No text extracted to summarize."
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Summarize this document in simple language:\n{text}",
        max_tokens=250
    )
    return response.choices[0].text.strip()

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
# 4️⃣ Streamlit App UI
# ===============================
st.title("AI Document Analyzer with OCR + NLP")

# File Upload Section
uploaded_file = st.file_uploader("Upload PDF/DOCX/Image", type=["pdf","docx","png","jpg","jpeg","tiff"])
lang = st.selectbox("Select Language", ["en","hi","ml","ar","fr"])

if uploaded_file is not None:
    extracted_text = extract_text_file(uploaded_file)
    summary = summarize_text_openai(extracted_text)
    translated = translate_text(summary, lang)
    st.subheader("Summary")
    st.write(translated)
    audio_base64 = text_to_speech(translated, lang)
    st.audio(base64.b64decode(audio_base64))
