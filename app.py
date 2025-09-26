import base64
import requests
import streamlit as st
from io import BytesIO
import PyPDF2
import docx
import json
import pandas as pd
from gtts import gTTS
import plotly.express as px

# ===============================
# 🔐 Secure API Key Handling
# ===============================
def get_api_keys():
    try:
        OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
        OCR_API_KEY = st.secrets.get("OCR_API_KEY", "K87313976288957")
        return OPENAI_API_KEY, OCR_API_KEY
    except Exception:
        return "", "K87313976288957"

OPENAI_API_KEY, OCR_API_KEY = get_api_keys()

# ===============================
# 🌐 Language Support
# ===============================
LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ml": "Malayalam",
    "ar": "Arabic",
    "ta": "Tamil",
    "fr": "French"
}

# ===============================
# 🏢 Departments
# ===============================
KMRL_DEPARTMENTS = {
    "operations": {"name": "🚇 Operations", "manager": "Mr. Rajesh Kumar", "email": "operations@kmrl.com"},
    "maintenance": {"name": "🔧 Maintenance", "manager": "Ms. Priya Sharma", "email": "maintenance@kmrl.com"},
    "safety": {"name": "🛡️ Safety", "manager": "Mr. Amit Patel", "email": "safety@kmrl.com"},
    "finance": {"name": "💰 Finance", "manager": "Ms. Anjali Nair", "email": "finance@kmrl.com"},
    "it": {"name": "💻 IT", "manager": "Mr. Sanjay Menon", "email": "it.support@kmrl.com"},
}

# ===============================
# 📄 Document Extractors
# ===============================
def extract_text_from_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    except:
        return "PDF extraction failed"

def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except:
        return "DOCX extraction failed"

def extract_text_from_image(file):
    try:
        r = requests.post(
            "https://api.ocr.space/parse/image",
            files={"file": file},
            data={"apikey": OCR_API_KEY, "language": "eng"},  # OCR best in English
            timeout=30
        )
        result = r.json()
        return result.get("ParsedResults", [{}])[0].get("ParsedText", "No text found")
    except:
        return "OCR extraction failed"

def extract_text_online(file):
    if file.type == "application/pdf":
        return extract_text_from_pdf(file)
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(file)
    elif file.type.startswith("image/"):
        return extract_text_from_image(file)
    else:
        return f"Unsupported file type: {file.type}"

# ===============================
# 🤖 AI Analysis
# ===============================
def analyze_document_with_ai(text, lang="en"):
    if not OPENAI_API_KEY:
        return {"error": "API key missing"}

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    prompt = f"""
Analyze this document and return JSON:
- main_category: operations/maintenance/safety/finance/it
- priority_level: low/medium/high/critical
- recommended_department: one of the above
- resolved: yes/no
- summary: 2-3 sentence summary in {LANGUAGES.get(lang,'English')}

Document: {text[:1500]}
"""
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a KMRL document assistant. Return only JSON."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 400,
        "temperature": 0.2
    }
    try:
        r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"].strip()
            if content.startswith("```"):
                content = content.split("```")[-2] if "```" in content else content
            return json.loads(content)
        return {"error": f"API error {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}

# ===============================
# 🔊 Text-to-Speech
# ===============================
def text_to_audio_base64(text, lang="en"):
    if not text.strip():
        return ""
    try:
        fp = BytesIO()
        gTTS(text=text, lang=lang, slow=False).write_to_fp(fp)
        fp.seek(0)
        return base64.b64encode(fp.read()).decode("utf-8")
    except:
        return ""

# ===============================
# 🚇 Streamlit App
# ===============================
st.set_page_config(page_title="KMRL AI Hub", page_icon="🚇", layout="wide")

st.markdown("<h1 style='text-align:center; color:#1e3c72;'>🚇 KMRL AI Document Hub</h1>", unsafe_allow_html=True)

# 🌐 Language selector in main UI
chosen_lang = st.selectbox(
    "🌐 Select output language",
    options=list(LANGUAGES.keys()),
    format_func=lambda x: LANGUAGES[x],
    index=0
)

tab1, tab2, tab3 = st.tabs(["📁 Upload", "🤖 AI Analysis", "📊 Dashboard"])

# ---------- TAB 1 ----------
with tab1:
    st.info("Upload PDF, DOCX, or Image for AI-powered analysis")
    file = st.file_uploader("Choose a file", type=["pdf","docx","png","jpg","jpeg","tiff"])
    if file and st.button("🔍 Extract Text"):
        text = extract_text_online(file)
        if text:
            st.session_state.extracted_text = text
            st.success("✅ Text extracted")
            st.text_area("Extracted Text", text[:1500] + "..." if len(text) > 1500 else text, height=200)

# ---------- TAB 2 ----------
with tab2:
    if st.session_state.get("extracted_text"):
        if st.button("🚀 Run AI Analysis"):
            result = analyze_document_with_ai(st.session_state.extracted_text, lang=chosen_lang)
            if "error" not in result:
                st.session_state.analysis = result
                st.success("✅ Analysis complete")
                col1, col2 = st.columns(2)
                with col1: st.json(result)
                with col2:
                    dept = result.get("recommended_department", "operations")
                    d = KMRL_DEPARTMENTS.get(dept, KMRL_DEPARTMENTS["operations"])
                    st.markdown(f"### {d['name']}")
                    st.write(f"👤 Manager: {d['manager']}")
                    st.write(f"📧 {d['email']}")
                    st.write(f"⚡ Priority: **{result.get('priority_level','medium').title()}**")
                    st.write(f"✅ Resolved: **{result.get('resolved','no').upper()}**")
                    audio_b64 = text_to_audio_base64(result.get("summary",""), lang=chosen_lang)
                    if audio_b64:
                        st.audio(base64.b64decode(audio_b64), format="audio/mp3")
            else:
                st.error(result["error"])
    else:
        st.info("Upload and extract text first")

# ---------- TAB 3 ----------
with tab3:
    st.markdown("### 📊 Department Performance")
    data = pd.DataFrame({
        "Department": [d["name"] for d in KMRL_DEPARTMENTS.values()],
        "Processed": [45,32,28,15,10],
        "Resolved": [40,30,25,12,8]
    })
    fig = px.bar(data, x="Department", y="Processed", color="Department", title="Documents Processed")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(data)
