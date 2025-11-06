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
        self.temperature = float(os.getenv("TEMPERATURE", 0.7))
        self.model = "gpt-4o-mini"  # Using the latest model
        
    def generate_article(
        self, 
        context: str, 
        keywords: str, 
        language: str = "English",
        tone: str = "Professional", 
        focus: str = "", 
        sections: int = 5,
        word_count: int = 600,
        promotion: str = "",
        seo_focus: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a complete article using multi-pass refinement approach
        
        Pass 1: Draft generation
        Pass 2: SEO optimization  
        Pass 3: Style and coherence refinement
        """
        
        # Parse keywords
        keyword_list = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else []
        primary_keyword = keyword_list[0] if keyword_list else "topic"
        
        try:
            # Pass 1: Generate initial draft
            draft_content = self._generate_draft(
                context, keyword_list, language, tone, focus, 
                sections, word_count, promotion
            )
            
            # Pass 2: SEO optimization pass
            if seo_focus:
                optimized_content = self._optimize_for_seo(draft_content, keyword_list, primary_keyword)
            else:
                optimized_content = draft_content
            
            # Pass 3: Style and coherence refinement
            final_content = self._refine_style_and_coherence(optimized_content, tone, language)
            
            # Parse and structure the final content
            article_data = self._parse_article_content(final_content, keyword_list, language, tone)
            
            return article_data
            
        except Exception as e:
            # Fallback to single-pass generation
            print(f"Multi-pass generation failed, falling back to single pass: {e}")
            return self._generate_single_pass(
                context, keyword_list, language, tone, focus, 
                sections, word_count, promotion
            )
    
    def _generate_draft(
        self, 
        context: str, 
        keywords: List[str], 
        language: str, 
        tone: str,
        focus: str, 
        sections: int, 
        word_count: int, 
        promotion: str
    ) -> str:
        """Generate the initial draft of the article"""
        
        # Construct comprehensive prompt
        prompt = self._build_draft_prompt(
            context, keywords, language, tone, focus, 
            sections, word_count, promotion
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert journalist and content creator specializing in creating engaging, well-structured articles. Focus on creating compelling, informative content that reads naturally and provides real value to readers."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"Draft generation failed: {e}")
    
    def _optimize_for_seo(self, draft_content: str, keywords: List[str], primary_keyword: str) -> str:
        """Second pass: Optimize content for SEO"""
        
        seo_prompt = f"""
        Please optimize the following article draft for SEO while maintaining its quality and readability.

        PRIMARY KEYWORD: {primary_keyword}
        TARGET KEYWORDS: {', '.join(keywords)}

        OPTIMIZATION REQUIREMENTS:
        1. Ensure primary keyword appears in title, first paragraph, and at least one H2 heading
        2. Distribute target keywords naturally throughout the content (aim for 1-2% keyword density)
        3. Add semantic variations and related terms
        4. Improve meta description to include primary keyword
        5. Enhance readability with transition words and varied sentence structures
        6. Add internal linking opportunities where natural
        7. Ensure each section provides unique value and targets specific keyword clusters

        MAINTAIN:
        - Natural, engaging writing style
        - Logical flow and structure
        - Factual accuracy and helpfulness
        - Original tone and voice

        ARTICLE DRAFT TO OPTIMIZE:
        {draft_content}

        Please provide the optimized version with improved SEO while keeping it human-readable and valuable.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an SEO expert who optimizes content while maintaining exceptional quality and readability. Balance SEO requirements with user experience."
                    },
                    {"role": "user", "content": seo_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.5,  # Lower temperature for more focused optimization
                presence_penalty=0.0,
                frequency_penalty=0.2  # Encourage keyword variation
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"SEO optimization failed: {e}")
            return draft_content  # Return original draft if optimization fails
    
    def _refine_style_and_coherence(self, content: str, tone: str, language: str) -> str:
        """Third pass: Refine style, coherence, and tone consistency"""
        
        style_prompt = f"""
        Please refine the following article for style, coherence, and tone consistency.

        TARGET TONE: {tone}
        LANGUAGE: {language}

        REFINEMENT FOCUS:
        1. Ensure consistent {tone.lower()} tone throughout
        2. Improve sentence variety and flow
        3. Enhance transitions between paragraphs and sections
        4. Polish grammar, punctuation, and clarity
        5. Strengthen the introduction and conclusion
        6. Add compelling subheadings if needed
        7. Ensure each paragraph has a clear purpose and flows logically
        8. Improve readability while maintaining depth

        CONTENT TO REFINE:
        {content}

        Please provide the refined version with improved style and coherence.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional editor specializing in {tone.lower()} content. Focus on clarity, flow, and engaging {language} prose while maintaining the original message and structure."
                    },
                    {"role": "user", "content": style_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.6,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Style refinement failed: {e}")
            return content  # Return previous version if refinement fails
    
    def _build_draft_prompt(
        self, 
        context: str, 
        keywords: List[str], 
        language: str, 
        tone: str,
        focus: str, 
        sections: int, 
        word_count: int, 
        promotion: str
    ) -> str:
        """Build comprehensive prompt for draft generation"""
        
        keyword_str = ', '.join(keywords) if keywords else "general topic"
        
        prompt = f"""
        Write a comprehensive {language} article with the following specifications:

        CONTEXT: {context}
        KEYWORDS TO TARGET: {keyword_str}
        FOCUS/ANGLE: {focus if focus else "Comprehensive overview and analysis"}
        TONE: {tone}
        TARGET WORD COUNT: {word_count} words
        NUMBER OF SECTIONS: {sections} H2 sections
        
        STRUCTURE REQUIREMENTS:
        1. Compelling H1 title that includes the primary keyword
        2. Engaging introduction (100-150 words) that hooks the reader
        3. {sections} well-structured H2 sections, each 80-120 words
        4. Natural conclusion with key takeaways
        5. SEO-optimized meta description (150-160 characters)
        6. Clean URL slug
        
        CONTENT REQUIREMENTS:
        - Informative and valuable to readers
        - Natural keyword integration (avoid keyword stuffing)
        - Use bullet points, numbered lists where appropriate
        - Include specific examples or data when relevant
        - Maintain consistent {tone.lower()} tone throughout
        - Each section should provide unique value
        - Smooth transitions between sections
        
        """
        
        if promotion:
            prompt += f"""
        PROMOTIONAL INTEGRATION:
        Naturally integrate this promotional content: "{promotion}"
        - Should feel organic and helpful, not forced
        - Include as a relevant example or recommendation
        - Maintain article's educational value
        
        """
        
        prompt += """
        OUTPUT FORMAT:
        Title: [SEO-optimized title]
        Meta Description: [150-160 character description]
        Slug: [clean-url-slug]
        
        [Introduction paragraph]
        
        ## Section 1 Heading
        [Section content]
        
        ## Section 2 Heading  
        [Section content]
        
        [Continue for all sections...]
        
        [Conclusion paragraph]
        
        IMPORTANT: Focus on creating genuinely helpful, engaging content that provides real value to readers while naturally incorporating the target keywords.
        """
        
        return prompt
    
    def _generate_single_pass(
        self, 
        context: str, 
        keywords: List[str], 
        language: str, 
        tone: str,
        focus: str, 
        sections: int, 
        word_count: int, 
        promotion: str
    ) -> Dict[str, Any]:
        """Fallback single-pass generation method"""
        
        prompt = self._build_draft_prompt(
            context, keywords, language, tone, focus, 
            sections, word_count, promotion
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert content creator. Generate high-quality, engaging articles that provide real value to readers."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content.strip()
            return self._parse_article_content(content, keywords, language, tone)
            
        except Exception as e:
            # Ultimate fallback - return structured placeholder
            return self._generate_fallback_content(keywords, language, tone)
    
    def _parse_article_content(self, content: str, keywords: List[str], language: str, tone: str) -> Dict[str, Any]:
        """Parse the generated content into structured article data"""
        
        try:
            # Extract title, meta description, and slug
            title_match = re.search(r'Title:\s*(.+)', content, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else "Generated Article"
            
            meta_match = re.search(r'Meta Description:\s*(.+)', content, re.IGNORECASE)
            meta_description = meta_match.group(1).strip() if meta_match else title[:150]
            
            slug_match = re.search(r'Slug:\s*(.+)', content, re.IGNORECASE)
            slug = slug_match.group(1).strip() if slug_match else self._generate_slug(title)
            
            # Extract sections
            sections = []
            section_pattern = r'##\s+(.+?)\n((?:(?!##).)+)'
            section_matches = re.findall(section_pattern, content, re.DOTALL)
            
            for i, (heading, section_content) in enumerate(section_matches):
                section_text = section_content.strip()
                sections.append({
                    'heading': heading.strip(),
                    'content': section_text,
                    'keywords': keywords[:2] if i == 0 else keywords[i:i+2] if i < len(keywords) else [],
                    'word_count': len(section_text.split())
                })
            
            # If no sections found, create from content
            if not sections:
                sections = self._create_sections_from_content(content, keywords)
            
            # Calculate total word count
            total_words = sum(section['word_count'] for section in sections)
            
            return {
                'title': title,
                'seo_title': title,  # Can be optimized further
                'meta_description': meta_description,
                'slug': slug,
                'sections': sections,
                'cta': self._generate_cta(title, keywords),
                'total_word_count': total_words,
                'focus_keywords': keywords[:3],
                'language': language,
                'tone': tone,
                'content': content  # Raw content for further processing
            }
            
        except Exception as e:
            print(f"Content parsing failed: {e}")
            return self._generate_fallback_content(keywords, language, tone)
    
    def _create_sections_from_content(self, content: str, keywords: List[str]) -> List[Dict[str, Any]]:
        """Create sections from unstructured content"""
        
        # Split content into paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        sections = []
        current_section = ""
        section_count = 0
        
        for paragraph in paragraphs:
            if len(paragraph.split()) > 20 and section_count < 5:  # Start new section
                if current_section:
                    sections.append({
                        'heading': f"Section {len(sections) + 1}",
                        'content': current_section.strip(),
                        'keywords': keywords[len(sections):len(sections)+2] if len(sections) < len(keywords) else [],
                        'word_count': len(current_section.split())
                    })
                current_section = paragraph
                section_count += 1
            else:
                current_section += f"\n\n{paragraph}"
        
        # Add final section
        if current_section:
            sections.append({
                'heading': f"Section {len(sections) + 1}",
                'content': current_section.strip(),
                'keywords': keywords[len(sections):len(sections)+2] if len(sections) < len(keywords) else [],
                'word_count': len(current_section.split())
            })
        
        return sections
    
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
        
        cta_options = [
            f"Ready to learn more about {primary_keyword}? Explore our comprehensive guides and resources.",
            f"Want to stay updated on {primary_keyword}? Subscribe to our newsletter for the latest insights.",
            f"Looking for expert advice on {primary_keyword}? Contact our team of specialists today.",
            f"Interested in {primary_keyword}? Check out our related articles and in-depth analysis."
        ]
        
        return cta_options[hash(title) % len(cta_options)]
    

    
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