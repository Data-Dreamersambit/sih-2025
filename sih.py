import streamlit as st
import google.generativeai as genai
from langchain_community.llms import GooglePalm
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import pandas as pd
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
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
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .crop-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #2E8B57;
    }
    .profit-indicator {
        font-size: 1.2rem;
        font-weight: bold;
        color: #228B22;
    }
    .sidebar-info {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
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


def create_crop_recommendation_prompt():
    """Create a detailed prompt template for crop recommendations"""
    template = """
    You are an expert agricultural consultant with deep knowledge of crop profitability, seasonal patterns, and regional farming conditions.
    
    Given the following information:
    - Month: {month}
    - Location: {location}
    - Budget: ${budget}
    
    Please provide crop recommendations that would be most profitable for this situation. Consider:
    1. Seasonal suitability for the given month
    2. Climate and soil conditions typical for the location
    3. Initial investment requirements within the budget
    4. Expected profit margins and ROI
    5. Market demand and pricing trends
    6. Growing duration and harvest timing
    
    Format your response as a JSON with the following structure:
    {{
        "recommendations": [
            {{
                "crop_name": "Crop Name",
                "profit_potential": "High/Medium/Low",
                "estimated_roi": "percentage",
                "investment_required": "amount",
                "growing_period": "duration in months",
                "key_benefits": ["benefit1", "benefit2", "benefit3"],
                "considerations": ["consideration1", "consideration2"],
                "market_price_range": "price range per unit"
            }}
        ],
        "general_advice": "Overall farming advice for the given conditions",
        "seasonal_notes": "Important seasonal considerations"
    }}
    
    Provide 3-5 crop recommendations ranked by profitability potential.
    """
    return template

def get_crop_recommendations(model, month, location, budget):
    """Get crop recommendations using Gemini API"""
    try:
        prompt_template = create_crop_recommendation_prompt()
        prompt = prompt_template.format(
            month=month,
            location=location,
            budget=budget
        )
        
        response = model.generate_content(prompt)
        
        # Try to extract JSON from the response
        response_text = response.text
        
        # Find JSON in the response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx != -1:
            json_str = response_text[start_idx:end_idx]
            return json.loads(json_str)
        else:
            # If no JSON found, create a structured response
            return {
                "recommendations": [
                    {
                        "crop_name": "Based on your inputs",
                        "profit_potential": "Variable",
                        "estimated_roi": "Contact local experts",
                        "investment_required": f"Within ${budget}",
                        "growing_period": "Varies",
                        "key_benefits": ["Location-specific analysis needed"],
                        "considerations": ["Consult local agricultural extension"],
                        "market_price_range": "Market dependent"
                    }
                ],
                "general_advice": response_text[:500] + "..." if len(response_text) > 500 else response_text,
                "seasonal_notes": f"For {month} in {location}, consider local climate patterns."
            }
    except Exception as e:
        st.error(f"Error getting recommendations: {str(e)}")
        return None

def display_crop_card(crop_data):
    """Display a crop recommendation card"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"""
        <div class="crop-card">
            <h3>🌱 {crop_data['crop_name']}</h3>
            <p><strong>Growing Period:</strong> {crop_data['growing_period']}</p>
            <p><strong>Investment Required:</strong> {crop_data['investment_required']}</p>
            <p><strong>Market Price Range:</strong> {crop_data['market_price_range']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        profit_color = {
            'High': '#228B22',
            'Medium': '#FFB347',
            'Low': '#CD5C5C'
        }.get(crop_data['profit_potential'], '#666666')
        
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem;">
            <div class="profit-indicator" style="color: {profit_color};">
                {crop_data['profit_potential']} Profit
            </div>
            <div style="font-size: 1.1rem; font-weight: bold;">
                ROI: {crop_data['estimated_roi']}
            </div>
        </div>
        """, unsafe_allow_html=True)

def create_profit_visualization(recommendations):
    """Create a visualization of profit potential"""
    crop_names = [crop['crop_name'] for crop in recommendations['recommendations']]
    profit_levels = [crop['profit_potential'] for crop in recommendations['recommendations']]
    
    # Convert profit levels to numeric values for visualization
    profit_numeric = []
    for level in profit_levels:
        if level == 'High':
            profit_numeric.append(3)
        elif level == 'Medium':
            profit_numeric.append(2)
        else:
            profit_numeric.append(1)
    
    fig = px.bar(
        x=crop_names,
        y=profit_numeric,
        title="Profit Potential Comparison",
        labels={'x': 'Crops', 'y': 'Profit Level'},
        color=profit_numeric,
        color_continuous_scale='Greens'
    )
    
    fig.update_layout(
        showlegend=False,
        yaxis=dict(tickmode='array', tickvals=[1, 2, 3], ticktext=['Low', 'Medium', 'High'])
    )
    
    return fig

# Main App
def main():
    # Header
    st.markdown('<h1 class="main-header">🌾 Crop Profit Advisor</h1>', unsafe_allow_html=True)
    st.markdown("*Get AI-powered crop recommendations based on your location, timing, and budget*")
    
    # Sidebar for inputs
    st.sidebar.markdown("## 📊 Input Parameters")
    
    # API Key input
    api_key = st.sidebar.text_input(
        "🔑 Google Gemini API Key",
        type="password",
        help="Enter your Google Gemini API key. Get it from: https://makersuite.google.com/app/apikey"
    )
    
    if not api_key:
        st.sidebar.markdown("""
        
             
            <a href="https://makersuite.google.com/app/apikey"</a>
            
    
        """, unsafe_allow_html=True)
        return
    
    # Input fields
    col1, col2 = st.sidebar.columns(2)
    
    months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    
    with col1:
        selected_month = st.selectbox("📅 Month", months, index=datetime.now().month - 1)
    
    with col2:
        budget = st.number_input("💰 Budget (rupees)", min_value=100, max_value=1000000, value=5000, step=500)
    
    location = st.sidebar.text_input(
        "📍 Location (City, State/Country)",
        placeholder="e.g., Iowa, USA or Punjab, India",
        help="Be as specific as possible for better recommendations"
    )
    
    # Advanced options
    with st.sidebar.expander("🔧 Advanced Options"):
        crop_experience = st.selectbox(
            "Experience Level",
            ["Beginner", "Intermediate", "Expert"]
        )
        
        farm_size = st.selectbox(
            "Farm Size",
            ["Small (< 5 acres)", "Medium (5-50 acres)", "Large (> 50 acres)"]
        )
        
        organic_preference = st.checkbox("Prefer Organic Farming")
    
    # Get recommendations button
    if st.sidebar.button("🚀 Get Crop Recommendations", type="primary"):
        if not location.strip():
            st.sidebar.error("Please enter a location")
            return
            
        # Setup Gemini API
        model = setup_gemini_api(api_key)
        if not model:
            return
        
        with st.spinner("🤖 Analyzing market conditions and generating recommendations..."):
            recommendations = get_crop_recommendations(model, selected_month, location, budget)
            
            if recommendations:
                st.session_state.recommendations = recommendations
                st.success("✅ Recommendations generated successfully!")
            else:
                st.error("❌ Failed to generate recommendations. Please try again.")
    
    # Display recommendations
    if st.session_state.recommendations:
        recommendations = st.session_state.recommendations
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📅 Month", selected_month)
        with col2:
            st.metric("📍 Location", location)
        with col3:
            st.metric("💰 Budget", f"${budget:,}")
        with col4:
            total_crops = len(recommendations['recommendations'])
            st.metric("🌱 Recommendations", total_crops)
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["📋 Recommendations", "📊 Analysis", "💡 Advice"])
        
        with tab1:
            st.subheader("🎯 Recommended Crops")
            
            for i, crop in enumerate(recommendations['recommendations']):
                st.markdown(f"### #{i+1} Recommendation")
                display_crop_card(crop)
                
                # Expandable details
                with st.expander(f"📝 Details for {crop['crop_name']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**🎯 Key Benefits:**")
                        for benefit in crop['key_benefits']:
                            st.write(f"• {benefit}")
                    
                    with col2:
                        st.markdown("**⚠️ Considerations:**")
                        for consideration in crop['considerations']:
                            st.write(f"• {consideration}")
        
        with tab2:
            st.subheader("📊 Profit Analysis")
            
            if len(recommendations['recommendations']) > 1:
                fig = create_profit_visualization(recommendations)
                st.plotly_chart(fig, use_container_width=True)
            
            # Investment breakdown
            st.subheader("💰 Investment Breakdown")
            investment_data = []
            
            for crop in recommendations['recommendations']:
                investment_data.append({
                    'Crop': crop['crop_name'],
                    'Investment Required': crop['investment_required'],
                    'ROI': crop['estimated_roi'],
                    'Profit Potential': crop['profit_potential']
                })
            
            df = pd.DataFrame(investment_data)
            st.dataframe(df, use_container_width=True)
        
        with tab3:
            st.subheader("💡 Expert Advice")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🌾 General Farming Advice")
                st.info(recommendations['general_advice'])
            
            with col2:
                st.markdown("#### 📅 Seasonal Notes")
                st.warning(recommendations['seasonal_notes'])
            
            # Additional tips
            st.markdown("#### 📚 Additional Tips")
            tips = [
                "🔍 Research local market prices before making final decisions",
                "🌡️ Consider climate change impacts on crop yields",
                "💧 Evaluate water availability and irrigation costs",
                "🚜 Factor in machinery and labor costs",
                "📈 Diversify crops to minimize risk",
                "🏪 Establish buyer relationships before planting"
            ]
            
            for tip in tips:
                st.write(tip)
    
    else:
        # Welcome message
        st.markdown("""
        ## 🌟 Welcome to Crop Profit Advisor!
        
        This AI-powered application helps farmers and agricultural entrepreneurs make informed decisions about crop selection based on:
        
        - **🗓️ Seasonal Timing:** Optimal planting months for maximum yield
        - **🌍 Location-Specific:** Climate and soil conditions in your area  
        - **💰 Budget Constraints:** Investment requirements and ROI analysis
        - **📊 Market Intelligence:** Current pricing trends and demand forecasts
        
        ### 🚀 How to Get Started:
        1. Enter your Google Gemini API key in the sidebar
        2. Specify your location, preferred month, and available budget
        3. Click "Get Crop Recommendations" to receive personalized suggestions
        4. Explore detailed analysis and expert advice for each recommended crop
        
        *Ready to maximize your agricultural profits? Start by entering your API key! 🌾*
        """)
        
        # Feature highlights
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            #### 🤖 AI-Powered
            Uses advanced Google Gemini AI for intelligent crop analysis
            """)
        
        with col2:
            st.markdown("""
            #### 📊 Data-Driven
            Considers market trends, climate data, and profitability metrics
            """)
        
        with col3:
            st.markdown("""
            #### 🌍 Location-Aware
            Provides region-specific recommendations for optimal results
            """)

if __name__ == "__main__":
    main()