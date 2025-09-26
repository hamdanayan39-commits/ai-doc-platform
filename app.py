import base64
import requests
import streamlit as st
from io import BytesIO
import PyPDF2
import docx
from PIL import Image

# API Keys from Streamlit Secrets
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    OCR_API_KEY = st.secrets["OCR_API_KEY"]
except:
    st.error("❌ API keys not found. Please configure secrets.toml")
    OPENAI_API_KEY = ""
    OCR_API_KEY = ""

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
                {"role": "system", "content": "You are a helpful assistant that creates concise summaries."},
                {"role": "user", "content": f"Please provide a clear and concise summary of this text:\n\n{text}"}
            ],
            "max_tokens": 200,
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

# Streamlit UI
st.set_page_config(page_title="Document Analyzer", page_icon="📄", layout="wide")
st.title("📄 AI Document Analyzer with Audio Output")

# Language selection
lang_options = {"English": "en", "Hindi": "hi", "Malayalam": "ml", "Arabic": "ar", "French": "fr"}
selected_lang = st.selectbox("Select Output Language", list(lang_options.keys()))
lang_code = lang_options[selected_lang]

# File upload with supported types
uploaded_file = st.file_uploader(
    "Upload Document (PDF, DOCX, PNG, JPG, JPEG, TIFF)", 
    type=["pdf", "docx", "png", "jpg", "jpeg", "tiff"]
)

if uploaded_file is not None:
    # Display file info
    file_type = uploaded_file.type
    st.info(f"📁 **File:** {uploaded_file.name} | **Type:** {file_type} | **Size:** {uploaded_file.size / 1024:.1f} KB")
    
    # Progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Step 1: Extract text based on file type
    status_text.text("📖 Extracting text from document...")
    extracted_text = extract_text_online(uploaded_file)
    progress_bar.progress(25)
    
    if extracted_text and not any(error in extracted_text for error in ["Error", "failed", "Unsupported"]):
        # Show extracted text preview
        with st.expander("📋 View Extracted Text (Click to expand)"):
            preview_text = extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text
            st.text_area("", preview_text, height=200)
            st.write(f"**Total characters extracted:** {len(extracted_text)}")
        
        # Step 2: Summarize
        status_text.text("🤖 Generating AI summary...")
        summary = summarize_text_openai(extracted_text)
        progress_bar.progress(50)
        
        if summary and not summary.startswith("Error"):
            # Step 3: Translate
            status_text.text("🌐 Translating summary...")
            translated = translate_text(summary, lang_code)
            progress_bar.progress(75)
            
            st.subheader("📝 AI Summary")
            st.success(translated)
            
            # Step 4: Audio
            status_text.text("🔊 Generating audio...")
            audio_data = text_to_speech(translated, lang_code)
            progress_bar.progress(100)
            status_text.text("✅ Processing complete!")
            
            if audio_data:
                st.subheader("🎧 Audio Summary")
                st.audio(base64.b64decode(audio_data), format="audio/mp3")
                
                # Download button for audio
                st.download_button(
                    label="📥 Download Audio",
                    data=base64.b64decode(audio_data),
                    file_name=f"summary_{lang_code}.mp3",
                    mime="audio/mp3"
                )
            else:
                st.info("🔇 Audio generation not available for this text")
                
        else:
            st.error("❌ Summary generation failed")
            if summary:
                st.info(f"**Error details:** {summary}")
    else:
        st.error("❌ Text extraction failed")
        if extracted_text:
            st.info(f"**Error details:** {extracted_text}")

else:
    # Welcome message
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("👆 **Upload a document to get started!**")
        st.markdown("""
        **Supported file types:**
        - 📄 **PDF** documents (text-based)
        - 📝 **DOCX** Word documents  
        - 🖼️ **Images** (PNG, JPG, JPEG, TIFF) with text
        
        **How it works:**
        1. Upload your document
        2. Text is automatically extracted
        3. AI generates a concise summary
        4. Listen to the summary in your preferred language
        """)

# Footer
st.markdown("---")
st.caption("Made with Streamlit • Supports PDF, DOCX, and image files")
