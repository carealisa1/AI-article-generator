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
        self.model = "gpt-4o-mini" # Using the latest model
        
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
        promotional_style: str = "No Promotion",
        seo_focus: bool = True
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
                sections, word_count, promotion, promotional_style, seo_focus
            )
            
            # Parse and structure the final content
            article_data = self._parse_article_content(final_content, keyword_list, language, tone, sections)
            
            return article_data
            
        except Exception as e:
            # Fallback to single-pass generation
            print(f"Multi-pass generation failed, falling back to single pass: {e}")
            return self._generate_single_pass(
                context, keyword_list, language, tone, focus, 
                sections, word_count, promotion, promotional_style
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
        promotion: str,
        promotional_style: str,
        seo_focus: bool = True
    ) -> str:
        """Generate the initial draft of the article"""
        
        # Construct comprehensive prompt
        prompt = self._build_draft_prompt(
            context, keywords, language, tone, focus, 
            sections, word_count, promotion, promotional_style, seo_focus
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": """You are an expert content writer who creates high-quality, SEO-optimized articles. 

CRITICAL ARTICLE REQUIREMENTS - MUST FOLLOW EXACTLY:
- Write the EXACT number of sections requested (no more, no less)
- Reach the EXACT target word count specified 
- Each section must be substantial and meet word count expectations
- Write clean, natural content without ** bold markers or formatting symbols
- Never use artificial labels like "Title:", "Meta Description:", "Section 1"
- Create specific, descriptive headings that tell readers exactly what each section covers
- Use ## for section headings only (no other markdown formatting)
- Write naturally flowing content that provides genuine value
- NEVER include SEO metadata, analysis, or technical notes in the article content

SEO OPTIMIZATION REQUIREMENTS (BUILT INTO CONTENT):
- Include primary keyword in title
- Use all target keywords naturally and organically throughout the content
- Keep sentences clear and concise (average 15-20 words)
- Create engaging, descriptive section headings that include relevant keywords when natural
- Maintain logical content flow with smooth transitions between paragraphs
- Write compelling introduction that hooks readers and includes primary keyword
- End with strong conclusion that reinforces main points and includes primary keyword
- Ensure keyword density feels natural (no keyword stuffing)
- Use semantic keywords and related terms to support main keywords

CONTENT STRUCTURE:
1. Start with a compelling title (no "Title:" label) - MUST include primary keyword
2. Follow with meta description (no "Meta:" label) - compelling and keyword-rich  
3. Write the article content with ## descriptive headings
4. Ensure each section has unique, valuable information and meets word targets
5. Include all specified keywords naturally throughout
6. End with a natural conclusion - NO SEO analysis or metadata

WORD COUNT ENFORCEMENT:
- If requesting 1 section with 500 words, write 500 words in that section
- If requesting 3 sections with 500 words, write ~167 words per section
- Always meet or exceed the minimum word count specified
- Each section should be comprehensive and detailed

STRICTLY FORBIDDEN IN CONTENT:
- SEO analysis comments (reading scores, keyword density, etc.)
- Technical metadata (target keywords lists, flesch scores)
- Implementation notes about SEO requirements
- Bullet points with technical analysis
- Any mention of "SEO requirements", "keyword density", or similar terms

QUALITY STANDARDS:
- Focus on reader value and comprehensive coverage
- Use the specified tone consistently
- Create content that flows logically from section to section
- Include specific examples and actionable insights
- End with practical conclusions or next steps
- Write ONLY the article content that readers should see"""
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.6,  # Slightly lower for more structured output
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"Draft generation failed: {e}")
    

    
 
    def _build_draft_prompt(
        self, 
        context: str, 
        keywords: List[str], 
        language: str, 
        tone: str,
        focus: str, 
        sections: int, 
        word_count: int, 
        promotion: str,
        promotional_style: str,
        seo_focus: bool = True
    ) -> str:
        """Build comprehensive prompt for draft generation"""
        
        keyword_str = ', '.join(keywords) if keywords else "general topic"
        primary_kw = keywords[0] if keywords else "topic"
        word_count += 150
        # Calculate words per section for balanced content
        intro_words = 50  # Brief introduction
        words_per_section = max(80, (word_count - intro_words) // sections)
        
        # Build context analysis
        context_type = "URL content analysis" if "Multi-URL Analysis" in context else "keyword-based content"
        
        # Create specific focus instructions
        focus_instruction = ""
        if focus:
            focus_instruction = f"""
        CRITICAL FOCUS REQUIREMENT:
        - This article MUST center around: {focus}
        - Every section should relate back to this focus angle
        - Use {focus} as the primary lens for analyzing {primary_kw}
        """
        
        # Create promotional integration strategy
        promotion_strategy = ""
        if promotion and promotional_style != "No Promotion":
            if promotional_style == "CTA only":
                promotion_strategy = f"""
        PROMOTIONAL CONTENT INTEGRATION:
        - Product/Service: {promotion}
        - Integration Style: Call-to-Action Only
        - Placement: End of article as natural CTA
        - Approach: Subtle recommendation in conclusion
        - Format: "For more insights on [topic], consider exploring {promotion}"
        """
            elif promotional_style == "Full Section + CTA":
                promotion_strategy = f"""
        PROMOTIONAL CONTENT INTEGRATION:
        - Product/Service: {promotion}
        - Integration Style: Dedicated Section + CTA
        - Placement: One dedicated section + conclusion mention
        - Section Focus: Educational content about {promotion} as it relates to {primary_kw}
        - Approach: Present as relevant solution/tool, maintain educational value
        - CTA: Include natural call-to-action at the end
        """
        
        # Create dynamic section heading examples based on keywords
        heading_examples = self._generate_heading_examples(primary_kw, focus, keywords)
        
        # Add SEO optimization instructions if enabled
        seo_instructions = ""
        if seo_focus:
            seo_instructions = f"""
        *** CRITICAL SEO OPTIMIZATION REQUIREMENTS ***:
        - PRIMARY KEYWORD "{primary_kw}" MUST appear in:
          * Title (naturally integrated)
          * First paragraph (within first 100 words)
          * At least 2 section headings (when it fits naturally)
          * Conclusion paragraph
        - ALL TARGET KEYWORDS must be used organically: {keyword_str}
        - Section headings should be descriptive AND keyword-rich when natural
        - Use semantic keywords and related terms throughout
        - Maintain keyword density of 1-2% for primary keyword (natural, no stuffing)
        - Create compelling meta description (150-155 chars) with primary keyword
        - Ensure content answers search intent for "{primary_kw}"
        """
        
        prompt = f"""
        Create a comprehensive {language} article using {context_type}.

        SOURCE CONTEXT: {context}

        ARTICLE SPECIFICATIONS:
        - Primary Keyword: {primary_kw}
        - Target Keywords: {keyword_str}
        - Language: {language}
        - Tone: {tone}
        - *** CRITICAL *** Target Length: {word_count} words TOTAL (YOU MUST WRITE EXACTLY THIS AMOUNT)
        - *** CRITICAL *** Section Count: EXACTLY {sections} section{'s' if sections != 1 else ''} - NO MORE, NO LESS
        - *** CRITICAL *** Words per section: ~{words_per_section} words each (COUNT YOUR WORDS AS YOU WRITE)

        {seo_instructions}

        {focus_instruction}

        {promotion_strategy}

        CONTENT STRUCTURE REQUIREMENTS:
        1. Title: Write a compelling title (50-60 characters) that includes "{primary_kw}"
        2. Meta Description: Create an engaging description (150-155 characters) 
        3. Article Body: {sections} sections with specific, descriptive headings

        SECTION HEADING REQUIREMENTS:
        - Create natural, engaging headings that describe the actual content
        - Headings should be specific to your content, not generic templates
        - Use action words and specific concepts relevant to {primary_kw}
        - Make readers curious about what they'll learn in each section
        - Include keywords naturally when they fit the content flow
        - Avoid generic headings like "Introduction", "Benefits", "Conclusion"

        HEADING INSPIRATION (create your own variations):
        {heading_examples}

        *** CRITICAL WORD COUNT ENFORCEMENT ***:
        - ABSOLUTE REQUIREMENT: Must reach EXACTLY {word_count} words (minimum {int(word_count * 0.95)} words)
        - SECTION COUNT: Must have EXACTLY {sections} section{'s' if sections != 1 else ''} with ## headings
        - WORD DISTRIBUTION: Each section MUST be approximately {words_per_section} words - WRITE DETAILED CONTENT
        - DO NOT STOP WRITING until you reach the required word count
        - Add examples, explanations, details, and elaboration to reach target length
        - Use {tone.lower()} tone throughout
        - Include {primary_kw} in title, first paragraph, and conclusion
        - Naturally incorporate all target keywords: {keyword_str}
        - Use clear, engaging language appropriate for {language} speakers
        - Add specific examples, data, or insights where relevant
        - Create smooth transitions between sections
        - End with actionable insights or next steps

        FORMATTING REQUIREMENTS:
        - Clean text only - no ** bold markers or formatting symbols
        - Use ## for section headings (no other heading levels)
        - Write naturally flowing paragraphs
        - No artificial labels like "Title:", "Meta:", etc.
        - Format: Title → Meta Description → Article Content with ## headings

        OUTPUT FORMAT:
        [Compelling Title Here]
        [Meta description here]
        
        [Opening paragraph introducing the topic]
        
        {self._generate_section_format_example(sections, words_per_section)}
        
        Write the complete article now with EXACTLY {sections} section{'s' if sections != 1 else ''} and {word_count} total words. Each section must be substantial (~{words_per_section} words) to reach the target length. Ensure every section provides unique value and relates to {focus if focus else primary_kw}.
        """
        
        return prompt
    
    def _generate_heading_examples(self, primary_keyword: str, focus: str, keywords: List[str]) -> str:
        """Generate contextual heading examples based on the topic and focus"""
        
        examples = []
        
        # Generate examples based on the primary keyword type
        keyword_lower = primary_keyword.lower()
        
        if 'bitcoin' in keyword_lower or 'crypto' in keyword_lower:
            examples = [
                f"Current {primary_keyword} Market Analysis and Trends",
                f"Technical Indicators Affecting {primary_keyword} Price",
                f"Institutional Impact on {primary_keyword} Adoption",
                f"Risk Management Strategies for {primary_keyword} Investors"
            ]
        elif 'price' in keyword_lower:
            examples = [
                f"Factors Driving {primary_keyword} Movements",
                f"Historical {primary_keyword} Patterns and Predictions", 
                f"Market Sentiment Impact on {primary_keyword}",
                f"Economic Indicators Affecting {primary_keyword}"
            ]
        elif 'investment' in keyword_lower or 'trading' in keyword_lower:
            examples = [
                f"Strategic Approaches to {primary_keyword}",
                f"Risk Assessment in {primary_keyword}",
                f"Portfolio Diversification with {primary_keyword}",
                f"Long-term vs Short-term {primary_keyword} Strategies"
            ]
        else:
            # Generic but specific examples
            examples = [
                f"Complete Guide to {primary_keyword} Implementation",
                f"Advanced {primary_keyword} Techniques and Methods",
                f"Common Challenges in {primary_keyword} Adoption",
                f"Future Developments in {primary_keyword} Technology"
            ]
        
        # If focus is provided, adjust examples to include it
        if focus:
            focused_examples = []
            for example in examples:
                # Integrate focus into heading examples
                if 'analysis' in focus.lower():
                    focused_examples.append(example.replace('Guide to', 'Analysis of').replace('Impact on', f'{focus} Impact on'))
                elif 'prediction' in focus.lower():
                    focused_examples.append(example.replace('Strategies', 'Predictions').replace('Techniques', 'Forecasting'))
                else:
                    focused_examples.append(f"{example} - {focus} Perspective")
            examples = focused_examples
        
        return "- " + "\n- ".join(examples[:4])
    
    def _generate_section_format_example(self, sections: int, words_per_section: int = 150) -> str:
        """Generate format example showing exact number of sections requested with word count guidance"""
        
        if sections == 1:
            return f"""## [Single Descriptive Heading]
[CRITICAL: Write EXACTLY {words_per_section} words here - no less! This single section must be comprehensive and detailed. Write multiple paragraphs covering all aspects with specific examples, detailed explanations, practical insights, and thorough analysis. Keep writing until you reach {words_per_section} words.]"""
        
        elif sections == 2:
            words_each = words_per_section // 2
            return f"""## [Specific Descriptive Heading 1]
[MUST write approximately {words_each} words - be detailed and thorough...]

## [Specific Descriptive Heading 2]
[MUST write approximately {words_each} words - be detailed and thorough...]"""
        
        else:
            # For 3+ sections, distribute words evenly
            words_each = words_per_section // sections
            example_parts = []
            for i in range(1, sections + 1):
                example_parts.append(f"""## [Specific Descriptive Heading {i}]
[MUST write approximately {words_each} words - include detailed explanations and examples...]""")
            return "\n\n".join(example_parts)
    
    def _generate_single_pass(
        self, 
        context: str, 
        keywords: List[str], 
        language: str, 
        tone: str,
        focus: str, 
        sections: int, 
        word_count: int, 
        promotion: str,
        promotional_style: str
    ) -> Dict[str, Any]:
        """Fallback single-pass generation method"""
        
        prompt = self._build_draft_prompt(
            context, keywords, language, tone, focus, 
            sections, word_count, promotion, promotional_style, seo_focus=False
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
            return self._parse_article_content(content, keywords, language, tone, sections)
            
        except Exception as e:
            # Ultimate fallback - return structured placeholder
            return self._generate_fallback_content(keywords, language, tone)
    
    def _parse_article_content(self, content: str, keywords: List[str], language: str, tone: str, max_sections: int = None) -> Dict[str, Any]:
        """Simple parsing - split on ## markers and extract sections"""
        
        try:
            # Clean content
            cleaned_content = content.replace('**', '').strip()
            
            # Extract title (first line)
            lines = cleaned_content.split('\n')
            title = lines[0].strip() if lines else "Generated Article"
            
            # Extract meta description (second non-empty line that looks like meta description)
            meta_description = ""
            for i, line in enumerate(lines[1:], 1):
                line = line.strip()
                if (line and 
                    len(line) > 80 and 
                    len(line) < 300 and 
                    not line.startswith('#') and
                    not line.lower().startswith(('title:', 'meta:', 'description:'))):
                    meta_description = line[:160]
                    break
            
            # Fallback meta description
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
    
    def _clean_content_artifacts(self, content: str) -> str:
        """Clean up formatting artifacts and malformed elements"""
        
        cleaned = content
        
        # Remove ** formatting
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)
        
        # Fix malformed titles that appear in content
        cleaned = re.sub(r'Title:\s*\[([^\]]+)\]\([^)]+\)', r'\1', cleaned)
        
        # Fix malformed meta descriptions
        cleaned = re.sub(r'Meta Description:\s*([^\n]+)', r'\1', cleaned)
        
        # Remove duplicate title/meta information that appears in content
        lines = cleaned.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip lines that are obviously misplaced metadata
            if (line.lower().startswith(('title:', 'meta description:', 'slug:')) or
                (len(line) < 200 and '](/' in line and line.count('[') != line.count(']'))):
                continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _extract_content_elements(self, content: str) -> Dict[str, Any]:
        """Simple extraction that preserves all content by splitting on ## headings"""
        
        # Split content on ## headings to get sections
        parts = content.split('\n##')
        
        elements = {
            'title_candidates': [],
            'meta_candidates': [],
            'headings': [],
            'paragraphs': [],
            'sections': []
        }
        
        # Process first part (everything before first ##)
        if parts:
            first_part = parts[0].strip()
            lines = [line.strip() for line in first_part.split('\n') if line.strip()]
            
            # First line is likely title
            if lines:
                elements['title_candidates'].append(lines[0])
            
            # Second line might be meta description
            if len(lines) > 1 and len(lines[1]) > 50:
                elements['meta_candidates'].append(lines[1])
            
            # Rest goes to paragraphs
            if len(lines) > 2:
                intro_content = '\n'.join(lines[2:])
                if intro_content.strip():
                    elements['paragraphs'].append(intro_content)
        
        # Process sections (everything after ## headings)
        for i, part in enumerate(parts[1:], 1):
            if not part.strip():
                continue
                
            # The part starts right after ##, so we need to extract heading and content
            lines = part.split('\n')
            if not lines:
                continue
                
            # First line is the heading
            heading = lines[0].strip()
            elements['headings'].append(heading)
            
            # Rest is the content for this section - preserve ALL of it
            content_lines = lines[1:]
            section_content = '\n'.join(content_lines).strip()
            
            if section_content:
                elements['sections'].append({
                    'heading': heading,
                    'content': section_content
                })
        
        return elements
    
    def _extract_clean_title(self, elements: Dict[str, Any], keywords: List[str]) -> str:
        """Extract or generate a clean title"""
        
        # Look for title candidates that contain keywords
        primary_keyword = keywords[0] if keywords else ""
        
        for candidate in elements['title_candidates']:
            # Clean the candidate
            clean_candidate = re.sub(r'[\[\](){}]', '', candidate).strip()
            
            # Check if it's a good title (contains keyword or looks title-like)
            if (primary_keyword.lower() in clean_candidate.lower() or 
                any(word in clean_candidate.lower() for word in ['guide', 'analysis', 'review', 'complete', 'ultimate', 'best'])):
                return clean_candidate
        
        # If no good title found, use first heading
        if elements['headings']:
            return elements['headings'][0]
        
        # Last resort - generate from keywords
        if primary_keyword:
            return f"Complete Guide to {primary_keyword}"
        
        return "Generated Article"
    
    def _extract_clean_meta_description(self, elements: Dict[str, Any], title: str) -> str:
        """Extract or generate clean meta description"""
        
        # Look for meta description candidates
        for candidate in elements['meta_candidates']:
            if 140 <= len(candidate) <= 160:
                return candidate
        
        # Generate from title and first paragraph
        if elements['paragraphs']:
            first_para = elements['paragraphs'][0]
            if len(first_para) <= 160:
                return first_para
            else:
                # Truncate smartly
                truncated = first_para[:150]
                last_space = truncated.rfind(' ')
                if last_space > 100:
                    return truncated[:last_space] + "..."
        
        # Fallback - generate from title
        return f"Explore {title.lower()} in this comprehensive guide. Discover key insights, benefits, and practical applications."[:160]
    
    def _extract_clean_sections(self, elements: Dict[str, Any], keywords: List[str], max_sections: int = None) -> List[Dict[str, Any]]:
        """Extract sections with minimal processing to preserve content"""
        
        sections = []
        
        for section_data in elements['sections']:
            # Stop if we've reached the maximum number of sections
            if max_sections and len(sections) >= max_sections:
                break
                
            heading = section_data['heading']
            content = section_data['content']
            
            # Skip empty sections
            if not content or not content.strip():
                continue
            
            # Just count words, don't filter based on length
            word_count = len(content.split())
            
            sections.append({
                'heading': heading.strip(),  # Minimal cleaning - just strip whitespace
                'content': content,  # Preserve all content as-is
                'keywords': keywords[:2] if len(sections) == 0 else keywords[len(sections):len(sections)+2],
                'word_count': word_count
            })
        
        return sections
    

    
    def _clean_section_heading(self, heading: str, keywords: List[str]) -> str:
        """Clean up section headings without modifying LLM-generated content"""
        
        # Only clean formatting artifacts, don't modify LLM-generated content
        clean_heading = re.sub(r'[#*\[\]()]', '', heading).strip()
        
        # Remove any leading/trailing quotes or special characters
        clean_heading = clean_heading.strip('"\'`')
        
        # Only reject headings that are clearly malformed (very short or obviously corrupted)
        if len(clean_heading) < 3:
            primary_keyword = keywords[0] if keywords else "Content"
            return f"{primary_keyword} Overview"
        
        # Return the LLM-generated heading as-is (this preserves the natural language)
        return clean_heading
    
    def _create_sections_from_content(self, content: str, keywords: List[str], max_sections: int = None) -> List[Dict[str, Any]]:
        """Create sections from unstructured content by parsing LLM-generated structure"""
        
        # This method should only be called if normal parsing fails
        # Try to extract natural sections from the content
        
        # Look for potential headings in the content (lines that could be headings)
        lines = content.split('\n')
        potential_sections = []
        current_content = []
        current_heading = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line looks like a heading
            is_heading = self._is_potential_heading(line, keywords)
            
            if is_heading and current_content:
                # Save previous section (if we haven't reached the limit)
                if current_heading and (not max_sections or len(potential_sections) < max_sections):
                    section_text = '\n\n'.join(current_content)
                    if len(section_text.split()) >= 30:  # Only include substantial sections
                        potential_sections.append({
                            'heading': current_heading,
                            'content': section_text,
                            'keywords': keywords[:2] if len(potential_sections) == 0 else keywords[len(potential_sections):len(potential_sections)+2],
                            'word_count': len(section_text.split())
                        })
                
                # Start new section
                current_heading = line
                current_content = []
            
            elif is_heading and not current_content:
                # This is the first heading
                current_heading = line
                current_content = []
            
            else:
                # This is regular content
                if current_heading:  # Only add content if we have a heading
                    current_content.append(line)
        
        # Add the final section (if we haven't reached the limit)
        if current_heading and current_content and (not max_sections or len(potential_sections) < max_sections):
            section_text = '\n\n'.join(current_content)
            if len(section_text.split()) >= 30:
                potential_sections.append({
                    'heading': current_heading,
                    'content': section_text,
                    'keywords': keywords[:2] if len(potential_sections) == 0 else keywords[len(potential_sections):len(potential_sections)+2],
                    'word_count': len(section_text.split())
                })
        
        # If no natural sections found, create one large section from all content
        if not potential_sections:
            primary_keyword = keywords[0] if keywords else "Content"
            all_content = '\n\n'.join([line.strip() for line in lines if line.strip()])
            
            if len(all_content.split()) >= 50:
                potential_sections.append({
                    'heading': f"Comprehensive {primary_keyword} Analysis",
                    'content': all_content,
                    'keywords': keywords[:3],
                    'word_count': len(all_content.split())
                })
        
        return potential_sections
    
    def _is_potential_heading(self, line: str, keywords: List[str]) -> bool:
        """Determine if a line could be a section heading"""
        
        # Skip if line is too long to be a heading
        if len(line) > 100 or len(line) < 10:
            return False
        
        # Skip if line ends with period (likely a sentence)
        if line.endswith('.'):
            return False
        
        # Skip if line has too many common words
        common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        line_words = line.lower().split()
        common_word_count = sum(1 for word in line_words if word in common_words)
        
        if common_word_count > len(line_words) * 0.4:  # More than 40% common words
            return False
        
        # Positive indicators for headings
        heading_indicators = 0
        
        # Contains keywords
        for keyword in keywords:
            if keyword.lower() in line.lower():
                heading_indicators += 2
                break
        
        # Title case or proper capitalization
        if line.istitle() or (line[0].isupper() and not line.isupper()):
            heading_indicators += 1
        
        # Contains action words or question words
        action_words = ['how', 'what', 'why', 'when', 'where', 'understanding', 'analyzing', 'exploring', 'discovering']
        if any(word in line.lower() for word in action_words):
            heading_indicators += 1
        
        # Contains topic-specific terms
        topic_terms = ['analysis', 'guide', 'overview', 'introduction', 'conclusion', 'summary', 'strategies', 'benefits', 'challenges']
        if any(term in line.lower() for term in topic_terms):
            heading_indicators += 1
        
        # Reasonable word count for a heading
        word_count = len(line_words)
        if 3 <= word_count <= 12:
            heading_indicators += 1
        
        # Return true if we have enough indicators
        return heading_indicators >= 2
    
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