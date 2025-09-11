import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from datetime import datetime
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="🌾 ଫସଲ ଲାଭ ସଲାହକାର",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Odia-themed CSS
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
    .profit-high { color: #228B22 !important; font-weight: bold; }
    .profit-medium { color: #FF8C00 !important; font-weight: bold; }
    .profit-low { color: #DC143C !important; font-weight: bold; }
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

# Embedded API Key
GEMINI_API_KEY = "AIzaSyDnxrqmQWtSi9f8nYAFIOl7FYDOkfYwKOE"

def setup_gemini_api():
    """Setup Gemini API configuration"""
    try:
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
    except:
        return None

def get_crop_recommendations(model, month, location, budget, experience, farm_size, organic):
    """Get crop recommendations using Gemini API"""
    try:
        prompt = f"""
        ଆପଣ ଜଣେ ଭାରତୀୟ କୃଷି ପରାମର୍ଶଦାତା | ନିମ୍ନଲିଖିତ ତଥ୍ୟ ଆଧାରରେ ଫସଲ ସୁପାରିଶ କରନ୍ତୁ:
        
        ମାସ: {month}
        ସ୍ଥାନ: {location}
        ବଜେଟ୍: ₹{budget}
        ଅନୁଭବ: {experience}
        ଜମି ଆକାର: {farm_size}
        ଜୈବିକ ଚାଷ: {'ହଁ' if organic else 'ନା'}
        
        JSON format ରେ ଉତ୍ତର ଦିଅନ୍ତୁ:
        {{
            "recommendations": [
                {{
                    "crop_name": "ଫସଲର ନାମ",
                    "profit_potential": "High/Medium/Low",
                    "estimated_roi": "ପ୍ରତିଶତ",
                    "investment_required": "ପରିମାଣ",
                    "growing_period": "ମାସରେ ସମୟ",
                    "key_benefits": ["ଲାଭ1", "ଲାଭ2", "ଲାଭ3"],
                    "considerations": ["ସତର୍କତା1", "ସତର୍କତା2"],
                    "market_price_range": "ବଜାର ଦର"
                }}
            ],
            "general_advice": "ସାଧାରଣ ପରାମର୍ଶ",
            "seasonal_notes": "ଋତୁଗତ ନୋଟ୍ସ"
        }}
        
        ଭାରତୀୟ ଋତୁ, ମାଟି ଏବଂ ବଜାର ଅବସ୍ଥା ଅନୁସାରେ 3-5 ଟି ଫସଲର ସୁପାରିଶ କରନ୍ତୁ |
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
                    "crop_name": "ସ୍ଥାନୀୟ ପରାମର୍ଶ ନିଅନ୍ତୁ",
                    "profit_potential": "Variable",
                    "estimated_roi": "ବିଶେଷଜ୍ଞଙ୍କ ସହ ଯୋଗାଯୋଗ କରନ୍ତୁ",
                    "investment_required": f"₹{budget} ମଧ୍ୟରେ",
                    "growing_period": "ବିଭିନ୍ନ",
                    "key_benefits": ["ସ୍ଥାନୀୟ ବିଶ୍ଳେଷଣ ଆବଶ୍ୟକ"],
                    "considerations": ["କୃଷି ବିଭାଗ ସହ ଯୋଗାଯୋଗ କରନ୍ତୁ"],
                    "market_price_range": "ବଜାର ଉପରେ ନିର୍ଭରଶୀଳ"
                }],
                "general_advice": response_text[:300],
                "seasonal_notes": f"{month} ରେ {location} ପାଇଁ ସ୍ଥାନୀୟ ଋତୁ pattern ଦେଖନ୍ତୁ |"
            }
    except Exception as e:
        st.error(f"ସୁପାରିଶ ପାଇବାରେ ସମସ୍ୟା: {str(e)}")
        return None

def display_crop_card(crop_data, index):
    """Display crop recommendation card"""
    # Map profit potential to CSS class
    profit_mapping = {
        'High': 'profit-high',
        'Medium': 'profit-medium', 
        'Low': 'profit-low'
    }
    profit_class = profit_mapping.get(crop_data['profit_potential'], 'profit-medium')
    
    st.markdown(f"""
    <div class="crop-card">
        <div class="crop-title">🌱 {crop_data['crop_name']}</div>
        <p><strong>ବୃଦ୍ଧିର ସମୟ:</strong> {crop_data['growing_period']}</p>
        <p><strong>ନିବେଶ ଆବଶ୍ୟକ:</strong> {crop_data['investment_required']}</p>
        <p><strong>ବଜାର ଦର:</strong> {crop_data['market_price_range']}</p>
        <p><strong>ଲାଭ ସମ୍ଭାବନା:</strong> <span class="{profit_class}">{crop_data['profit_potential']}</span></p>
        <p><strong>ROI:</strong> {crop_data['estimated_roi']}</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">🌾 ଫସଲ ଲାଭ ସଲାହକାର</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">ଓଡ଼ିଆ କୃଷକଙ୍କ ପାଇଁ AI-ଆଧାରିତ ଫସଲ ସୁପାରିଶ ସିଷ୍ଟମ</p>', unsafe_allow_html=True)
    
    # Input Section
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        months = ['ଜାନୁଆରୀ', 'ଫେବୃଆରୀ', 'ମାର୍ଚ୍ଚ', 'ଏପ୍ରିଲ୍', 'ମଇ', 'ଜୁନ୍',
                 'ଜୁଲାଇ', 'ଅଗଷ୍ଟ', 'ସେପ୍ଟେମ୍ବର', 'ଅକ୍ଟୋବର', 'ନଭେମ୍ବର', 'ଡିସେମ୍ବର']
        selected_month = st.selectbox("📅 ମାସ", months, index=datetime.now().month - 1)
        
        location = st.text_input("📍 ସ୍ଥାନ", placeholder="ଯେପରି: ଓଡ଼ିଶା, ଭାରତ କିମ୍ବା କଟକ")
    
    with col2:
        budget = st.number_input("💰 ବଜେଟ୍ (₹)", min_value=1000, max_value=10000000, value=50000, step=5000)
        
        experience = st.selectbox("ଅନୁଭବ ସ୍ତର", ["ନୂଆ କୃଷକ", "ମଧ୍ୟମ ଅନୁଭବ", "ଅନୁଭବୀ କୃଷକ"])
        
        farm_size = st.selectbox("ଜମି ଆକାର", ["ଛୋଟ (5 ଏକର କମ୍)", "ମଧ୍ୟମ (5-50 ଏକର)", "ବଡ଼ (50+ ଏକର)"])
        
        organic = st.checkbox("ଜୈବିକ ଚାଷକୁ ପ୍ରାଧାନ୍ୟ")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Get Recommendations Button
    if st.button("🚀 ଫସଲ ସୁପାରିଶ ପାଆନ୍ତୁ", type="primary", use_container_width=True):
        if not location.strip():
            st.error("ଦୟାକରି ସ୍ଥାନ ଦିଅନ୍ତୁ")
            return
        
        model = setup_gemini_api()
        if not model:
            st.error("Gemini API ସଂଯୋଗରେ ସମସ୍ୟା | ଦୟାକରି ଆପଣଙ୍କର ଇଣ୍ଟରନେଟ୍ ସଂଯୋଗ ଯାଞ୍ଚ କରନ୍ତୁ |")
            return
        
        with st.spinner("🤖 ବଜାର ଅବସ୍ଥାର ବିଶ୍ଳେଷଣ ଏବଂ ସୁପାରିଶ ପ୍ରସ୍ତୁତ କରାଯାଉଛି..."):
            recommendations = get_crop_recommendations(model, selected_month, location, budget, 
                                                     experience, farm_size, organic)
            
            if recommendations:
                st.session_state.recommendations = recommendations
                st.success("✅ ସୁପାରିଶଗୁଡ଼ିକ ସଫଳତାର ସହ ପ୍ରସ୍ତୁତ କରାଯାଇଛି!")
            else:
                st.error("❌ ସୁପାରିଶ ପ୍ରସ୍ତୁତ କରିବାରେ ବିଫଳ | ଦୟାକରି ପୁନଃ ଚେଷ୍ଟା କରନ୍ତୁ |")
    
    # Display Recommendations
    if st.session_state.recommendations:
        recommendations = st.session_state.recommendations
        
        # Summary Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📅 ମାସ", selected_month)
        with col2:
            st.metric("📍 ସ୍ଥାନ", location)
        with col3:
            st.metric("💰 ବଜେଟ୍", f"₹{budget:,}")
        with col4:
            st.metric("🌱 ସୁପାରିଶ", len(recommendations['recommendations']))
        
        # Recommendations
        st.markdown('<h2 class="recommendation-header">🎯 ସୁପାରିଶିତ ଫସଲଗୁଡ଼ିକ</h2>', unsafe_allow_html=True)
        
        for i, crop in enumerate(recommendations['recommendations']):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                display_crop_card(crop, i)
            
            with col2:
                st.markdown(f"### #{i+1}")
                with st.expander("📝 ବିସ୍ତାର ସହିତ"):
                    st.markdown("**🎯 ମୁଖ୍ୟ ଲାଭଗୁଡ଼ିକ:**")
                    for benefit in crop['key_benefits']:
                        st.write(f"• {benefit}")
                    
                    st.markdown("**⚠️ ସତର୍କତାଗୁଡ଼ିକ:**")
                    for consideration in crop['considerations']:
                        st.write(f"• {consideration}")
        
        # Analysis Tab
        if len(recommendations['recommendations']) > 1:
            st.subheader("📊 ଲାଭ ବିଶ୍ଳେଷଣ")
            
            crop_names = [crop['crop_name'] for crop in recommendations['recommendations']]
            profit_levels = [crop['profit_potential'] for crop in recommendations['recommendations']]
            
            profit_numeric = []
            for level in profit_levels:
                if level == 'High':
                    profit_numeric.append(3)
                elif level == 'Medium':
                    profit_numeric.append(2)
                else:
                    profit_numeric.append(1)
            
            fig = px.bar(x=crop_names, y=profit_numeric, title="ଲାଭ ତୁଳନା",
                        labels={'x': 'ଫସଲଗୁଡ଼ିକ', 'y': 'ଲାଭ ସ୍ତର'},
                        color=profit_numeric, color_continuous_scale='Oranges')
            
            fig.update_layout(showlegend=False,
                            yaxis=dict(tickmode='array', tickvals=[1, 2, 3], 
                                     ticktext=['କମ୍', 'ମଧ୍ୟମ', 'ଉଚ୍ଚ']))
            st.plotly_chart(fig, use_container_width=True)
        
        # Advice Section
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🌾 ସାଧାରଣ ପରାମର୍ଶ")
            st.info(recommendations['general_advice'])
        
        with col2:
            st.markdown("#### 📅 ଋତୁଗତ ନୋଟ୍ସ")
            st.warning(recommendations['seasonal_notes'])
        
        # Additional Tips
        st.markdown("#### 📚 ଅତିରିକ୍ତ ସୁଝାବ")
        tips = [
            "🔍 ଶେଷ ନିଷ୍ପତ୍ତି ପୂର୍ବରୁ ସ୍ଥାନୀୟ ବଜାର ମୂଲ୍ୟ ଯାଞ୍ଚ କରନ୍ତୁ",
            "🌡️ ଜଳବାୟୁ ପରିବର୍ତ୍ତନର ପ୍ରଭାବ ଉପରେ ବିଚାର କରନ୍ତୁ",
            "💧 ପାଣି ଉପଲବ୍ଧତା ଏବଂ ଜଳସେଚନ ଖର୍ଚ୍ଚର ମୂଲ୍ୟାଙ୍କନ କରନ୍ତୁ",
            "🚜 ଯନ୍ତ୍ରପାତି ଏବଂ ଶ୍ରମ ଖର୍ଚ୍ଚର ହିସାବ ରଖନ୍ତୁ",
            "📈 ଝୁଙ୍କି କମାଇବା ପାଇଁ ଫସଲରେ ବିବିଧତା ଆଣନ୍ତୁ"
        ]
        
        for tip in tips:
            st.write(tip)
    
    else:
        # Welcome Section
        st.markdown("""
        ## 🌟 ଫସଲ ଲାଭ ସଲାହକାରରେ ଆପଣଙ୍କର ସ୍ୱାଗତ!
        
        ଏହି AI-ଆଧାରିତ ଏପ୍ଲିକେସନ୍ ଓଡ଼ିଆ କୃଷକଙ୍କୁ ସଠିକ ଫସଲ ବାଛିବାରେ ସାହାଯ୍ୟ କରେ:
        
        - **🗓️ ଋତୁଗତ ସମୟ:** ଅଧିକତମ ଉତ୍ପାଦନ ପାଇଁ ସଠିକ ସମୟ
        - **🌍 ସ୍ଥାନ-ନିର୍ଦ୍ଦିଷ୍ଟ:** ଆପଣଙ୍କ ଅଞ୍ଚଳର ଜଳବାୟୁ ଏବଂ ମାଟି ଅନୁସାରେ
        - **💰 ବଜେଟ୍ ଅନୁକୂଳ:** ନିବେଶ ଏବଂ ROI ର ବିଶ୍ଳେଷଣ
        - **📊 ବଜାର ବୁଦ୍ଧି:** ବର୍ତ୍ତମାନର ମୂଲ୍ୟ ଧାରା ଏବଂ ମାଗ ପୂର୍ବାନୁମାନ
        
        ### 🚀 କିପରି ଆରମ୍ଭ କରିବେ:
        1. ଆପଣଙ୍କର ସ୍ଥାନ ଏବଂ ପସନ୍ଦର ମାସ ଦିଅନ୍ତୁ
        2. ଆପଣଙ୍କର ଉପଲବ୍ଧ ବଜେଟ୍ ଏବଂ ଜମିର ବିବରଣୀ କୁହନ୍ତୁ
        3. ବ୍ୟକ୍ତିଗତ ସୁଝାବ ପାଇବା ପାଇଁ ବଟନ୍ ଦବାନ୍ତୁ
        
        *ଆପଣଙ୍କର କୃଷି ଲାଭକୁ ଅଧିକତମ କରିବା ପାଇଁ ପ୍ରସ୍ତୁତ? ଚାଲନ୍ତୁ ଆରମ୍ଭ କରିବା! 🌾*
        """)

if __name__ == "__main__":
    main()