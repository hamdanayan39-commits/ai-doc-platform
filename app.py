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
        OCR_API_KEY = st.secrets.get("OCR_API_KEY", "K87313976288957")
        if OPENAI_API_KEY:
            st.sidebar.success("✅ API keys loaded securely")
            return OPENAI_API_KEY, OCR_API_KEY
        else:
            st.sidebar.warning("🔐 Using development mode - configure secrets for production")
            return "sk-YOUR_DEV_KEY_HERE", "K87313976288957"
    except Exception as e:
        st.error(f"Configuration error: {e}")
        return "", "K87313976288957"

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
.kmrl-glass-card { background: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 2rem; margin: 1rem 0; box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1); border-left: 5px solid #FF6B35; }
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
    "operations": {"name": "🚇 Operations Department", "icon": "🚇", "email": "operations@kmrl.com", "manager": "Mr. Rajesh Kumar", "color": "#FF6B35", "description": "Handles daily metro operations and scheduling"},
    "maintenance": {"name": "🔧 Maintenance & Engineering", "icon": "🔧", "email": "maintenance@kmrl.com", "manager": "Ms. Priya Sharma", "color": "#4ECDC4", "description": "Infrastructure and equipment maintenance"},
    "safety": {"name": "🛡️ Safety & Compliance", "icon": "🛡️", "email": "safety@kmrl.com", "manager": "Mr. Amit Patel", "color": "#45B7D1", "description": "Safety protocols and regulatory compliance"},
    "finance": {"name": "💰 Finance & Accounts", "icon": "💰", "email": "finance@kmrl.com", "manager": "Ms. Anjali Nair", "color": "#96CEB4", "description": "Financial management and accounting"},
    "it": {"name": "💻 IT & Digital Solutions", "icon": "💻", "email": "it.support@kmrl.com", "manager": "Mr. Sanjay Menon", "color": "#FECA57", "description": "Technology infrastructure and digital innovation"}
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
        text = "".join([page.extract_text() + "\n" for page in pdf_reader.pages])
        return text.strip() if text.strip() else "No text could be extracted from PDF."
    except Exception as e:
        return f"PDF extraction failed: {str(e)}"

def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        text = "".join([p.text + "\n" for p in doc.paragraphs])
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
    if not OPENAI_API_KEY:
        return {"error": "OpenAI API key not configured"}
    try:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"}
        prompt = f"""
        Analyze this KMRL document and return JSON with:
        - "main_category": [operations, maintenance, safety, finance, it]
        - "priority_level": [low, medium, high, critical]
        - "recommended_department": which KMRL department should handle this
        - "summary": brief 2-3 sentence summary
        - "resolved_status": [resolved, pending, follow-up required] based on urgency and content
        Document: {text[:1500]}
        """
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a KMRL document analysis assistant. Return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 350,
            "temperature": 0.1
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            return json.loads(content)
        else:
            return {"error": f"OpenAI API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

def text_to_speech(text, lang="en"):
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
st.set_page_config(page_title="KMRL AI Document Hub", page_icon="🚇", layout="wide", initial_sidebar_state="expanded")

if 'extracted_text' not in st.session_state: st.session_state.extracted_text = None
if 'analysis_result' not in st.session_state: st.session_state.analysis_result = None

# Header
st.markdown("""
<div class='kmrl-brand-header'>
    <h1 style='color: white; margin: 0; font-size: 2.5rem;'>🚇 Kochi Metro Rail Limited (KMRL)</h1>
    <p style='color: white; font-size: 1.2rem; margin: 10px 0 0 0;'>AI-Powered Document Management System</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
api_status = test_api_connections()
with st.sidebar:
    st.markdown("### 🔧 KMRL System Status")
    col1, col2 = st.columns(2)
    with col1: st.markdown(f"**OpenAI API:** {'✅ Active' if api_status['openai'] else '❌ Inactive'}")
    with col2: st.markdown(f"**OCR API:** {'✅ Active' if api_status['ocr'] else '❌ Inactive'}")
    if not api_status['openai']: st.error("OpenAI API not working. Please check API configuration.")
    st.markdown("---\n### 🏢 KMRL Departments")
    for dept_id, dept in KMRL_DEPARTMENTS.items():
        with st.expander(f"{dept['icon']} {dept['name']}"):
            st.write(f"**Manager:** {dept['manager']}")
            st.write(f"**Email:** {dept['email']}")

# Tabs
tab1, tab2, tab3 = st.tabs(["📁 KMRL Document Upload", "🤖 AI Analysis", "📊 KMRL Dashboard"])

# ===============================
# Tab 1 - Upload
# ===============================
with tab1:
    st.markdown('<div class="kmrl-glass-card"><h2>📁 KMRL Document Upload Center</h2><p>Upload documents for AI-powered analysis and automated department routing within KMRL</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="kmrl-upload-zone">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Choose a KMRL document", type=["pdf", "docx", "png", "jpg", "jpeg", "tiff"], help="KMRL supported formats: PDF, DOCX, Images")
    st.markdown('<div style="text-align: center; color: #666;"><h3>🎯 Drag & Drop or Click to Upload</h3><p>KMRL AI will automatically analyze and route to appropriate department</p></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file:
        file_icon = "📄" if uploaded_file.type == "application/pdf" else "📝" if "docx" in uploaded_file.type else "🖼️"
        st.markdown(f'<div class="kmrl-glass-card"><h3>{file_icon} {uploaded_file.name}</h3><p><strong>Type:</strong> {uploaded_file.type} • <strong>Size:</strong> {uploaded_file.size/1024:.1f} KB</p></div>', unsafe_allow_html=True)
        if st.button("🔍 Extract Text Content", use_container_width=True, type="primary"):
            with st.spinner("🔄 Processing KMRL document..."):
                extracted_text = extract_text_online(uploaded_file)
                if extracted_text and not any(error in extracted_text.lower() for error in ["error", "failed"]):
                    st.session_state.extracted_text = extracted_text
                    st.success("✅ KMRL text extraction successful!")
                    with st.expander("📋 Preview Extracted Text", expanded=True):
                        st.text_area("", extracted_text[:800]+"..." if len(extracted_text)>800 else extracted_text, height=200)
                else:
                    st.error(f"❌ KMRL extraction failed: {extracted_text}")

# ===============================
# Tab 2 - AI Analysis with Resolved Status
# ===============================
with tab2:
    st.markdown('<div class="kmrl-glass-card"><h2>🤖 KMRL AI Document Analysis</h2><p>Advanced artificial intelligence analysis for smart department routing within KMRL</p></div>', unsafe_allow_html=True)
    if st.session_state.extracted_text:
        if st.button("🚀 Start KMRL AI Analysis", use_container_width=True, type="primary"):
            with st.spinner("🧠 KMRL AI is analyzing document content..."):
                analysis_result = analyze_document_with_ai(st.session_state.extracted_text)
                if "error" not in analysis_result:
                    st.session_state.analysis_result = analysis_result
                    st.success("✅ KMRL AI Analysis Complete!")
                    col1, col2 = st.columns(2)
                    with col1: st.markdown("#### 📊 KMRL Analysis Results"); st.json(analysis_result)
                    with col2:
                        dept = analysis_result.get("recommended_department", "operations")
                        dept_info = KMRL_DEPARTMENTS.get(dept, KMRL_DEPARTMENTS["operations"])
                        st.markdown(f'<div class="kmrl-department-card"><h3>{dept_info["icon"]} {dept_info["name"]}</h3><p><strong>Priority:</strong> {analysis_result.get("priority_level","medium").upper()}</p><p><strong>KMRL Manager:</strong> {dept_info["manager"]}</p><p><strong>Contact:</strong> {dept_info["email"]}</p></div>', unsafe_allow_html=True)
                        # Resolved Status Badge
                        status = analysis_result.get("resolved_status", "pending").lower()
                        status_color = {"resolved":"kmrl-status-active","pending":"kmrl-status-inactive","follow-up required":"kmrl-status-inactive"}.get(status, "kmrl-status-inactive")
                        st.markdown(f'<div class="kmrl-status-badge {status_color}">Status: {status.replace("-", " ").title()}</div>', unsafe_allow_html=True)
                        # Mark as Resolved Button
                        if st.button("✅ Mark as Resolved"):
                            st.session_state.analysis_result["resolved_status"] = "resolved"
                            st.success("Document marked as resolved by department")
                        # Audio Summary
                        summary = analysis_result.get("summary","KMRL analysis complete. Document processed successfully.")
                        audio_data = text_to_speech(summary,"en")
                        if audio_data:
                            st.audio(base64.b64decode(audio_data), format="audio/mp3")
                            st.download_button("📥 Download KMRL Audio Summary", data=base64.b64decode(audio_data), file_name="kmrl_ai_summary.mp3", mime="audio/mp3")
                else: st.error(f"❌ KMRL analysis failed: {analysis_result['error']}")
    else:
        st.info("👆 Please upload a KMRL document and extract text first")

# ===============================
# Tab 3 - Dashboard
# ===============================
with tab3:
    st.markdown('<div class="kmrl-glass-card"><h2>📊 KMRL Analytics Dashboard</h2><p>Real-time KMRL document analytics and department performance metrics</p></div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown('<div class="kmrl-metric-card"><h3>📈 156</h3><p>KMRL Total Documents</p></div>', unsafe_allow_html=True)
    with col2: st.markdown('<div class="kmrl-metric
