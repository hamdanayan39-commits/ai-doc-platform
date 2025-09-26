import base64
import streamlit as st
from io import BytesIO
import PyPDF2
import docx
import requests
import json
import pandas as pd
import plotly.express as px
from datetime import datetime
import openai

# ===============================
# 🔐 SECURE API KEY MANAGEMENT
# ===============================
def get_api_keys():
    """Secure API key handling"""
    try:
        # Streamlit secrets
        OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
        OCR_API_KEY = st.secrets.get("OCR_API_KEY", "K87313976288957")
        
        if OPENAI_API_KEY:
            st.sidebar.success("✅ API keys loaded securely")
            return OPENAI_API_KEY, OCR_API_KEY
        else:
            st.sidebar.warning("🔐 Using development mode - configure secrets for production")
            return ("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",
                    "K87313976288957")
    except Exception as e:
        st.error(f"Configuration error: {e}")
        return "", "K87313976288957"

OPENAI_API_KEY, OCR_API_KEY = get_api_keys()
openai.api_key = OPENAI_API_KEY  # Set OpenAI key

# ===============================
# 🔧 CORE FUNCTIONS
# ===============================
def test_api_connections():
    """Test API connections"""
    results = {}
    try:
        models = openai.Model.list()
        results['openai'] = True
    except:
        results['openai'] = False
    results['ocr'] = bool(OCR_API_KEY)
    return results

def extract_text_from_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip() if text.strip() else "No text could be extracted from PDF."
    except Exception as e:
        return f"PDF extraction failed: {str(e)}"

def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip() if text.strip() else "No text could be extracted from DOCX."
    except Exception as e:
        return f"DOCX extraction failed: {str(e)}"

def extract_text_from_image(file):
    try:
        r = requests.post(
            "https://api.ocr.space/parse/image",
            files={"file": file},
            data={"apikey": OCR_API_KEY, "language": "eng"},
            timeout=30
        )
        result = r.json()
        if r.status_code == 200 and "ParsedResults" in result:
            extracted_text = result["ParsedResults"][0]["ParsedText"]
            return extracted_text.strip() if extracted_text.strip() else "No text found in image."
        else:
            return "OCR API Error"
    except Exception as e:
        return f"OCR extraction failed: {str(e)}"

def extract_text_online(file):
    file_type = file.type
    if file_type == "application/pdf":
        return extract_text_from_pdf(file)
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(file)
    elif file_type.startswith('image/'):
        return extract_text_from_image(file)
    else:
        return f"Unsupported file type: {file_type}"

def analyze_document_with_ai(text):
    """AI analysis function using official OpenAI library"""
    if not OPENAI_API_KEY:
        return {"error": "OpenAI API key not configured"}
    
    try:
        prompt = f"""
        Analyze this KMRL document and return JSON with:
        - "main_category": [operations, maintenance, safety, finance, it]
        - "priority_level": [low, medium, high, critical]
        - "recommended_department": which KMRL department should handle this
        - "summary": brief 2-3 sentence summary
        
        Document: {text[:1500]}
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a KMRL document analysis assistant. Return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.1
        )
        
        content = response['choices'][0]['message']['content'].strip()
        # Clean JSON if wrapped in ```
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            content = content.split('```')[1].split('```')[0]
        
        return json.loads(content)
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

def text_to_speech(text, lang="en"):
    """Convert text to speech"""
    if not text.strip():
        return ""
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_fp = BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        return base64.b64encode(audio_fp.read()).decode("utf-8")
    except:
        return ""

# ===============================
# 🚀 STREAMLIT APP
# ===============================
st.set_page_config(page_title="KMRL AI Document Hub", page_icon="🚇", layout="wide")

if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = None
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

# KMRL UI Header
st.markdown("<h1 style='text-align:center; color:#FF6B35;'>🚇 KMRL AI Document Hub</h1>", unsafe_allow_html=True)

# Test APIs
api_status = test_api_connections()
st.sidebar.markdown("### 🔧 API Status")
st.sidebar.write(f"OpenAI API: {'✅ Active' if api_status['openai'] else '❌ Inactive'}")
st.sidebar.write(f"OCR API: {'✅ Active' if api_status['ocr'] else '❌ Inactive'}")

# Upload Tab
uploaded_file = st.file_uploader("Upload document (PDF, DOCX, Images)", type=["pdf","docx","png","jpg","jpeg","tiff"])
if uploaded_file:
    if st.button("Extract Text"):
        text = extract_text_online(uploaded_file)
        st.session_state.extracted_text = text
        st.text_area("Extracted Text Preview", text, height=200)

# AI Analysis Tab
if st.session_state.extracted_text:
    if st.button("Analyze Document with AI"):
        result = analyze_document_with_ai(st.session_state.extracted_text)
        st.session_state.analysis_result = result
        st.json(result)
        if "summary" in result:
            audio_data = text_to_speech(result["summary"])
            if audio_data:
                st.audio(base64.b64decode(audio_data), format="audio/mp3")

# Simple Dashboard Example
st.markdown("### 📊 KMRL Dashboard")
dept_data = pd.DataFrame({
    'Department': ["Operations","Maintenance","Safety","Finance","IT"],
    'Documents': [45,32,28,15,8]
})
fig = px.bar(dept_data, x='Department', y='Documents', color='Department')
st.plotly_chart(fig, use_container_width=True)
