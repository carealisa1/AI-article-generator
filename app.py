import streamlit as st
import streamlit.components.v1 as components
import os
from datetime import datetime
import json
import time
import re
from urllib.parse import urlparse
from dotenv import load_dotenv
from llm_engine import LLMEngine
from image_engine import ImageEngine
from content_tools import ContentTools
from seo_tools import SEOTools
from exporter import Exporter
from auth_config import create_authenticator

# Load environment variables
load_dotenv()

def validate_url(url):
    """Validate if a URL is properly formatted"""
    try:
        # Basic URL pattern check
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            return False, "Invalid URL format. URLs must start with http:// or https://"
        
        # Parse URL for additional validation
        parsed = urlparse(url)
        if not parsed.netloc:
            return False, "URL must contain a valid domain"
        
        return True, "Valid URL"
    except Exception as e:
        return False, f"URL validation error: {str(e)}"

def validate_urls_input(urls_text):
    """Validate multiple URLs from text input"""
    if not urls_text or not urls_text.strip():
        return True, []  # Empty input is valid
    
    urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
    invalid_urls = []
    
    for i, url in enumerate(urls, 1):
        # Skip URLs that are just descriptions (for link integration)
        if ' - ' in url:
            url_part = url.split(' - ')[0].strip()
        else:
            url_part = url
        
        is_valid, error_msg = validate_url(url_part)
        if not is_valid:
            invalid_urls.append(f"Line {i}: {error_msg}")
    
    if invalid_urls:
        return False, invalid_urls
    return True, []

# Page configuration
st.set_page_config(
    page_title="AI Article Generator",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)


def create_sidebar():
    """Create a professional sidebar with organized input controls"""
    
    # Header section
    with st.sidebar.container():
        st.markdown("## Content Configuration")
        st.markdown("Configure your article generation parameters")
    
    st.sidebar.divider()
    
    # Content Source Section
    with st.sidebar.expander("📝 Content Source", expanded=True):
        input_type = st.radio(
            "Choose input method:",
            ["Topic & Keywords", "URL Analysis"],
            help="Select how you want to provide content input"
        )
        
        if input_type == "URL Analysis":
            url_input = st.text_area(
                "Enter Source URLs (one per line):",
                placeholder="https://example.com/article\nhttps://another-source.com/page",
                height=120,
                help="URLs that the model can use as context or reference. One URL per line."
            )
            
            # Validate URLs in real-time
            if url_input:
                is_valid, errors = validate_urls_input(url_input)
                if not is_valid:
                    st.error("⚠️ Invalid URLs detected")
                    # for error in errors:
                    #     st.error(f"• {error}")
                else:
                    url_count = len([url.strip() for url in url_input.split('\n') if url.strip()])
                    st.success(f"✓ {url_count} valid URLs configured")

            # Optional keywords when using URL analysis
            keywords = st.text_area(
                "Optional Keywords (one per line):",
                placeholder="Optional keywords to guide generation (first = primary).\nE.g. Bitcoin fiyat tahmini",
                height=80,
                help="Optional. If provided, keywords will guide generation alongside URL content. One per line."
            )
        else:
            url_input = None

            keywords = st.text_area(
                "Keywords (one per line):",
                placeholder="Bitcoin fiyat tahmini\nkripto para analizi\nfiyat tahminleri",
                height=120,
                help="Keywords to guide the article (first = primary keyword). One keyword per line."
            )

        if keywords:
            keyword_count = len([k.strip() for k in keywords.split("\n") if k.strip()])
            st.success(f"✓ {keyword_count} keywords configured")
    
    # Content Style Section  
    with st.sidebar.expander("🎨 Content Style", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            language = st.selectbox(
                "Select Language:",
                ["English", "French", "Turkish", "Italian", "Spanish", "German", "Korean", "Japanese", "Thai"],
                help="Choose your preferred language for content generation"
            )
        
        with col2:
            tone = st.selectbox(
                "Writing Tone:",
                ["Professional", "Conversational", "Academic", "Technical", "Creative"],
                help="Article tone and style"
            )
        
        focus = st.text_input(
            "News Angle / Focus:",
            placeholder="e.g., price prediction, staking, new updates",
            help="Optional input to specify focus (e.g., 'price prediction', 'staking', 'new updates')"
        )
        
        additional_content = st.text_area(
            "Additional Content:",
            placeholder="Optional. Additional text source for inspiration...",
            height=80,
            help="Optional. Treated as another text source for inspiration."
        )
    
    # Article Structure Section
    with st.sidebar.expander("📊 Article Structure", expanded=True):
        sections = st.slider(
            "Number of Sections:",
            min_value=1,
            max_value=6,
            value=4,
            help="Controls how many H2 sections the article should contain (1-6)"
        )
        
        # Hardcoded word count
        word_count = 800
    
    # Enhancement Options Section
    with st.sidebar.expander("⚡ Enhancement Options"):
        # Hardcoded enhancement values
        include_images = True
        seo_focus = True
        
        st.markdown("**Promotional Content:**")
        
        # Promotional Content Dropdown
        promotional_options = [
            "None",
            "Doge coins", 
            "Shiba", 
            "Pepe", 
            "Best Wallet", 
            "Bitcoin Hyper", 
            "BlockchainFX", 
            "MAXI DOGE", 
            "Pepenode", 
            "Snorter", 
            "Subbd", 
            "Spacepay"
        ]
        
        selected_promotion = st.selectbox(
            "Select Promotional Content:",
            promotional_options,
            help="Choose a predefined promotional content"
        )
        
        # Custom promotional text (override dropdown if filled)
        custom_promotion = st.text_area(
            "Custom Promotional Text (Optional):",
            placeholder="Override dropdown selection with custom content...",
            height=60,
            help="If filled, this will override the dropdown selection"
        )
        
        # Promotional Style Options
        promotional_style = st.radio(
            "Promotional Style:",
            ["No Promotion", "CTA only", "Full Section + CTA"],
            help="Choose how to integrate promotional content"
        )
        
        # Determine final promotion content
        promotion = custom_promotion if custom_promotion.strip() else (selected_promotion if selected_promotion != "None" else "")
        
        # Image Settings Section
        st.markdown("**Image Settings:**")
        
        # Image Provider Selection
        available_providers = ["OpenAI", "SeeDream"]
        
        image_provider = st.selectbox(
            "Image Provider:",
            available_providers,
            help="Choose the AI image generation service"
        )
        
        image_tone = st.selectbox(
            "Image Tone:",
            ["professional", "warm", "playful", "dark", "elegant"],
            help="Tone and style for AI-generated images"
        )
        
        internal_links = st.text_area(
            "Internal Links:",
            placeholder="Link Text: /url\nAnother Link: /page",
            height=60,
            help="Format: Link Text: /url-path"
        )
    
    # Configuration Summary
    with st.sidebar.container():
        st.divider()
        st.markdown("### Configuration Summary")
        
        # Calculate dynamic metrics
        url_count = len([url.strip() for url in (url_input or '').split('\n') if url.strip()]) if url_input else 0
        keyword_count = len([k.strip() for k in keywords.split('\n') if k.strip()]) if keywords else 0
        
        st.markdown(f"""
        <div style="background-color: rgba(59, 130, 246, 0.1); padding: 15px; border-radius: 8px; border-left: 4px solid #3b82f6;">
            <p style="color: #1e3a8a; margin: 0; line-height: 1.6;">
                <strong>Language:</strong> {language}<br>
                <strong>Tone:</strong> {tone} | <strong>Image:</strong> {image_provider.split()[0]} - {image_tone}<br>
                <strong>Structure:</strong> {sections} sections, ~800 words<br>
                <strong>Sources:</strong> {url_count} URLs, {keyword_count} keywords<br>
                <strong>Promotion:</strong> {promotional_style} - {selected_promotion if selected_promotion != 'None' else 'Disabled'}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Reset Configuration Button
        st.divider()
        if st.button("🔄 Reset Configuration", help="Clear all settings", use_container_width=True):
            st.rerun()
    
    return {
        "input_type": input_type,
        "url_input": url_input,
        "keywords": keywords,
        "language": language,
        "tone": tone,
        "focus": focus,
        "additional_content": additional_content,
        "sections": int(sections),
        "promotion": promotion,
        "promotional_style": promotional_style,
        "selected_promotion": selected_promotion,
        "custom_promotion": custom_promotion,
        "image_provider": image_provider,
        "image_tone": image_tone,
        "internal_links": internal_links,
        "word_count": int(word_count),
        "include_images": include_images,
        "seo_focus": seo_focus
    }

def show_progress():
    """Initialize progress tracking"""
    if 'progress_bar' not in st.session_state:
        progress_placeholder = st.empty()
        progress_bar = st.progress(0)
        st.session_state.progress_placeholder = progress_placeholder
        st.session_state.progress_bar = progress_bar

def update_progress(message, progress):
    """Update progress bar and message"""
    with st.session_state.progress_placeholder.container():
        st.markdown(f"**Processing:** {message}")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.session_state.progress_bar.progress(progress)
        with col2:
            st.caption(f"{int(progress * 100)}% Complete")

def display_seo_metrics(seo_data):
    """Display SEO metrics"""
    cols = st.columns(4)
    
    metrics = [
        ("Keyword Density", f"{seo_data.get('keyword_density', 0):.1f}%"),
        ("Readability Score", seo_data.get('readability_score', 0)),
        ("Word Count", seo_data.get('word_count', 0)),
        ("SEO Score", f"{seo_data.get('seo_score', 0)}/100")
    ]
    
    for i, (label, value) in enumerate(metrics):
        with cols[i]:
            st.metric(label, value)

def initialize_session_state():
    """Initialize session state variables"""
    if 'article_data' not in st.session_state:
        st.session_state.article_data = None
    if 'seo_data' not in st.session_state:
        st.session_state.seo_data = None
    if 'images_data' not in st.session_state:
        st.session_state.images_data = None
    if 'exporter_instance' not in st.session_state:
        st.session_state.exporter_instance = None
    if 'extraction_summary' not in st.session_state:
        st.session_state.extraction_summary = None

def regenerate_image(section_idx, image_index, new_prompt, selected_model, tone):
    """Regenerate a specific image with new parameters"""
    
    if not new_prompt.strip():
        st.error("❌ Please provide a valid prompt for regeneration.")
        return
    
    # Store the original image data for restoration if needed
    if st.session_state.images_data is None:
        st.session_state.images_data = {}
    
    original_image = st.session_state.images_data.get(section_idx, {})
    
    try:
        # Determine provider
        provider = "openai" if selected_model == "OpenAI" else "seedream"
        model_name = "DALL-E 3" if provider == "openai" else "SeeDream"
        
        # Show status message using spinner
        with st.spinner(f"🎨 Regenerating image with {model_name}..."):
            # Initialize engine
            try:
                image_engine = ImageEngine(provider=provider)
            except ValueError as ve:
                if "SeeDream" in str(ve) or "ARK_API_KEY" in str(ve):
                    st.warning(f"⚠️ SeeDream initialization failed: {str(ve)}")
                    st.info("🔄 Falling back to OpenAI DALL-E...")
                    image_engine = ImageEngine(provider="openai")
                    provider = "openai"
                    model_name = "DALL-E 3"
                else:
                    st.error(f"❌ Image engine initialization failed: {str(ve)}")
                    return
            
            # Generate image
            new_image_data = image_engine.regenerate_image_with_prompt(new_prompt, tone, image_index)
        
        if new_image_data:
            # Update session state with new image
            st.session_state.images_data[section_idx] = new_image_data
            
            # Show success message and auto-refresh
            st.success(f"✅ Image regenerated successfully with {model_name}!")
            
            # Add a small delay to show the success message
            time.sleep(1)
            
            # Automatically refresh the page
            st.rerun()
        else:
            st.error(f"❌ Failed to regenerate image. Please try a different prompt or check your API keys.")
                
    except Exception as e:
        st.error(f"❌ Error regenerating image: {str(e)}")
        st.info("Please check your API keys and prompt, then try again.")
        print(f"Regeneration error: {e}")  # Log for debugging

def integrate_links_with_ai(link_input, link_style, link_density):
    """Integrate links into the article using AI"""
    
    if not st.session_state.article_data:
        st.error("❌ No article available for link integration.")
        return
    
    try:
        print("\n" + "="*60)
        print("🔗 SMART LINK INTEGRATION PROCESS STARTED")
        print("="*60)
        
        # Parse links
        links = []
        print(f"📝 Parsing input links...")
        
        for i, line in enumerate(link_input.strip().split('\n'), 1):
            if line.strip():
                if ' - ' in line:
                    url, description = line.split(' - ', 1)
                    links.append({"url": url.strip(), "description": description.strip()})
                    print(f"   {i}. {url.strip()} -> '{description.strip()}'")
                else:
                    links.append({"url": line.strip(), "description": ""})
                    print(f"   {i}. {line.strip()} (no description)")
        
        if not links:
            print("❌ ERROR: No valid links found in input")
            st.error("❌ No valid links found.")
            return
        
        print(f"✅ Successfully parsed {len(links)} links")
        print(f"🎯 Integration Style: {link_style}")
        print(f"📊 Link Density: {link_density}")
        
        # Show progress
        with st.spinner("🤖 AI is analyzing your article and strategically placing links..."):
            
            print("\n🤖 Initializing AI Link Integration Engine...")
            
            # Initialize LLM engine
            llm_engine = LLMEngine()
            print("✅ LLM Engine initialized successfully")
            
            # Get current article content
            current_content = st.session_state.article_data.get('content', '')
            current_word_count = len(current_content.split())
            print(f"📄 Article loaded: {current_word_count} words")
            
            # Create AI prompt for link integration
            density_instructions = {
                "Conservative": "Only integrate links where they fit perfectly and naturally - skip links that would feel forced.",
                "Moderate": "Integrate links where they add clear value and context - balance quality with coverage.",
                "Aggressive": "Try to integrate all provided links if they can add value - prioritize comprehensive coverage while maintaining quality."
            }
            
            style_instructions = {
                "Natural Integration": "Integrate links naturally within sentences and paragraphs where they flow smoothly.",
                "Contextual Placement": "Place links where they provide additional context or support the content being discussed.",
                "Strategic SEO": "Focus on SEO-friendly anchor text and strategic placement for maximum link value."
            }
            
            print(f"🎯 Using integration strategy: {density_instructions[link_density]}")
            print(f"🎨 Using style approach: {style_instructions[link_style]}")
            
            print("\n🚀 Building AI prompt for link integration...")
            
            prompt = f"""
You are an expert content editor. Your task is to integrate the provided links into the existing article content at the most appropriate positions.

ARTICLE CONTENT:
{current_content}

LINKS TO INTEGRATE (USE EACH EXACTLY ONCE):
{chr(10).join([f"- {link['url']} ({link['description']})" if link['description'] else f"- {link['url']}" for link in links])}

INTEGRATION STYLE: {link_style}
INTEGRATION DENSITY: {link_density}

*** CRITICAL LINK USAGE REQUIREMENTS ***:
- USE EACH LINK EXACTLY ONCE - never duplicate or reuse the same URL
- You have {len(links)} link(s) to integrate - aim to use ALL of them if they fit naturally
- Each URL should appear only ONE TIME in the final article
- If a link doesn't fit naturally anywhere, it's better to skip it than force it
- Focus on quality placement over quantity

INSTRUCTIONS:
- {style_instructions[link_style]}
- {density_instructions[link_density]}
- Use descriptive, natural anchor text that fits the context
- Maintain the article's flow and readability
- Only place links where they genuinely add value
- Preserve all existing formatting, headers, and structure
- Return the complete article with links integrated

RULES:
1. Links should be in HTML format: <a href="URL" target="_blank">anchor text</a>
2. ALWAYS include target="_blank" to make links open in new tabs
3. Choose anchor text that naturally fits the sentence context
4. Don't force links where they don't belong
5. Maintain article quality and readability
6. Keep all existing content structure intact
7. *** NEVER USE THE SAME URL MORE THAN ONCE ***

LINK INTEGRATION STRATEGY:
- Review the entire article first
- Identify {len(links)} best positions for the provided links
- Place each link only once in the most contextually relevant location
- Ensure anchor text is natural and descriptive

Return only the updated article content with integrated links:
"""
            
            print("📤 Sending request to AI for link integration...")
            
            # Generate updated content with links
            updated_content = llm_engine.generate_link_integration(prompt)
            
            print("📥 AI response received, analyzing results...")
            
            if updated_content and updated_content.strip():
                # Count integrated links
                integrated_links = updated_content.count('<a href=')
                new_word_count = len(updated_content.split())
                
                print(f"\n✅ LINK INTEGRATION SUCCESSFUL!")
                print(f"   📊 Links integrated: {integrated_links}/{len(links)}")
                print(f"   📝 Article length: {current_word_count} → {new_word_count} words")
                print(f"   🔄 Updating article in session state...")
                
                # Debug: Show a sample of the content with links
                if integrated_links > 0:
                    # Find and show the first link for verification
                    import re
                    link_matches = re.findall(r'<a href="[^"]+">.*?</a>', updated_content)
                    if link_matches:
                        print(f"   📎 Sample link: {link_matches[0]}")
                    else:
                        print(f"   ⚠️  Link count mismatch - counted {integrated_links} but regex found 0")
                
                # Update session state with new content (same pattern as image regeneration)
                st.session_state.article_data['content'] = updated_content
                
                # Verify the update was successful
                verification_content = st.session_state.article_data.get('content', '')
                verification_links = verification_content.count('<a href=')
                print(f"   🔍 Verification: Session state now contains {verification_links} links")
                
                # Debug: If links disappeared, investigate
                if integrated_links > 0 and verification_links == 0:
                    print(f"   🚨 CRITICAL: Links disappeared during session state update!")
                    print(f"   🔍 Original updated_content type: {type(updated_content)}")
                    print(f"   🔍 Session state content type: {type(verification_content)}")
                    print(f"   🔍 Are they the same object? {updated_content is verification_content}")
                    print(f"   🔍 Content lengths: {len(updated_content)} → {len(verification_content)}")
                    
                    # Check if there's some processing happening
                    if len(updated_content) != len(verification_content):
                        print(f"   🔍 Content was modified during storage!")
                elif integrated_links > 0 and verification_links > 0:
                    print(f"   ✅ Links successfully preserved in session state")
                
                print(f"   ✅ Article successfully updated with {integrated_links} integrated links")
                print("="*60)
                print("🔗 LINK INTEGRATION PROCESS COMPLETED")
                print("="*60 + "\n")
                
                # Show success message and auto-refresh (exact same pattern as image regeneration)
                st.success(f"✅ Successfully integrated {integrated_links} links into your article!")
                
                # Add a small delay to show the success message
                time.sleep(1)
                
                # Automatically refresh the page (same as image regeneration)
                st.rerun()
                
            else:
                print("❌ ERROR: AI returned empty or invalid content")
                print("   🔍 Response length:", len(updated_content) if updated_content else 0)
                print("="*60 + "\n")
                st.error("❌ Failed to integrate links. Please try again with different settings.")
                
    except Exception as e:
        print(f"\n❌ LINK INTEGRATION ERROR: {str(e)}")
        print(f"   🔍 Error type: {type(e).__name__}")
        print("="*60 + "\n")
        st.error(f"❌ Error during link integration: {str(e)}")
        st.info("Please check your article content and try again.")

def show_login_page():
    """Display a professional centralized login page"""
    
    # Custom CSS for login page styling
    st.markdown("""
    <style>
    /* Remove all padding/margin for login container and children */
    .login-container,
    .login-container *,
    div[data-testid="stMarkdownContainer"] .login-container,
    div[data-testid="stMarkdownContainer"] .login-container * {
        padding: 0 !important;
        margin: 0 !important;
        box-sizing: border-box !important;
    }
    
    /* Remove top padding specifically from login header */
    .login-header,
    h1.login-header,
    #ai-content-studio,
    h1#ai-content-studio {
        padding-top: 0 !important;
        margin-top: 0 !important;
        color: #1f2937;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    /* Streamlit override for main container */
    .main .block-container,
    .stMainBlockContainer,
    div[data-testid="stMainBlockContainer"],
    .block-container.st-emotion-cache-zy6yx3 {
        padding-top: 0 !important;
    }
    
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        text-align: center;
    }
    .login-subtitle,
    p.login-subtitle {
        color: #6b7280;
        font-size: 1.1rem;
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    .protected-notice {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        margin: 1.5rem 0;
        font-size: 0.9rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
    }
    .login-footer {
        color: #9ca3af;
        font-size: 0.85rem;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #e5e7eb;
    }
    
    /* Style login form button to match protected notice - targeting specific authenticator button */
    button[data-testid="stBaseButton-secondaryFormSubmit"],
    button[kind="secondaryFormSubmit"],
    .st-emotion-cache-5qfegl,
    .stButton > button,
    div[data-testid="stButton"] > button,
    .stForm button[type="submit"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2) !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    
    /* Login button text color override */
    button[data-testid="stBaseButton-secondaryFormSubmit"] p,
    button[kind="secondaryFormSubmit"] p,
    .st-emotion-cache-5qfegl p {
        color: white !important;
        margin: 0 !important;
    }
    
    button[data-testid="stBaseButton-secondaryFormSubmit"]:hover,
    button[kind="secondaryFormSubmit"]:hover,
    .st-emotion-cache-5qfegl:hover,
    .stButton > button:hover,
    div[data-testid="stButton"] > button:hover,
    .stForm button[type="submit"]:hover {
        background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3) !important;
        transform: translateY(-1px) !important;
    }
    
    button[data-testid="stBaseButton-secondaryFormSubmit"]:active,
    button[kind="secondaryFormSubmit"]:active,
    .st-emotion-cache-5qfegl:active,
    .stButton > button:active,
    div[data-testid="stButton"] > button:active,
    .stForm button[type="submit"]:active {
        transform: translateY(0px) !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2) !important;
    }
    
    /* Constrain alert messages within login page layout */
    .main .block-container [data-testid="stAlert"] {
        max-width: 100%;
        margin: 1rem auto;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Centered login container
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # Header
        st.markdown('<h1 class="login-header">✨ AI Content Studio</h1>', unsafe_allow_html=True)
        st.markdown('<p class="login-subtitle">Professional Article Generation Platform</p>', unsafe_allow_html=True)
        
        # Protected notice
        st.markdown("""
        <div class="protected-notice">
            🔒 <strong>Protected Access</strong><br>
            This application is restricted to authorized users only.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main application function"""
    
    # Authentication check
    authenticator = create_authenticator()
    
    # Check if user is not authenticated - show login page
    if not st.session_state.get('authentication_status'):
        show_login_page()
        
        # Create login widget in a centered column
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            try:
                authenticator.login()
            except Exception as e:
                st.error(f"Authentication error: {e}")
        
        # Handle authentication status
        if st.session_state.get('authentication_status') == False:
            # Constrain error message to login column width
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.error('❌ Invalid credentials. Please check your username and password.')
            
        elif st.session_state.get('authentication_status') == None:
            # Show footer info
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown("""
                <div class="login-footer">
                    <p>Contact your administrator for access credentials.</p>
                </div>
                """, unsafe_allow_html=True)
        
        return  # Don't proceed to main app until authenticated
    
    # User is authenticated - show logout option in sidebar
    with st.sidebar:
        authenticator.logout(location='sidebar')
    
    # Initialize session state
    initialize_session_state()
    
    # Create sidebar
    config = create_sidebar()
    
    # Main application header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("AI Content Studio")
        st.markdown("**Professional Article Generation Platform**")

    
    # Check API key configuration
    openai_key = os.getenv("OPENAI_API_KEY")
    ark_key = os.getenv("ARK_API_KEY")
    
    # Always require OpenAI key for content generation
    if not openai_key or openai_key.startswith("sk-your-") or openai_key == "demo-mode":
        st.error("🔑 Please configure your OpenAI API key in the .env file")
        st.code("OPENAI_API_KEY=sk-your-actual-api-key-here")
        st.info("💡 Your OpenAI API key is required for content generation (GPT-4)")
        return
    
    # Check image provider specific keys when images are enabled
    if config.get("include_images", True):
        selected_provider = config.get("image_provider", "OpenAI")
        
        if selected_provider == "SeeDream" and (not ark_key or ark_key == "your-ark-api-key-here"):
            st.warning("⚠️ SeeDream selected but ARK_API_KEY not configured. Using OpenAI DALL-E instead.")
            st.code("ARK_API_KEY=your-actual-ark-api-key-here")
            # Force fallback to OpenAI
            config["image_provider"] = "OpenAI"
    
    st.divider()
    
    # Generation Controls
    generate_ready = bool(config["keywords"] or config["url_input"])
    
    # Check if URLs are valid if provided
    if config["url_input"]:
        is_valid, _ = validate_urls_input(config["url_input"])
        if not is_valid:
            generate_ready = False
    
    if not generate_ready:
        if not config["keywords"] and not config["url_input"]:
            st.warning("⚠️ Please configure keywords or provide a URL to proceed")
        elif config["url_input"]:
            is_valid, _ = validate_urls_input(config["url_input"])
            if not is_valid:
                st.warning("⚠️ Please fix invalid URLs or provide keywords to proceed")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_button = st.button(
            "Generate Content", 
            type="primary", 
            disabled=not generate_ready,
            help="Start AI content generation process",
            use_container_width=True
        )
    
    # Generate button logic
    if generate_button:
        if not config["keywords"] and not config["url_input"]:
            st.error("❌ Configuration Error: Please provide either keywords or a URL to analyze")
            return
        
        # Validate URLs before starting the process
        if config["url_input"]:
            is_valid, errors = validate_urls_input(config["url_input"])
            if not is_valid:
                st.error("❌ Cannot start generation - Invalid URLs detected:")
                for error in errors:
                    st.error(f"• {error}")
                st.info("💡 Please fix the invalid URLs before proceeding.")
                return
        
        # Clear all previous session state data for fresh generation
        st.session_state.article_data = None
        st.session_state.seo_data = None
        st.session_state.images_data = None
        st.session_state.exporter_instance = None
        st.session_state.extraction_summary = None
        
        # Clear any cached widget states that might interfere with new prompt display
        keys_to_clear = [key for key in st.session_state.keys() if key.startswith('prompt_')]
        for key in keys_to_clear:
            del st.session_state[key]
            print(f"🗑️ Cleared cached widget state: {key}")
        
        # Initialize engines
        try:
            llm_engine = LLMEngine()
            
            # Initialize image engine with selected provider
            if config["include_images"]:
                provider = "openai" if config["image_provider"] == "OpenAI" else "seedream"
                try:
                    image_engine = ImageEngine(provider=provider)
                except ValueError as ve:
                    if "SeeDream" in str(ve) or "ARK_API_KEY" in str(ve):
                        st.warning(f"⚠️ SeeDream initialization failed: {str(ve)}")
                        st.info("� Falling back to OpenAI DALL-E for image generation...")
                        image_engine = ImageEngine(provider="openai")
                    else:
                        raise ve
            else:
                image_engine = None
            content_tools = ContentTools()
            seo_tools = SEOTools()
            exporter = Exporter()
        except ValueError as e:
            st.error(f"❌ Configuration Error: {str(e)}")
            return
        
        try:
            # Initialize progress tracking
            show_progress()
            
            # Step 1: Content Analysis
            update_progress("Analyzing content and preparing outline...", 0.15)
            if config["url_input"]:
                # Multi-URL batch processing mode with enhanced extraction
                urls = [url.strip() for url in config["url_input"].split('\n') if url.strip()]
                
                update_progress(f"Batch processing {len(urls)} URL(s) with Jina API...", 0.05)
                
                # Use enhanced batch processing
                extracted_contents = content_tools.extract_multiple_urls_content(urls, max_urls=5)
                
                # Combine extracted contents intelligently
                combined_data = content_tools.combine_extracted_contents(extracted_contents)
                
                if combined_data['successful_extractions'] > 0:
                    # Create comprehensive context for LLM
                    context = f"""Multi-URL Analysis Results:
Title: {combined_data['combined_title']}
Sources Analyzed: {combined_data['source_count']}/{combined_data['total_urls_attempted']}
Success Rate: {combined_data['success_rate']:.1f}%
Extraction Methods: {', '.join(combined_data['extraction_methods'])}

Combined Content:
{combined_data['combined_content']}

Key Topics Identified: {', '.join(combined_data['combined_keywords'][:10])}

Source Summaries:
{chr(10).join(combined_data['source_summaries'])}"""
                    
                    # Store extraction summary for later display but don't show during generation
                    st.session_state.extraction_summary = {
                        'urls_attempted': combined_data['total_urls_attempted'],
                        'successful_extractions': combined_data['successful_extractions'],
                        'success_rate': combined_data['success_rate'],
                        'keywords_found': len(combined_data['combined_keywords']),
                        'source_summaries': combined_data['source_summaries'],
                        'extraction_methods': combined_data['extraction_methods']
                    }
                    
                else:
                    st.error("❌ No content could be extracted from any URLs. Using keywords instead.")
                    context = f"Keywords: {config['keywords']}"
            else:
                context = f"Keywords: {config['keywords']}"
                
            # Include additional content if provided
            if config.get('additional_content'):
                context += f"\n\nAdditional Inspiration Content: {config['additional_content']}"
            
            # Step 2: Generate Article Structure
            update_progress("Generating article content with GPT-4...", 0.35)
            article_data = llm_engine.generate_article(
                context=context,
                keywords=config["keywords"],
                language=config["language"],
                tone=config["tone"],
                focus=config["focus"],
                sections=config["sections"],
                word_count=config["word_count"],
                promotion=config["promotion"],
                promotional_style=config["promotional_style"],
                seo_focus=config["seo_focus"]
            )
            
            # Step 3: SEO Optimization
            update_progress("Optimizing content for search engines...", 0.55)
            seo_data = seo_tools.optimize_content(
                article_data,
                keywords=config["keywords"],
                focus_keyword=config["keywords"].split(",")[0] if config["keywords"] else None
            )
            
            # Step 4: Generate Images
            if config["include_images"] and image_engine:
                provider_name = "DALL-E 3" if image_engine.provider == "openai" else "SeeDream"
                update_progress(f"Creating AI-powered images with {provider_name}...", 0.75)
                images = image_engine.generate_images(
                    article_data,
                    tone=config["image_tone"]
                )
                
                # Note: Image generation summary will be shown in the final content
            else:
                images = {}
            
            # Step 5: Final Enhancement
            update_progress("Enhancing and finalizing content...", 0.90)
            enhanced_content = content_tools.enhance_content(
                article_data,
                internal_links=config["internal_links"],
                seo_data=seo_data
            )
            
            # Complete
            update_progress("Article generation complete!", 1.0)
            
            # Store results in session state
            st.session_state.article_data = enhanced_content
            st.session_state.seo_data = seo_data
            st.session_state.images_data = images
            st.session_state.exporter_instance = exporter
            
            # Debug logging for session state storage
            if images:
                for key, img_data in images.items():
                    prompt_preview = img_data.get('prompt', 'NO_PROMPT')[:100]
                    print(f"📦 STORED in session: {key} -> prompt: {prompt_preview}...")
            else:
                print("📦 STORED in session: No images generated")
            
            # Clear progress indicators and show success
            st.session_state.progress_placeholder.empty()
            st.session_state.progress_bar.empty()
            
            # Professional completion notification
            st.success("✅ Content generation completed successfully")
            
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            st.info("Please check your API keys and try again.")
    
    # Display content if available in session state
    if st.session_state.article_data is not None:
        display_generated_content()
    
def display_generated_content():
    """Display the generated content in simplified format"""
    if not st.session_state.article_data:
        return

    enhanced_content = st.session_state.article_data
    seo_data = st.session_state.seo_data
    images = st.session_state.images_data
    exporter = st.session_state.exporter_instance
    
    # Debug logging for content display
    current_content = enhanced_content.get('content', '')
    current_link_count = current_content.count('<a href=')
    print(f"🖥️ Display Function Called: Article contains {current_link_count} links, {len(current_content.split())} words")
    
    # Generate slug programmatically from title
    def generate_slug(title):
        import re
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        return slug[:50] if len(slug) > 50 else slug
    
    # Clean formatting
    title_text = enhanced_content['title'].replace('**', '').strip()
    meta_text = enhanced_content['meta_description'].replace('**', '').strip()
    slug = generate_slug(title_text)
    
    # Display article information in an organized expander
    with st.expander("📋 Article Information", expanded=True):
        # Article metadata in a structured layout with integrated copy buttons
        
        # Title section - heading and content in same row
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown("**📝 Title:**")
        with col2:
            # Escape text for JavaScript
            escaped_title = title_text.replace('`', '\\`').replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"')
            components.html(f"""
                <html>
                <head>
                    <style>
                        .copy-container {{
                            position: relative;
                            background-color: #f0f2f6;
                            padding: 0.25rem 0.5rem;
                            padding-right: 2.5rem;
                            border-radius: 4px;
                            font-family: monospace;
                            font-size: 0.9rem;
                            margin: 0.25rem 0;
                            border: 1px solid #e0e0e0;
                        }}
                        .copy-btn {{
                            position: absolute;
                            top: 50%;
                            right: 0.5rem;
                            transform: translateY(-50%);
                            background: rgba(255, 255, 255, 0.8);
                            border: 1px solid #ddd;
                            border-radius: 3px;
                            padding: 2px 6px;
                            cursor: pointer;
                            font-size: 11px;
                            opacity: 0.6;
                            transition: all 0.2s ease;
                        }}
                        .copy-btn:hover {{
                            opacity: 1;
                            background: rgba(76, 175, 80, 0.1);
                            border-color: #4CAF50;
                        }}
                        .copy-btn.copied {{
                            background: #4CAF50;
                            color: white;
                            opacity: 1;
                            border-color: #4CAF50;
                        }}
                    </style>
                </head>
                <body>
                    <div class="copy-container">
                        {title_text}
                        <button class="copy-btn" onclick="copyText(this, '{escaped_title}')">📋</button>
                    </div>
                    
                    <script>
                    async function copyText(button, text) {{
                        try {{
                            await navigator.clipboard.writeText(text);
                            // Change icon to checkmark
                            button.innerHTML = '✓';
                            button.classList.add('copied');
                            
                            // Reset after 2 seconds
                            setTimeout(() => {{
                                button.innerHTML = '📋';
                                button.classList.remove('copied');
                            }}, 2000);
                        }} catch (err) {{
                            console.error('Failed to copy:', err);
                            // Fallback for older browsers
                            const textArea = document.createElement('textarea');
                            textArea.value = text;
                            document.body.appendChild(textArea);
                            textArea.select();
                            document.execCommand('copy');
                            document.body.removeChild(textArea);
                            
                            // Show success visual feedback
                            button.innerHTML = '✓';
                            button.classList.add('copied');
                            setTimeout(() => {{
                                button.innerHTML = '📋';
                                button.classList.remove('copied');
                            }}, 2000);
                        }}
                    }}
                    </script>
                </body>
                </html>
            """, height=50)
        
        # Compact divider
        st.markdown('<hr style="margin: 0.5rem 0; border: 1px solid #e0e0e0;">', unsafe_allow_html=True)
        
        # Meta Description section - heading and content in same row
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown("**📄 Meta Description:**")
        with col2:
            escaped_meta = meta_text.replace('`', '\\`').replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"')
            components.html(f"""
                <html>
                <head>
                    <style>
                        .copy-container {{
                            position: relative;
                            background-color: #f0f2f6;
                            padding: 0.25rem 0.5rem;
                            padding-right: 2.5rem;
                            border-radius: 4px;
                            font-family: monospace;
                            font-size: 0.9rem;
                            margin: 0.25rem 0;
                            border: 1px solid #e0e0e0;
                        }}
                        .copy-btn {{
                            position: absolute;
                            top: 50%;
                            right: 0.5rem;
                            transform: translateY(-50%);
                            background: rgba(255, 255, 255, 0.8);
                            border: 1px solid #ddd;
                            border-radius: 3px;
                            padding: 2px 6px;
                            cursor: pointer;
                            font-size: 11px;
                            opacity: 0.6;
                            transition: all 0.2s ease;
                        }}
                        .copy-btn:hover {{
                            opacity: 1;
                            background: rgba(76, 175, 80, 0.1);
                            border-color: #4CAF50;
                        }}
                        .copy-btn.copied {{
                            background: #4CAF50;
                            color: white;
                            opacity: 1;
                            border-color: #4CAF50;
                        }}
                    </style>
                </head>
                <body>
                    <div class="copy-container">
                        {meta_text}
                        <button class="copy-btn" onclick="copyText(this, '{escaped_meta}')">📋</button>
                    </div>
                    
                    <script>
                    async function copyText(button, text) {{
                        try {{
                            await navigator.clipboard.writeText(text);
                            // Change icon to checkmark
                            button.innerHTML = '✓';
                            button.classList.add('copied');
                            
                            // Reset after 2 seconds
                            setTimeout(() => {{
                                button.innerHTML = '📋';
                                button.classList.remove('copied');
                            }}, 2000);
                        }} catch (err) {{
                            console.error('Failed to copy:', err);
                            // Fallback for older browsers
                            const textArea = document.createElement('textarea');
                            textArea.value = text;
                            document.body.appendChild(textArea);
                            textArea.select();
                            document.execCommand('copy');
                            document.body.removeChild(textArea);
                            
                            // Show success visual feedback
                            button.innerHTML = '✓';
                            button.classList.add('copied');
                            setTimeout(() => {{
                                button.innerHTML = '📋';
                                button.classList.remove('copied');
                            }}, 2000);
                        }}
                    }}
                    </script>
                </body>
                </html>
            """, height=50)
        
        # Compact divider
        st.markdown('<hr style="margin: 0.5rem 0; border: 1px solid #e0e0e0;">', unsafe_allow_html=True)
        
        # URL Slug section - heading and content in same row
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown("**🌐 URL Slug:**")
        with col2:
            escaped_slug = slug.replace('`', '\\`').replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"')
            components.html(f"""
                <html>
                <head>
                    <style>
                        .copy-container {{
                            position: relative;
                            background-color: #f0f2f6;
                            padding: 0.25rem 0.5rem;
                            padding-right: 2.5rem;
                            border-radius: 4px;
                            font-family: monospace;
                            font-size: 0.9rem;
                            margin: 0.25rem 0;
                            border: 1px solid #e0e0e0;
                        }}
                        .copy-btn {{
                            position: absolute;
                            top: 50%;
                            right: 0.5rem;
                            transform: translateY(-50%);
                            background: rgba(255, 255, 255, 0.8);
                            border: 1px solid #ddd;
                            border-radius: 3px;
                            padding: 2px 6px;
                            cursor: pointer;
                            font-size: 11px;
                            opacity: 0.6;
                            transition: all 0.2s ease;
                        }}
                        .copy-btn:hover {{
                            opacity: 1;
                            background: rgba(76, 175, 80, 0.1);
                            border-color: #4CAF50;
                        }}
                        .copy-btn.copied {{
                            background: #4CAF50;
                            color: white;
                            opacity: 1;
                            border-color: #4CAF50;
                        }}
                    </style>
                </head>
                <body>
                    <div class="copy-container">
                        {slug}
                        <button class="copy-btn" onclick="copyText(this, '{escaped_slug}')">📋</button>
                    </div>
                    
                    <script>
                    async function copyText(button, text) {{
                        try {{
                            await navigator.clipboard.writeText(text);
                            // Change icon to checkmark
                            button.innerHTML = '✓';
                            button.classList.add('copied');
                            
                            // Reset after 2 seconds
                            setTimeout(() => {{
                                button.innerHTML = '📋';
                                button.classList.remove('copied');
                            }}, 2000);
                        }} catch (err) {{
                            console.error('Failed to copy:', err);
                            // Fallback for older browsers
                            const textArea = document.createElement('textarea');
                            textArea.value = text;
                            document.body.appendChild(textArea);
                            textArea.select();
                            document.execCommand('copy');
                            document.body.removeChild(textArea);
                            
                            // Show success visual feedback
                            button.innerHTML = '✓';
                            button.classList.add('copied');
                            setTimeout(() => {{
                                button.innerHTML = '📋';
                                button.classList.remove('copied');
                            }}, 2000);
                        }}
                    }}
                    </script>
                </body>
                </html>
            """, height=50)
    
    # Always display full article
    st.markdown("---")
    
    # Check if links are present in the content
    current_content = enhanced_content.get('content', '')
    link_count = current_content.count('<a href=')
    
    with st.expander("📄 Complete Article Preview", expanded=True):
        # Action buttons at the top right
        col1, col2, col3 = st.columns([2, 1, 1])
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            # Check if links have been integrated and log it
            current_content = enhanced_content.get('content', '')
            link_count = current_content.count('<a href=')
            if link_count > 0:
                print(f"🔗 Display: Article content contains {link_count} links - generating HTML...")
            else:
                print(f"📄 Display: Article content has no links - generating standard HTML...")
            
            # Generate the complete HTML content using the exporter
            html_content = exporter.generate_html(enhanced_content, seo_data, images)
            html_filename = f"article_{timestamp}.html"
            
            with col2:
                # Custom download HTML button
                import base64
                html_b64 = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
                
                components.html(f"""
                <div style="width: 100%; padding: 0; margin: 0; display: flex; flex-direction: column; align-items: stretch;">
                    <button id="downloadBtn" onclick="downloadHTML()" style="
                        width: 100%; 
                        height: 40px; 
                        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                        border: none; 
                        border-radius: 0.375rem; 
                        color: white; 
                        font-weight: 500; 
                        font-size: 14px;
                        cursor: pointer; 
                        transition: all 0.3s ease;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 6px;
                        padding: 0.5rem 0.75rem;
                        margin: 0;
                        box-sizing: border-box;
                        line-height: 1;
                        vertical-align: top;
                    ">
                        <span id="downloadIcon">📄</span> <span id="downloadText">Download HTML</span>
                    </button>
                    <div id="downloadStatus" style="margin-top: 8px; text-align: center; font-size: 12px; opacity: 0; transition: opacity 0.3s;"></div>
                </div>
                
                <script>
                const htmlContent = atob('{html_b64}');
                const filename = '{html_filename}';
                
                function downloadHTML() {{
                    const btn = document.getElementById('downloadBtn');
                    const icon = document.getElementById('downloadIcon');
                    const text = document.getElementById('downloadText');
                    const status = document.getElementById('downloadStatus');
                    
                    try {{
                        // Show downloading state
                        btn.style.background = 'linear-gradient(135deg, #ffc107 0%, #fd7e14 100%)';
                        icon.innerHTML = '⏳';
                        text.innerHTML = 'Preparing...';
                        status.innerHTML = 'Creating download...';
                        status.style.opacity = '1';
                        status.style.color = '#666';
                        
                        // Create blob and download
                        const blob = new Blob([htmlContent], {{ type: 'text/html' }});
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.style.display = 'none';
                        a.href = url;
                        a.download = filename;
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);
                        document.body.removeChild(a);
                        
                        // Show success state
                        btn.style.background = 'linear-gradient(135deg, #28a745 0%, #20c997 100%)';
                        icon.innerHTML = '✅';
                        text.innerHTML = 'Downloaded!';
                        status.innerHTML = 'File saved successfully';
                        status.style.color = '#28a745';
                        
                        // Reset after 3 seconds
                        setTimeout(() => {{
                            icon.innerHTML = '📄';
                            text.innerHTML = 'Download HTML';
                            status.style.opacity = '0';
                        }}, 3000);
                        
                    }} catch (err) {{
                        console.error('Download failed:', err);
                        
                        // Show error state
                        btn.style.background = '#dc3545';
                        icon.innerHTML = '❌';
                        text.innerHTML = 'Failed';
                        status.innerHTML = 'Download failed';
                        status.style.color = '#dc3545';
                        
                        // Reset after 4 seconds
                        setTimeout(() => {{
                            btn.style.background = 'linear-gradient(135deg, #28a745 0%, #20c997 100%)';
                            icon.innerHTML = '📄';
                            text.innerHTML = 'Download HTML';
                            status.style.opacity = '0';
                        }}, 4000);
                    }}
                }}
                </script>
                """, height=70)
            
            with col3:
                # Custom copy HTML button with base64 encoding for reliable copying
                components.html(f"""
                <div style="width: 100%; padding: 0; margin: 0; display: flex; flex-direction: column; align-items: stretch;">
                    <button id="copyBtn" onclick="copyToClipboard()" style="
                        width: 100%; 
                        height: 40px; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        border: none; 
                        border-radius: 0.375rem; 
                        color: white; 
                        font-weight: 500; 
                        font-size: 14px;
                        cursor: pointer; 
                        transition: all 0.3s ease;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 6px;
                        padding: 0.5rem 0.75rem;
                        margin: 0;
                        box-sizing: border-box;
                        line-height: 1;
                        vertical-align: top;
                    ">
                        <span id="btnIcon">📋</span> <span id="btnText">Copy HTML</span>
                    </button>
                    <div id="status" style="margin-top: 8px; text-align: center; font-size: 12px; opacity: 0; transition: opacity 0.3s;"></div>
                </div>
                
                <script>
                const copyHtmlContent = atob('{html_b64}');
                
                async function copyToClipboard() {{
                    const btn = document.getElementById('copyBtn');
                    const icon = document.getElementById('btnIcon');
                    const text = document.getElementById('btnText');
                    const status = document.getElementById('status');
                    
                    try {{
                        // Show copying state
                        btn.style.background = 'linear-gradient(135deg, #ffa726 0%, #ff7043 100%)';
                        icon.innerHTML = '⏳';
                        text.innerHTML = 'Copying...';
                        status.innerHTML = 'Processing...';
                        status.style.opacity = '1';
                        status.style.color = '#666';
                        
                        // Copy to clipboard
                        if (navigator.clipboard && navigator.clipboard.writeText) {{
                            await navigator.clipboard.writeText(copyHtmlContent);
                        }} else {{
                            // Fallback for older browsers
                            const textarea = document.createElement('textarea');
                            textarea.value = copyHtmlContent;
                            textarea.style.position = 'fixed';
                            textarea.style.opacity = '0';
                            document.body.appendChild(textarea);
                            textarea.select();
                            document.execCommand('copy');
                            document.body.removeChild(textarea);
                        }}
                        
                        // Show success state
                        btn.style.background = 'linear-gradient(135deg, #66bb6a 0%, #43a047 100%)';
                        icon.innerHTML = '✅';
                        text.innerHTML = 'Copied!';
                        status.innerHTML = 'HTML copied (' + Math.round(copyHtmlContent.length/1024) + 'KB)';
                        status.style.color = '#4caf50';
                        
                        // Reset after 3 seconds
                        setTimeout(() => {{
                            btn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                            icon.innerHTML = '📋';
                            text.innerHTML = 'Copy HTML';
                            status.style.opacity = '0';
                        }}, 3000);
                        
                    }} catch (err) {{
                        console.error('Copy failed:', err);
                        
                        // Show error state
                        btn.style.background = '#f44336';
                        icon.innerHTML = '❌';
                        text.innerHTML = 'Failed';
                        status.innerHTML = 'Copy failed';
                        status.style.color = '#f44336';
                        
                        // Reset after 4 seconds
                        setTimeout(() => {{
                            btn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                            icon.innerHTML = '📋';
                            text.innerHTML = 'Copy HTML';
                            status.style.opacity = '0';
                        }}, 4000);
                    }}
                }}
                </script>
                """, height=70)
            
            
            # Display the HTML content using components.html
            try:
                components.html(
                    html_content,
                    height=800,
                    scrolling=True
                )
            except Exception as html_error:
                st.error(f"HTML component error: {html_error}")
                st.info("Falling back to markdown display...")
                st.markdown("### Article Content (Fallback)")
                st.markdown(current_content, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error displaying HTML preview: {e}")
            st.info("Falling back to basic text preview...")
            
            # Fallback to simple text display with links preserved
            article_content = enhanced_content.get('content', '')
            if article_content:
                st.markdown("### Article Content")
                # Display with HTML enabled to show integrated links
                st.markdown(article_content, unsafe_allow_html=True)
    
    # Professional Image Management Section
    if enhanced_content and images:
        st.markdown("---")
        
        

        
        # Image Assets Grid
        for i, (section_idx, image_data) in enumerate(images.items()):
            
            # Image Regeneration Expander
            with st.expander(f"🎨 Image Management", expanded=True):
                # Content Area
                with st.container():
                    # First Row - Image Display (Smaller Size)
                    st.markdown("**📷 Current Asset**")
                    
                    # Create centered column for smaller image
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        # Image display with professional border
                        if image_data.get('is_loading', False):
                            # Show loading state with animated spinner
                            st.markdown("""
                            <div style="text-align: center; padding: 2rem; background: #e3f2fd; border-radius: 8px; border: 2px solid #2196f3;">
                                <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #bbdefb; border-top: 4px solid #2196f3; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                                <p style="margin-top: 1rem; color: #1565c0; font-weight: 600;">🎨 Generating New Image...</p>
                                <p style="margin: 0.5rem 0 0 0; color: #1976d2; font-size: 0.85rem;">Please wait while we create your custom image</p>
                            </div>
                            <style>
                                @keyframes spin {
                                    0% { transform: rotate(0deg); }
                                    100% { transform: rotate(360deg); }
                                }
                            </style>
                            """, unsafe_allow_html=True)
                        elif image_data.get('is_placeholder', False):
                            st.image(
                                image_data['url'], 
                                width='stretch',
                                caption="⚠️ Image Generation Failed - Placeholder Active"
                            )
                            
                            # Get fallback reason if available
                            fallback_reason = image_data.get('fallback_reason', 'AI image generation temporarily unavailable')
                            
                            st.markdown(f"""
                            <div style="background: #fff3cd; padding: 0.75rem; border-radius: 6px; border-left: 3px solid #ffc107; margin-top: 0.5rem;">
                                <p style="margin: 0; color: #856404; font-size: 0.85rem; font-weight: 500;">
                                    ⚠️ <strong>Image Generation Failed:</strong> {fallback_reason}
                                </p>
                                <p style="margin: 0.5rem 0 0 0; color: #6c5700; font-size: 0.8rem;">
                                    💡 <em>Use the regeneration controls below to try generating a new image with different settings.</em>
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.image(image_data['url'], width='stretch')
                    
                    # Second Row - Controls in Two Columns
                    prompt_col, settings_col = st.columns(2)
                    
                    with prompt_col:
                        with st.container(border=True):
                            st.markdown("**📝 Edit Prompt**")
                            
                            # Professional prompt editing section with improved handling
                            current_prompt = image_data.get('prompt', '')
                            
                            # Handle edge cases for prompt display
                            if not current_prompt or current_prompt.strip() == '':
                                # Try to get a fallback prompt from other fields
                                fallback_prompt = (
                                    image_data.get('alt_text', '') or 
                                    image_data.get('caption', '') or 
                                    'No prompt available - this may be a placeholder image'
                                )
                                current_prompt = fallback_prompt
                                print(f"⚠️  DEBUG: No prompt found for image {section_idx}, using fallback: {fallback_prompt[:50]}...")
                                print(f"   🔍 Available image_data keys: {list(image_data.keys())}")
                            else:
                                # Check if this is the expected crypto prompt or the generic fallback
                                if "cryptocurrency trading interface" in current_prompt:
                                    print(f"✅ DEBUG: CORRECT crypto prompt for image {section_idx}: {current_prompt[:100]}...")
                                elif "modern professional concept illustration" in current_prompt:
                                    print(f"❌ DEBUG: WRONG generic fallback prompt for image {section_idx}: {current_prompt[:100]}...")
                                    print(f"   🚨 This should be the crypto prompt! Investigating...")
                                    print(f"   🔍 Session state images keys: {list(st.session_state.images_data.keys()) if st.session_state.images_data else 'None'}")
                                    if st.session_state.images_data:
                                        for key, data in st.session_state.images_data.items():
                                            stored_prompt = data.get('prompt', 'NO_PROMPT')[:100]
                                            print(f"   📦 {key}: {stored_prompt}...")
                                else:
                                    print(f"🔍 DEBUG: Different prompt for image {section_idx}: {current_prompt[:100]}...")
                            
                            # Create a unique key that includes prompt hash to force refresh when prompt changes
                            prompt_hash = hash(current_prompt[:50]) % 1000
                            
                            new_prompt = st.text_area(
                                "Asset Description Prompt",
                                value=current_prompt,
                                height=150,
                                key=f"prompt_{section_idx}_{i}_{prompt_hash}",
                                help="Describe the visual elements, style, and composition for the regenerated image",
                                placeholder="Enter detailed description for image generation..."
                            )
                            
                            # Show prompt analytics and reset button
                            prompt_length = len(new_prompt.split())
                            prompt_changed = new_prompt.strip() != current_prompt.strip()
                            
                            analytics_col1, analytics_col2 = st.columns([2, 1])
                            with analytics_col1:
                                if prompt_changed:
                                    st.caption("✏️ Modified • 📊 " + f"{prompt_length} words")
                                else:
                                    st.caption("📋 Original • 📊 " + f"{prompt_length} words")
                            with analytics_col2:
                                # Reset button inside prompt section
                                if st.button(
                                    "Reset",
                                    key=f"reset_{section_idx}_{i}",
                                    help="Reset to original prompt",
                                    use_container_width=True
                                ):
                                    st.rerun()
                    
                    with settings_col:
                        with st.container(border=True):
                            st.markdown("**🔧 Technical Settings**")
                            
                            # Model selection with professional styling
                            available_models = ["OpenAI"]
                            
                            # Check SeeDream availability
                            ark_key = os.getenv("ARK_API_KEY")
                            if ark_key and ark_key != "your-ark-api-key-here":
                                available_models.append("SeeDream")
                            
                            selected_model = st.selectbox(
                                "🤖 AI Model",
                                available_models,
                                key=f"model_{section_idx}_{i}",
                                help="Select the AI engine for image generation"
                            )
                            
                            # Image tone selection
                            regenerate_tone = st.selectbox(
                                "🎨 Visual Style",
                                ["professional", "warm", "playful", "dark", "elegant"],
                                index=0,
                                key=f"tone_{section_idx}_{i}",
                                help="Choose the visual tone and aesthetic"
                            )
                            
                            # Main regeneration button
                            regenerate_key = f"regenerate_{section_idx}_{i}"
                            button_type = "primary" if prompt_changed else "secondary"
                            button_text = "🔄 Regenerate Asset" if prompt_changed else "🔄 Regenerate"
                            
                            if st.button(
                                button_text,
                                key=regenerate_key,
                                help="Generate new image asset with current configuration",
                                use_container_width=True,
                                type=button_type
                            ):
                                regenerate_image(section_idx, i, new_prompt, selected_model, regenerate_tone)
                    

    # Smart Link Integration Section
    st.markdown("---")
    
    with st.expander("🔗 Smart Link Integration", expanded=True):
        st.markdown("""
        **AI-Powered Link Placement** - Provide links and let GPT intelligently insert them at the most appropriate positions in your article.
        """)
        
        # Link input area
        col1, col2 = st.columns([3, 2])
        
        with col1:
            link_input = st.text_area(
                "Enter Links (one per line):",
                placeholder="https://example.com - Brief description of the link\nhttps://another-site.com/page - What this link is about\nhttps://internal-link.com/article - Related article",
                height=155,
                help="Format: URL - Description (optional). GPT will use descriptions to place links contextually.",
                key="smart_links_input"
            )
            
            # Validate links in real-time
            if link_input:
                is_valid, errors = validate_urls_input(link_input)
                if not is_valid:
                    st.error("⚠️ Invalid URLs detected:")
                    for error in errors:
                        st.error(f"• {error}")
                else:
                    link_count = len([link.strip() for link in link_input.split('\n') if link.strip()])
                    st.success(f"✓ {link_count} valid links ready for integration")
        
        with col2:

            
            link_style = st.selectbox(
                "Link Style:",
                ["Natural Integration", "Contextual Placement", "Strategic SEO"],
                help="How GPT should integrate the links into the content"
            )
            
            link_density = st.selectbox(
                "Link Density:",
                ["Conservative", "Moderate", "Aggressive"],
                index=1,
                help="How many links to try to integrate"
            )
        
        # Process links button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Check if URLs are valid before enabling the button
            urls_valid = True
            if link_input:
                is_valid, _ = validate_urls_input(link_input)
                urls_valid = is_valid
            
            if st.button(
                "🚀 Integrate Links with AI",
                type="primary",
                disabled=not link_input or not st.session_state.article_data or not urls_valid,
                help="Use GPT to intelligently place links in the article" if urls_valid else "Fix invalid URLs before proceeding",
                use_container_width=True,
                key="integrate_links_btn"
            ):
                if not st.session_state.article_data:
                    st.error("❌ Please generate an article first before integrating links.")
                elif not link_input.strip():
                    st.error("❌ Please provide at least one link to integrate.")
                else:
                    # Double-check URL validation before processing
                    is_valid, errors = validate_urls_input(link_input)
                    if not is_valid:
                        st.error("❌ Cannot integrate links - Invalid URLs detected:")
                        for error in errors:
                            st.error(f"• {error}")
                        st.info("💡 Please fix the invalid URLs before proceeding.")
                    else:
                        integrate_links_with_ai(link_input, link_style, link_density)
    
    # Display empty state if no images
    if not (enhanced_content and images):
        # Professional empty state
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; padding: 3rem 1rem; background: #f9fafb; border-radius: 12px; border: 2px dashed #d1d5db;">
            <h3 style="color: #6b7280; margin-bottom: 1rem;">📷 No Image Assets Available</h3>
            <p style="color: #9ca3af; margin-bottom: 0;">
                Generate an article with images enabled to access the Image Asset Management system.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Image Generation Summary
        if images:
            st.markdown("---")
            generated_count = sum(1 for img in images.values() if not img.get('is_placeholder', False))
            total_count = len(images)
            
            st.markdown("### � Image Generation Summary")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Images", total_count)
            with col2:
                st.metric("Generated", generated_count)
            with col3:
                st.metric("Success Rate", f"{(generated_count/total_count*100):.1f}%" if total_count > 0 else "0%")
            with col4:
                # Show which models were used
                models_used = set()
                for img in images.values():
                    model = img.get('model', 'Unknown')
                    if 'dall-e' in model.lower():
                        models_used.add('DALL-E')
                    elif 'seedream' in model.lower():
                        models_used.add('SeeDream')
                    else:
                        models_used.add('Other')
                pass  # Analytics now integrated in main section

if __name__ == "__main__":
    main()