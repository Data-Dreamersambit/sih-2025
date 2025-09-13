import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from datetime import datetime
import plotly.express as px
import os
from dotenv import load_dotenv
from gtts import gTTS
import tempfile

# Load .env file
load_dotenv()

# Get API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# Page configuration
st.set_page_config(
    page_title="🌾 फसल मुनाफा सलाहकार",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Indian-themed CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        font-weight: bold;
        color: #FF6B35;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .sub-header {
        color: #138808;
        text-align: center;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .crop-card {
        background: linear-gradient(135deg, #FFF8DC 0%, #F0E68C 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 5px solid #FF6B35;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        color: #2C3E50 !important;
    }
    .crop-card p {
        color: #2C3E50 !important;
        font-size: 1rem;
        margin: 0.5rem 0;
    }
    .crop-card strong {
        color: #8B4513 !important;
    }
    .crop-title {
        color: #8B4513;
        font-size: 1.4rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .profit-high { color: #228B22; font-weight: bold; }
    .profit-medium { color: #FF8C00; font-weight: bold; }
    .profit-low { color: #DC143C; font-weight: bold; }
    .input-container {
        background: linear-gradient(135deg, #FFE4B5 0%, #FFDAB9 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        border: 2px solid #FF6B35;
    }
    .recommendation-header {
        color: #8B4513;
        font-size: 1.8rem;
        font-weight: bold;
        text-align: center;
        margin: 1rem 0;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = None

def speak_text(text, lang="en"):
    """Convert text to speech and return audio file path"""
    try:
        tts = gTTS(text=text, lang=lang)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(temp_file.name)
        return temp_file.name
    except Exception as e:
        st.error(f"आवाज़ त्रुटि: {e}")
        return None
 

def setup_gemini_api():
    """Setup Gemini API configuration"""
    try:
        if not GEMINI_API_KEY:
            st.error("❌ Gemini API Key नहीं मिली। कृपया इसे अपनी .env फ़ाइल में सेट करें।")
            return None

        genai.configure(api_key=GEMINI_API_KEY)
        model_names = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                test_response = model.generate_content("Test")
                return model
            except:
                continue
        return None
    except Exception as e:
        st.error(f"Gemini सेटअप त्रुटि: {e}")
        return None


def get_crop_recommendations(model, month, location, budget, experience, farm_size, organic):
    """Get crop recommendations using Gemini API"""
    try:
        prompt = f"""
        आप एक भारतीय कृषि सलाहकार हैं। निम्नलिखित जानकारी के आधार पर, फसलों की सिफारिश करें:
        
        महीना: {month}
        स्थान: {location}
        बजट: ₹{budget}
        अनुभव: {experience}
        खेत का आकार: {farm_size}
        जैविक खेती: {'हाँ' if organic else 'नहीं'}
        
        कृपया JSON प्रारूप में उत्तर दें (सभी जानकारी हिंदी में):
        {{
            "recommendations": [
                {{
                    "crop_name": "फसल का नाम",
                    "profit_potential": "उच्च/मध्यम/कम",
                    "estimated_roi": "प्रतिशत में",
                    "investment_required": "राशि",
                    "growing_period": "महीनों में समय",
                    "key_benefits": ["लाभ1", "लाभ2", "लाभ3"],
                    "considerations": ["विचार1", "विचार2"],
                    "market_price_range": "बाजार दर"
                }}
            ],
            "general_advice": "सामान्य सलाह हिंदी में",
            "seasonal_notes": "मौसमी टिप्पणी हिंदी में"
        }}
        
        भारतीय मौसम पैटर्न, मिट्टी की स्थिति और बाजार की स्थिति के आधार पर 3-5 फसलों की सिफारिश करें।
        सभी जानकारी हिंदी में दें।
        """
        
        response = model.generate_content(prompt)
        response_text = response.text
        
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx != -1:
            json_str = response_text[start_idx:end_idx]
            return json.loads(json_str)
        else:
            return {
                "recommendations": [{
                    "crop_name": "स्थानीय विशेषज्ञ से सलाह लें",
                    "profit_potential": "परिवर्तनशील",
                    "estimated_roi": "विशेषज्ञ से संपर्क करें",
                    "investment_required": f"₹{budget} के भीतर",
                    "growing_period": "अलग-अलग",
                    "key_benefits": ["स्थानीय विश्लेषण आवश्यक"],
                    "considerations": ["कृषि विभाग से संपर्क करें"],
                    "market_price_range": "बाजार पर निर्भर"
                }],
                "general_advice": response_text[:300],
                "seasonal_notes": f"{location} में {month} के लिए स्थानीय मौसम पैटर्न देखें।"
            }
    except Exception as e:
        st.error(f"सिफारिशें प्राप्त करने में त्रुटि: {str(e)}")
        return None

def display_crop_card(crop_data, index):
    """Display crop recommendation card"""
    # Map profit potential to CSS class
    profit_mapping = {
        'उच्च': 'profit-high',
        'High': 'profit-high',
        'मध्यम': 'profit-medium',
        'Medium': 'profit-medium', 
        'कम': 'profit-low',
        'Low': 'profit-low'
    }
    profit_class = profit_mapping.get(crop_data['profit_potential'], 'profit-medium')
    
    st.markdown(f"""
    <div class="crop-card">
        <div class="crop-title">🌱 {crop_data['crop_name']}</div>
        <p><strong>उगाने की अवधि:</strong> {crop_data['growing_period']}</p>
        <p><strong>आवश्यक निवेश:</strong> {crop_data['investment_required']}</p>
        <p><strong>बाजार दर:</strong> {crop_data['market_price_range']}</p>
        <p><strong>मुनाफे की संभावना:</strong> <span class="{profit_class}">{crop_data['profit_potential']}</span></p>
        <p><strong>ROI:</strong> {crop_data['estimated_roi']}</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">🌾 फसल मुनाफा सलाहकार</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">भारतीय किसानों के लिए AI-आधारित फसल सिफारिश सिस्टम</p>', unsafe_allow_html=True)
    
    # Input Section
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        months = ['जनवरी', 'फरवरी', 'मार्च', 'अप्रैल', 'मई', 'जून',
                 'जुलाई', 'अगस्त', 'सितंबर', 'अक्टूबर', 'नवंबर', 'दिसंबर']
        selected_month = st.selectbox("📅 महीना", months, index=datetime.now().month - 1)
        
        location = st.text_input("📍 स्थान", placeholder="जैसे: पंजाब, भारत या महाराष्ट्र")
    
    with col2:
        budget = st.number_input("💰 बजट (₹)", min_value=1000, max_value=10000000, value=50000, step=5000)
        
        experience = st.selectbox("अनुभव स्तर", ["नया किसान", "मध्यम", "अनुभवी किसान"])
        
        farm_size = st.selectbox("खेत का आकार", ["छोटा (5 एकड़ से कम)", "मध्यम (5-50 एकड़)", "बड़ा (50+ एकड़)"])
        
        organic = st.checkbox("जैविक खेती पसंद करें")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Get Recommendations Button
    if st.button("🚀 फसल सिफारिशें प्राप्त करें", type="primary", use_container_width=True):
        if not location.strip():
            st.error("कृपया अपना स्थान दर्ज करें")
            return
        
        model = setup_gemini_api()
        if not model:
            st.error("Gemini API कनेक्शन समस्या। कृपया अपना इंटरनेट कनेक्शन जांचें।")
            return
        
        with st.spinner("🤖 बाजार की स्थिति का विश्लेषण और सिफारिशें तैयार कर रहा हूं..."):
            recommendations = get_crop_recommendations(model, selected_month, location, budget, 
                                                     experience, farm_size, organic)
            
            if recommendations:
                st.session_state.recommendations = recommendations
                st.success("✅ सिफारिशें सफलतापूर्वक तैयार हो गईं!")
            else:
                st.error("❌ सिफारिशें तैयार करने में असफल। कृपया पुनः प्रयास करें।")
    
    # Display Recommendations
    if st.session_state.recommendations:
        recommendations = st.session_state.recommendations
        
        # Summary Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📅 महीना", selected_month)
        with col2:
            st.metric("📍 स्थान", location)
        with col3:
            st.metric("💰 बजट", f"₹{budget:,}")
        with col4:
            st.metric("🌱 सिफारिशें", len(recommendations['recommendations']))
        
        # Recommendations
        st.markdown('<h2 class="recommendation-header">🎯 सुझाई गई फसलें</h2>', unsafe_allow_html=True)
        
        for i, crop in enumerate(recommendations['recommendations']):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                display_crop_card(crop, i)
            
            with col2:
                st.markdown(f"### #{i+1}")
                with st.expander("📝 विवरण"):
                    st.markdown("**🎯 मुख्य लाभ:**")
                    for benefit in crop['key_benefits']:
                        st.write(f"• {benefit}")
                    
                    st.markdown("**⚠️ विचारणीय बातें:**")
                    for consideration in crop['considerations']:
                        st.write(f"• {consideration}")
        
        # Analysis Tab
        if len(recommendations['recommendations']) > 1:
            st.subheader("📊 मुनाफा विश्लेषण")
            
            crop_names = [crop['crop_name'] for crop in recommendations['recommendations']]
            profit_levels = [crop['profit_potential'] for crop in recommendations['recommendations']]
            
            profit_numeric = []
            for level in profit_levels:
                if level in ['उच्च', 'High']:
                    profit_numeric.append(3)
                elif level in ['मध्यम', 'Medium']:
                    profit_numeric.append(2)
                else:
                    profit_numeric.append(1)
            
            fig = px.bar(x=crop_names, y=profit_numeric, title="मुनाफे की तुलना",
                        labels={'x': 'फसलें', 'y': 'मुनाफे का स्तर'},
                        color=profit_numeric, color_continuous_scale='Oranges')
            
            fig.update_layout(showlegend=False,
                            yaxis=dict(tickmode='array', tickvals=[1, 2, 3], 
                                     ticktext=['कम', 'मध्यम', 'उच्च']))
            st.plotly_chart(fig, use_container_width=True)
        
        # Advice Section
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🌾 सामान्य सलाह")
            st.info(recommendations['general_advice'])
        
        with col2:
            st.markdown("#### 📅 मौसमी टिप्पणी")
            st.warning(recommendations['seasonal_notes'])

        # 👉 Voice Feature
        st.markdown("### 🔊 सिफारिशें सुनें")
        speech_text = (
            "यहाँ आपकी फसल सिफारिशें हैं। "
            + " , ".join([crop['crop_name'] for crop in recommendations['recommendations']])
            + ". सामान्य सलाह: " + recommendations['general_advice']
            + ". मौसमी टिप्पणी: " + recommendations['seasonal_notes']
        )
        
        audio_path = speak_text(speech_text, lang="hi")
        if audio_path:
            st.audio(audio_path, format="audio/mp3")
        
        # Additional Tips
        st.markdown("#### 📚 अतिरिक्त सुझाव")
        tips = [
            "🔍 अंतिम निर्णय लेने से पहले स्थानीय बाजार की कीमतें जांचें",
            "🌡️ अपनी चुनी गई फसलों पर जलवायु परिवर्तन के प्रभावों पर विचार करें",
            "💧 पानी की उपलब्धता और सिंचाई की लागत का मूल्यांकन करें",
            "🚜 मशीनरी और श्रम की लागत का हिसाब रखें",
            "📈 जोखिम कम करने के लिए अपनी फसलों में विविधता लाएं"
        ]
        
        for tip in tips:
            st.write(tip)
    
    else:
        # Welcome Section
        st.markdown("""
        ## 🌟 फसल मुनाफा सलाहकार में आपका स्वागत है!
        
        यह AI-आधारित एप्लिकेशन भारतीय किसानों को सही फसल चुनने में मदद करता है:
        
        - **🗓️ मौसमी समय:** अधिकतम उत्पादन के लिए सही समय
        - **🌍 स्थान-विशिष्ट:** आपके क्षेत्र की जलवायु और मिट्टी के अनुसार
        - **💰 बजट अनुकूल:** निवेश और ROI का विश्लेषण
        - **📊 बाजार बुद्धि:** वर्तमान मूल्य रुझान और मांग पूर्वानुमान
        
        ### 🚀 शुरुआत कैसे करें:
        1. अपना स्थान और पसंदीदा महीना दर्ज करें
        2. अपनी उपलब्ध बजट और खेत की जानकारी दें
        3. व्यक्तिगत सुझाव प्राप्त करने के लिए बटन दबाएं
        
        *अपने कृषि मुनाफे को अधिकतम करने के लिए तैयार हैं? चलिए शुरू करते हैं! 🌾*
        """)

if __name__ == "__main__":
    main()