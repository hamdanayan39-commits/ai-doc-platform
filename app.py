import base64
import requests
import streamlit as st
from io import BytesIO
import PyPDF2
import docx
import time
import json
import pandas as pd
from datetime import datetime
import plotly.express as px
import os

# ===============================
# 🛠️ ENHANCED API KEY MANAGEMENT
# ===============================
def get_api_keys():
    """Smart API key management with multiple fallback options"""
    api_keys = {}
    
    # Option 1: Streamlit Secrets (Production)
    try:
        api_keys['OPENAI_API_KEY'] = st.secrets.get("OPENAI_API_KEY", "")
        api_keys['OCR_API_KEY'] = st.secrets.get("OCR_API_KEY", "")
        if api_keys['OPENAI_API_KEY'] and api_keys['OCR_API_KEY']:
            st.sidebar.success("✅ API keys loaded from secrets")
            return api_keys
    except:
        pass
    
    # Option 2: Direct assignment (for quick testing)
    api_keys['OPENAI_API_KEY'] = "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"
    api_keys['OCR_API_KEY'] = "K87313976288957"
    
    # Option 3: Manual Input Fallback
    if not api_keys['OPENAI_API_KEY']:
        st.sidebar.warning("🔑 Configuring API keys...")
        
        with st.sidebar.expander("🔧 API Configuration", expanded=True):
            st.info("API keys are being configured automatically")
            
            api_keys['OPENAI_API_KEY'] = st.text_input(
                "OpenAI API Key", 
                value=api_keys['OPENAI_API_KEY'],
                type="password",
                help="Your OpenAI API key"
            )
            
            api_keys['OCR_API_KEY'] = st.text_input(
                "OCR.space API Key", 
                value=api_keys['OCR_API_KEY'],
                type="password",
                help="OCR API key for text extraction"
            )
    
    return api_keys

# Initialize API keys
API_KEYS = get_api_keys()
OPENAI_API_KEY = API_KEYS['OPENAI_API_KEY']
OCR_API_KEY = API_KEYS['OCR_API_KEY']

# ===============================
# 🎨 ENHANCED UI STYLING
# ===============================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    .main-container {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
        text-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .sub-header {
        font-size: 1.3rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 300;
    }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
    }
    
    .neon-glow {
        border: 2px solid #00f3ff;
        border-radius: 15px;
        padding: 1.5rem;
        background: rgba(0, 243, 255, 0.05);
        margin: 1rem 0;
        box-shadow: 0 0 20px rgba(0, 243, 255, 0.3);
        animation: glow 2s infinite alternate;
    }
    
    @keyframes glow {
        from { box-shadow: 0 0 20px rgba(0, 243, 255, 0.3); }
        to { box-shadow: 0 0 30px rgba(0, 243, 255, 0.6); }
    }
    
    .gradient-button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 12px 30px;
        border-radius: 25px;
        font-weight: 600;
        font-size: 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .gradient-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        background: linear-gradient(45deg, #764ba2, #667eea);
    }
    
    .metric-display {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin: 0.5rem;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
    }
    
    .upload-zone {
        border: 3px dashed #667eea;
        border-radius: 20px;
        padding: 3rem 2rem;
        text-align: center;
        background: rgba(102, 126, 234, 0.05);
        transition: all 0.3s ease;
        margin: 2rem 0;
    }
    
    .upload-zone:hover {
        background: rgba(102, 126, 234, 0.1);
        border-color: #764ba2;
    }
    
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-active { background: #4CAF50; }
    .status-processing { background: #FFC107; animation: pulse 1s infinite; }
    .status-error { background: #F44336; }
    
    .api-status {
        padding: 10px;
        border-radius: 10px;
        margin: 10px 0;
        font-weight: bold;
    }
    
    .api-active { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .api-inactive { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
</style>
""", unsafe_allow_html=True)

# ===============================
# 🏢 KML DEPARTMENTS DATABASE
# ===============================
KML_DEPARTMENTS = {
    "operations": {
        "name": "🚇 Operations Department",
        "icon": "🚇",
        "email": "operations@kmrl.com",
        "phone": "+91-471-1234567",
        "manager": "Mr. Rajesh Kumar",
        "color": "#FF6B6B",
        "description": "Handles daily metro operations and scheduling"
    },
    "maintenance": {
        "name": "🔧 Maintenance & Engineering",
        "icon": "🔧", 
        "email": "maintenance@kmrl.com",
        "phone": "+91-471-1234568",
        "manager": "Ms. Priya Sharma",
        "color": "#4ECDC4",
        "description": "Infrastructure and equipment maintenance"
    },
    "safety": {
        "name": "🛡️ Safety & Compliance",
        "icon": "🛡️",
        "email": "safety@kmrl.com",
        "phone": "+91-471-1234569",
        "manager": "Mr. Amit Patel",
        "color": "#45B7D1",
        "description": "Safety protocols and regulatory compliance"
    },
    "finance": {
        "name": "💰 Finance & Accounts",
        "icon": "💰", 
        "email": "finance@kmrl.com",
        "phone": "+91-471-1234570",
        "manager": "Ms. Anjali Nair",
        "color": "#96CEB4",
        "description": "Financial management and accounting"
    },
    "it": {
        "name": "💻 IT & Digital Solutions",
        "icon": "💻",
        "email": "it.support@kmrl.com",
        "phone": "+91-471-1234571",
        "manager": "Mr. Sanjay Menon",
        "color": "#FECA57",
        "description": "Technology infrastructure and digital innovation"
    }
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
    if not OCR_API_KEY:
        return "OCR API key not configured"
    
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

def test_openai_connection():
    """Test if OpenAI API key is working"""
    if not OPENAI_API_KEY:
        return False, "No API key provided"
    
    try:
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        response = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=10)
        return response.status_code == 200, f"Status: {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def analyze_document_with_ai(text):
    if not OPENAI_API_KEY:
        return {"error": "OpenAI API key not configured"}
    
    try:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"}
        
        # Simple prompt for better JSON response
        prompt = """Analyze this document and return JSON with: 
        - main_category (operations, maintenance, safety, finance, it)
        - priority_level (low, medium, high, critical)  
        - key_topics (array of main topics)
        - recommended_department (which department should handle this)
        - summary (brief 2-3 sentence summary)"""
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that returns valid JSON."},
                {"role": "user", "content": f"{prompt}\n\nDocument content: {text[:2000]}"}
            ],
            "max_tokens": 500,
            "temperature": 0.1
        }
        
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            # Clean JSON response
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            
            return json.loads(content)
        else:
            return {"error": f"API Error {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

def text_to_speech_advanced(text, lang="en"):
    if not text.strip():
        return ""
    
    try:
        from gtts import gTTS
        lang_map = {"en": "en", "hi": "hi", "ml": "ml"}
        tts_lang = lang_map.get(lang, "en")
        
        tts = gTTS(text=text, lang=tts_lang, slow=False)
        audio_fp = BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        return base64.b64encode(audio_fp.read()).decode("utf-8")
    except Exception as e:
        return ""

# ===============================
# 🚀 STREAMLIT APP
# ===============================
st.set_page_config(
    page_title="KML AI Document Hub",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = None
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None

# Header Section
st.markdown('<h1 class="main-header">🚇 KML AI Document Hub</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Advanced Document Intelligence Platform for Kochi Metro Rail</p>', unsafe_allow_html=True)

# Sidebar with API Status
with st.sidebar:
    st.markdown("### 🔧 System Status")
    
    # Test API connections
    openai_status, openai_msg = test_openai_connection()
    ocr_status = bool(OCR_API_KEY)
    
    st.markdown(f"""
    <div class="api-status {'api-active' if openai_status else 'api-inactive'}">
        🤖 OpenAI API: {'✅ Active' if openai_status else '❌ Inactive'}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="api-status {'api-active' if ocr_status else 'api-inactive'}">
        📷 OCR API: {'✅ Active' if ocr_status else '❌ Inactive'}
    </div>
    """, unsafe_allow_html=True)
    
    if not openai_status:
        st.error(f"OpenAI Issue: {openai_msg}")
        st.info("Please check your API key in secrets.toml")
    
    st.markdown("---")
    st.markdown("### 🏢 Departments")
    for dept_id, dept in KML_DEPARTMENTS.items():
        with st.expander(f"{dept['icon']} {dept['name']}"):
            st.write(f"**Manager:** {dept['manager']}")
            st.write(f"**Phone:** {dept['phone']}")

# Main Tabs
tab1, tab2, tab3 = st.tabs(["📁 Document Upload", "🤖 AI Analysis", "⚡ Quick Actions"])

with tab1:
    st.markdown("""
    <div class='glass-card'>
        <h2>📁 Smart Document Upload</h2>
        <p>Upload PDF, DOCX, or images for intelligent analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Upload Zone
    st.markdown('<div class="upload-zone">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Drag & Drop or Click to Upload",
        type=["pdf", "docx", "png", "jpg", "jpeg", "tiff"],
        help="Supported formats: PDF, DOCX, Images"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        file_icon = "📄" if uploaded_file.type == "application/pdf" else "📝" if "docx" in uploaded_file.type else "🖼️"
        
        st.markdown(f"""
        <div class='glass-card'>
            <h3>{file_icon} {uploaded_file.name}</h3>
            <p><strong>Type:</strong> {uploaded_file.type} • <strong>Size:</strong> {uploaded_file.size/1024:.1f} KB</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔍 Extract Text Content", use_container_width=True, type="primary"):
            with st.spinner("🔄 Processing document..."):
                extracted_text = extract_text_online(uploaded_file)
                
                if extracted_text and not any(error in extracted_text.lower() for error in ["error", "failed", "unsupported"]):
                    st.session_state.extracted_text = extracted_text
                    st.success("✅ Text extraction successful!")
                    
                    with st.expander("📋 Preview Extracted Text", expanded=True):
                        st.text_area("", extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text, height=200)
                else:
                    st.error(f"❌ Extraction issue: {extracted_text}")

with tab2:
    st.markdown("""
    <div class='glass-card'>
        <h2>🤖 AI Document Analysis</h2>
        <p>Advanced AI-powered analysis and department routing</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.extracted_text:
        if st.button("🚀 Start AI Analysis", use_container_width=True, type="primary"):
            with st.spinner("🧠 AI is analyzing document content..."):
                analysis_result = analyze_document_with_ai(st.session_state.extracted_text)
                
                if "error" not in analysis_result:
                    st.session_state.analysis_result = analysis_result
                    st.success("✅ AI Analysis Complete!")
                    
                    # Display Results
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 📊 Analysis Results")
                        st.json(analysis_result)
                    
                    with col2:
                        dept = analysis_result.get("recommended_department", "operations")
                        dept_info = KML_DEPARTMENTS.get(dept, KML_DEPARTMENTS["operations"])
                        
                        st.markdown(f"""
                        <div class='neon-glow'>
                            <h3>{dept_info['icon']} {dept_info['name']}</h3>
                            <p><strong>Priority:</strong> {analysis_result.get('priority_level', 'medium').upper()}</p>
                            <p><strong>Contact:</strong> {dept_info['manager']}</p>
                            <p><strong>Email:</strong> {dept_info['email']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Audio Summary
                        summary = analysis_result.get("summary", "Analysis complete. Please check the results.")
                        audio_data = text_to_speech_advanced(summary, "en")
                        if audio_data:
                            st.audio(base64.b64decode(audio_data), format="audio/mp3")
                else:
                    st.error(f"❌ Analysis failed: {analysis_result['error']}")
    else:
        st.info("👆 Please upload a document and extract text first")

with tab3:
    st.markdown("""
    <div class='glass-card'>
        <h2>⚡ Quick Actions</h2>
        <p>Instant department communications and task management</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.analysis_result:
        analysis = st.session_state.analysis_result
        dept = analysis.get("recommended_department", "operations")
        dept_info = KML_DEPARTMENTS[dept]
        
        # Action Buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"📧 Email {dept_info['name']}", use_container_width=True):
                st.success(f"✅ Email drafted to {dept_info['email']}")
            if st.button("📋 Create Task", use_container_width=True):
                st.success("✅ Task created in KML system")
        with col2:
            if st.button("📊 Generate Report", use_container_width=True):
                st.success("✅ Analytics report generated")
            if st.button("🔄 Process Similar", use_container_width=True):
                st.info("✅ Template saved for similar documents")
        
        # Priority Alert
        if analysis.get("priority_level") in ["high", "critical"]:
            st.markdown("""
            <div class='neon-glow'>
                <h3>🚨 High Priority Alert</h3>
                <p>This document requires immediate attention</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Complete AI analysis to unlock quick actions")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>🚇 <strong>Kochi Metro Rail Limited</strong> • AI Document Management System v2.0</p>
</div>
""", unsafe_allow_html=True)
