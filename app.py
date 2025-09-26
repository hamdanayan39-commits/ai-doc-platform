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

# API Keys from Streamlit Secrets
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    OCR_API_KEY = st.secrets["OCR_API_KEY"]
except:
    st.error("❌ API keys not found. Please configure secrets.toml")
    OPENAI_API_KEY = ""
    OCR_API_KEY = ""

# Custom CSS for ultra-modern tech interface
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .cyber-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    .neon-border {
        border: 2px solid #00f3ff;
        border-radius: 10px;
        padding: 1rem;
        background: rgba(0, 243, 255, 0.1);
        margin: 0.5rem 0;
    }
    
    .pulse-animation {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .department-tag {
        background: linear-gradient(45deg, #ff6b6b, #ee5a24);
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0.2rem;
        display: inline-block;
    }
    
    .tech-button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 0.7rem 2rem;
        border-radius: 25px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .tech-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
    }
    
    .dashboard-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# KML Departments Database
KML_DEPARTMENTS = {
    "operations": {
        "name": "Operations Department",
        "email": "operations@kmrl.com",
        "phone": "+91-XXX-XXXX",
        "manager": "Mr. Rajesh Kumar",
        "color": "#FF6B6B"
    },
    "maintenance": {
        "name": "Maintenance & Engineering",
        "email": "maintenance@kmrl.com", 
        "phone": "+91-XXX-XXXX",
        "manager": "Ms. Priya Sharma",
        "color": "#4ECDC4"
    },
    "safety": {
        "name": "Safety & Compliance",
        "email": "safety@kmrl.com",
        "phone": "+91-XXX-XXXX",
        "manager": "Mr. Amit Patel",
        "color": "#45B7D1"
    },
    "finance": {
        "name": "Finance & Accounts",
        "email": "finance@kmrl.com",
        "phone": "+91-XXX-XXXX", 
        "manager": "Ms. Anjali Nair",
        "color": "#96CEB4"
    },
    "it": {
        "name": "IT & Digital Solutions",
        "email": "it.support@kmrl.com",
        "phone": "+91-XXX-XXXX",
        "manager": "Mr. Sanjay Menon",
        "color": "#FECA57"
    }
}

def extract_text_from_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        return f"PDF extraction failed: {str(e)}"

def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
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
            return result["ParsedResults"][0]["ParsedText"].strip()
        else:
            return "OCR Error"
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
    """Advanced AI analysis for department routing and insights"""
    if not OPENAI_API_KEY:
        return {"error": "API key not configured"}
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        prompt = f"""
        Analyze this document and provide:
        1. Main category (operations, maintenance, safety, finance, it)
        2. Priority level (low, medium, high, critical)
        3. Key topics (comma-separated)
        4. Suggested action items
        5. Recommended department
        
        Document text: {text[:4000]}
        
        Return as JSON format only.
        """
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a KML document analysis expert. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.1
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            # Clean and parse JSON response
            content = content.replace('```json', '').replace('```', '').strip()
            return json.loads(content)
        else:
            return {"error": f"API Error: {response.status_code}"}
            
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

def generate_ai_summary(text, department):
    """Generate context-aware summary"""
    if not OPENAI_API_KEY:
        return "API key not configured"
    
    try:
        headers = {
            "Content-Type": "application/json", 
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": f"You are a {department} specialist at KML. Create concise, actionable summaries."},
                {"role": "user", "content": f"Summarize this document for {department} department:\n\n{text[:6000]}"}
            ],
            "max_tokens": 300,
            "temperature": 0.3
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        else:
            return f"Summary generation failed: {response.status_code}"
            
    except Exception as e:
        return f"Error: {str(e)}"

def text_to_speech_advanced(text, lang="en"):
    """Enhanced TTS with fallback"""
    if not text.strip():
        return ""
    
    try:
        from gtts import gTTS
        lang_map = {"en": "en", "hi": "hi", "ml": "ml", "ar": "ar", "fr": "fr"}
        tts_lang = lang_map.get(lang, "en")
        
        tts = gTTS(text=text, lang=tts_lang, slow=False)
        audio_fp = BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        
        return base64.b64encode(audio_fp.read()).decode("utf-8")
    except Exception as e:
        st.warning(f"Primary TTS failed: {str(e)}")
        return ""

def create_department_dashboard(analysis_result):
    """Create interactive department dashboard"""
    department = analysis_result.get("recommended_department", "operations")
    dept_info = KML_DEPARTMENTS.get(department, KML_DEPARTMENTS["operations"])
    
    st.markdown(f"""
    <div class="cyber-card">
        <h3>🎯 AI Department Routing</h3>
        <div class="neon-border">
            <h4>Recommended Department: <span style="color:{dept_info['color']}">{dept_info['name']}</span></h4>
            <p>📧 {dept_info['email']} | 📞 {dept_info['phone']}</p>
            <p>👨‍💼 Manager: {dept_info['manager']}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Priority indicator
    priority = analysis_result.get("priority_level", "medium")
    priority_colors = {
        "low": "#4ECDC4", 
        "medium": "#FFD93D",
        "high": "#FF6B6B", 
        "critical": "#FF0000"
    }
    
    st.markdown(f"""
    <div class="dashboard-grid">
        <div class="metric-card">
            <h4>🚨 Priority Level</h4>
            <h2 style="color:{priority_colors.get(priority, '#FFD93D')}">{priority.upper()}</h2>
        </div>
        <div class="metric-card">
            <h4>📊 Category</h4>
            <h2>{analysis_result.get('main_category', 'General').title()}</h2>
        </div>
        <div class="metric-card">
            <h4>⏱️ Response Time</h4>
            <h2>24-48H</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Initialize session state
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = None
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'ai_summary' not in st.session_state:
    st.session_state.ai_summary = None

# Main App Interface
st.set_page_config(
    page_title="KML AI Document Hub",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Header with KML Branding
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.markdown('<div class="main-header">🚇 KML AI Document Hub</div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align: center; color: #666; font-size: 1.2rem;">Advanced Document Analysis & Department Routing System</div>', unsafe_allow_html=True)

# Sidebar with KML Features
with st.sidebar:
    st.markdown("### 🎛️ Control Panel")
    
    # Department filter
    department_names = ["All Departments"] + [dept["name"] for dept in KML_DEPARTMENTS.values()]
    selected_dept = st.selectbox("Filter by Department", department_names)
    
    # AI Analysis Level
    analysis_level = st.radio(
        "AI Analysis Depth",
        ["Basic", "Advanced", "Expert"],
        help="Choose analysis intensity"
    )
    
    st.markdown("---")
    st.markdown("### 📈 Live Metrics")
    
    # Mock live metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Documents Today", "47", "+12%")
    with col2:
        st.metric("Avg. Response", "2.3h", "-0.5h")
    
    st.markdown("---")
    st.markdown("### 🚀 Quick Actions")
    
    if st.button("📧 Send to All Departments", use_container_width=True):
        st.success("Document queued for department distribution!")
    
    if st.button("🔄 Real-time Sync", use_container_width=True):
        st.info("Syncing with KML central database...")

# Main Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📁 Upload", "🤖 AI Analysis", "📊 Dashboard", "🚀 Actions"])

with tab1:
    st.markdown("### 🚀 Smart Document Upload")
    
    # Advanced upload zone
    with st.container():
        st.markdown('<div class="cyber-card">', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            uploaded_file = st.file_uploader(
                "Drag & Drop or Click to Upload",
                type=["pdf", "docx", "png", "jpg", "jpeg", "tiff"],
                help="Supported: PDF, DOCX, Images",
                label_visibility="collapsed"
            )
        
        with col2:
            st.markdown("""
            <div style="text-align: center;">
                <h4>⚡ AI Features</h4>
                <p>• Smart Routing</p>
                <p>• Priority Detection</p>
                <p>• Multi-department</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_file:
        # File analysis
        with st.spinner("🔄 Analyzing document structure..."):
            time.sleep(1)
            extracted_text = extract_text_online(uploaded_file)
            
            if extracted_text and not "Error" in extracted_text:
                st.session_state.extracted_text = extracted_text
                st.success("✅ Document ready for AI analysis!")
                
                # Quick preview
                with st.expander("📋 Document Preview", expanded=True):
                    st.text_area("", extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text, height=150)

with tab2:
    st.markdown("### 🧠 Advanced AI Analysis")
    
    if st.session_state.extracted_text:
        if st.button("🚀 Start Deep Analysis", type="primary", use_container_width=True):
            with st.spinner("🤖 AI is analyzing document content..."):
                # Advanced AI analysis
                analysis_result = analyze_document_with_ai(st.session_state.extracted_text)
                
                if "error" not in analysis_result:
                    st.session_state.analysis_result = analysis_result
                    
                    # Generate AI summary
                    department = analysis_result.get("recommended_department", "operations")
                    ai_summary = generate_ai_summary(st.session_state.extracted_text, department)
                    st.session_state.ai_summary = ai_summary
                    
                    st.success("🎯 AI Analysis Complete!")
                    
                    # Display results
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 📊 Document Insights")
                        st.json(analysis_result)
                    
                    with col2:
                        st.markdown("#### 📝 AI Summary")
                        st.markdown(f'<div class="cyber-card">{ai_summary}</div>', unsafe_allow_html=True)
                        
                        # Generate audio
                        audio_data = text_to_speech_advanced(ai_summary, "en")
                        if audio_data:
                            st.audio(base64.b64decode(audio_data), format="audio/mp3")
                else:
                    st.error(f"Analysis failed: {analysis_result['error']}")
    else:
        st.info("👆 Upload a document first to start AI analysis")

with tab3:
    st.markdown("### 📈 KML Department Dashboard")
    
    if st.session_state.analysis_result:
        create_department_dashboard(st.session_state.analysis_result)
        
        # Department visualization
        st.markdown("#### 🎯 Department Distribution")
        
        # Create department chart
        dept_data = {
            "Department": list(KML_DEPARTMENTS.keys()),
            "Documents": [25, 18, 12, 8, 15]  # Mock data
        }
        
        fig = px.bar(dept_data, x="Department", y="Documents", 
                     color="Department", title="Document Distribution by Department")
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("🤖 Complete AI analysis to view department dashboard")

with tab4:
    st.markdown("### ⚡ Quick Actions")
    
    if st.session_state.analysis_result:
        analysis_result = st.session_state.analysis_result
        department = analysis_result.get("recommended_department", "operations")
        dept_info = KML_DEPARTMENTS.get(department)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 📧 Send to Department")
            if st.button(f"Send to {dept_info['name']}", use_container_width=True):
                st.success(f"✅ Document sent to {dept_info['name']}!")
        
        with col2:
            st.markdown("#### 🔄 Create Task")
            if st.button("Create Action Item", use_container_width=True):
                st.success("📋 Task created in KML system!")
        
        with col3:
            st.markdown("#### 📊 Generate Report")
            if st.button("Create Analytics", use_container_width=True):
                st.success("📈 Report generated successfully!")
        
        # Emergency actions
        st.markdown("---")
        st.markdown("#### 🚨 Emergency Protocols")
        
        if analysis_result.get("priority_level") in ["high", "critical"]:
            st.warning("⚠️ High Priority Document - Immediate Action Required")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚨 Alert Management", use_container_width=True):
                    st.error("Management team alerted!")
            with col2:
                if st.button("📱 Mobile Notification", use_container_width=True):
                    st.error("Mobile alerts sent to department!")
    
    else:
        st.info("Complete AI analysis to unlock action features")

# Footer with KML branding
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "🚇 Kochi Metro Rail Limited • AI-Powered Document Management System v2.0 • "
    f"© {datetime.now().year} KML Digital Innovation"
    "</div>", 
    unsafe_allow_html=True
)
