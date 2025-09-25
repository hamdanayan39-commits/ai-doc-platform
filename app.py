import os
import base64
import requests
import openai
from deep_translator import GoogleTranslator
from gtts import gTTS
import streamlit as st
from io import BytesIO
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import speech_recognition as sr

# ===============================
# 1️⃣ API KEYS
# ===============================
OPENAI_API_KEY = "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"
OCR_API_KEY = "K87313976288957"
GMAIL_CREDENTIALS_FILE = "credentials.json"  # Gmail OAuth credentials JSON

openai.api_key = OPENAI_API_KEY

# ===============================
# 2️⃣ Gmail API Setup
# ===============================
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    service = build('gmail', 'v1', credentials=creds)
    return service

def fetch_unread_emails():
    service = get_gmail_service()
    results = service.users().messages().list(userId='me', labelIds=['INBOX','UNREAD']).execute()
    messages = results.get('messages', [])
    email_texts = []

    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        payload = msg_data['payload']
        parts = payload.get('parts', [])
        body = ""
        if parts:
            for part in parts:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body += base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        email_texts.append(body)
    return email_texts

# ===============================
# 3️⃣ OCR & Summarization
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
# 4️⃣ Voice Command Input
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
# 5️⃣ Streamlit App UI
# ===============================
st.title("Hackathon Voice-Controlled Analyzer")

# File Upload Section
uploaded_file = st.file_uploader("Upload PDF/DOCX/Image", type=["pdf","docx","png","jpg","jpeg","tiff"])
selected_class = st.selectbox("Choose Class / Department", ["General","ClassA","ClassB"])
lang = st.selectbox("Select Language", ["en","hi","ml","ar","fr"])

# Process uploaded files
if uploaded_file is not None:
    extracted_text = extract_text_online(uploaded_file)
    summary = summarize_text_openai(extracted_text)
    translated = translate_text(summary, lang)
    st.subheader("Summary")
    st.write(translated)
    audio_base64 = text_to_speech(translated, lang)
    st.audio(base64.b64decode(audio_base64))

# Voice Command Section
if st.button("Use Voice Command"):
    command = voice_command_input()
    st.success(f"Command detected: {command}")
    
    if "upload" in command or "file" in command:
        st.info("Please upload a file above to process it.")
    
    if "email" in command or "gmail" in command:
        st.info("Fetching unread emails...")
        emails = fetch_unread_emails()
        if emails:
            for i, email_text in enumerate(emails):
                summary = summarize_text_openai(email_text)
                translated = translate_text(summary, lang)
                st.subheader(f"Email {i+1} Summary")
                st.write(translated)
                audio_base64 = text_to_speech(translated, lang)
                st.audio(base64.b64decode(audio_base64))
        else:
            st.success("No unread emails found.")

