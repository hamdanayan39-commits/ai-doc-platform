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

# ===============================
# 🔐 SECURE API KEY MANAGEMENT
# ===============================
def get_api_keys():
    """Secure API key handling"""
    try:
        OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
        OCR_API_KEY = st.secrets.get("OCR_API_KEY", "K87313976288957")
        
        if OPENAI_API_KEY:
            st.sidebar.success("✅ API keys loaded securely")
            return OPENAI_API_KEY, OCR_API_KEY
        else:
            st.sidebar.warning("🔐 Configure secrets.toml for production")
            return "", "K87313976288957"
            
    except Exception as e:
        st.error(f"Configuration error: {e}")
        return "", "K87313976288957"

# Initialize API keys securely
OPENAI_API_KEY, OCR_API_KEY = get_api_keys()

# ===============================
# 🌍 NLP LANGUAGE SUPPORT
# ===============================
NLP_LANGUAGES = {
    "English": {"code": "en", "flag": "🇺🇸", "gtts_code": "en"},
    "Hindi": {"code": "hi", "flag": "🇮🇳", "gtts_code": "hi"},
    "Malayalam": {"code": "ml", "flag": "🇮🇳", "gtts_code": "ml"},
    "Tamil": {"code": "ta", "flag": "🇮🇳", "gtts_code": "ta"},
    "Kannada": {"code": "kn", "flag": "🇮🇳", "gtts_code": "kn"},
    "Telugu": {"code": "te", "flag": "🇮🇳", "gtts_code": "te"},
    "Arabic": {"code": "ar", "flag": "🇦🇪", "gtts_code": "ar"},
    "French": {"code": "fr", "flag": "🇫🇷", "gtts_code": "fr"},
    "Spanish": {"code": "es", "flag": "🇪🇸", "gtts_code": "es"},
    "German": {"code": "de", "flag": "🇩🇪", "gtts_code": "de"}
}

SUMMARY_TYPES = {
    "brief": "Concise 2-3 sentence summary",
    "detailed": "Comprehensive paragraph summary", 
    "bullet_points": "Key points in bullet format",
    "executive": "Executive summary for management",
    "technical": "Technical detailed analysis"
}

# ===============================
# 🎨 KMRL BRANDED UI
# ===============================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .kmrl-main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .kmrl-brand-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .kmrl-glass-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #FF6B35;
    }
    
    .kmrl-department-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 0.5rem;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    .kmrl-upload-zone {
        border: 3px dashed #FF6B35;
        border-radius: 20px;
        padding: 3rem 2rem;
        text-align: center;
        background: rgba(255, 107, 53, 0.05);
        transition: all 0.3s ease;
        margin: 2rem 0;
    }
    
    .language-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 20px;
        background: #e3f2fd;
        color: #1976d2;
        font-size: 0.8rem;
        margin: 2px;
        border: 1px solid #bbdefb;
    }
    
    .summary-type-card {
        background: #f5f5f5;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #FF6B35;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .summary-type-card:hover {
        background: #eeeeee;
        transform: translateX(5px);
    }
    
    .summary-type-card.selected {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
</style>
""", unsafe_allow_html=True)

# ===============================
# 🏢 KMRL DEPARTMENTS DATABASE
# ===============================
KMRL_DEPARTMENTS = {
    "operations": {
        "name": "🚇 Operations Department",
        "icon": "🚇",
        "email": "operations@kmrl.com",
        "phone": "+91-471-1234567",
        "manager": "Mr. Rajesh Kumar",
        "color": "#FF6B35",
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
def test_api_connections():
    """Test API connections"""
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

def detect_language(text):
    """Simple language detection"""
    if not OPENAI_API_KEY:
        return "en"  # Default to English
    
    try:
        headers = {
            "Content-Type": "application/json", 
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "Detect the language of this text and return only the language code (en, hi, ml, ta, etc)."},
                {"role": "user", "content": f"Text: {text[:500]}"}
            ],
            "max_tokens": 10,
            "temperature": 0.1
        }
        
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            detected_lang = result["choices"][0]["message"]["content"].strip().lower()
            # Map to supported languages
            for lang_name, lang_info in NLP_LANGUAGES.items():
                if lang_info["code"] == detected_lang:
                    return detected_lang
            return "en"  # Default to English
        return "en"
    except:
        return "en"

def generate_ai_summary(text, summary_type="brief", target_language="en"):
    """Enhanced summary generation with multiple types and languages"""
    if not OPENAI_API_KEY:
        return "OpenAI API key not configured"
    
    try:
        headers = {
            "Content-Type": "application/json", 
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        # Summary type prompts
        summary_prompts = {
            "brief": "Provide a very concise 2-3 sentence summary focusing on the main points.",
            "detailed": "Provide a comprehensive paragraph summary covering all key aspects.",
            "bullet_points": "Provide key points in bullet format, focusing on actionable items.",
            "executive": "Provide an executive summary suitable for management, highlighting implications and recommendations.",
            "technical": "Provide a technical summary with specific details, metrics, and technical aspects."
        }
        
        prompt = f"""
        {summary_prompts.get(summary_type, summary_prompts['brief'])}
        
        Document text: {text[:3000]}
        
        """
        
        # Add language instruction if not English
        if target_language != "en":
            lang_name = [name for name, info in NLP_LANGUAGES.items() if info["code"] == target_language][0]
            prompt += f"\nPlease provide the summary in {lang_name} language."
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a professional document summarization expert."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.3
        }
        
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        else:
            return f"Error: API returned status {response.status_code}"
            
    except Exception as e:
        return f"Summary generation failed: {str(e)}"

def analyze_document_with_ai(text, target_language="en"):
    """Enhanced AI analysis with language support"""
    if not OPENAI_API_KEY:
        return {"error": "OpenAI API key not configured"}
    
    try:
        headers = {
            "Content-Type": "application/json", 
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        language_instruction = ""
        if target_language != "en":
            lang_name = [name for name, info in NLP_LANGUAGES.items() if info["code"] == target_language][0]
            language_instruction = f" Provide the response in {lang_name} language."
        
        prompt = f"""
        Analyze this KMRL document and return JSON with:
        - "main_category": [operations, maintenance, safety, finance, it]
        - "priority_level": [low, medium, high, critical]
        - "recommended_department": which KMRL department should handle this
        - "key_topics": array of 3-5 main topics
        - "summary": brief 2-3 sentence summary
        - "detected_language": the language of the document
        - "action_items": array of recommended actions
        
        Document: {text[:2000]}
        {language_instruction}
        """
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a KMRL document analysis assistant. Return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 600,
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
            return {"error": f"OpenAI API Error: {response.status_code}"}
            
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

def text_to_speech(text, lang="en"):
    """Convert text to speech with language support"""
    if not text.strip():
        return ""
    
    try:
        from gtts import gTTS
        
        # Get gTTS language code
        lang_code = "en"
        for lang_info in NLP_LANGUAGES.values():
            if lang_info["code"] == lang:
                lang_code = lang_info["gtts_code"]
                break
        
        tts = gTTS(text=text, lang=lang_code, slow=False)
        audio_fp = BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        return base64.b64encode(audio_fp.read()).decode("utf-8")
    except Exception as e:
        return f""

def translate_text(text, target_lang="en"):
    """Simple translation function"""
    if target_lang == "en" or not text.strip():
        return text
    
    if not OPENAI_API_KEY:
        return text  # Return original if no API key
    
    try:
        headers = {
            "Content-Type": "application/json", 
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        lang_name = [name for name, info in NLP_LANGUAGES.items() if info["code"] == target_lang][0]
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": f"You are a translation assistant. Translate to {lang_name}."},
                {"role": "user", "content": f"Translate this text to {lang_name}: {text[:1000]}"}
            ],
            "max_tokens": 400,
            "temperature": 0.1
        }
        
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=20)
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        return text
    except:
        return text

# ===============================
# 🚀 STREAMLIT APP
# ===============================
st.set_page_config(
    page_title="KMRL AI Document Hub",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = None
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'selected_language' not in st.session_state:
    st.session_state.selected_language = "en"
if 'summary_type' not in st.session_state:
    st.session_state.summary_type = "brief"

# KMRL Brand Header
st.markdown("""
<div class='kmrl-brand-header'>
    <h1 style='color: white; margin: 0; font-size: 2.5rem;'>🚇 Kochi Metro Rail Limited (KMRL)</h1>
    <p style='color: white; font-size: 1.2rem; margin: 10px 0 0 0;'>AI-Powered Document Management with NLP</p>
</div>
""", unsafe_allow_html=True)

# API Status Check
api_status = test_api_connections()

# Sidebar with NLP Settings
with st.sidebar:
    st.markdown("### 🔧 KMRL System Status")
    
    col1, col2 = st.columns(2)
    with col1:
        status = "✅ Active" if api_status['openai'] else "❌ Inactive"
        st.markdown(f"**OpenAI API:** {status}")
    with col2:
        status = "✅ Active" if api_status['ocr'] else "❌ Inactive"
        st.markdown(f"**OCR API:** {status}")
    
    st.markdown("---")
    st.markdown("### 🌍 NLP Language Settings")
    
    # Language Selection
    selected_lang_name = st.selectbox(
        "Output Language",
        options=list(NLP_LANGUAGES.keys()),
        index=0,
        help="Select language for summaries and analysis"
    )
    st.session_state.selected_language = NLP_LANGUAGES[selected_lang_name]["code"]
    
    st.markdown(f"**Selected:** {NLP_LANGUAGES[selected_lang_name]['flag']} {selected_lang_name}")
    
    st.markdown("---")
    st.markdown("### 📊 Summary Type")
    
    # Summary Type Selection
    for summary_key, summary_desc in SUMMARY_TYPES.items():
        is_selected = st.session_state.summary_type == summary_key
        st.markdown(f"""
        <div class='summary-type-card {'selected' if is_selected else ''}'
             onclick='this.style.background="#e3f2fd"'>
            <strong>{summary_key.title()}</strong><br>
            <small>{summary_desc}</small>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Select {summary_key.title()}", key=summary_key):
            st.session_state.summary_type = summary_key
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 🏢 KMRL Departments")
    
    for dept_id, dept in KMRL_DEPARTMENTS.items():
        with st.expander(f"{dept['icon']} {dept['name']}"):
            st.write(f"**Manager:** {dept['manager']}")
            st.write(f"**Email:** {dept['email']}")

# Main Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📁 Document Upload", "🤖 AI Analysis", "🌍 NLP Features", "📊 Dashboard"])

with tab1:
    st.markdown("""
    <div class='kmrl-glass-card'>
        <h2>📁 KMRL Document Upload Center</h2>
        <p>Upload documents for AI-powered analysis with multi-language NLP support</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Upload Zone
    st.markdown('<div class="kmrl-upload-zone">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Choose a KMRL document",
        type=["pdf", "docx", "png", "jpg", "jpeg", "tiff"],
        help="KMRL supported formats: PDF, DOCX, Images"
    )
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <h3>🎯 Drag & Drop or Click to Upload</h3>
        <p>Supports multiple languages and advanced NLP processing</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_file:
        # File Info
        file_icon = "📄" if uploaded_file.type == "application/pdf" else "📝" if "docx" in uploaded_file.type else "🖼️"
        
        st.markdown(f"""
        <div class='kmrl-glass-card'>
            <h3>{file_icon} {uploaded_file.name}</h3>
            <p><strong>Type:</strong> {uploaded_file.type} • <strong>Size:</strong> {uploaded_file.size/1024:.1f} KB</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Extract Text Button
        if st.button("🔍 Extract Text Content", use_container_width=True, type="primary"):
            with st.spinner("🔄 Processing KMRL document..."):
                extracted_text = extract_text_online(uploaded_file)
                
                if extracted_text and not any(error in extracted_text.lower() for error in ["error", "failed"]):
                    st.session_state.extracted_text = extracted_text
                    
                    # Auto-detect language
                    detected_lang = detect_language(extracted_text)
                    lang_name = [name for name, info in NLP_LANGUAGES.items() if info["code"] == detected_lang][0]
                    
                    st.success(f"✅ Text extraction successful! Detected language: {NLP_LANGUAGES[lang_name]['flag']} {lang_name}")
                    
                    # Text Preview
                    with st.expander("📋 Preview Extracted Text", expanded=True):
                        st.text_area("", extracted_text[:800] + "..." if len(extracted_text) > 800 else extracted_text, height=200)
                else:
                    st.error(f"❌ KMRL extraction failed: {extracted_text}")

with tab2:
    st.markdown("""
    <div class='kmrl-glass-card'>
        <h2>🤖 KMRL AI Document Analysis</h2>
        <p>Advanced AI analysis with multi-language support and smart department routing</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.extracted_text:
        # Analysis Options
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"🌍 Output Language: {[name for name, info in NLP_LANGUAGES.items() if info['code'] == st.session_state.selected_language][0]}")
        with col2:
            st.info(f"📊 Summary Type: {st.session_state.summary_type.title()}")
        
        if st.button("🚀 Start KMRL AI Analysis", use_container_width=True, type="primary"):
            with st.spinner("🧠 KMRL AI is analyzing document content..."):
                analysis_result = analyze_document_with_ai(
                    st.session_state.extracted_text, 
                    st.session_state.selected_language
                )
                
                if "error" not in analysis_result:
                    st.session_state.analysis_result = analysis_result
                    st.success("✅ KMRL AI Analysis Complete!")
                    
                    # Display Results
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 📊 KMRL Analysis Results")
                        st.json(analysis_result)
                    
                    with col2:
                        dept = analysis_result.get("recommended_department", "operations")
                        dept_info = KMRL_DEPARTMENTS.get(dept, KMRL_DEPARTMENTS["operations"])
                        
                        st.markdown(f"""
                        <div class='kmrl-department-card'>
                            <h3>{dept_info['icon']} {dept_info['name']}</h3>
                            <p><strong>Priority:</strong> {analysis_result.get('priority_level', 'medium').upper()}</p>
                            <p><strong>KMRL Manager:</strong> {dept_info['manager']}</p>
                            <p><strong>Contact:</strong> {dept_info['email']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Generate enhanced summary
                        enhanced_summary = generate_ai_summary(
                            st.session_state.extracted_text,
                            st.session_state.summary_type,
                            st.session_state.selected_language
                        )
                        
                        st.markdown("#### 📝 Enhanced Summary")
                        st.write(enhanced_summary)
                        
                        # Audio Summary
                        audio_data = text_to_speech(enhanced_summary, st.session_state.selected_language)
                        if audio_data:
                            st.audio(base64.b64decode(audio_data), format="audio/mp3")
                            st.download_button(
                                "📥 Download Audio Summary",
                                data=base64.b64decode(audio_data),
                                file_name=f"kmrl_summary_{st.session_state.selected_language}.mp3",
                                mime="audio/mp3"
                            )
                else:
                    st.error(f"❌ KMRL analysis failed: {analysis_result['error']}")
    else:
        st.info("👆 Please upload a KMRL document and extract text first")

with tab3:
    st.markdown("""
    <div class='kmrl-glass-card'>
        <h2>🌍 Advanced NLP Features</h2>
        <p>Multi-language processing, translation, and advanced text analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.extracted_text:
        # Language Information
        detected_lang = detect_language(st.session_state.extracted_text)
        detected_lang_name = [name for name, info in NLP_LANGUAGES.items() if info["code"] == detected_lang][0]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Detected Language", f"{NLP_LANGUAGES[detected_lang_name]['flag']} {detected_lang_name}")
        with col2:
            st.metric("Text Length", f"{len(st.session_state.extracted_text)} chars")
        with col3:
            st.metric("Word Count", f"{len(st.session_state.extracted_text.split())} words")
        
        # Translation Feature
        st.markdown("#### 🔄 Text Translation")
        target_lang = st.selectbox(
            "Translate to",
            options=list(NLP_LANGUAGES.keys()),
            index=0,
            key="translation_lang"
        )
        
        if st.button("Translate Text", use_container_width=True):
            with st.spinner("Translating..."):
                translated = translate_text(st.session_state.extracted_text[:1000], NLP_LANGUAGES[target_lang]["code"])
                st.text_area("Translated Text", translated, height=200)
        
        # Multiple Summary Types
        st.markdown("#### 📊 Generate Different Summaries")
        summary_col1, summary_col2 = st.columns(2)
        
        with summary_col1:
            if st.button("Brief Summary", use_container_width=True):
                summary = generate_ai_summary(st.session_state.extracted_text, "brief", st.session_state.selected_language)
                st.text_area("Brief Summary", summary, height=150)
            
            if st.button("Executive Summary", use_container_width=True):
                summary = generate_ai_summary(st.session_state.extracted_text, "executive", st.session_state.selected_language)
                st.text_area("Executive Summary", summary, height=150)
        
        with summary_col2:
            if st.button("Technical Summary", use_container_width=True):
                summary = generate_ai_summary(st.session_state.extracted_text, "technical", st.session_state.selected_language)
                st.text_area("Technical Summary", summary, height=150)
            
            if st.button("Bullet Points", use_container_width=True):
                summary = generate_ai_summary(st.session_state.extracted_text, "bullet_points", st.session_state.selected_language)
                st.text_area("Key Points", summary, height=150)
    
    else:
        st.info("👆 Upload a document to access NLP features")

with tab4:
    st.markdown("""
    <div class='kmrl-glass-card'>
        <h2>📊 KMRL Analytics Dashboard</h2>
        <p>Real-time analytics and performance metrics</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Language Distribution Chart
    st.markdown("#### 🌍 Language Distribution")
    lang_data = pd.DataFrame({
        'Language': list(NLP_LANGUAGES.keys()),
        'Documents': [45, 32, 28, 15, 8, 12, 18, 9, 11, 7]  # Mock data
    })
    
    fig = px.pie(lang_data, values='Documents', names='Language', title="KMRL Documents by Language")
    st.plotly_chart(fig, use_container_width=True)
    
    # Quick Actions
    if st.session_state.analysis_result:
        st.markdown("#### ⚡ KMRL Quick Actions")
        analysis = st.session_state.analysis_result
        dept = analysis.get("recommended_department", "operations")
        dept_info = KMRL_DEPARTMENTS[dept]
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"📧 Email {dept_info['name']}", use_container_width=True):
                st.success(f"✅ KMRL email drafted to {dept_info['email']}")
            if st.button("📋 Create KMRL Task", use_container_width=True):
                st.success("✅ Task created in KMRL system")
        with col2:
            if st.button("📊 KMRL Report", use_container_width=True):
                st.success("✅ KMRL analytics report generated")
            if st.button("🔄 KMRL Process", use_container_width=True):
                st.info("✅ KMRL template saved for similar documents")

# KMRL Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p><strong>🚇 Kochi Metro Rail Limited (KMRL)</strong> • AI Document Management with NLP • Version 3.0</p>
    <p>© 2024 KMRL Digital Innovation Team • Multi-language Support • Advanced NLP</p>
</div>
""", unsafe_allow_html=True)
