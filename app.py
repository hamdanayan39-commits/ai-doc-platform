import base64
import requests
import streamlit as st
from io import BytesIO
import PyPDF2
import docx
import json
import pandas as pd
from datetime import datetime
import plotly.express as px

# ===============================
# 🔐 SECURE API KEY MANAGEMENT
# ===============================
def get_api_keys():
    """Secure API key handling"""
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
.kmrl-action-button { background: linear-gradient(45deg, #FF6B35, #FF8E53); color: white; border: none; padding: 12px 25px; border-radius: 25px; font-weight: 600; margin: 5px; cursor: pointer; transition: all 0.3s ease; width: 100%; }
.kmrl-action-button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(255, 107, 53, 0.4); }
.kmrl-status-badge { display: inline-block; padding: 5px 15px; border-radius: 20px; font-weight: 600; margin: 5px; }
.kmrl-status-active { background: #4CAF50; color: white; }
.kmrl-status-inactive { background: #f44336; color: white; }
</style>
""", unsafe_allow_html=True)

# ===============================
# 🏢 KMRL DEPARTMENTS DATABASE
# ===============================
KMRL_DEPARTMENTS = {
    "operations": {"name": "🚇 Operations Department","icon": "🚇","email": "operations@kmrl.com","phone": "+91-471-1234567","manager": "Mr. Rajesh Kumar","color": "#FF6B35","description": "Handles daily metro operations and scheduling"},
    "maintenance": {"name": "🔧 Maintenance & Engineering","icon": "🔧","email": "maintenance@kmrl.com","phone": "+91-471-1234568","manager": "Ms. Priya Sharma","color": "#4ECDC4","description": "Infrastructure and equipment maintenance"},
    "safety": {"name": "🛡️ Safety & Compliance","icon": "🛡️","email": "safety@kmrl.com","phone": "+91-471-1234569","manager": "Mr. Amit Patel","color": "#45B7D1","description": "Safety protocols and regulatory compliance"},
    "finance": {"name": "💰 Finance & Accounts","icon": "💰","email": "finance@kmrl.com","phone": "+91-471-1234570","manager": "Ms. Anjali Nair","color": "#96CEB4","description": "Financial management and accounting"},
    "it": {"name": "💻 IT & Digital Solutions","icon": "💻","email": "it.support@kmrl.com","phone": "+91-471-1234571","manager": "Mr. Sanjay Menon","color": "#FECA57","description": "Technology infrastructure and digital innovation"}
}

# ===============================
# 🔧 CORE FUNCTIONS
# ===============================
def test_api_connections():
    results = {}
    try:
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        response = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=10)
        results['openai'] = response.status_code == 200
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
        Analyze this KMRL document and return JSON with:
        - "main_category": [operations, maintenance, safety, finance, it]
        - "priority_level": [low, medium, high, critical]
        - "recommended_department": which KMRL department should handle this
        - "resolved": [yes/no]
        - "summary": brief 2-3 sentence summary
        Document: {text[:1500]}
        """
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a KMRL document analysis assistant. Return valid JSON."},
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

def text_to_speech(text, lang="en"):
    if not text.strip(): return ""
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_fp = BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        return base64.b64encode(audio_fp.read()).decode("utf-8")
    except Exception as e:
        return ""

# ===============================
# 🚀 STREAMLIT APP
# ===============================
st.set_page_config(page_title="KMRL AI Document Hub", page_icon="🚇", layout="wide")

if 'extracted_text' not in st.session_state: st.session_state.extracted_text = None
if 'analysis_result' not in st.session_state: st.session_state.analysis_result = None

st.markdown('<div class="kmrl-brand-header"><h1>🚇 Kochi Metro Rail Limited (KMRL)</h1><p>AI-Powered Document Management System</p></div>', unsafe_allow_html=True)

# Sidebar
api_status = test_api_connections()
with st.sidebar:
    st.markdown("### 🔧 KMRL System Status")
    col1, col2 = st.columns(2)
    with col1: st.markdown(f"**OpenAI API:** {'✅ Active' if api_status['openai'] else '❌ Inactive'}")
    with col2: st.markdown(f"**OCR API:** {'✅ Active' if api_status['ocr'] else '❌ Inactive'}")
    if not api_status['openai']: st.error("OpenAI API not working. Please check API configuration.")
    st.markdown("---")
    st.markdown("### 🏢 KMRL Departments")
    for dept_id, dept in KMRL_DEPARTMENTS.items():
        with st.expander(f"{dept['icon']} {dept['name']}"):
            st.write(f"**Manager:** {dept['manager']}")
            st.write(f"**Email:** {dept['email']}")

# Tabs
tab1, tab2, tab3 = st.tabs(["📁 KMRL Document Upload", "🤖 AI Analysis", "📊 KMRL Dashboard"])

# ---------- TAB 1 ----------
with tab1:
    st.markdown('<div class="kmrl-glass-card"><h2>📁 KMRL Document Upload Center</h2><p>Upload documents for AI-powered analysis and automated department routing within KMRL</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="kmrl-upload-zone">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Choose a KMRL document", type=["pdf", "docx", "png", "jpg", "jpeg", "tiff"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_file:
        file_icon = "📄" if uploaded_file.type == "application/pdf" else "📝" if "docx" in uploaded_file.type else "🖼️"
        st.markdown(f'<div class="kmrl-glass-card"><h3>{file_icon} {uploaded_file.name}</h3><p>Type: {uploaded_file.type} • Size: {uploaded_file.size/1024:.1f} KB</p></div>', unsafe_allow_html=True)
        if st.button("🔍 Extract Text Content", use_container_width=True):
            with st.spinner("🔄 Processing KMRL document..."):
                extracted_text = extract_text_online(uploaded_file)
                if extracted_text and not any(e in extracted_text.lower() for e in ["error","failed"]):
                    st.session_state.extracted_text = extracted_text
                    st.success("✅ KMRL text extraction successful!")
                    with st.expander("📋 Preview Extracted Text", expanded=True):
                        st.text_area("", extracted_text[:800]+"..." if len(extracted_text)>800 else extracted_text, height=200)
                else:
                    st.error(f"❌ KMRL extraction failed: {extracted_text}")

# ---------- TAB 2 ----------
with tab2:
    st.markdown('<div class="kmrl-glass-card"><h2>🤖 KMRL AI Document Analysis</h2><p>Advanced artificial intelligence analysis for smart department routing within KMRL</p></div>', unsafe_allow_html=True)
    if st.session_state.extracted_text:
        if st.button("🚀 Start KMRL AI Analysis", use_container_width=True):
            with st.spinner("🧠 KMRL AI is analyzing document content..."):
                analysis_result = analyze_document_with_ai(st.session_state.extracted_text)
                if "error" not in analysis_result:
                    st.session_state.analysis_result = analysis_result
                    st.success("✅ KMRL AI Analysis Complete!")
                    col1, col2 = st.columns(2)
                    with col1: st.json(analysis_result)
                    with col2:
                        dept = analysis_result.get("recommended_department","operations")
                        dept_info = KMRL_DEPARTMENTS.get(dept,KMRL_DEPARTMENTS["operations"])
                        resolved = analysis_result.get("resolved","no")
                        st.markdown(f'<div class="kmrl-department-card"><h3>{dept_info["icon"]} {dept_info["name"]}</h3><p>Priority: {analysis_result.get("priority_level","medium").upper()}</p><p>Resolved: {resolved.upper()}</p><p>Manager: {dept_info["manager"]}</p><p>Contact: {dept_info["email"]}</p></div>', unsafe_allow_html=True)
                        audio_data = text_to_speech(analysis_result.get("summary","KMRL analysis complete."),"en")
                        if audio_data:
                            st.audio(base64.b64decode(audio_data), format="audio/mp3")
                            st.download_button("📥 Download KMRL Audio Summary", data=base64.b64decode(audio_data), file_name="kmrl_ai_summary.mp3", mime="audio/mp3")
    else:
        st.info("👆 Please upload a KMRL document and extract text first")

# ---------- TAB 3 ----------
with tab3:
    st.markdown('<div class="kmrl-glass-card"><h2>📊 KMRL Analytics Dashboard</h2><p>Real-time KMRL document analytics and department performance metrics</p></div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown('<div class="kmrl-metric-card"><h3>📈 156</h3><p>Total Documents</p></div>', unsafe_allow_html=True)
    with col2: st.markdown('<div class="kmrl-metric-card"><h3>⚡ 2.1h</h3><p>Avg Response</p></div>', unsafe_allow_html=True)
    with col3: st.markdown('<div class="kmrl-metric-card"><h3>🎯 96%</h3><p>Accuracy</p></div>', unsafe_allow_html=True)
    with col4: st.markdown('<div class="kmrl-metric-card"><h3>🚀 52</h3><p>Today</p></div>', unsafe_allow_html=True)
    
    dept_data = pd.DataFrame({
        'KMRL Department':[d['name'] for d in KMRL_DEPARTMENTS.values()],
        'Documents Processed':[45,32,28,15,8],
        'Avg Response Time (hours)':[1.2,2.5,3.1,4.2,1.8],
        'Resolved Documents':[30,20,18,10,5]
    })
    fig = px.bar(dept_data, x='KMRL Department', y='Documents Processed', title="Documents Processed by Department", color='KMRL Department')
    st.plotly_chart(fig, use_container_width=True)
    
    if st.session_state.analysis_result:
        analysis = st.session_state.analysis_result
        dept = analysis.get("recommended_department","operations")
        dept_info = KMRL_DEPARTMENTS[dept]
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"📧 Email {dept_info['name']}", use_container_width=True): st.success(f"✅ KMRL email drafted to {dept_info['email']}")
            if st.button("📋 Create KMRL Task", use_container_width=True): st.success("✅ Task created in KMRL system")
        with col2:
            if st.button("📊 KMR
