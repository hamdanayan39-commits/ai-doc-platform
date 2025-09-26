import base64
import requests
import streamlit as st
from io import BytesIO
import PyPDF2
import docx
from PIL import Image
import time

# API Keys from Streamlit Secrets
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    OCR_API_KEY = st.secrets["OCR_API_KEY"]
except:
    st.error("❌ API keys not found. Please configure secrets.toml")
    OPENAI_API_KEY = ""
    OCR_API_KEY = ""

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    .success-card {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
    }
    .warning-card {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
    }
    .feature-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .upload-area {
        border: 2px dashed #1f77b4;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
        background-color: #f8f9fa;
    }
    .step-number {
        background-color: #1f77b4;
        color: white;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-right: 10px;
    }
</style>
""", unsafe_allow_html=True)

def extract_text_from_pdf(file):
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip() if text.strip() else "No text could be extracted from PDF."
    except Exception as e:
        return f"PDF extraction failed: {str(e)}"

def extract_text_from_docx(file):
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip() if text.strip() else "No text could be extracted from DOCX."
    except Exception as e:
        return f"DOCX extraction failed: {str(e)}"

def extract_text_from_image(file):
    """Extract text from image using OCR"""
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
            if extracted_text.strip():
                return extracted_text
            else:
                return "No text could be extracted from the image."
        else:
            error_msg = result.get('ErrorMessage', 'Unknown error')
            return f"OCR Error: {error_msg}"
    except Exception as e:
        return f"OCR extraction failed: {str(e)}"

def extract_text_online(file):
    """Extract text based on file type"""
    file_type = file.type
    
    if file_type == "application/pdf":
        return extract_text_from_pdf(file)
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(file)
    elif file_type.startswith('image/'):
        return extract_text_from_image(file)
    else:
        return f"Unsupported file type: {file_type}"

def summarize_text_openai(text):
    """Summarize text using OpenAI API"""
    if not OPENAI_API_KEY:
        return "OpenAI API key not configured"
    
    if len(text.strip()) < 20:
        return "Text too short for meaningful summary."
    
    try:
        if len(text) > 8000:
            text = text[:8000] + "... [text truncated]"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that creates concise, professional summaries."},
                {"role": "user", "content": f"Please provide a clear and concise summary of this text. Focus on key points and main ideas:\n\n{text}"}
            ],
            "max_tokens": 250,
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
            return f"OpenAI API Error: {response.status_code}"
            
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def translate_text(text, target_lang="en"):
    """Translate text using LibreTranslate"""
    if target_lang == "en" or not text.strip():
        return text
    
    try:
        url = "https://libretranslate.com/translate"
        payload = {
            "q": text,
            "source": "auto",
            "target": target_lang,
            "format": "text"
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("translatedText", text)
        else:
            return text
            
    except:
        return text

def text_to_speech(text, lang="en"):
    """Convert text to speech using gTTS"""
    if not text.strip() or len(text.strip()) < 10:
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
    except:
        return ""

# Main App Interface
st.set_page_config(
    page_title="DocuMind AI - Smart Document Analysis",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Header Section
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<div class="main-header">🧠 DocuMind AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Smart Document Analysis & Audio Summarization</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    
    # Language selection
    lang_options = {
        "English 🇺🇸": "en",
        "Hindi 🇮🇳": "hi", 
        "Malayalam 🇮🇳": "ml",
        "Arabic 🇦🇪": "ar",
        "French 🇫🇷": "fr"
    }
    
    selected_lang = st.selectbox("🎯 Output Language", list(lang_options.keys()))
    lang_code = lang_options[selected_lang]
    
    st.markdown("---")
    st.markdown("### 📊 File Statistics")
    if 'file_stats' in st.session_state:
        st.write(f"**File Type:** {st.session_state.file_stats.get('type', 'N/A')}")
        st.write(f"**Text Length:** {st.session_state.file_stats.get('chars', 0)} characters")
        st.write(f"**Processing Time:** {st.session_state.file_stats.get('time', 0):.1f}s")
    
    st.markdown("---")
    st.markdown("### 🚀 Features")
    st.markdown("""
    - 📄 **Multi-format Support** (PDF, DOCX, Images)
    - 🤖 **AI-Powered Summarization**
    - 🌍 **Multi-language Translation**
    - 🔊 **Text-to-Speech Audio**
    - ⚡ **Real-time Processing**
    """)

# Main Content Area
tab1, tab2, tab3 = st.tabs(["📁 Upload Document", "🔍 Analysis Results", "ℹ️ About"])

with tab1:
    st.markdown("### 📥 Upload Your Document")
    
    # Upload area with better styling
    with st.container():
        st.markdown('<div class="upload-area">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            " ",
            type=["pdf", "docx", "png", "jpg", "jpeg", "tiff"],
            help="Drag and drop or click to upload your document",
            label_visibility="collapsed"
        )
        st.markdown("""
        <div style="text-align: center; color: #666;">
            <p>📄 PDF • 📝 DOCX • 🖼️ PNG/JPG/TIFF</p>
            <p>Max file size: 10MB</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_file is not None:
        # File info card
        file_type_icons = {
            "application/pdf": "📄",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "📝",
            "image/png": "🖼️", "image/jpeg": "🖼️", "image/jpg": "🖼️", "image/tiff": "🖼️"
        }
        
        icon = file_type_icons.get(uploaded_file.type, "📁")
        
        st.markdown(f"""
        <div class="card">
            <h4>{icon} File Uploaded Successfully</h4>
            <p><strong>Filename:</strong> {uploaded_file.name}</p>
            <p><strong>Type:</strong> {uploaded_file.type}</p>
            <p><strong>Size:</strong> {uploaded_file.size / 1024:.1f} KB</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Process button
        if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
            start_time = time.time()
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Extract text
            with st.spinner("📖 Extracting text from document..."):
                status_text.text("Step 1/4: Extracting text...")
                extracted_text = extract_text_online(uploaded_file)
                progress_bar.progress(25)
                time.sleep(0.5)
            
            if extracted_text and not any(error in extracted_text for error in ["Error", "failed", "Unsupported"]):
                # Step 2: Summarize
                with st.spinner("🤖 Generating AI summary..."):
                    status_text.text("Step 2/4: Creating summary...")
                    summary = summarize_text_openai(extracted_text)
                    progress_bar.progress(50)
                    time.sleep(0.5)
                
                if summary and not summary.startswith("Error"):
                    # Step 3: Translate
                    with st.spinner("🌐 Translating content..."):
                        status_text.text("Step 3/4: Translating...")
                        translated = translate_text(summary, lang_code)
                        progress_bar.progress(75)
                        time.sleep(0.5)
                    
                    # Step 4: Audio generation
                    with st.spinner("🔊 Generating audio..."):
                        status_text.text("Step 4/4: Creating audio...")
                        audio_data = text_to_speech(translated, lang_code)
                        progress_bar.progress(100)
                        time.sleep(0.5)
                    
                    # Store results in session state
                    st.session_state.analysis_results = {
                        'extracted_text': extracted_text,
                        'summary': summary,
                        'translated': translated,
                        'audio_data': audio_data,
                        'language': selected_lang
                    }
                    
                    # Store file stats
                    st.session_state.file_stats = {
                        'type': uploaded_file.type,
                        'chars': len(extracted_text),
                        'time': time.time() - start_time
                    }
                    
                    status_text.text("✅ Analysis complete!")
                    st.success("Document analysis finished successfully!")
                    st.rerun()
                    
                else:
                    st.error("Summary generation failed")
            else:
                st.error("Text extraction failed")

with tab2:
    st.markdown("### 📊 Analysis Results")
    
    if 'analysis_results' in st.session_state:
        results = st.session_state.analysis_results
        
        # Results in cards
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📋 Extracted Text")
            with st.expander("View Full Text", expanded=False):
                st.text_area("", results['extracted_text'][:1500] + "..." 
                           if len(results['extracted_text']) > 1500 else results['extracted_text'], 
                           height=200)
        
        with col2:
            st.markdown("#### 🎯 AI Summary")
            st.markdown(f'<div class="card success-card">{results["translated"]}</div>', unsafe_allow_html=True)
            
            if results['audio_data']:
                st.markdown("#### 🔊 Audio Summary")
                st.audio(base64.b64decode(results['audio_data']), format="audio/mp3")
                st.download_button(
                    label="📥 Download Audio",
                    data=base64.b64decode(results['audio_data']),
                    file_name=f"summary_{lang_code}.mp3",
                    mime="audio/mp3",
                    use_container_width=True
                )
            else:
                st.info("Audio generation not available for this content")
    
    else:
        st.info("👆 Upload a document and click 'Start Analysis' to see results here")

with tab3:
    st.markdown("### ℹ️ About DocuMind AI")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-box">
            <h4>🎯 Our Mission</h4>
            <p>Make document analysis accessible and efficient for everyone</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-box">
            <h4>⚡ Technology Stack</h4>
            <p>• OpenAI GPT-3.5 Turbo<br>• OCR.space API<br>• LibreTranslate<br>• Google TTS</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-box">
            <h4>🛠️ How It Works</h4>
            <p>1. Upload document<br>2. AI extracts & analyzes<br>3. Get summary & audio</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-box">
            <h4>📞 Support</h4>
            <p>For issues or feature requests, contact our support team</p>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "Made with ❤️ using Streamlit • DocuMind AI v1.0"
    "</div>", 
    unsafe_allow_html=True
)
