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
# 🔐 API KEYS
# ===============================
def get_api_keys():
    try:
        OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
        OCR_API_KEY = st.secrets.get("OCR_API_KEY", "")
        return OPENAI_API_KEY, OCR_API_KEY
    except:
        return "", ""

OPENAI_API_KEY, OCR_API_KEY = get_api_keys()

# ===============================
# 🎨 UI STYLING
# ===============================
st.set_page_config(page_title="KMRL AI Hub", page_icon="🚇", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; }
.kmrl-brand-header { background: linear-gradient(135deg,#1e3c72 0%,#2a5298 100%); color:white; padding:2rem; border-radius:15px; text-align:center; margin-bottom:2rem; }
.kmrl-glass-card { background: rgba(255,255,255,0.95); border-radius:15px; padding:2rem; margin:1rem 0; box-shadow:0 15px 35px rgba(0,0,0,0.1); border-left:5px solid #FF6B35; }
.kmrl-department-card { background: linear-gradient(135deg,#667eea 0%,#764ba2 100%); color:white; padding:1.5rem; border-radius:15px; margin:0.5rem; text-align:center; box-shadow:0 5px 15px rgba(0,0,0,0.1); }
.kmrl-upload-zone { border: 3px dashed #FF6B35; border-radius: 20px; padding: 3rem 2rem; text-align: center; background: rgba(255,107,53,0.05); margin: 2rem 0; transition: all 0.3s ease; }
.kmrl-upload-zone:hover { background: rgba(255,107,53,0.1); border-color: #2a5298; }
.kmrl-metric-card { background: linear-gradient(135deg,#1e3c72 0%,#2a5298 100%); color:white; padding:1.5rem; border-radius:10px; text-align:center; margin:0.5rem; }
.kmrl-status { padding:0.5rem 1rem; border-radius:20px; color:white; font-weight:600; display:inline-block; }
.kmrl-status-resolved { background:#4CAF50; }
.kmrl-status-pending { background:#f44336; }
</style>
""", unsafe_allow_html=True)

# ===============================
# 🏢 Departments
# ===============================
KMRL_DEPARTMENTS = {
    "operations": {"name":"🚇 Operations","icon":"🚇","email":"operations@kmrl.com","manager":"Mr. Rajesh Kumar"},
    "maintenance": {"name":"🔧 Maintenance","icon":"🔧","email":"maintenance@kmrl.com","manager":"Ms. Priya Sharma"},
    "safety": {"name":"🛡️ Safety","icon":"🛡️","email":"safety@kmrl.com","manager":"Mr. Amit Patel"},
    "finance": {"name":"💰 Finance","icon":"💰","email":"finance@kmrl.com","manager":"Ms. Anjali Nair"},
    "it": {"name":"💻 IT & Digital","icon":"💻","email":"it.support@kmrl.com","manager":"Mr. Sanjay Menon"}
}

# ===============================
# 🔧 Functions
# ===============================
def extract_text_from_pdf(file):
    try:
        pdf = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
        return text.strip() or "No text found"
    except Exception as e:
        return f"PDF extraction failed: {e}"

def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        text = "\n".join([p.text for p in doc.paragraphs])
        return text.strip() or "No text found"
    except Exception as e:
        return f"DOCX extraction failed: {e}"

def extract_text_from_image(file):
    try:
        r = requests.post(
            "https://api.ocr.space/parse/image",
            files={"file": file},
            data={"apikey": OCR_API_KEY,"language":"eng"},
            timeout=30
        )
        result = r.json()
        if "ParsedResults" in result:
            return result["ParsedResults"][0]["ParsedText"].strip()
        return "OCR API Error"
    except Exception as e:
        return f"OCR failed: {e}"

def extract_text_online(file):
    if file.type=="application/pdf": return extract_text_from_pdf(file)
    if file.type=="application/vnd.openxmlformats-officedocument.wordprocessingml.document": return extract_text_from_docx(file)
    if file.type.startswith("image/"): return extract_text_from_image(file)
    return f"Unsupported file type: {file.type}"

def analyze_document_with_ai(text):
    if not OPENAI_API_KEY: return {"error":"OpenAI API key not configured"}
    try:
        headers = {"Content-Type":"application/json","Authorization":f"Bearer {OPENAI_API_KEY}"}
        prompt = f"""
        Analyze this document and return JSON:
        - main_category: operations/maintenance/safety/finance/it
        - priority_level: low/medium/high/critical
        - recommended_department
        - resolved: yes/no
        - summary: 2-3 sentences
        Document: {text[:1500]}
        """
        payload = {"model":"gpt-3.5-turbo","messages":[{"role":"system","content":"You are a KMRL assistant. Return valid JSON."},{"role":"user","content":prompt}],"max_tokens":300,"temperature":0.1}
        res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
        if res.status_code==200:
            content = res.json()["choices"][0]["message"]["content"].strip()
            if '```json' in content: content=content.split('```json')[1].split('```')[0]
            elif '```' in content: content=content.split('```')[1].split('```')[0]
            return json.loads(content)
        return {"error":f"OpenAI API Error {res.status_code}"}
    except Exception as e:
        return {"error":str(e)}

def text_to_speech(text):
    if not text.strip(): return ""
    try:
        from gtts import gTTS
        tts= gTTS(text=text, lang="en", slow=False)
        audio_fp=BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        return base64.b64encode(audio_fp.read()).decode("utf-8")
    except: return ""

# ===============================
# SESSION STATE
# ===============================
if 'extracted_text' not in st.session_state: st.session_state.extracted_text=None
if 'analysis_result' not in st.session_state: st.session_state.analysis_result=None

# ===============================
# HEADER
# ===============================
st.markdown('<div class="kmrl-brand-header"><h1>🚇 KMRL AI Document Hub</h1></div>', unsafe_allow_html=True)

# ===============================
# TABS
# ===============================
tab1, tab2, tab3 = st.tabs(["📁 Upload","🤖 AI Analysis","📊 Dashboard"])

# ----- TAB 1 -----
with tab1:
    st.markdown('<div class="kmrl-upload-zone"><h2>Upload Document</h2><p>PDF, DOCX, Images</p></div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=["pdf","docx","png","jpg","jpeg","tiff"])
    if uploaded_file:
        if st.button("🔍 Extract Text", use_container_width=True):
            with st.spinner("Extracting..."):
                text = extract_text_online(uploaded_file)
                if "failed" not in text.lower() and "error" not in text.lower():
                    st.session_state.extracted_text = text
                    st.success("✅ Text Extracted Successfully")
                    with st.expander("Preview", expanded=True):
                        st.text_area("", text[:1000]+"..." if len(text)>1000 else text, height=200)
                else:
                    st.error(f"❌ {text}")

# ----- TAB 2 -----
with tab2:
    if st.session_state.extracted_text:
        if st.button("🚀 Analyze Document", use_container_width=True):
            with st.spinner("Analyzing..."):
                result = analyze_document_with_ai(st.session_state.extracted_text)
                if "error" not in result:
                    st.session_state.analysis_result=result
                    st.success("✅ Analysis Complete")
                    # Department Card
                    dept = result.get("recommended_department","operations")
                    dept_info = KMRL_DEPARTMENTS.get(dept,KMRL_DEPARTMENTS["operations"])
                    resolved = result.get("resolved","no")
                    status_color = "kmrl-status-resolved" if resolved.lower()=="yes" else "kmrl-status-pending"
                    st.markdown(f"""
                        <div class='kmrl-department-card'>
                        <h3>{dept_info['icon']} {dept_info['name']}</h3>
                        <p>Manager: {dept_info['manager']}</p>
                        <p>Contact: {dept_info['email']}</p>
                        <p>Priority: {result.get('priority_level','medium').upper()}</p>
                        <p class="kmrl-status {status_color}">{resolved.upper()}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    # AI JSON
                    with st.expander("AI Analysis JSON", expanded=True):
                        st.json(result)
                    # Audio
                    summary = result.get("summary","")
                    audio_data = text_to_speech(summary)
                    if audio_data:
                        st.audio(base64.b64decode(audio_data), format="audio/mp3")
                        st.download_button("📥 Download Audio Summary", data=base64.b64decode(audio_data), file_name="kmrl_summary.mp3", mime="audio/mp3")
                else:
                    st.error(f"❌ {result['error']}")
    else:
        st.info("👆 Upload and extract text first.")

# ----- TAB 3 -----
with tab3:
    st.markdown("### 📊 KMRL Dashboard")
    dept_data = pd.DataFrame({
        "Department":[d['name'] for d in KMRL_DEPARTMENTS.values()],
        "Documents Processed":[45,32,28,15,8],
        "Avg Response Time":[1.2,2.5,3.1,4.2,1.8]
    })
    fig = px.bar(dept_data, x="Department", y="Documents Processed", color="Department")
    st.plotly_chart(fig, use_container_width=True)
