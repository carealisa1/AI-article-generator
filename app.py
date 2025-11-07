import streamlit as st
import os
from datetime import datetime
import json
import time
from dotenv import load_dotenv
from llm_engine import LLMEngine
from image_engine import ImageEngine
from content_tools import ContentTools
from seo_tools import SEOTools
from exporter import Exporter

# Load environment variables
load_dotenv()

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
                ["English", "French", "Turkish", "Spanish", "German"],
                help="Choose one: English, French, Turkish, Spanish, German"
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
        word_count = 500
    
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
        
        # Image Tone Selection
        st.markdown("**Image Settings:**")
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
                <strong>Tone:</strong> {tone} | <strong>Image Tone:</strong> {image_tone}<br>
                <strong>Structure:</strong> {sections} sections, ~500 words<br>
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

def main():
    """Main application function"""
    
    # Initialize session state
    initialize_session_state()
    
    # Create sidebar
    config = create_sidebar()
    
    # Main application header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("AI Content Studio")
        st.markdown("**Professional Article Generation Platform**")

    
    # Check if OpenAI API key is configured
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_key or openai_key.startswith("sk-your-") or openai_key == "demo-mode":
        st.error("🔑 Please configure your OpenAI API key in the .env file")
        st.code("OPENAI_API_KEY=sk-your-actual-api-key-here")
        st.info("💡 Your OpenAI API key enables both content generation (GPT-4) and image generation (DALL-E 3)")
        return
    
    st.divider()
    
    # Generation Controls
    generate_ready = bool(config["keywords"] or config["url_input"])
    
    if not generate_ready:
        st.warning("⚠️ Please configure keywords or provide a URL to proceed")
    
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
        
        # Clear all previous session state data for fresh generation
        st.session_state.article_data = None
        st.session_state.seo_data = None
        st.session_state.images_data = None
        st.session_state.exporter_instance = None
        st.session_state.extraction_summary = None
        
        # Initialize engines
        try:
            llm_engine = LLMEngine()
            image_engine = ImageEngine() if config["include_images"] else None
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
                update_progress("Creating AI-powered images with DALL-E 3...", 0.75)
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
    
    # Display article information
    st.markdown("## 📋 Article Information")
    
    # Article Title
    st.markdown("### 📝 Article Title")
    st.code(title_text, language='text')
    
    # Meta Description
    st.markdown("### 📄 Meta Description")
    st.code(meta_text, language='text')
    
    # Slug
    st.markdown("### 🔗 URL Slug")
    st.code(slug, language='text')
    
    # Article HTML Download
    st.markdown("### 📥 Download Article")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        html_content = exporter.generate_html(enhanced_content, seo_data, images)
        html_filename = f"article_{timestamp}.html"
        
        st.download_button(
            label="📄 Download HTML Article",
            data=html_content,
            file_name=html_filename,
            mime="text/html",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Error generating HTML: {e}")
    
    # Image Prompts Section
    if enhanced_content and images:
        st.markdown("---")
        st.markdown("### 🎨 Generated Image Prompts")
        
        for i, (section_idx, image_data) in enumerate(images.items()):
            with st.container():
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    # Display the image
                    if image_data.get('is_placeholder', False):
                        st.image(image_data['url'], use_container_width=True)
                        st.caption("⚠️ Placeholder image")
                    else:
                        st.image(image_data['url'], use_container_width=True)
                
                with col2:
                    # Display prompt and model info
                    st.markdown("**Prompt:**")
                    st.write(image_data.get('prompt', 'No prompt available'))
                    
                    st.markdown(f"**Model:** {image_data.get('model', 'DALL-E 3')}")
                
                if i < len(images) - 1:  # Add separator except for last item
                    st.markdown("---")
    else:
        st.info("No image prompts available. Generate an article with images enabled to see prompts.")

        # Image Prompts view
        if enhanced_content and images:
            st.markdown("### 🎨 Generated Image Prompts")
            st.markdown("Here are the AI-generated prompts used to create images for your article:")
            
            for i, (section_idx, image_data) in enumerate(images.items()):
                # section_idx may be 'cover' or an integer index
                if isinstance(section_idx, str) and section_idx == 'cover':
                    section_heading = 'Cover Image'
                else:
                    try:
                        idx = int(section_idx)
                        section = enhanced_content.get('sections', [])[idx] if idx < len(enhanced_content.get('sections', [])) else {}
                        section_heading = section.get('heading', f'Section {idx + 1}')
                    except Exception:
                        section_heading = 'Image'
                
                with st.container():
                    st.markdown(f"#### 🖼️ Image {i + 1}: {section_heading}")
                    
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        # Display the image (no captions)
                        if image_data.get('is_placeholder', False):
                            st.image(image_data['url'], use_container_width=True)
                            st.warning("⚠️ This is a placeholder. DALL-E was temporarily unavailable.")
                        else:
                            st.image(image_data['url'], use_container_width=True)
                    
                    with col2:
                        # Display the prompt
                        st.markdown("**Generated Prompt:**")
                        st.code(image_data.get('prompt', 'No prompt available'), language='text')
                        
                        st.markdown("**Image Details:**")
                        # captions removed per UX request
                        st.write(f"• **Tone:** {image_data.get('tone', 'N/A')}")
                        st.write(f"• **Model:** {image_data.get('model', 'DALL-E 3')}")
                    
                    st.markdown("---")
            
            # Summary
            generated_count = sum(1 for img in images.values() if not img.get('is_placeholder', False))
            total_count = len(images)
            
            st.markdown("### 📊 Image Generation Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Images", total_count)
            with col2:
                st.metric("Generated", generated_count)
            with col3:
                st.metric("Success Rate", f"{(generated_count/total_count*100):.1f}%" if total_count > 0 else "0%")
        
        else:
            st.info("No image prompts available. Generate an article with images enabled to see prompts.")

if __name__ == "__main__":
    main()