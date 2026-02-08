# ocr_app.py
# OCR Streamlit Web Application
# Run with: streamlit run ocr_app.py

import streamlit as st
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import re
from collections import Counter
import io
import platform
if platform.system() == 'Windows':
    pytesseract.pytesseract.tesseract_cmd = r"C:\Users\Samee\Tesseract-OCR\tesseract.exe"
else:
    # On Linux (Streamlit Cloud), tesseract is in PATH
    pass
# Configure page
st.set_page_config(
    page_title="OCR Text Extractor",
    page_icon="📄",
    layout="wide"
)

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\Samee\Tesseract-OCR\tesseract.exe"

# Title
st.title("📄 OCR - Image to Text Converter")
st.markdown("*Extract text from images and scanned documents using AI*")

# Sidebar
st.sidebar.header("⚙️ Settings")
preprocess_option = st.sidebar.selectbox(
    "Preprocessing Method",
    ["Grayscale (Recommended)", "No Preprocessing", "Full Preprocessing"]
)
language = st.sidebar.selectbox("Language", ["eng", "eng+fra", "eng+deu", "eng+spa"])

# Functions
def extract_text_from_image(img, preprocess_method="Grayscale (Recommended)"):
    """Extract text from image"""
    try:
        # Apply preprocessing based on selection
        if preprocess_method == "Grayscale (Recommended)":
            img = img.convert('L')
        elif preprocess_method == "Full Preprocessing":
            img = img.convert('L')
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(2.0)
            img = img.point(lambda p: 255 if p > 128 else 0)
            img = img.filter(ImageFilter.MedianFilter(size=3))
        
        # Extract text
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(img, config=custom_config)
        
        # Get confidence
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'text': text,
            'word_count': len(text.split()),
            'line_count': len([line for line in text.split('\n') if line.strip()]),
            'char_count': len(text),
            'avg_confidence': avg_confidence
        }
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def analyze_text(text):
    """Analyze extracted text"""
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    word_freq = Counter(words)
    
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    phones = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)
    dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', text)
    amounts = re.findall(r'\$\d+(?:,\d{3})*(?:\.\d{2})?', text)
    
    return {
        'word_freq': word_freq,
        'emails': emails,
        'phones': phones,
        'dates': dates,
        'amounts': amounts
    }

# Main app
st.markdown("---")

# File uploader
uploaded_file = st.file_uploader(
    "📤 Upload an image",
    type=['png', 'jpg', 'jpeg', 'tiff', 'bmp'],
    help="Upload an image containing text"
)

if uploaded_file is not None:
    # Display image
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📷 Uploaded Image")
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True)
    
    with col2:
        st.subheader("⚙️ Processing Options")
        st.info(f"Method: {preprocess_option}")
        st.info(f"Language: {language}")
        
        extract_button = st.button("🚀 Extract Text", type="primary", use_container_width=True)
    
    # Extract text when button is clicked
    if extract_button:
        with st.spinner("🔄 Extracting text..."):
            result = extract_text_from_image(image, preprocess_option)
            
            if result:
                st.session_state['result'] = result
                st.session_state['image'] = image
                st.success("✅ Text extraction complete!")

# Display results if available
if 'result' in st.session_state:
    result = st.session_state['result']
    
    st.markdown("---")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Words", result['word_count'])
    col2.metric("Lines", result['line_count'])
    col3.metric("Characters", result['char_count'])
    
    confidence_color = "🟢" if result['avg_confidence'] > 70 else "🟡" if result['avg_confidence'] > 50 else "🔴"
    col4.metric("Confidence", f"{confidence_color} {result['avg_confidence']:.1f}%")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📝 Extracted Text", "📊 Analysis", "📥 Export"])
    
    with tab1:
        st.subheader("Extracted Text")
        extracted_text = st.text_area(
            "Edit if needed:",
            value=result['text'],
            height=400,
            key="text_area"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Copy Text"):
                st.code(extracted_text)
                st.info("Select and copy the text above")
    
    with tab2:
        st.subheader("Text Analysis")
        
        analysis = analyze_text(result['text'])
        
        # Entities
        st.markdown("### 🔍 Detected Entities")
        col1, col2 = st.columns(2)
        
        with col1:
            if analysis['emails']:
                st.markdown("**📧 Emails:**")
                for email in analysis['emails']:
                    st.code(email)
            else:
                st.info("No emails detected")
            
            if analysis['dates']:
                st.markdown("**📅 Dates:**")
                for date in analysis['dates']:
                    st.code(date)
            else:
                st.info("No dates detected")
        
        with col2:
            if analysis['phones']:
                st.markdown("**📱 Phone Numbers:**")
                for phone in analysis['phones']:
                    st.code(phone)
            else:
                st.info("No phone numbers detected")
            
            if analysis['amounts']:
                st.markdown("**💰 Dollar Amounts:**")
                for amount in analysis['amounts']:
                    st.code(amount)
            else:
                st.info("No amounts detected")
        
        # Word frequency chart
        if analysis['word_freq']:
            st.markdown("### 📊 Most Common Words")
            top_words = analysis['word_freq'].most_common(10)
            if top_words:
                words, counts = zip(*top_words)
                
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.barh(words, counts, color='skyblue')
                ax.set_xlabel('Frequency')
                ax.set_title('Top 10 Most Common Words')
                ax.invert_yaxis()
                st.pyplot(fig)
    
    with tab3:
        st.subheader("Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 📄 Plain Text")
            st.download_button(
                label="📥 Download TXT",
                data=result['text'],
                file_name=f"extracted_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        
        with col2:
            st.markdown("### 📊 CSV")
            if analysis['emails'] or analysis['phones'] or analysis['dates']:
                entities_df = pd.DataFrame({
                    'Type': ['Email']*len(analysis['emails']) + 
                            ['Phone']*len(analysis['phones']) + 
                            ['Date']*len(analysis['dates']),
                    'Value': analysis['emails'] + analysis['phones'] + analysis['dates']
                })
                
                csv = entities_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"entities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No entities to export")
        
        with col3:
            st.markdown("### 📋 JSON")
            import json
            json_data = {
                'text': result['text'],
                'statistics': {
                    'word_count': result['word_count'],
                    'line_count': result['line_count'],
                    'char_count': result['char_count'],
                    'confidence': result['avg_confidence']
                },
                'entities': {
                    'emails': analysis['emails'],
                    'phones': analysis['phones'],
                    'dates': analysis['dates'],
                    'amounts': analysis['amounts']
                }
            }
            
            st.download_button(
                label="📥 Download JSON",
                data=json.dumps(json_data, indent=2),
                file_name=f"ocr_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

else:
    st.info("👆 Upload an image to get started!")

# Sidebar info
st.sidebar.markdown("---")
st.sidebar.markdown("""
### 📖 How to Use
1. Upload an image
2. Choose preprocessing method
3. Click 'Extract Text'
4. View results and export

### 🎯 Tips
- Use Grayscale for screenshots
- Full Preprocessing for scans
- Higher resolution = better accuracy
""")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Built with Streamlit & Tesseract OCR</p>
</div>

""", unsafe_allow_html=True)
