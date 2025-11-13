import os
import requests
import json
import time
from typing import Dict, List, Optional, Any
import re
from urllib.parse import urlparse
import hashlib
from openai import OpenAI

class ImageEngine:
    """
    Multi-Model Image Generation Engine
    Supports both OpenAI DALL-E and SeeDream image generation
    """
    
    def __init__(self, provider="openai"):
        """Initialize the image engine with specified provider configuration"""
        self.provider = provider.lower()
        self.max_images = int(os.getenv("MAX_IMAGES_PER_ARTICLE", 5))
        
        if self.provider == "openai":
            self._init_openai()
        elif self.provider == "seedream":
            self._init_seedream()
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'openai' or 'seedream'")
    
    def _init_openai(self):
        """Initialize OpenAI DALL-E configuration"""
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key or api_key.startswith("sk-your-") or api_key == "demo-mode":
            raise ValueError("Please configure a valid OpenAI API key in the .env file")
        
        self.openai_client = OpenAI(api_key=api_key)
        self.dalle_model = os.getenv("DALLE_MODEL", "dall-e-3")
        self.dalle_size = os.getenv("DALLE_SIZE", "1024x1024")
        self.dalle_quality = os.getenv("DALLE_QUALITY", "standard")
        
        # Validate DALL-E size
        self._validate_dalle_size()
        
        # Image style templates based on tone
        self.style_templates = {
            "professional": "clean, minimalist, corporate style, professional lighting, high-quality",
            "conversational": "friendly, approachable, warm lighting, casual but polished",
            "academic": "scholarly, detailed, educational illustration, clear and informative",
            "elegant": "sophisticated, refined, luxurious, beautiful composition, artistic",
            "warm": "cozy, inviting, soft lighting, friendly atmosphere, comfortable",
            "technical": "precise, detailed, schematic style, clear diagrams, technical illustration",
            "creative": "artistic, innovative, bold colors, creative composition, inspiring",
            "playful": "fun, vibrant, colorful, engaging, dynamic composition",
            "dark": "moody, dramatic lighting, dark tones, sophisticated contrast"
        }
        
        print(f"✅ ImageEngine initialized with OpenAI DALL-E (model: {self.dalle_model})")
    
    def _init_seedream(self):
        """Initialize SeeDream configuration using direct API calls"""
        api_key = os.getenv("ARK_API_KEY")
        
        if not api_key:
            raise ValueError("Please configure ARK_API_KEY in the .env file for SeeDream")
        
        # Use direct HTTP API calls
        self.api_key = api_key
        self.base_url = "https://ark.ap-southeast.bytepluses.com/api/v3"
        self.seedream_model = os.getenv("SEEDREAM_MODEL", "seedream-4-0-250828")
        self.seedream_size = os.getenv("SEEDREAM_SIZE", "2K")
        
        print(f"✅ ImageEngine initialized with SeeDream API (model: {self.seedream_model})")

        # Image style templates based on tone
        self.style_templates = {
            "professional": "clean, minimalist, corporate style, professional lighting, high-quality",
            "conversational": "friendly, approachable, warm lighting, casual but polished",
            "academic": "scholarly, detailed, educational illustration, clear and informative",
            "elegant": "sophisticated, refined, luxurious, beautiful composition, artistic",
            "warm": "cozy, inviting, soft lighting, friendly atmosphere, comfortable",
            "technical": "precise, detailed, schematic style, clear diagrams, technical illustration",
            "creative": "artistic, innovative, bold colors, creative composition, inspiring",
            "playful": "fun, vibrant, colorful, engaging, dynamic composition",
            "dark": "moody, dramatic lighting, dark tones, sophisticated contrast"
        }

    
    def generate_images(self, article_data: Dict[str, Any], tone: str = "professional") -> Dict[int, Dict[str, str]]:
        """
        Generate AI images for each article section using OpenAI DALL-E
        
        Args:
            article_data: The generated article data
            tone: The desired tone/style for images
            
        Returns:
            Dictionary mapping section index to image data
        """
        
        try:
            # Generate only one cover image per article
            images = {}

            # Build comprehensive content analysis from the entire article
            cover_source = {
                'heading': article_data.get('title', 'Article Cover'),
                'content': self._extract_comprehensive_content(article_data)
            }

            # Extract keywords from meta description and content for better context
            article_keywords = self._extract_article_keywords(article_data)
            cover_source['keywords'] = article_keywords

            image_prompt = self._create_image_prompt(
                cover_source,
                article_data.get('title', ''),
                tone
            )

            # Generate image using selected provider
            if self.provider == "openai":
                image_data = self._generate_dalle_image(image_prompt, tone, 0)
            elif self.provider == "seedream":
                image_data = self._generate_seedream_image(image_prompt, tone, 0)
            else:
                image_data = None
                
            if image_data:
                # Debug logging for prompt storage
                stored_prompt = image_data.get('prompt', 'NOT_FOUND')
                print(f"\n🎨 IMAGE GENERATION COMPLETE:")
                print(f"   📝 Stored prompt: {stored_prompt[:150]}...")
                print(f"   🔑 Image data keys: {list(image_data.keys())}")
                
                # Use a consistent key for cover image
                images['cover'] = image_data

            return images
            
        except Exception as e:
            print(f"Image generation failed: {e}")
            return self._generate_placeholder_images(article_data, tone)
    
    def _extract_comprehensive_content(self, article_data: Dict[str, Any]) -> str:
        """
        Extract and combine content from entire article for comprehensive analysis
        """
        content_parts = []
        
        # Add title and meta description for context
        if article_data.get('title'):
            content_parts.append(article_data['title'])
        
        if article_data.get('meta_description'):
            content_parts.append(article_data['meta_description'])
        
        # Add all section content
        sections = article_data.get('sections', [])
        for section in sections:
            if section.get('heading'):
                content_parts.append(section['heading'])
            if section.get('content'):
                # Take first 200 words of each section to avoid overwhelming the analysis
                section_content = section['content']
                words = section_content.split()[:200]
                content_parts.append(' '.join(words))
        
        # Add conclusion if available
        if article_data.get('conclusion'):
            conclusion_words = article_data['conclusion'].split()[:100]
            content_parts.append(' '.join(conclusion_words))
        
        return ' '.join(content_parts)
    
    def _extract_article_keywords(self, article_data: Dict[str, Any]) -> List[str]:
        """
        Extract keywords from the article content for better image context
        """
        import re
        
        # Combine all text content
        full_content = self._extract_comprehensive_content(article_data)
        
        # Simple keyword extraction based on frequency and importance
        words = re.findall(r'\b[a-zA-Z]{4,}\b', full_content.lower())
        
        # Common words to exclude
        stop_words = {
            'this', 'that', 'with', 'have', 'they', 'from', 'been', 'your', 
            'more', 'will', 'time', 'like', 'make', 'than', 'into', 'could',
            'other', 'after', 'first', 'well', 'many', 'some', 'what', 'know',
            'would', 'there', 'think', 'people', 'take', 'year', 'good', 'just',
            'most', 'work', 'life', 'only', 'over', 'also', 'back', 'very',
            'where', 'much', 'should', 'through', 'long', 'little', 'before'
        }
        
        # Filter and count word frequency
        word_counts = {}
        for word in words:
            if word not in stop_words and len(word) > 3:
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Return top keywords sorted by frequency
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:15]]
    
    def _create_image_prompt(self, section: Dict[str, Any], title: str, tone: str) -> str:
        """
        Create dynamic, contextually relevant image prompts using advanced prompt engineering
        """
        
        heading = section.get('heading', '')
        content = section.get('content', '')
        keywords = section.get('keywords', [])
        
        # Extract key visual concepts and themes from the section
        key_concepts = self._extract_key_concepts(heading, content, keywords)
        visual_themes = self._analyze_content_themes(heading, content)
        
        # Get style template for the tone
        style_base = self.style_templates.get(tone.lower(), self.style_templates['professional'])
        
        # Build contextually rich prompt using proven prompt engineering techniques
        prompt_structure = []
        
        # 1. Subject/Main Focus (clear, specific description)
        main_subject = self._determine_main_subject(heading, key_concepts, visual_themes)
        prompt_structure.append(f"A {tone.lower()}, high-quality illustration of {main_subject}")
        
        # 2. Context and Setting (environmental details)
        context = self._generate_context_setting(key_concepts, visual_themes, tone)
        if context:
            prompt_structure.append(f"set in {context}")
        
        # 3. Visual Elements and Composition
        visual_elements = self._select_visual_elements(key_concepts, tone)
        if visual_elements:
            prompt_structure.append(f"featuring {visual_elements}")
        
        # 4. Style and Artistic Direction
        artistic_style = self._craft_artistic_style(tone, style_base)
        prompt_structure.append(f"rendered in {artistic_style}")
        
        # 5. Technical Quality and Format
        technical_specs = self._get_technical_specifications(tone)
        prompt_structure.append(technical_specs)
        
        # Combine with proper flow and readability
        full_prompt = ", ".join(prompt_structure)
        
        # Add sophisticated lighting and mood enhancement
        lighting_mood = self._enhance_lighting_mood(tone, visual_themes)
        if lighting_mood:
            full_prompt += f", {lighting_mood}"
        
        # Ensure optimal length while preserving key elements
        return self._optimize_prompt_length(full_prompt, 450)
    
    def _extract_key_concepts(self, heading: str, content: str, keywords: List[str]) -> List[str]:
        """
        Extract key visual concepts from text content using enhanced analysis
        """
        
        # Combine all text sources with proper weighting
        combined_text = f"{heading} {heading} {content} {' '.join(keywords)}".lower()
        
        print(f"\n🎨 IMAGE ANALYSIS: Analyzing content for visual concepts...")
        print(f"   📄 Content length: {len(content)} characters")
        print(f"   🔤 Keywords provided: {len(keywords)}")
        print(f"   📝 Sample content: {content[:200]}...")
        
        # Enhanced concept categories with richer visual associations
        visual_concepts = {
            # Technology & AI - Enhanced crypto detection
            'technology': ['sleek digital interfaces', 'futuristic holographic displays', 'modern smart devices'],
            'ai': ['neural network visualizations', 'abstract data flows', 'algorithmic patterns'],
            'artificial intelligence': ['neural network visualizations', 'machine learning patterns', 'AI interface designs'],
            'blockchain': ['interconnected digital blocks', 'digital chains with glowing nodes', 'cryptographic matrix'],
            'bitcoin': ['golden cryptocurrency symbols', 'Bitcoin logos with charts', 'digital gold coins'],
            'cryptocurrency': ['floating digital currencies', 'crypto trading displays', 'blockchain networks'],
            'crypto': ['cryptocurrency symbols', 'digital currency patterns', 'crypto market visualization'],
            'ethereum': ['Ethereum symbols', 'smart contract visualizations', 'crypto network nodes'],
            'trading': ['real-time market displays', 'candlestick chart patterns', 'crypto trading screens'],
            'digital currency': ['digital coin patterns', 'currency flow visualizations', 'crypto exchange interfaces'],
            'machine learning': ['data visualization patterns', 'algorithmic trees', 'predictive models'],
            
            # Business & Finance - Enhanced
            'business': ['modern corporate boardroom', 'professional team collaboration', 'strategic planning'],
            'finance': ['dynamic financial dashboards', 'investment portfolios', 'market analysis graphs'],
            'financial': ['financial growth charts', 'money management concepts', 'investment strategies'],
            'investment': ['ascending growth trajectories', 'portfolio diversification', 'wealth building concepts'],
            'market': ['economic trend visualizations', 'supply-demand dynamics', 'global market connections'],
            'price': ['price chart movements', 'value indicators', 'market price displays'],
            'prediction': ['forecasting graphics', 'predictive analysis charts', 'future trend visualizations'],
            'analysis': ['data analysis interfaces', 'analytical charts', 'research visualization'],
            'startup': ['innovative workspace', 'entrepreneurial energy', 'breakthrough moments'],
            
            # Health & Wellness
            'health': ['medical innovation symbols', 'wellness lifestyle imagery', 'healthcare technology'],
            'fitness': ['dynamic exercise movements', 'athletic performance', 'health tracking devices'],
            'nutrition': ['vibrant organic foods', 'balanced meal compositions', 'healthy lifestyle choices'],
            'medical': ['advanced medical equipment', 'healthcare professionals', 'treatment innovations'],
            
            # Education & Learning
            'education': ['modern learning environments', 'knowledge transfer concepts', 'academic excellence'],
            'training': ['skill development workshops', 'hands-on learning', 'professional growth'],
            'course': ['interactive classroom settings', 'digital learning platforms', 'educational resources'],
            'learning': ['knowledge acquisition processes', 'study methodologies', 'academic achievement'],
            
            # Travel & Lifestyle
            'travel': ['scenic destination views', 'journey exploration themes', 'cultural experiences'],
            'lifestyle': ['modern living concepts', 'work-life balance', 'personal fulfillment'],
            'home': ['contemporary living spaces', 'family gatherings', 'comfort and security'],
            'real estate': ['architectural showcases', 'property investments', 'home ownership dreams'],
            
            # Industry Specific
            'marketing': ['brand storytelling visuals', 'audience engagement', 'creative campaigns'],
            'design': ['aesthetic compositions', 'creative processes', 'artistic innovations'],
            'innovation': ['breakthrough concepts', 'creative solutions', 'future possibilities'],
            'sustainability': ['eco-friendly practices', 'environmental harmony', 'green innovations']
        }
        
        detected_concepts = []
        concept_priority = {}
        
        # Find matching concepts with weighted scoring
        for concept, visuals in visual_concepts.items():
            if concept in combined_text:
                # Count occurrences for priority (title gets double weight)
                occurrences = combined_text.count(concept)
                
                # Boost priority for keywords that appear in title/heading
                if concept in heading.lower():
                    occurrences += 3
                
                # Check if it appears in the extracted keywords list
                if any(concept in keyword.lower() for keyword in keywords):
                    occurrences += 2
                
                concept_priority[concept] = occurrences
                detected_concepts.extend(visuals[:2])  # Take up to 2 visuals per concept for richer variety
                
                print(f"   ✅ Found concept: '{concept}' (priority: {occurrences})")
        
        # Sort by priority and select top concepts
        primary_concepts = []
        if concept_priority:
            sorted_concepts = sorted(concept_priority.items(), key=lambda x: x[1], reverse=True)
            primary_concepts = [concept for concept, priority in sorted_concepts[:5]]  # Top 5 concepts
            print(f"   🎯 Top concepts detected: {primary_concepts}")
        
        # Fallback to generic professional elements if no concepts detected
        if not detected_concepts:
            detected_concepts = ['modern abstract composition', 'clean professional design', 'contemporary visual elements']
            print(f"   ⚠️ No specific concepts found, using fallback: {detected_concepts}")
        else:
            print(f"   🎨 Selected visual concepts: {detected_concepts[:6]}")
        
        return detected_concepts[:6]  # Return top 6 concepts for richer prompts
    
    def _analyze_content_themes(self, heading: str, content: str) -> List[str]:
        """
        Analyze content to identify overarching themes and emotional context
        """
        
        text = f"{heading} {content}".lower()
        
        # Theme patterns for deeper context understanding
        theme_patterns = {
            'growth': ['increase', 'grow', 'expand', 'rise', 'boost', 'improve', 'progress'],
            'innovation': ['new', 'innovative', 'revolutionary', 'breakthrough', 'cutting-edge', 'advanced'],
            'security': ['secure', 'protect', 'safe', 'trust', 'reliable', 'stable'],
            'success': ['achieve', 'successful', 'win', 'victory', 'accomplish', 'excel'],
            'collaboration': ['team', 'together', 'partnership', 'cooperation', 'community'],
            'future': ['future', 'tomorrow', 'next', 'upcoming', 'predict', 'forecast'],
            'global': ['world', 'global', 'international', 'worldwide', 'universal'],
            'personal': ['personal', 'individual', 'custom', 'tailored', 'specific']
        }
        
        detected_themes = []
        for theme, patterns in theme_patterns.items():
            if any(pattern in text for pattern in patterns):
                detected_themes.append(theme)
        
        return detected_themes[:3]
    
    def _determine_main_subject(self, heading: str, concepts: List[str], themes: List[str]) -> str:
        """
        Determine the main subject for the image based on content analysis
        """
        
        # Enhanced priority subject mappings based on content type
        subject_mappings = {
            # Cryptocurrency & Blockchain - Enhanced detection
            'bitcoin': 'golden Bitcoin cryptocurrency symbols with rising price charts and digital elements',
            'btc': 'Bitcoin cryptocurrency logo with financial growth indicators and market data',
            'cryptocurrency': 'multiple cryptocurrency symbols floating with blockchain network background',
            'crypto': 'cryptocurrency trading interface with digital coins and market charts',
            'ethereum': 'Ethereum cryptocurrency symbols with smart contract visualizations',
            'blockchain': 'interconnected digital blocks with glowing cryptocurrency connections',
            'digital currency': 'digital currency symbols with futuristic financial interfaces',
            'trading': 'cryptocurrency trading screens with candlestick charts and market data',
            
            # AI & Technology
            'ai': 'abstract neural network with flowing data streams and AI interfaces',
            'artificial intelligence': 'AI neural network patterns with machine learning visualizations',
            'technology': 'sleek modern technology interface with holographic elements',
            'machine learning': 'algorithmic data flows with predictive analytics visualization',
            
            # Business & Finance
            'business': 'professional business meeting with modern financial technology',
            'finance': 'dynamic financial dashboard with growth indicators and charts',
            'financial': 'financial analysis workspace with investment charts and data',
            'investment': 'investment portfolio visualization with growth trending upward',
            'market': 'financial market data displays with economic trend indicators',
            'analysis': 'data analysis interface with charts and predictive models',
            
            # Other categories
            'health': 'modern healthcare innovation with medical technology',
            'education': 'contemporary learning environment with digital educational tools'
        }
        
        heading_lower = heading.lower()
        combined_text = f"{heading_lower} {' '.join(concepts)}"
        
        print(f"\n🎯 MAIN SUBJECT DETECTION:")
        print(f"   📝 Analyzing: '{heading}'")
        print(f"   🔍 Concepts: {concepts[:3]}")
        
        # Find the best matching subject with enhanced detection
        best_match = None
        best_priority = 0
        
        for key, subject in subject_mappings.items():
            priority = 0
            
            # Check in heading (highest priority)
            if key in heading_lower:
                priority += 10
                print(f"   ✅ Found '{key}' in heading (priority +10)")
            
            # Check in concepts
            concept_matches = sum(1 for concept in concepts if key in concept.lower())
            if concept_matches > 0:
                priority += concept_matches * 3
                print(f"   ✅ Found '{key}' in {concept_matches} concept(s) (priority +{concept_matches * 3})")
            
            # Check for related terms
            related_terms = {
                'bitcoin': ['btc', 'satoshi', 'crypto', 'cryptocurrency'],
                'crypto': ['bitcoin', 'ethereum', 'blockchain', 'digital currency'],
                'blockchain': ['crypto', 'bitcoin', 'ethereum', 'digital ledger'],
                'finance': ['financial', 'money', 'investment', 'trading'],
                'ai': ['artificial intelligence', 'machine learning', 'neural']
            }
            
            if key in related_terms:
                for related in related_terms[key]:
                    if related in combined_text:
                        priority += 1
                        print(f"   ✅ Found related term '{related}' for '{key}' (priority +1)")
            
            if priority > best_priority:
                best_priority = priority
                best_match = subject
                print(f"   🏆 New best match: '{key}' -> '{subject}' (total priority: {priority})")
        
        # If we found a high-confidence match, use it
        if best_match and best_priority >= 3:
            print(f"   🎯 Selected main subject: {best_match}")
            return best_match
        
        # Fallback based on themes
        if 'growth' in themes:
            fallback = 'ascending growth visualization with dynamic financial elements'
        elif 'innovation' in themes:
            fallback = 'innovative concept representation with futuristic technology elements'
        elif 'collaboration' in themes:
            fallback = 'team collaboration in modern workspace with digital technology'
        else:
            fallback = 'modern professional concept illustration with clean design elements'
        
        print(f"   ⚠️ Using theme-based fallback: {fallback}")
        return fallback
    
    def _generate_context_setting(self, concepts: List[str], themes: List[str], tone: str) -> str:
        """
        Generate appropriate context and setting for the image
        """
        
        # Context based on detected concepts and themes
        context_options = {
            'business': 'a sleek modern office environment with floor-to-ceiling windows',
            'technology': 'a futuristic digital landscape with ambient lighting',
            'finance': 'a sophisticated trading floor with multiple screens',
            'health': 'a bright, clean medical facility with advanced equipment',
            'education': 'an innovative classroom with interactive technology'
        }
        
        # Check concepts for context clues
        for concept in concepts:
            for key, context in context_options.items():
                if key in concept.lower():
                    return context
        
        # Theme-based context
        if 'global' in themes:
            return 'a world map background with connecting network lines'
        elif 'future' in themes:
            return 'a futuristic environment with holographic displays'
        elif 'growth' in themes:
            return 'an upward trending environment with dynamic elements'
        
        # Tone-based fallback context
        tone_contexts = {
            'professional': 'a clean, minimalist professional environment',
            'elegant': 'a sophisticated space with refined architectural elements',
            'warm': 'a comfortable, welcoming space with natural lighting',
            'creative': 'an inspiring creative workspace with artistic elements'
        }
        
        return tone_contexts.get(tone.lower(), 'a modern professional setting')
    
    def _select_visual_elements(self, concepts: List[str], tone: str) -> str:
        """
        Select specific visual elements to enhance the composition
        """
        
        elements = []
        
        # Extract visual elements from concepts
        for concept in concepts[:3]:  # Use top 3 concepts
            if 'digital' in concept:
                elements.append('glowing digital interfaces')
            elif 'chart' in concept or 'graph' in concept:
                elements.append('dynamic data visualizations')
            elif 'network' in concept:
                elements.append('interconnected node patterns')
            elif 'modern' in concept:
                elements.append('sleek contemporary design elements')
        
        # Add tone-specific elements
        tone_elements = {
            'professional': 'geometric shapes and clean lines',
            'elegant': 'sophisticated gradients and refined textures',
            'warm': 'soft organic shapes and natural textures',
            'creative': 'bold artistic elements and vibrant accents',
            'technical': 'precise diagrams and structured layouts'
        }
        
        if tone.lower() in tone_elements:
            elements.append(tone_elements[tone.lower()])
        
        return ', '.join(elements) if elements else 'balanced compositional elements'
    
    def _craft_artistic_style(self, tone: str, style_base: str) -> str:
        """
        Craft detailed artistic style description
        """
        
        # Enhanced style templates with more specific descriptions
        enhanced_styles = {
            'professional': 'crisp vector illustration style with corporate color palette, clean typography, and minimalist composition',
            'conversational': 'approachable illustration style with friendly colors, soft edges, and welcoming visual hierarchy',
            'academic': 'scholarly infographic style with clear information design, educational color scheme, and structured layout',
            'elegant': 'sophisticated artistic style with premium color palette, refined typography, and luxurious composition',
            'warm': 'inviting illustration style with natural color tones, soft lighting, and comfortable visual flow',
            'technical': 'precise technical illustration style with accurate diagrams, systematic color coding, and structured presentation',
            'creative': 'artistic creative style with bold color choices, innovative composition, and inspiring visual elements',
            'playful': 'vibrant illustration style with energetic colors, dynamic shapes, and engaging visual rhythm',
            'dark': 'sophisticated dark theme with premium contrast, dramatic lighting, and mysterious atmospheric elements'
        }
        
        return enhanced_styles.get(tone.lower(), enhanced_styles['professional'])
    
    def _get_technical_specifications(self, tone: str) -> str:
        """
        Get technical quality specifications for the image
        """
        
        base_specs = [
            'high resolution 4K quality',
            'professional grade composition',
            'balanced color harmony',
            'optimal contrast and clarity'
        ]
        
        # Add tone-specific technical requirements
        tone_specs = {
            'professional': 'corporate brand standards compliance',
            'elegant': 'luxury brand aesthetic quality',
            'technical': 'technical illustration precision',
            'creative': 'artistic excellence standards'
        }
        
        if tone.lower() in tone_specs:
            base_specs.append(tone_specs[tone.lower()])
        
        return ', '.join(base_specs)
    
    def _enhance_lighting_mood(self, tone: str, themes: List[str]) -> str:
        """
        Add sophisticated lighting and mood enhancement
        """
        
        lighting_options = {
            'professional': 'studio lighting with soft shadows and professional ambiance',
            'elegant': 'premium lighting with sophisticated mood and refined atmosphere',
            'warm': 'natural warm lighting with cozy ambiance and inviting glow',
            'creative': 'dramatic artistic lighting with inspiring mood and creative energy',
            'technical': 'clear consistent lighting with precision focus and analytical clarity'
        }
        
        base_lighting = lighting_options.get(tone.lower(), lighting_options['professional'])
        
        # Theme-based mood enhancements
        mood_enhancements = []
        if 'growth' in themes:
            mood_enhancements.append('uplifting optimistic atmosphere')
        if 'innovation' in themes:
            mood_enhancements.append('forward-thinking progressive mood')
        if 'success' in themes:
            mood_enhancements.append('confident achievement ambiance')
        
        if mood_enhancements:
            return f"{base_lighting}, {', '.join(mood_enhancements)}"
        
        return base_lighting
    
    def _optimize_prompt_length(self, prompt: str, max_length: int) -> str:
        """
        Optimize prompt length while preserving key elements
        """
        
        if len(prompt) <= max_length:
            return prompt
        
        # Split by commas and prioritize sections
        sections = [s.strip() for s in prompt.split(',')]
        
        # Priority order: subject, context, style, technical specs
        essential_sections = sections[:3]  # Keep first 3 sections
        optional_sections = sections[3:]
        
        # Rebuild with essential sections first
        optimized = ', '.join(essential_sections)
        
        # Add optional sections if space allows
        for section in optional_sections:
            if len(optimized) + len(section) + 2 <= max_length:  # +2 for ', '
                optimized += f', {section}'
            else:
                break
        
        return optimized
    
    def _generate_dalle_image(self, prompt: str, tone: str, index: int) -> Optional[Dict[str, str]]:
        """
        Generate a single image using OpenAI DALL-E API with retry logic
        """
        
        max_retries = 3
        retry_delay = 2  # seconds
        reason = "Unknown error occurred during OpenAI DALL-E generation."
        
        for attempt in range(max_retries):
            try:
                # Optimize prompt for DALL-E (max 4000 characters, but keeping it shorter for better results)
                optimized_prompt = self._optimize_prompt_for_dalle(prompt)
                
                print(f"Generating image {index + 1} (attempt {attempt + 1}/{max_retries})...")
                
                # Generate image using DALL-E
                response = self.openai_client.images.generate(
                    model=self.dalle_model,
                    prompt=optimized_prompt,
                    size=self.dalle_size,
                    n=1,
                    # style="vivid" if tone.lower() in ["creative", "elegant"] else "natural"
                )
                
                # Get the generated image URL
                image_url = response.data[0].url
                
                # Save image locally
                local_path = self._save_image_locally(image_url, index)
                
                print(f"✅ Successfully generated image {index + 1}")
                
                return {
                    'url': image_url,
                    'local_path': local_path,
                    'caption': self._generate_image_caption(prompt),
                    'alt_text': self._generate_alt_text(prompt),
                    'prompt': optimized_prompt,
                    'tone': tone,
                    'model': self.dalle_model,
                    'generated': True
                }
                    
            except Exception as e:
                error_message = str(e)
                print(f"❌ DALL-E attempt {attempt + 1} failed: {error_message}")
                
                # Check if it's a server error (5xx) that we should retry
                if "500" in error_message or "502" in error_message or "503" in error_message or "server_error" in error_message:
                    if attempt < max_retries - 1:
                        print(f"🔄 Server error detected. Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        print("❌ Max retries reached for server error. Using placeholder image.")
                        reason = "OpenAI DALL-E server is experiencing issues. Please try regenerating in a few minutes."
                        break
                
                # For other errors (rate limit, invalid prompt, etc.), don't retry
                elif "rate_limit" in error_message:
                    print("⏳ Rate limit exceeded. Using placeholder image.")
                    reason = "OpenAI DALL-E rate limit exceeded. Please wait a moment and try regenerating."
                    break
                elif "content_policy" in error_message:
                    print("🚫 Content policy violation. Using placeholder image.")
                    reason = "Image prompt violates OpenAI content policy. Please modify the prompt and try again."
                    break
                else:
                    print(f"❌ Unretryable error: {error_message}")
                    reason = f"OpenAI DALL-E error: {error_message}. Please try regenerating with a different prompt."
                    break
        
        # If all attempts failed, return placeholder
        print(f"🖼️ Falling back to placeholder image for section {index + 1}")
        return self._create_placeholder_image(prompt, index, reason)
    
    def _generate_seedream_image(self, prompt: str, tone: str, index: int) -> Optional[Dict[str, str]]:
        """
        Generate a single image using SeeDream API with retry logic
        """
        
        max_retries = 3
        retry_delay = 2  # seconds
        reason = "Unknown error occurred during SeeDream generation."
        
        for attempt in range(max_retries):
            try:
                # Optimize prompt for SeeDream
                optimized_prompt = self._optimize_prompt_for_seedream(prompt)
                
                print(f"Generating image {index + 1} with SeeDream (attempt {attempt + 1}/{max_retries})...")
                print(f"Using model: {self.seedream_model}")
                
                # Generate image using SeeDream direct API call
                image_url = self._generate_seedream_via_api(optimized_prompt)
                
                if not image_url:
                    # Treat empty response as a retryable error
                    raise Exception("No image URL returned from SeeDream API - connection may have timed out")
                
                # Save image locally
                local_path = self._save_image_locally(image_url, index)
                
                print(f"✅ Successfully generated image {index + 1} with SeeDream")
                
                return {
                    'url': image_url,
                    'local_path': local_path,
                    'caption': self._generate_image_caption(prompt),
                    'alt_text': self._generate_alt_text(prompt),
                    'prompt': optimized_prompt,
                    'tone': tone,
                    'model': self.seedream_model,
                    'generated': True
                }
                    
            except Exception as e:
                error_message = str(e).lower()
                print(f"❌ SeeDream attempt {attempt + 1} failed: {str(e)}")
                
                # Define retryable errors
                retryable_errors = [
                    "timeout", "connection", "max retries exceeded", "connection timed out",
                    "httpsconnectionpool", "connecttimeouterror", "no image url returned",
                    "500", "502", "503", "504", "server_error", "internal server error"
                ]
                
                # Check if it's a retryable error
                is_retryable = any(error_keyword in error_message for error_keyword in retryable_errors)
                
                if is_retryable and attempt < max_retries - 1:
                    print(f"🔄 Retryable error detected. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                elif is_retryable:
                    print("❌ Max retries reached for network/server error. Using placeholder image.")
                    reason = "SeeDream API connection failed after multiple attempts. Please check your internet connection and try again."
                    break
                else:
                    # Non-retryable errors (rate limit, content policy, etc.)
                    if "rate_limit" in error_message:
                        print("⏳ Rate limit exceeded. Using placeholder image.")
                        reason = "SeeDream API rate limit exceeded. Please wait a moment and try regenerating."
                    elif "content_policy" in error_message or "inappropriate" in error_message:
                        print("🚫 Content policy violation. Using placeholder image.")
                        reason = "Image prompt violates SeeDream content policy. Please modify the prompt and try again."
                    else:
                        print(f"❌ Non-retryable error: {str(e)}")
                        reason = f"SeeDream API error: {str(e)}. Please try regenerating with different settings."
                    break
        
        # If all attempts failed, return placeholder
        print(f"🖼️ Falling back to placeholder image for section {index + 1}")
        return self._create_placeholder_image(prompt, index, reason)
    
    def _optimize_prompt_for_dalle(self, prompt: str) -> str:
        """
        Optimize prompt specifically for DALL-E's requirements and capabilities
        """
        
        # DALL-E works better with more descriptive, visual prompts
        # Remove any technical jargon and focus on visual elements
        
        # Clean up the prompt
        optimized = prompt.lower()
        
        # Add DALL-E-specific style guidance
        style_additions = [
            "high quality digital art",
            "professional illustration", 
            "clean composition",
            "modern design aesthetic"
        ]
        
        # Ensure the prompt is descriptive and visual
        if len(optimized) < 50:
            optimized += ", detailed professional illustration, modern style"
        
        # Add style guidance
        optimized += f", {', '.join(style_additions[:2])}"
        
        # Limit length (DALL-E has a 4000 character limit, but shorter is often better)
        if len(optimized) > 400:
            optimized = optimized[:400].rsplit(',', 1)[0]
        
        return optimized.capitalize()
    
    def _optimize_prompt_for_seedream(self, prompt: str) -> str:
        """
        Optimize prompt specifically for SeeDream's requirements and capabilities
        """
        
        # SeeDream works well with detailed, cinematic prompts
        optimized = prompt.lower()
        
        # Add SeeDream-specific style guidance for better results
        style_additions = [
            "high quality digital art",
            "cinematic composition",
            "detailed rendering",
            "professional photography style"
        ]
        
        # Ensure the prompt is descriptive and visual
        if len(optimized) < 50:
            optimized += ", detailed professional illustration, cinematic style"
        
        # Add style guidance
        optimized += f", {', '.join(style_additions[:2])}"
        
        # SeeDream can handle longer prompts better than DALL-E
        if len(optimized) > 800:
            optimized = optimized[:800].rsplit(',', 1)[0]
        
        return optimized.capitalize()
    
    def _generate_seedream_via_api(self, prompt: str) -> Optional[str]:
        """
        Generate image using direct SeeDream API call with improved error handling
        """
        
        try:
            import requests
            from requests.exceptions import ConnectTimeout, ReadTimeout, ConnectionError, Timeout
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': self.seedream_model,
                'prompt': prompt,
                'size': self.seedream_size,
                'response_format': 'url',
                'watermark': False
            }
            
            # Use longer timeout and handle specific timeout types
            response = requests.post(
                f"{self.base_url}/images/generations",
                headers=headers,
                json=payload,
                timeout=(30, 120)  # (connect_timeout, read_timeout)
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'data' in result and len(result['data']) > 0 and 'url' in result['data'][0]:
                    return result['data'][0]['url']
                else:
                    print(f"SeeDream API returned invalid response structure: {result}")
                    return None
            else:
                print(f"SeeDream API HTTP error: {response.status_code} - {response.text}")
                # Re-raise for retry logic to catch
                raise Exception(f"SeeDream API HTTP {response.status_code}: {response.text}")
                
        except (ConnectTimeout, ConnectionError) as e:
            print(f"SeeDream API connection error: {str(e)}")
            # Re-raise connection errors for retry
            raise Exception(f"Connection error to SeeDream API: {str(e)}")
            
        except (ReadTimeout, Timeout) as e:
            print(f"SeeDream API timeout error: {str(e)}")
            # Re-raise timeout errors for retry
            raise Exception(f"Timeout error from SeeDream API: {str(e)}")
            
        except requests.exceptions.RequestException as e:
            print(f"SeeDream API request error: {str(e)}")
            # Re-raise request errors for retry
            raise Exception(f"Request error to SeeDream API: {str(e)}")
            
        except Exception as e:
            print(f"Unexpected SeeDream API error: {str(e)}")
            # Re-raise unexpected errors for retry
            raise Exception(f"Unexpected SeeDream API error: {str(e)}")
            
        return None

    def _validate_dalle_size(self):
        """
        Ensure the configured image size is one of the supported DALL-E sizes.
        If not, map it to a safe default and log the change.
        """
        supported = {"1024x1024", "1024x1792", "1792x1024"}
        if self.dalle_size not in supported:
            # Try to coerce common aspect ratios to closest supported value
            size_map = {
                "1024x720": "1024x1024",
                "800x600": "1024x1024",
                "1280x720": "1024x1792",
            }
            coerced = size_map.get(self.dalle_size)
            if coerced:
                print(f"Invalid DALLE_SIZE '{self.dalle_size}' detected. Coercing to supported size '{coerced}'.")
                self.dalle_size = coerced
            else:
                print(f"Invalid DALLE_SIZE '{self.dalle_size}' detected. Falling back to '1024x1024'.")
                self.dalle_size = "1024x1024"
    

    
    def _save_image_locally(self, image_url: str, index: int) -> str:
        """
        Save generated image to local assets folder
        """
        
        try:
            # Create unique filename
            timestamp = int(time.time())
            filename = f"generated_image_{index}_{timestamp}.jpg"
            local_path = os.path.join("assets", "outputs", filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Download and save image
            response = requests.get(image_url, timeout=30)
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                return local_path
            
        except Exception as e:
            print(f"Failed to save image locally: {e}")
        
        return image_url  # Return original URL if local save fails
    
    def _generate_image_caption(self, prompt: str) -> str:
        """
        Generate a user-friendly caption for the image
        """
        
        # Extract main concept from prompt
        words = prompt.lower().split()
        
        # Find key descriptive words
        key_words = []
        important_terms = ['illustration', 'concept', 'representing', 'featuring', 'showing']
        
        for word in words:
            if len(word) > 4 and word not in important_terms:
                key_words.append(word.capitalize())
        
        if key_words:
            return f"Professional illustration showcasing {' and '.join(key_words[:3])}"
        
        return "AI-generated professional illustration"
    
    def _generate_alt_text(self, prompt: str) -> str:
        """
        Generate SEO-friendly alt text for the image
        """
        
        # Simplify prompt for alt text
        alt_text = prompt.split(',')[0]  # Take first part of prompt
        alt_text = re.sub(r'create|illustration|image|of|the', '', alt_text, flags=re.IGNORECASE)
        alt_text = alt_text.strip().capitalize()
        
        return f"{alt_text} - Professional AI illustration" if alt_text else "AI-generated professional illustration"
    
    def _generate_placeholder_images(self, article_data: Dict[str, Any], tone: str) -> Dict[int, Dict[str, str]]:
        """
        Generate placeholder images when API is not available
        """
        
        sections = article_data.get('sections', [])
        placeholder_images = {}
        
        # Determine appropriate fallback reason based on provider
        if self.provider == "openai":
            fallback_reason = "OpenAI DALL-E API failed during initial generation. Please try regenerating the images."
        elif self.provider == "seedream":
            fallback_reason = "SeeDream API failed during initial generation. Please check your network connection and try regenerating."
        else:
            fallback_reason = "AI image generation service failed during initial generation."
        
        for i, section in enumerate(sections[:self.max_images]):
            heading = section.get('heading', f'Section {i+1}')
            
            # Create placeholder image data
            placeholder_images[i] = {
                'url': f"https://picsum.photos/800/600?random={hash(heading) % 1000}",
                'local_path': f"assets/placeholder_{i}.jpg",
                'caption': f"Illustration for: {heading}",
                'alt_text': f"{heading} - Professional illustration",
                'prompt': f"Placeholder for {heading}",
                'tone': tone,
                'is_placeholder': True,
                'fallback_reason': fallback_reason
            }
        
        return placeholder_images
    
    def _create_placeholder_image(self, prompt: str, index: int, reason: str = None) -> Dict[str, str]:
        """
        Create a single placeholder image entry with better fallback
        """
        
        # Use a more professional placeholder service with better images
        seed = hash(prompt) % 1000
        
        # Determine appropriate fallback reason
        if not reason:
            if self.provider == "openai":
                reason = "OpenAI DALL-E API temporarily unavailable. Please try again in a few moments."
            elif self.provider == "seedream":
                reason = "SeeDream API connection failed. Please check your network connection and try again."
            else:
                reason = "AI image generation service temporarily unavailable."
        
        return {
            'url': f"https://picsum.photos/800/600?random={seed}",
            'local_path': f"assets/placeholder_{index}_{seed}.jpg",
            'caption': f"Professional placeholder for: {self._generate_image_caption(prompt)}",
            'alt_text': f"Placeholder image - {self._generate_alt_text(prompt)}",
            'prompt': prompt,
            'tone': 'placeholder',
            'is_placeholder': True,
            'generated': False,
            'fallback_reason': reason
        }
    
    def get_image_stats(self, images: Dict[int, Dict[str, str]]) -> Dict[str, Any]:
        """
        Get statistics about generated images
        """
        
        total_images = len(images)
        placeholder_count = sum(1 for img in images.values() if img.get('is_placeholder', False))
        generated_count = total_images - placeholder_count
        
        return {
            'total_images': total_images,
            'generated_count': generated_count,
            'placeholder_count': placeholder_count,
            'success_rate': (generated_count / total_images * 100) if total_images > 0 else 0,
            'model_used': self.dalle_model if self.provider == "openai" else self.seedream_model
        }
    
    def regenerate_image(self, section_data: Dict[str, Any], tone: str, index: int) -> Optional[Dict[str, str]]:
        """
        Regenerate a specific image with improved prompt using current provider
        """
        
        # Create enhanced prompt for regeneration
        enhanced_prompt = self._create_image_prompt(section_data, "", tone)
        enhanced_prompt += ", enhanced quality, improved composition, professional grade"
        
        # Generate image using selected provider
        if self.provider == "openai":
            return self._generate_dalle_image(enhanced_prompt, tone, index)
        elif self.provider == "seedream":
            return self._generate_seedream_image(enhanced_prompt, tone, index)
        else:
            return None
    
    def regenerate_image_with_prompt(self, custom_prompt: str, tone: str, index: int) -> Optional[Dict[str, str]]:
        """
        Regenerate a specific image with a custom prompt using current provider
        """
        
        # Generate image using selected provider with custom prompt
        if self.provider == "openai":
            return self._generate_dalle_image(custom_prompt, tone, index)
        elif self.provider == "seedream":
            return self._generate_seedream_image(custom_prompt, tone, index)
        else:
            return None