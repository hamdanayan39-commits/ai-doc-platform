import base64
import requests
import streamlit as st
from io import BytesIO
import PyPDF2
import docx
import json
import pandas as pd
import plotly.express as px

# ===============================
# 🔐 SECURE API KEY MANAGEMENT
# ===============================
def get_api_keys():
    try:
        OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
        OCR_API_KEY = st.secrets.get("OCR_API_KEY", "")
        if OPENAI_API_KEY:
            st.sidebar.success("✅ API keys loaded securely")
        else:
            st.sidebar.warning("🔐 OpenAI API key not configured. Set in Streamlit secrets.")
        return OPENAI_API_KEY, OCR_API_KEY
    except Exception as e:
        st.error(f"Configuration error: {e}")
        return "", ""

OPENAI_API_KEY, OCR_API_KEY = get_api_keys()

# ===============================
# 🎨 KMRL BRANDED UI
# ===============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; }
.kmrl-main-header { font-size: 3rem; font-weight: 800; background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 0.5rem; }
.kmrl-brand-header { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 2rem; border-radius: 15px; text-align: center; margin-bottom: 2rem; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
.kmrl-glass-card { background: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 2rem; margin: 1rem 0; box-shadow: 0 15px 35px rgba(0,0,0,0.1); border-left: 5px solid #FF6B35; }
.kmrl-department-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 15px; margin: 0.5rem; text-align: center; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
.kmrl-upload-zone { border: 3px dashed #FF6B35; border-radius: 20px; padding: 3rem 2rem; text-align: center; background: rgba(255, 107, 53, 0.05); transition: all 0.3s ease; margin: 2rem 0; }
.kmrl-upload-zone:hover { background: rgba(255, 107, 53, 0.1); border-color: #2a5298; }
.kmrl-metric-card { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 1.5rem; border-radius: 10px; text-align: center; margin: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ===============================
# 🏢 KMRL DEPARTMENTS DATABASE
# ===============================
KMRL_DEPARTMENTS = {
    "operations": {"name": "🚇 Operations Department","icon": "🚇","email": "operations@kmrl.com","manager": "Mr. Rajesh Kumar"},
    "maintenance": {"name": "🔧 Maintenance & Engineering","icon": "🔧","email": "maintenance@kmrl.com","manager": "Ms. Priya Sharma"},
    "safety": {"name": "🛡️ Safety & Compliance","icon": "🛡️","email": "safety@kmrl.com","manager": "Mr. Amit Patel"},
    "finance": {"name": "💰 Finance & Accounts","icon": "💰","email": "finance@kmrl.com","manager": "Ms. Anjali Nair"},
    "it": {"name": "💻 IT & Digital Solutions","icon": "💻","email": "it.support@kmrl.com","manager": "Mr. Sanjay Menon"}
}

# ===============================
# 🔧 CORE FUNCTIONS
# ===============================
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
            return result["ParsedResults"][0]["ParsedText"].strip()
        return "OCR API Error"
    except Exception as e:
        return f"OCR extraction failed: {str(e)}"

def extract_text_online(file):
    if file.type == "application/pdf":
        return extract_text_from_pdf(file)
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(file)
    elif file.type.startswith('image/'):
        return extract_text_from_image(file)
    else:
        return f"Unsupported file type: {file.type}"

def analyze_document_with_ai(text):
    if not OPENAI_API_KEY:
        return {"error": "OpenAI API key not configured"}
    try:
        headers = {"Content-Type": "application/json","Authorization": f"Bearer {OPENAI_API_KEY}"}
        prompt = f"""
        Analyze this document and return JSON:
        - "main_category": [operations, maintenance, safety, finance, it]
        - "priority_level": [low, medium, high, critical]
        - "recommended_department": [operations, maintenance, safety, finance, it]
        - "resolved": [yes/no]
        - "summary": 2-3 sentence summary
        Document: {text[:1500]}
        """
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a KMRL document assistant. Return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 300,
            "temperature": 0.1
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"].strip()
            if '```json' in content: content = content.split('```json')[1].split('```')[0]
            elif '```' in content: content = content.split('```')[1].split('```')[0]
            return json.loads(content)
        return {"error": f"OpenAI API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

def text_to_speech(text):
    if not text.strip(): return ""
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="en", slow=False)
        audio_fp = BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        return base64.b64encode(audio_fp.read()).decode("utf-8")
    except:
        return ""

# ===============================
# 🚀 STREAMLIT APP
# ===============================
st.set_page_config(page_title="KMRL AI Hub", page_icon="🚇", layout="wide")
if 'extracted_text' not in st.session_state: st.session_state.extracted_text = None
if 'analysis_result' not in st.session_state: st.session_state.analysis_result = None

st.markdown('<div class="kmrl-brand-header"><h1>🚇 KMRL AI Document Management</h1></div>', unsafe_allow_html=True)

# ---------- TABS ----------
tab1, tab2, tab3 = st.tabs(["📁 Upload", "🤖 AI Analysis", "📊 Dashboard"])

# ----- TAB 1: Upload -----
with tab1:
    uploaded_file = st.file_uploader(
        "Choose a document", 
        type=["pdf","docx","png","jpg","jpeg","tiff"]
    )
    if uploaded_file:
        if st.button("🔍 Extract Text Content", use_container_width=True):
            with st.spinner("Extracting text..."):
                extracted_text = extract_text_online(uploaded_file)
                if extracted_text and not any(err in extracted_text.lower() for err in ["error", "failed"]):
                    st.session_state.extracted_text = extracted_text
                    st.success("✅ Text extraction successful!")
                    with st.expander("📋 Preview Extracted Text", expanded=True):
                        st.text_area(
                            "", 
                            extracted_text[:800] + "..." if len(extracted_text) > 800 else extracted_text, 
                            height=200
                        )
                else:
                    st.error(f"❌ Extraction failed: {extracted_text}")

# ----- TAB 2: AI Analysis -----
with tab2:
    if st.session_state.extracted_text:
        if st.button("🚀 Start AI Analysis", use_container_width=True):
            with st.spinner("Analyzing document..."):
                result = analyze_document_with_ai(st.session_state.extracted_text)
                if "error" not in result:
                    st.session_state.analysis_result = result
                    st.success("✅ AI Analysis Complete!")
                    st.json(result)
                    summary = result.get("summary", "")
                    audio_data = text_to_speech(summary)
                    if audio_data:
                        st.audio(base64.b64decode(audio_data), format="audio/mp3")
                        st.download_button(
                            "📥 Download Audio Summary",
                            data=base64.b64decode(audio_data),
                            file_name="kmrl_summary.mp3",
                            mime="audio/mp3"
                        )
                else:
                    st.error(f"❌ {result['error']}")
    else:
        st.info("👆 Upload a document first.")

# ----- TAB 3: Dashboard -----
with tab3:
    st.markdown("### 📊 Department Metrics")
    dept_data = pd.DataFrame({
        'Department': [d['name'] for d in KMRL_DEPARTMENTS.values()],
        'Documents Processed': [45,32,28,15,8],
        'Avg Response Time': [1.2,2.5,3.1,4.2,1.8]
    })
    fig = px.bar(dept_data, x='Department', y='Documents Processed', color='Department')
    st.plotly_chart(fig, use_container_width=True)
