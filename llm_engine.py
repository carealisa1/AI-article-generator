import os
import json
from typing import Dict, List, Optional, Any
import openai
from openai import OpenAI
import time
from dataclasses import dataclass
import re

@dataclass
class ArticleSection:
    heading: str
    content: str
    keywords: List[str]
    word_count: int

@dataclass  
class ArticleData:
    title: str
    seo_title: str
    meta_description: str
    slug: str
    sections: List[ArticleSection]
    cta: Optional[str]
    total_word_count: int
    focus_keywords: List[str]
    language: str
    tone: str

class LLMEngine:
    """Advanced OpenAI engine with multi-pass refinement and prompt engineering"""
    
    def __init__(self):
        """Initialize the LLM engine with OpenAI configuration"""
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key or api_key.startswith("sk-your-") or api_key == "demo-mode":
            raise ValueError("Please configure a valid OpenAI API key in the .env file")
        
        self.client = OpenAI(api_key=api_key)
            
        self.max_tokens = int(os.getenv("MAX_TOKENS", 4000))
        self.model = "gpt-5" # Using the latest model
        
        # Custom tone profiles for specialized content (matching website options)
        self.custom_tone_profiles = {
            "Professional": {
                "personality": "Professional, informative, and authoritative tone suitable for business and formal content.",
                "writing_style": "professional_formal",
                "target_audience": "business professionals",
                "voice_characteristics": [
                    "Formal and structured",
                    "Industry-standard terminology",
                    "Objective and factual",
                    "Clear and concise"
                ]
            },
            "Casual": {
                "personality": "Friendly, conversational, and approachable tone for general audiences.",
                "writing_style": "casual_friendly",
                "target_audience": "general readers",
                "voice_characteristics": [
                    "Relaxed and friendly",
                    "Easy to understand",
                    "Engaging and relatable",
                    "Uses everyday language"
                ]
            }
        }
        
        # Store client's crypto personality requirements (applied automatically for crypto topics)
        self.crypto_personality_template = """Write as an authoritative source covering cryptocurrency-related topics. Use a casual and personable tone and include slang specific to crypto to make your content relatable to the target audience (cryptocurrency enthusiasts). Be talkative and conversational. Use quick and clever humor when appropriate. Address the reader in the second person singular but never refer to yourself or ask questions directly."""
    
    def get_available_tones(self) -> List[str]:
        """Get list of available tone profiles"""
        return list(self.custom_tone_profiles.keys())
    
    def get_tone_description(self, tone: str) -> str:
        """Get description of a specific tone profile"""
        if tone in self.custom_tone_profiles:
            profile = self.custom_tone_profiles[tone]
            return f"{profile['personality']} (Target: {profile['target_audience']})"
        return "Standard tone profile"
        
    def generate_article(
        self, 
        context: str, 
        keywords: str, 
        language: str = "English",
        tone: str = "Professional", 
        focus: str = "", 
        sections: int = 5,
        promotion: str = "",
        promotional_style: str = "No Promotion",
        seo_focus: bool = True,
        external_links: str = "",
        promotional_context: str = ""
    ) -> Dict[str, Any]:
        """
        Generate a complete article using multi-pass refinement approach
        
        Pass 1: Draft generation
        Pass 2: SEO optimization  
        Pass 3: Style and coherence refinement
        """
        
        # Parse keywords (support both newline and comma separation for flexibility)
        if keywords:
            # Try newline separation first (primary format)
            if '\n' in keywords:
                keyword_list = [k.strip() for k in keywords.split("\n") if k.strip()]
            else:
                # Fallback to comma separation for backward compatibility
                keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
        else:
            keyword_list = []
        primary_keyword = keyword_list[0] if keyword_list else "topic"
        
        try:
            # Generate SEO-optimized content in single pass
            final_content = self._generate_draft(
                context, keyword_list, language, tone, focus, 
                sections, promotion, promotional_style, seo_focus, external_links, promotional_context
            )
            
            # Parse and structure the final content
            article_data = self._parse_article_content(final_content, keyword_list, language, tone, sections)
            
            return article_data
            
        except Exception as e:
            # Fallback to single-pass generation
            print(f"Multi-pass generation failed, falling back to single pass: {e}")
            # Ultimate fallback - return structured placeholder
            return self._generate_fallback_content(keywords, language, tone)
    
    def _generate_draft(
        self, 
        context: str, 
        keywords: List[str], 
        language: str, 
        tone: str,
        focus: str, 
        sections: int, 
        promotion: str,
        promotional_style: str,
        seo_focus: bool = True,
        external_links: str = "",
        promotional_context: str = ""
    ) -> str:
        """Generate the initial draft of the article"""
        
        # Construct comprehensive prompt
        prompt = self._build_draft_prompt(
            context, keywords, language, tone, focus, 
            sections, promotion, promotional_style, seo_focus, external_links, promotional_context
        )
        
        # Always apply crypto expert tone as per client requirements
        is_crypto_topic = True  # Client requirement: Always use crypto expert personality
        
        try:
            # Build enhanced system prompt with custom personality
            system_prompt = self._build_enhanced_system_prompt(tone, is_crypto_topic)
            
            # DEBUG: Print system and user prompts
            print("\n" + "="*80)
            print("🤖 DEBUG: AI PROMPTS")
            print("="*80)
            print(f"Is Crypto Topic: {is_crypto_topic}")
            print(f"Tone: {tone}")
            print("\n📝 SYSTEM PROMPT:")
            print("-" * 40)
            print(system_prompt)
            print("\n💬 USER PROMPT:")
            print("-" * 40)
            print(prompt[:1000] + "..." if len(prompt) > 1000 else prompt)
            print("="*80 + "\n")
            
            # Use the correct parameter for GPT-5
            completion_params = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system", 
                        "content": system_prompt
                    },
                    {"role": "user", "content": prompt}
                ],

            }
            
            response = self.client.chat.completions.create(**completion_params)

            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"Draft generation failed: {e}")
    
    def _build_enhanced_system_prompt(self, tone: str, is_crypto_topic: bool = False) -> str:
        """Build simplified system prompt with tone customization"""
        
        # Get the tone profile (only use available tones from the website)
        available_tones = {
            "Professional": self.custom_tone_profiles["Professional"],
            "Conversational": self.custom_tone_profiles["Casual"],  # Map Conversational to Casual
            "Academic": {"personality": "Academic, scholarly, and research-oriented tone with formal language and detailed analysis."},
            "Technical": {"personality": "Technical, precise, and detailed tone focusing on specifications and technical accuracy."},
            "Creative": {"personality": "Creative, engaging, and imaginative tone that captures reader attention with vivid language."}
        }
        
        tone_profile = available_tones.get(tone, available_tones["Professional"])
        
        # Apply client's crypto personality requirements for crypto topics
        if is_crypto_topic:
            # Apply client's custom crypto personality regardless of selected tone
            personality = f"""You are a crypto expert writer. {self.crypto_personality_template}

Use crypto slang naturally: HODL, diamond hands, moon, rugpull, ape in, degens, DYOR, "few understand", "not financial advice".
Be conversational and engaging while maintaining expertise.
Maintain the overall {tone.lower()} structure while applying crypto personality."""
        else:
            # Standard personality for non-crypto content based on selected tone
            personality = f"""You are an expert content writer. {tone_profile['personality']}"""

        return f"""{personality}

CRITICAL ORIGINAL WRITING REQUIREMENTS:
- Write original content using source material as factual foundation
- Maintain ALL factual accuracy (numbers, dates, prices, statistics, company names)
- Keep ALL numerical data and quotes UNCHANGED from source
- Keep meta description 100% EXACTLY the same as original - no changes whatsoever
- Create engaging, natural headings (avoid "topic", "general topic", placeholder language)
- Write as if creating original analysis, not transforming existing content
- Use specific, confident language about the subject matter
- Apply crypto tone while maintaining complete factual accuracy
- Use ## for section headings only
- No artificial labels like "Title:", "Meta:", etc.
- STRICT RULE: Follow the exact number of sections requested - count carefully before finishing

FORBIDDEN: Using placeholder language, copying sentence structures, changing factual data, exceeding the requested section count."""

    def _build_draft_prompt(
        self, 
        context: str, 
        keywords: List[str], 
        language: str, 
        tone: str,
        focus: str, 
        sections: int, 
        promotion: str,
        promotional_style: str,
        seo_focus: bool = True,
        external_links: str = "",
        promotional_context: str = ""
    ) -> str:
        """Build comprehensive prompt for draft generation"""
        
        keyword_str = ', '.join(keywords) if keywords else "general topic"
        primary_kw = keywords[0] if keywords else "topic"
        
        # Build context analysis
        context_type = "URL content analysis" if "Multi-URL Analysis" in context else "keyword-based content"
        
        # Detect if this is finance/crypto content and add specialized guidance
        domain_expertise = ""
        finance_crypto_keywords = ['bitcoin', 'crypto', 'cryptocurrency', 'blockchain', 'defi', 'nft', 'trading', 'investment', 'finance', 'financial', 'market', 'price', 'altcoin', 'ethereum', 'binance', 'wallet', 'exchange', 'staking', 'mining', 'portfolio', 'stocks', 'forex', 'web3', 'metaverse', 'dao', 'yield', 'rugpull', 'hodl', 'memecoin', 'shitcoin']
        
        # Check if any finance/crypto keywords are present
        all_keywords_text = ' '.join(keywords).lower()
        is_finance_crypto_topic = any(keyword.lower() in all_keywords_text for keyword in finance_crypto_keywords)
        
        # Get tone-specific expertise instructions
        tone_profile = self.custom_tone_profiles.get(tone, self.custom_tone_profiles["Professional"])
        
        # Create specific focus instructions
        focus_instruction = ""
        if focus:
            focus_instruction = f"""
        CRITICAL FOCUS REQUIREMENT:
        - This article MUST center around: {focus}
        - Every section should relate back to this focus angle
        - Use {focus} as the primary lens for analyzing {primary_kw}
        """
        
        # Parse external links for integration
        links_instruction = ""
        if external_links and external_links.strip():
            links = []
            for line in external_links.strip().split('\n'):
                if line.strip():
                    if ' - ' in line:
                        url, description = line.split(' - ', 1)
                        links.append({"url": url.strip(), "description": description.strip()})
                    else:
                        links.append({"url": line.strip(), "description": ""})
            
            if links:
                links_instruction = f"""
        *** EXTERNAL LINKS INTEGRATION REQUIREMENTS ***:
        
        LINKS TO INTEGRATE (USE EACH EXACTLY ONCE):
        {chr(10).join([f"- {link['url']} ({link['description']})" if link['description'] else f"- {link['url']}" for link in links])}
        
        INTEGRATION RULES:
        - MANDATORY: USE ALL LINKS - you MUST integrate every single link provided
        - USE EACH LINK EXACTLY ONCE - never duplicate any URL
        - Place links strategically within relevant paragraphs 
        - Use HTML format: <a href="URL" target="_blank">descriptive anchor text</a>
        - ALWAYS include target="_blank" to open links in new tabs
        - Choose natural anchor text that fits the sentence context
        - FORCE integration - find appropriate places for ALL links
        - You have {len(links)} links and must use all {len(links)} of them
        - Creative placement is required - make them fit naturally but USE ALL
        """
        
        # Create promotional integration strategy using client-specific templates
        promotion_strategy = ""
        if promotion and promotional_style != "No Promotion":
            if promotional_style == "CTA only":
                promotion_strategy = f"""
        *** PROMOTIONAL CONTENT INTEGRATION - CTA ONLY TEMPLATE ***:
        
        MANDATORY STRUCTURE AT END OF ARTICLE:
        
        Section 1 (Informative Transition + Insight):
        - Write H2 heading about {promotion} following market trends and relating to main article topic
        - Start with 1 sentence referencing the article's topic to create natural flow
        - Add 1-5 educational sentences about {promotion} (latest updates, market relevance, ecosystem growth)
        - Tone: Factual, educational, consistent with article - NOT overly promotional
        - Focus on project insights, technology, or market position
        
        Section 2 (Simple CTA):
        - Write EXACTLY this format (optimize wording for natural flow):
        "Visit the {promotion} official website."
        
        CRITICAL REQUIREMENTS:
        - Language: {language}
        - Style: Human, natural writing that flows from main content
        - Educational focus, not advertisement-like
        - Must feel like natural continuation of article, not unrelated ad
        - Keep factual and informative tone throughout
        """
            elif promotional_style == "Full Section + CTA":
                promotion_strategy = f"""
        *** PROMOTIONAL CONTENT INTEGRATION - FULL SECTION + CTA TEMPLATE ***:
        
        MANDATORY STRUCTURE AT END OF ARTICLE:
        
        Section 1 (Informative Transition + Insight):
        - Write H2 heading about {promotion} following market trends and relating to main article topic
        - Start with 1 sentence referencing the article's topic to create natural flow
        - Add 1-5 educational sentences about {promotion} (latest updates, market relevance, ecosystem growth)
        - Tone: Factual, educational, consistent with article - NOT overly promotional
        - Focus on project insights, technology, or market position
        
        Section 2 (Informative CTA - EXACT FORMAT REQUIRED):
        Write this section using EXACTLY this structure (optimize wording to fit article naturally):
        
        "If you're considering {promotion}, read our {promotion} price analysis and be sure to check out our step-by-step guide to buying {promotion} to build confidence and plan more accurately.

        Stay updated on the latest news via the {promotion} official website, X (Twitter), and Telegram channels.

        Visit the {promotion} official website."
        
        CRITICAL REQUIREMENTS:
        - Language: {language}
        - Style: Human, natural writing that flows from main content
        - Educational focus, not advertisement-like
        - Must feel like natural continuation of article, not unrelated ad
        - Keep all key elements (price analysis, buying guide, official links)
        - Make it sound relevant and informative
        - Maintain factual tone throughout
        """
        
        # Add promotional context if available
        promotional_info = ""
        if promotional_context:
            promotional_info = f"""
        
*** PROMOTIONAL CONTEXT INFORMATION ***:
Use the following detailed information about {promotion} to create accurate, informative content:

{promotional_context}

This information provides comprehensive background about {promotion} including tokenomics, features, roadmap, and market positioning. Use this to ensure accuracy and relevance in your promotional sections.
"""

        
        prompt = f"""
TASK: Write an original, comprehensive article using the provided source material as factual foundation and inspiration.

SOURCE MATERIAL FOR REFERENCE:
{context}

REQUIREMENTS:
- Target Language: {language}
- Apply crypto expert tone (casual, authoritative, crypto slang)
- Keywords to include naturally: {keyword_str}
- Write as if you're creating original content, not transforming existing text
- MANDATORY: Create exactly {sections} main content sections (## headings) - no more, no less

{links_instruction}

WRITING APPROACH:
✅ USE SOURCE FACTS & DATA:
- Extract all factual information (numbers, prices, dates, statistics, company names)
- Use technical details and market data as foundation
- Reference key developments and trends mentioned
- Maintain accuracy of all numerical data and quotes
- Keep meta description EXACTLY as it appears in source - word for word

✅ CREATE ORIGINAL NARRATIVE:
- Write in your own words using crypto expert voice
- Natural crypto slang: HODL, diamond hands, moon, ape in, degens, DYOR  
- Casual expert commentary: "few understand this", "not financial advice"
- Conversational tone with authoritative insights
- Make it feel like original analysis, not copied content

✅ AVOID COPY-LIKE LANGUAGE:
- Never use placeholder words like "topic", "general topic", "the article"
- Write specific, engaging headings (not "Analysis - topic")
- Make content flow naturally as if written from scratch
- Use direct, confident language about the subject matter

{focus_instruction}
{promotion_strategy}
{promotional_info}

OUTPUT FORMAT (clean, engaging):
[Compelling Original Title]
[Engaging Meta Description]

CRITICAL: Write EXACTLY {sections} main sections with ## headings:

## [Section 1: Specific, Natural Heading]
[Original content with crypto tone, using source facts...]

## [Section 2: Another Engaging Heading]
[Original analysis and insights with source data...]

[Continue for exactly {sections} sections total - count them carefully!]

STOP after {sections} sections. Do not add extra sections beyond this limit.
        """
        
        return prompt
    
    def _parse_article_content(self, content: str, keywords: List[str], language: str, tone: str, max_sections: int = None) -> Dict[str, Any]:
        """Simple parsing - split on ## markers and extract sections"""
        
        try:
            # Clean content
            cleaned_content = content.replace('**', '').strip()
            
            # Extract title (first line)
            lines = cleaned_content.split('\n')
            title = lines[0].strip() if lines else "Generated Article"
            
            # Extract meta description (second non-empty line that looks like meta description)
            # PRESERVE EXACTLY as it appears in source - no truncation or modification
            meta_description = ""
            for i, line in enumerate(lines[1:], 1):
                line = line.strip()
                if (line and 
                    len(line) > 80 and 
                    len(line) < 500 and  # Increased limit to preserve full original
                    not line.startswith('#') and
                    not line.lower().startswith(('title:', 'meta:', 'description:'))):
                    meta_description = line  # Keep exactly as is - no [:160] truncation
                    break
            
            # Fallback meta description only if no original found
            if not meta_description:
                if keywords:
                    meta_description = f"Comprehensive analysis of {keywords[0]} and its impact. Explore key insights, trends, and implications in this detailed guide."
                else:
                    meta_description = "Discover key insights and analysis in this comprehensive guide covering important trends and developments."
            
            # Simple section parsing: split on "## " (with space)
            sections = []
            
            # Find all ## markers and split content
            section_parts = []
            current_part = []
            
            for line in lines:
                if line.startswith('## '):
                    # Found a section heading - save previous part if exists
                    if current_part:
                        section_parts.append('\n'.join(current_part))
                    # Start new section with the heading line
                    current_part = [line]
                else:
                    current_part.append(line)
            
            # Add the final part
            if current_part:
                section_parts.append('\n'.join(current_part))
            
            # Process sections
            for part in section_parts:
                part = part.strip()
                if not part or not part.startswith('## '):
                    continue
                
                # Split into lines
                part_lines = part.split('\n')
                
                # First line is heading (remove ## )
                heading_line = part_lines[0]
                heading = heading_line.replace('## ', '').strip()
                
                # Rest is content
                content_lines = part_lines[1:]
                section_content = '\n'.join(content_lines).strip()
                
                # Only add if we have both heading and content
                if heading and section_content:
                    sections.append({
                        'heading': heading,
                        'content': section_content,
                        'keywords': keywords[:3],
                        'word_count': len(section_content.split())
                    })
            
            # Enforce section count limit - trim excess sections if AI generated too many
            if max_sections and len(sections) > max_sections:
                print(f"⚠️ AI generated {len(sections)} sections, trimming to requested {max_sections}")
                sections = sections[:max_sections]
            
            # If no sections found, create one section from all content after title/meta
            if not sections:
                # Find where content starts (skip title and meta description)
                content_start_idx = 2  # Skip title and likely meta description
                
                # Adjust if we have more lines to find actual content start
                for i, line in enumerate(lines[2:], 2):
                    if line.strip() and not (len(line) > 80 and len(line) < 300):
                        content_start_idx = i
                        break
                
                if content_start_idx < len(lines):
                    all_content = '\n'.join(lines[content_start_idx:]).strip()
                    if all_content:
                        sections.append({
                            'heading': f"Understanding {keywords[0] if keywords else 'the Topic'}",
                            'content': all_content,
                            'keywords': keywords[:3],
                            'word_count': len(all_content.split())
                        })
            
            # Final fallback
            if not sections:
                sections = [{
                    'heading': f"Understanding {keywords[0] if keywords else 'the Topic'}",
                    'content': "Content parsing encountered an issue. Please review the generated content.",
                    'keywords': keywords[:3],
                    'word_count': 10
                }]
            
            # Calculate total word count
            total_words = sum(section['word_count'] for section in sections)
            print("Total Sections: ",len(sections))
            return {
                'title': title,
                'seo_title': title,
                'meta_description': meta_description,
                'slug': self._generate_slug(title),
                'sections': sections,
                'cta': self._generate_cta(title, keywords),
                'total_word_count': total_words,
                'focus_keywords': keywords[:3],
                'language': language,
                'tone': tone,
                'content': cleaned_content
            }
            
        except Exception as e:
            print(f"Content parsing failed: {e}")
            return self._generate_fallback_content(keywords, language, tone)
    
    def _generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug from title"""
        
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        
        return slug[:50] if len(slug) > 50 else slug
    
    def _generate_cta(self, title: str, keywords: List[str]) -> str:
        """Generate a relevant call-to-action"""
        
        primary_keyword = keywords[0] if keywords else "this topic"
        
        # Generate a simple, professional CTA
        cta_options = [
            f"Stay informed about {primary_keyword} developments by following our latest updates.",
            f"Explore more insights about {primary_keyword} in our related articles.",
            f"Keep up with {primary_keyword} trends and analysis through our newsletter.",
            f"Discover more about {primary_keyword} with our comprehensive resources."
        ]
        
        return cta_options[hash(title) % len(cta_options)]
    
    def generate_link_integration(self, prompt: str) -> str:
        """Generate updated article content with integrated links using AI"""
        
        try:
            print(f"   🤖 Using model: {self.model}")
            print(f"   📏 Prompt length: {len(prompt)} characters")
            
            start_time = time.time()
            print(f"   ⏳ Waiting for AI response...")
            
            completion_params = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system", 
                        "content": """You are an expert content editor with specialized knowledge in finance and cryptocurrency, capable of expertly handling link integration across all topics and industries.

SPECIALIZED EXPERTISE:
- Finance & Crypto: Deep knowledge in markets, blockchain, trading, DeFi, investment strategies, and regulatory developments
- General Content: Proficient in technology, health, education, lifestyle, business, and all other subject areas

ADAPTIVE LINK INTEGRATION:
- For finance/crypto content: Apply domain expertise to ensure financial relevance and accuracy
- For other topics: Use appropriate subject matter knowledge without forcing financial context
- Always prioritize content relevance and reader value regardless of topic

Your task is to intelligently place links within existing content using appropriate domain knowledge to ensure maximum relevance and value.

CRITICAL REQUIREMENTS:
1. Preserve ALL existing content structure, formatting, and quality
2. Only integrate links where they add genuine value to readers
3. Use natural, contextual anchor text that fits seamlessly into sentences
4. Maintain article flow and readability
5. Return the complete article with links integrated in HTML format
6. Do not remove or significantly alter existing content
7. Place links strategically where they support or enhance the content being discussed

LINK INTEGRATION GUIDELINES:
- Use descriptive anchor text that clearly indicates what the link is about
- Integrate links within relevant paragraphs and sentences
- Avoid cramming multiple links in one sentence
- Ensure links feel natural and not forced
- Maintain the professional tone and quality of the original content
- ALWAYS use target="_blank" attribute to open links in new tabs

OUTPUT FORMAT:
Return the complete article content with links integrated using HTML <a href="URL" target="_blank">anchor text</a> format. ALWAYS include target="_blank" to ensure links open in new browser tabs."""
                    },
                    {"role": "user", "content": prompt}
                ]
            }
            
            print("   ⏳ Waiting for AI response...")
            start_time = time.time()
            
            response = self.client.chat.completions.create(**completion_params)
            
            processing_time = time.time() - start_time
            response_content = response.choices[0].message.content.strip()
            
            print(f"   ✅ AI processing completed in {processing_time:.2f}s")
            print(f"   📏 Response length: {len(response_content)} characters")
            print(f"   🔗 Links found in response: {response_content.count('<a href=')}")
            
            return response_content
            
        except Exception as e:
            print(f"   ❌ Link integration API error: {e}")
            print(f"   🔍 Error details: {type(e).__name__}")
            return ""
    
    def _generate_fallback_content(self, keywords: List[str], language: str, tone: str) -> Dict[str, Any]:
        """Generate fallback content when all else fails"""
        
        primary_keyword = keywords[0] if keywords else "Topic"
        
        return {
            'title': f"Understanding {primary_keyword}: A Comprehensive Guide",
            'seo_title': f"{primary_keyword} Guide - Everything You Need to Know",
            'meta_description': f"Discover everything about {primary_keyword} in this comprehensive guide. Learn key concepts, benefits, and practical applications.",
            'slug': self._generate_slug(f"understanding-{primary_keyword}-guide"),
            'sections': [
                {
                    'heading': f"What is {primary_keyword}?",
                    'content': f"Understanding {primary_keyword} is essential in today's landscape. This comprehensive guide will explore the key aspects and provide valuable insights.",
                    'keywords': keywords[:2],
                    'word_count': 25
                },
                {
                    'heading': f"Benefits of {primary_keyword}",
                    'content': f"{primary_keyword} offers numerous advantages that can significantly impact your understanding and decision-making process.",
                    'keywords': keywords[1:3] if len(keywords) > 1 else keywords,
                    'word_count': 20
                }
            ],
            'cta': f"Learn more about {primary_keyword} and discover how it can benefit you. Contact our experts for personalized guidance.",
            'total_word_count': 45,
            'focus_keywords': keywords[:3],
            'language': language,
            'tone': tone,
            'content': "This is fallback content generated when the main generation process fails."
        }