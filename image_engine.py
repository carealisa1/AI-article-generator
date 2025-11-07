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
    OpenAI DALL-E Image Generation Engine
    Generates contextually relevant, professionally styled images using DALL-E 3
    """
    
    def __init__(self):
        """Initialize the image engine with OpenAI DALL-E configuration"""
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key or api_key.startswith("sk-your-") or api_key == "demo-mode":
            raise ValueError("Please configure a valid OpenAI API key in the .env file")
        
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("DALLE_MODEL", "dall-e-3")
        self.default_size = os.getenv("DALLE_SIZE", "1024x1024")
        self.quality = os.getenv("DALLE_QUALITY", "standard")
        self.max_images = int(os.getenv("MAX_IMAGES_PER_ARTICLE", 5))

        # Image style templates based on tone
        self.style_templates = {
            "professional": "clean, minimalist, corporate style, professional lighting, high-quality",
            "conversational": "friendly, approachable, warm lighting, casual but polished",
            "academic": "scholarly, detailed, educational illustration, clear and informative",
            "elegant": "sophisticated, refined, luxurious, beautiful composition, artistic",
            "warm": "cozy, inviting, soft lighting, friendly atmosphere, comfortable",
            "technical": "precise, detailed, schematic style, clear diagrams, technical illustration",
            "creative": "artistic, innovative, bold colors, creative composition, inspiring"
        }
        # Validate size - map invalid values to a supported default
        self._validate_image_size()
    
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

            # Build a representative section for prompt generation
            cover_source = {
                'heading': article_data.get('title', 'Article Cover'),
                'content': ''
            }

            # Prefer the first section content to enrich the prompt
            sections = article_data.get('sections', [])
            if sections:
                cover_source['content'] = sections[0].get('content', '')

            image_prompt = self._create_image_prompt(
                cover_source,
                article_data.get('title', ''),
                tone
            )

            image_data = self._generate_dalle_image(image_prompt, tone, 0)
            if image_data:
                # Use a consistent key for cover image
                images['cover'] = image_data

            return images
            
        except Exception as e:
            print(f"Image generation failed: {e}")
            return self._generate_placeholder_images(article_data, tone)
    
    def _create_image_prompt(self, section: Dict[str, Any], title: str, tone: str) -> str:
        """
        Create dynamic, contextually relevant image prompts
        """
        
        heading = section.get('heading', '')
        content = section.get('content', '')
        keywords = section.get('keywords', [])
        
        # Extract key nouns and concepts from the section
        key_concepts = self._extract_key_concepts(heading, content, keywords)
        
        # Get style template for the tone
        style_base = self.style_templates.get(tone.lower(), self.style_templates['professional'])
        
        # Build comprehensive prompt
        prompt_parts = [
            "Create a stunning, professional illustration representing",
            f"the concept of '{heading.lower()}'",
        ]
        
        # Add key concepts
        if key_concepts:
            concepts_str = ', '.join(key_concepts[:3])  # Limit to top 3 concepts
            prompt_parts.append(f"featuring elements of {concepts_str}")
        
        # Add style and mood
        prompt_parts.extend([
            f"Style: {style_base}",
            f"Mood: {tone.lower()}, engaging, visually appealing",
            "Format: editorial illustration, high resolution, detailed"
        ])
        
        # Combine and clean up the prompt
        full_prompt = ", ".join(prompt_parts)
        
        # Add specific visual enhancements based on detected topics
        visual_enhancements = self._get_visual_enhancements(key_concepts, tone)
        if visual_enhancements:
            full_prompt += f", {visual_enhancements}"
        
        return full_prompt[:500]  # Limit prompt length
    
    def _extract_key_concepts(self, heading: str, content: str, keywords: List[str]) -> List[str]:
        """
        Extract key visual concepts from text content
        """
        
        # Combine all text sources
        text = f"{heading} {content} {' '.join(keywords)}".lower()
        
        # Define concept categories with associated visual elements
        visual_concepts = {
            # Technology
            'technology': ['digital interface', 'futuristic elements', 'modern devices'],
            'ai': ['neural networks', 'digital brain', 'algorithmic patterns'],
            'blockchain': ['connected blocks', 'digital chains', 'cryptographic symbols'],
            'bitcoin': ['gold coins', 'digital currency', 'financial charts'],
            'cryptocurrency': ['digital coins', 'trading charts', 'blockchain networks'],
            
            # Business & Finance
            'business': ['professional setting', 'corporate environment', 'meeting room'],
            'finance': ['financial charts', 'money symbols', 'banking elements'],
            'investment': ['growth charts', 'financial graphs', 'portfolio visualization'],
            'trading': ['market charts', 'candlestick graphs', 'trading floor'],
            'market': ['supply and demand curves', 'economic indicators', 'market trends'],
            
            # Health & Wellness
            'health': ['medical symbols', 'wellness imagery', 'healthcare setting'],
            'fitness': ['exercise equipment', 'active lifestyle', 'sports elements'],
            'nutrition': ['healthy foods', 'balanced diet', 'organic produce'],
            
            # Education & Learning
            'education': ['books', 'learning environment', 'academic setting'],
            'training': ['skill development', 'workshop setting', 'instructional materials'],
            'course': ['classroom', 'educational materials', 'learning journey'],
            
            # Travel & Lifestyle
            'travel': ['destinations', 'journey elements', 'exploration themes'],
            'lifestyle': ['modern living', 'daily activities', 'personal choices'],
            'home': ['domestic setting', 'comfortable space', 'family environment']
        }
        
        detected_concepts = []
        
        # Find matching concepts
        for concept, visuals in visual_concepts.items():
            if concept in text:
                detected_concepts.extend(visuals[:1])  # Take one visual per concept
        
        # If no specific concepts found, use generic professional elements
        if not detected_concepts:
            detected_concepts = ['abstract professional design', 'clean composition']
        
        return detected_concepts[:3]  # Limit to top 3 concepts
    
    def _get_visual_enhancements(self, concepts: List[str], tone: str) -> str:
        """
        Get additional visual enhancements based on concepts and tone
        """
        
        enhancements = []
        
        # Tone-based enhancements
        tone_enhancements = {
            'professional': 'clean lines, corporate colors, minimalist design',
            'conversational': 'friendly colors, approachable design, welcoming atmosphere',
            'academic': 'educational clarity, informative layout, scholarly presentation',
            'elegant': 'sophisticated palette, refined composition, luxury feel',
            'warm': 'cozy atmosphere, soft textures, inviting colors',
            'technical': 'precise details, technical accuracy, clear diagrams',
            'creative': 'artistic flair, bold creativity, inspiring composition'
        }
        
        base_enhancement = tone_enhancements.get(tone.lower(), tone_enhancements['professional'])
        enhancements.append(base_enhancement)
        
        # Lighting and composition
        enhancements.extend([
            'professional lighting',
            'balanced composition',
            'high detail and clarity',
            '16:9 aspect ratio suitable for web use'
        ])
        
        return ', '.join(enhancements)
    
    def _generate_dalle_image(self, prompt: str, tone: str, index: int) -> Optional[Dict[str, str]]:
        """
        Generate a single image using OpenAI DALL-E API with retry logic
        """
        
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Optimize prompt for DALL-E (max 4000 characters, but keeping it shorter for better results)
                optimized_prompt = self._optimize_prompt_for_dalle(prompt)
                
                print(f"Generating image {index + 1} (attempt {attempt + 1}/{max_retries})...")
                
                # Generate image using DALL-E
                response = self.client.images.generate(
                    model=self.model,
                    prompt=optimized_prompt,
                    size=self.default_size,
                    quality=self.quality,
                    n=1,
                    style="vivid" if tone.lower() in ["creative", "elegant"] else "natural"
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
                    'model': self.model,
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
                        break
                
                # For other errors (rate limit, invalid prompt, etc.), don't retry
                elif "rate_limit" in error_message:
                    print("⏳ Rate limit exceeded. Using placeholder image.")
                    break
                elif "content_policy" in error_message:
                    print("🚫 Content policy violation. Using placeholder image.")
                    break
                else:
                    print(f"❌ Unretryable error: {error_message}")
                    break
        
        # If all attempts failed, return placeholder
        print(f"🖼️ Falling back to placeholder image for section {index + 1}")
        return self._create_placeholder_image(prompt, index)
    
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

    def _validate_image_size(self):
        """
        Ensure the configured image size is one of the supported DALL-E sizes.
        If not, map it to a safe default and log the change.
        """
        supported = {"1024x1024", "1024x1792", "1792x1024"}
        if self.default_size not in supported:
            # Try to coerce common aspect ratios to closest supported value
            size_map = {
                "1024x720": "1024x1024",
                "800x600": "1024x1024",
                "1280x720": "1024x1792",
            }
            coerced = size_map.get(self.default_size)
            if coerced:
                print(f"Invalid DALLE_SIZE '{self.default_size}' detected. Coercing to supported size '{coerced}'.")
                self.default_size = coerced
            else:
                print(f"Invalid DALLE_SIZE '{self.default_size}' detected. Falling back to '1024x1024'.")
                self.default_size = "1024x1024"
    

    
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
        
        # Placeholder service URLs (using picsum for high-quality placeholders)
        placeholder_bases = [
            "https://picsum.photos/800/600?random=",
            "https://via.placeholder.com/800x600/667eea/ffffff?text=",
        ]
        
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
                'is_placeholder': True
            }
        
        return placeholder_images
    
    def _create_placeholder_image(self, prompt: str, index: int) -> Dict[str, str]:
        """
        Create a single placeholder image entry with better fallback
        """
        
        # Use a more professional placeholder service with better images
        seed = hash(prompt) % 1000
        
        return {
            'url': f"https://picsum.photos/800/600?random={seed}",
            'local_path': f"assets/placeholder_{index}_{seed}.jpg",
            'caption': f"Professional placeholder for: {self._generate_image_caption(prompt)}",
            'alt_text': f"Placeholder image - {self._generate_alt_text(prompt)}",
            'prompt': prompt,
            'tone': 'placeholder',
            'is_placeholder': True,
            'generated': False,
            'fallback_reason': "DALL-E temporarily unavailable"
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
            'model_used': self.model
        }
    
    def regenerate_image(self, section_data: Dict[str, Any], tone: str, index: int) -> Optional[Dict[str, str]]:
        """
        Regenerate a specific image with improved prompt using DALL-E
        """
        
        # Create enhanced prompt for regeneration
        enhanced_prompt = self._create_image_prompt(section_data, "", tone)
        enhanced_prompt += ", enhanced quality, improved composition, professional grade"
        
        return self._generate_dalle_image(enhanced_prompt, tone, index)