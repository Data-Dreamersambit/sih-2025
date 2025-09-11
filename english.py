import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from datetime import datetime
import plotly.express as px
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# Page configuration
st.set_page_config(
    page_title="🌾 Crop Profit Advisor",
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

 

def setup_gemini_api():
    """Setup Gemini API configuration"""
    try:
        if not GEMINI_API_KEY:
            st.error("❌ Gemini API Key not found. Please set it in your .env file.")
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
        st.error(f"Gemini setup error: {e}")
        return None


def get_crop_recommendations(model, month, location, budget, experience, farm_size, organic):
    """Get crop recommendations using Gemini API"""
    try:
        prompt = f"""
        You are an Indian agriculture consultant. Based on the following information, recommend crops:
        
        Month: {month}
        Location: {location}
        Budget: ₹{budget}
        Experience: {experience}
        Farm Size: {farm_size}
        Organic Farming: {'Yes' if organic else 'No'}
        
        Respond in JSON format:
        {{
            "recommendations": [
                {{
                    "crop_name": "Crop Name",
                    "profit_potential": "High/Medium/Low",
                    "estimated_roi": "percentage",
                    "investment_required": "amount",
                    "growing_period": "time in months",
                    "key_benefits": ["benefit1", "benefit2", "benefit3"],
                    "considerations": ["consideration1", "consideration2"],
                    "market_price_range": "market rate"
                }}
            ],
            "general_advice": "General advice",
            "seasonal_notes": "Seasonal notes"
        }}
        
        Recommend 3-5 crops based on Indian weather patterns, soil conditions, and market conditions.
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
                    "crop_name": "Consult Local Expert",
                    "profit_potential": "Variable",
                    "estimated_roi": "Contact specialist",
                    "investment_required": f"Within ₹{budget}",
                    "growing_period": "Varies",
                    "key_benefits": ["Local analysis required"],
                    "considerations": ["Contact agriculture department"],
                    "market_price_range": "Market dependent"
                }],
                "general_advice": response_text[:300],
                "seasonal_notes": f"For {location} in {month}, check local weather patterns."
            }
    except Exception as e:
        st.error(f"Error getting recommendations: {str(e)}")
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
        <p><strong>Growing Period:</strong> {crop_data['growing_period']}</p>
        <p><strong>Investment Required:</strong> {crop_data['investment_required']}</p>
        <p><strong>Market Rate:</strong> {crop_data['market_price_range']}</p>
        <p><strong>Profit Potential:</strong> <span class="{profit_class}">{crop_data['profit_potential']}</span></p>
        <p><strong>ROI:</strong> {crop_data['estimated_roi']}</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">🌾 Crop Profit Advisor</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-powered Crop Recommendation System for Indian Farmers</p>', unsafe_allow_html=True)
    
    # Input Section
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        months = ['January', 'February', 'March', 'April', 'May', 'June',
                 'July', 'August', 'September', 'October', 'November', 'December']
        selected_month = st.selectbox("📅 Month", months, index=datetime.now().month - 1)
        
        location = st.text_input("📍 Location", placeholder="e.g., Punjab, India or Maharashtra")
    
    with col2:
        budget = st.number_input("💰 Budget (₹)", min_value=1000, max_value=10000000, value=50000, step=5000)
        
        experience = st.selectbox("Experience Level", ["New Farmer", "Intermediate", "Experienced Farmer"])
        
        farm_size = st.selectbox("Farm Size", ["Small (Less than 5 acres)", "Medium (5-50 acres)", "Large (50+ acres)"])
        
        organic = st.checkbox("Prefer Organic Farming")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Get Recommendations Button
    if st.button("🚀 Get Crop Recommendations", type="primary", use_container_width=True):
        if not location.strip():
            st.error("Please enter your location")
            return
        
        model = setup_gemini_api()
        if not model:
            st.error("Gemini API connection issue. Please check your internet connection.")
            return
        
        with st.spinner("🤖 Analyzing market conditions and preparing recommendations..."):
            recommendations = get_crop_recommendations(model, selected_month, location, budget, 
                                                     experience, farm_size, organic)
            
            if recommendations:
                st.session_state.recommendations = recommendations
                st.success("✅ Recommendations generated successfully!")
            else:
                st.error("❌ Failed to generate recommendations. Please try again.")
    
    # Display Recommendations
    if st.session_state.recommendations:
        recommendations = st.session_state.recommendations
        
        # Summary Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📅 Month", selected_month)
        with col2:
            st.metric("📍 Location", location)
        with col3:
            st.metric("💰 Budget", f"₹{budget:,}")
        with col4:
            st.metric("🌱 Recommendations", len(recommendations['recommendations']))
        
        # Recommendations
        st.markdown('<h2 class="recommendation-header">🎯 Recommended Crops</h2>', unsafe_allow_html=True)
        
        for i, crop in enumerate(recommendations['recommendations']):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                display_crop_card(crop, i)
            
            with col2:
                st.markdown(f"### #{i+1}")
                with st.expander("📝 Details"):
                    st.markdown("**🎯 Key Benefits:**")
                    for benefit in crop['key_benefits']:
                        st.write(f"• {benefit}")
                    
                    st.markdown("**⚠️ Considerations:**")
                    for consideration in crop['considerations']:
                        st.write(f"• {consideration}")
        
        # Analysis Tab
        if len(recommendations['recommendations']) > 1:
            st.subheader("📊 Profit Analysis")
            
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
            
            fig = px.bar(x=crop_names, y=profit_numeric, title="Profit Comparison",
                        labels={'x': 'Crops', 'y': 'Profit Level'},
                        color=profit_numeric, color_continuous_scale='Oranges')
            
            fig.update_layout(showlegend=False,
                            yaxis=dict(tickmode='array', tickvals=[1, 2, 3], 
                                     ticktext=['Low', 'Medium', 'High']))
            st.plotly_chart(fig, use_container_width=True)
        
        # Advice Section
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🌾 General Advice")
            st.info(recommendations['general_advice'])
        
        with col2:
            st.markdown("#### 📅 Seasonal Notes")
            st.warning(recommendations['seasonal_notes'])
        
        # Additional Tips
        st.markdown("#### 📚 Additional Tips")
        tips = [
            "🔍 Check local market prices before making final decisions",
            "🌡️ Consider climate change impacts on your chosen crops",
            "💧 Evaluate water availability and irrigation costs",
            "🚜 Account for machinery and labor costs",
            "📈 Diversify your crops to reduce risks"
        ]
        
        for tip in tips:
            st.write(tip)
    
    else:
        # Welcome Section
        st.markdown("""
        ## 🌟 Welcome to Crop Profit Advisor!
        
        This AI-powered application helps Indian farmers choose the right crops:
        
        - **🗓️ Seasonal Timing:** Right timing for maximum yield
        - **🌍 Location-Specific:** Based on your region's climate and soil
        - **💰 Budget-Friendly:** Investment and ROI analysis
        - **📊 Market Intelligence:** Current price trends and demand forecasts
        
        ### 🚀 How to Get Started:
        1. Enter your location and preferred month
        2. Specify your available budget and farm details
        3. Click the button to get personalized recommendations
        
        *Ready to maximize your agricultural profits? Let's get started! 🌾*
        """)

if __name__ == "__main__":
    main()