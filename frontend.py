import streamlit as st
import json
import time
from typing import Dict, Any
from datetime import datetime, timedelta
import pandas as pd
from main import run_linkedin_growth_agent, save_results

# Page configuration
st.set_page_config(
    page_title="LinkedIn Growth Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Exact same styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 3rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .post-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .day-badge {
        background: #667eea;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 1rem;
    }
    .hook-text {
        font-weight: bold;
        color: #333;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
    .content-text {
        line-height: 1.6;
        color: #555;
        margin-bottom: 1rem;
    }
    .hashtags {
        color: #667eea;
        font-style: italic;
    }
    .cta-text {
        background: #f8f9fa;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #667eea;
        margin-top: 1rem;
    }
    .image-suggestion {
        background: #e8f2ff;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 25px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = None
if 'is_generating' not in st.session_state:
    st.session_state.is_generating = False

def display_post(post: Dict[str, Any], index: int):
    """Display a single post with all its details"""
    
    with st.container():
        st.markdown(f"""
        <div class="post-card">
            <div class="day-badge">Day {post['day']} - {post['posting_day']}</div>
            <div class="hook-text">🎯 {post['hook']}</div>
            <div class="content-text">{post['post_text']}</div>
            <div class="hashtags">{' '.join(post['hashtags'])}</div>
            # <div class="cta-text">📢 CTA: {post['cta']}</div>
            <div class="cta-text">📢 <strong>CTA:</strong> {post['cta']}</div>
            # <div class="cta-text">📢 <strong>CTA:</strong></div>
        """, unsafe_allow_html=True)
        # 
        # st.markdown(post["cta"])
        # 
        # Image suggestions
        if post.get('suggested_images'):
            st.markdown("**🖼️ Image Suggestions:**")
            for i, img in enumerate(post['suggested_images'][:3], 1):
                if isinstance(img, dict) and 'url' in img:
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        try:
                            st.image(img['url'], width=150)
                        except:
                            st.info("Image preview unavailable")
                    with col2:
                        st.markdown(f"""
                        <div class="image-suggestion">
                        <strong>Image {i}</strong><br>
                        <a href="{img['url']}" target="_blank">View Full Image</a>
                        </div>
                        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

def display_results(state: Dict[str, Any]):
    """Display the complete content plan"""
    
    # Header metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
        <h3>Niche Identified</h3>
        <p>{state['niche']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
        <h3>Content Theme</h3>
        <p>{state['content_theme']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
        <h3>Tone</h3>
        <p>{state['tone']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Strategy section
    with st.expander("📊 Content Strategy Overview", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Niche Summary:**")
            st.info(state['niche_summary'])
        with col2:
            st.markdown("**Content Strategy:**")
            st.success(state['content_strategy'])
    
    st.markdown("---")
    
    # Posts section
    st.markdown("## 📝 5-Day Content Plan")
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📅 Day-by-Day View", "📋 Table View", "📊 Analytics"])
    
    with tab1:
        for i, post in enumerate(state['generated_posts']):
            display_post(post, i)
    
    with tab2:
        # Create a DataFrame for table view
        posts_df = pd.DataFrame(state['generated_posts'])
        
        # Display key information in a table
        display_df = posts_df[['day', 'posting_day', 'content_type', 'hook', 'cta']].copy()
        display_df.columns = ['Day', 'Posting Day', 'Type', 'Hook', 'Call to Action']
        
        st.dataframe(display_df, use_container_width=True)
        
        # Download options
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Content Plan as CSV",
            data=csv,
            file_name=f"linkedin_content_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with tab3:
        # Analytics section
        col1, col2 = st.columns(2)
        
        with col1:
            # Content type distribution
            content_types = [post['content_type'] for post in state['generated_posts']]
            type_counts = pd.Series(content_types).value_counts()
            
            st.markdown("**Content Type Distribution:**")
            st.bar_chart(type_counts)
        
        with col2:
            # Hashtag analysis
            all_hashtags = []
            for post in state['generated_posts']:
                all_hashtags.extend(post['hashtags'])
            
            hashtag_counts = pd.Series(all_hashtags).value_counts().head(10)
            
            st.markdown("**Top Hashtags:**")
            st.write(hashtag_counts)
    
    # Download full results
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save Results to JSON", type="primary"):
            filename = f"linkedin_content_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            save_results(state, filename)
            st.success(f"✅ Results saved to {filename}")
    
    with col2:
        json_data = json.dumps(state, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 Download Full Results (JSON)",
            data=json_data,
            file_name=f"linkedin_content_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<h1 class="main-header">🚀 LinkedIn Growth Agent</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Content Strategy for LinkedIn Success</p>', unsafe_allow_html=True)
    
    # Sidebar for input
    with st.sidebar:
        st.markdown("## 🎯 Input Your Details")
        
        with st.form("user_input_form"):
            desc = st.text_area(
                "Your Description",
                placeholder="e.g., HR manager helping companies implement better hiring frameworks",
                help="Describe what you do and your professional background",
                height=100
            )
            
            expertise = st.text_input(
                "Your Expertise Areas",
                placeholder="e.g., HR, hiring, recruitment, ATS, interviewing",
                help="Comma-separated list of your expertise areas"
            )
            
            audience = st.text_input(
                "Target Audience",
                placeholder="e.g., Job seekers, HR professionals, recruiters",
                help="Who are you trying to reach on LinkedIn?"
            )
            
            submit_button = st.form_submit_button(
                "🚀 Generate Content Plan",
                use_container_width=True
            )
    
    # Main content area
    if submit_button:
        if not all([desc, expertise, audience]):
            st.error("❌ Please fill in all required fields!")
            return
        
        st.session_state.is_generating = True
        
        # Progress tracking
        progress_container = st.container()
        with progress_container:
            st.markdown("### 🔄 Generating Your Content Plan...")
            
            # Create progress bar and status
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simulate progress
            for i, step in enumerate([
                "🔍 Analyzing your profile and niche...",
                "📊 Researching successful content patterns...",
                "🎨 Creating your 5-day content plan...",
                "🖼️ Finding relevant images...",
                "✅ Finalizing your strategy..."
            ]):
                status_text.text(step)
                progress_bar.progress((i + 1) * 20)
                time.sleep(0.5)
        
        try:
            # Generate content
            result = run_linkedin_growth_agent(
                desc=desc,
                expertise=expertise,
                audience=audience
            )
            
            st.session_state.generated_content = result
            st.session_state.is_generating = False
            
            # Clear progress
            progress_container.empty()
            
            # Display results
            display_results(result)
            
        except Exception as e:
            st.session_state.is_generating = False
            st.error(f"❌ An error occurred: {str(e)}")
            st.info("Please check your API keys and try again.")
    
    elif st.session_state.generated_content:
        # Display existing results
        display_results(st.session_state.generated_content)
    
    else:
        # Welcome screen
        st.markdown("""
        ## 🎯 Welcome to LinkedIn Growth Agent!
        
        This AI-powered tool helps you create a comprehensive 5-day LinkedIn content strategy.
        
        ### How it works:
        1. **📝 Input Your Details** - Fill in your description, expertise, and target audience
        2. **🤖 AI Analysis** - Our agents analyze your profile and research successful content
        3. **📊 Content Plan** - Get a complete 5-day content strategy with images
        4. **📈 Grow Your Presence** - Implement the strategy and watch your LinkedIn grow!
        
        ### Features:
        - ✅ AI-powered niche identification
        - ✅ Content pattern analysis
        - ✅ 5-day posting schedule
        - ✅ Image suggestions
        - ✅ Hashtag optimization
        - ✅ Multiple export formats
        
        **Ready to grow your LinkedIn presence? Fill in your details in the sidebar and let's get started!** 🚀
        """)
        
        # Sample preview
        with st.expander("👀 See Sample Output"):
            st.markdown("""
            Here's what your content plan will look like:
            
            - **Day 1**: Monday - Educational post about hiring best practices
            - **Day 2**: Tuesday - Industry insight about recruitment trends  
            - **Day 3**: Wednesday**: Personal story about career growth
            - **Day 4**: Thursday - Tips for job seekers
            - **Day 5**: Friday - Weekend reflection post
            
            Each post includes:
            - Compelling hook
            - Engaging content
            - Relevant hashtags
            - Clear call-to-action
            - Image suggestions
            """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
    Made with ❤️ by LinkedIn Growth Agent | 
    <a href="https://github.com/your-repo" target="_blank">GitHub</a> | 
    <a href="https://linkedin.com/in/your-profile" target="_blank">LinkedIn</a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
