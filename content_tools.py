import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter
import json
from urllib.parse import urljoin, urlparse
import time

class ContentTools:
    """
    Advanced content intelligence and enhancement tools
    Handles URL extraction, link insertion, and content analysis
    """
    
    def __init__(self):
        """Initialize content tools with basic text processing"""
        # Basic stop words for English
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'would', 'you', 'your', 'this', 'they',
            'we', 'our', 'can', 'have', 'been', 'were', 'their', 'said', 'each',
            'which', 'do', 'if', 'will', 'up', 'other', 'how', 'out', 'many',
            'time', 'them', 'these', 'so', 'some', 'her', 'would', 'make', 'like',
            'into', 'him', 'has', 'two', 'more', 'very', 'what', 'know', 'just',
            'first', 'get', 'over', 'think', 'also', 'back', 'after', 'use',
            'work', 'life', 'only', 'new', 'way', 'may', 'say'
        }
        
        # Common internal link patterns
        self.link_patterns = {
            'guide': 'comprehensive guide',
            'tutorial': 'step-by-step tutorial',
            'tips': 'expert tips',
            'review': 'detailed review',
            'comparison': 'detailed comparison',
            'analysis': 'in-depth analysis'
        }
    
    def _simple_word_tokenize(self, text: str) -> List[str]:
        """Simple word tokenization without NLTK"""
        # Remove punctuation and split on whitespace
        import string
        text = text.translate(str.maketrans('', '', string.punctuation))
        return text.split()
    
    def _simple_sent_tokenize(self, text: str) -> List[str]:
        """Simple sentence tokenization without NLTK"""
        # Split on sentence endings
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def extract_url_content(self, url: str) -> Dict[str, Any]:
        """
        Extract and analyze content from a URL for context generation
        """
        
        try:
            # Fetch the webpage
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract structured data
            extracted_data = {
                'title': self._extract_title(soup),
                'meta_description': self._extract_meta_description(soup),
                'headings': self._extract_headings(soup),
                'main_content': self._extract_main_content(soup),
                'keywords': self._extract_keywords_from_content(soup),
                'images': self._extract_images(soup, url),
                'links': self._extract_links(soup, url),
                'url': url,
                'content_summary': ''
            }
            
            # Generate content summary
            extracted_data['content_summary'] = self._generate_content_summary(extracted_data)
            
            return extracted_data
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch URL {url}: {e}")
            return self._create_fallback_url_data(url)
        
        except Exception as e:
            print(f"Error processing URL {url}: {e}")
            return self._create_fallback_url_data(url)
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # Fallback to h1
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return "Extracted Content"
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Fallback to Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        return ""
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all headings with hierarchy"""
        headings = []
        
        for level in range(1, 7):  # h1 to h6
            heading_tags = soup.find_all(f'h{level}')
            for tag in heading_tags:
                headings.append({
                    'level': level,
                    'text': tag.get_text().strip(),
                    'id': tag.get('id', '')
                })
        
        return headings
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content"""
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'menu']):
            element.decompose()
        
        # Try to find main content areas
        content_selectors = [
            'main',
            'article',
            '[role="main"]',
            '.content',
            '.post-content',
            '.entry-content',
            '.article-body',
            '#content'
        ]
        
        main_content = ""
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                main_content = content_elem.get_text(separator=' ', strip=True)
                break
        
        # Fallback: extract all paragraphs
        if not main_content:
            paragraphs = soup.find_all('p')
            main_content = ' '.join([p.get_text().strip() for p in paragraphs])
        
        return main_content[:2000]  # Limit content length
    
    def _extract_keywords_from_content(self, soup: BeautifulSoup) -> List[str]:
        """Extract relevant keywords from content"""
        
        # Get meta keywords if available
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords = [kw.strip() for kw in meta_keywords['content'].split(',')]
            return keywords[:10]
        
        # Extract from content using NLP
        content = self._extract_main_content(soup)
        return self._extract_keywords_nlp(content)[:10]
    
    def _extract_keywords_nlp(self, text: str) -> List[str]:
        """Extract keywords using NLP techniques"""
        
        try:
            # Tokenize and clean
            words = self._simple_word_tokenize(text.lower())
            words = [word for word in words if word.isalpha() and len(word) > 2]
            words = [word for word in words if word not in self.stop_words]
            
            # Count frequencies
            word_freq = Counter(words)
            
            # Get most common words
            return [word for word, count in word_freq.most_common(15)]
            
        except Exception as e:
            print(f"NLP keyword extraction failed: {e}")
            return []
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract images from the page"""
        
        images = []
        img_tags = soup.find_all('img', src=True)
        
        for img in img_tags[:5]:  # Limit to first 5 images
            src = img['src']
            
            # Convert relative URLs to absolute
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = urljoin(base_url, src)
            
            images.append({
                'src': src,
                'alt': img.get('alt', ''),
                'title': img.get('title', '')
            })
        
        return images
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract internal and external links"""
        
        links = []
        link_tags = soup.find_all('a', href=True)
        
        for link in link_tags[:20]:  # Limit to first 20 links
            href = link['href']
            text = link.get_text().strip()
            
            if not text or len(text) > 100:
                continue
            
            # Determine if internal or external
            is_internal = self._is_internal_link(href, base_url)
            
            links.append({
                'url': href,
                'text': text,
                'title': link.get('title', ''),
                'is_internal': is_internal
            })
        
        return links
    
    def _is_internal_link(self, href: str, base_url: str) -> bool:
        """Check if a link is internal"""
        
        if href.startswith('/') or href.startswith('#'):
            return True
        
        try:
            base_domain = urlparse(base_url).netloc
            link_domain = urlparse(href).netloc
            return base_domain == link_domain
        except:
            return False
    
    def _generate_content_summary(self, extracted_data: Dict[str, Any]) -> str:
        """Generate a summary of the extracted content"""
        
        summary_parts = []
        
        if extracted_data['title']:
            summary_parts.append(f"Title: {extracted_data['title']}")
        
        if extracted_data['meta_description']:
            summary_parts.append(f"Description: {extracted_data['meta_description']}")
        
        if extracted_data['keywords']:
            keywords_str = ', '.join(extracted_data['keywords'][:5])
            summary_parts.append(f"Key topics: {keywords_str}")
        
        if extracted_data['headings']:
            heading_texts = [h['text'] for h in extracted_data['headings'][:3]]
            summary_parts.append(f"Main sections: {', '.join(heading_texts)}")
        
        return ' | '.join(summary_parts)
    
    def _create_fallback_url_data(self, url: str) -> Dict[str, Any]:
        """Create fallback data when URL extraction fails"""
        
        return {
            'title': f"Content from {urlparse(url).netloc}",
            'meta_description': f"Extracted content from {url}",
            'headings': [],
            'main_content': f"Content analysis from {url}",
            'keywords': [],
            'images': [],
            'links': [],
            'url': url,
            'content_summary': f"URL analysis from {url}"
        }
    
    def enhance_content(
        self, 
        article_data: Dict[str, Any], 
        internal_links: str = "", 
        seo_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Enhance article content with intelligent link insertion and improvements
        """
        
        enhanced_article = article_data.copy()
        
        # Parse internal links configuration
        link_map = self._parse_internal_links(internal_links)
        
        # Enhance each section
        for i, section in enumerate(enhanced_article['sections']):
            # Fix any malformed URLs first
            fixed_content = self._fix_malformed_urls(section['content'])
            
            # Insert internal links
            enhanced_content = self._insert_links_in_content(
                fixed_content, 
                link_map, 
                section.get('keywords', [])
            )
            
            # Add transition improvements
            enhanced_content = self._improve_transitions(enhanced_content, i, len(enhanced_article['sections']))
            
            # Update section
            enhanced_article['sections'][i]['content'] = enhanced_content
        
        # Add SEO enhancements
        if seo_data:
            enhanced_article = self._apply_seo_enhancements(enhanced_article, seo_data)
        
        # Generate CTA if not present
        if not enhanced_article.get('cta'):
            enhanced_article['cta'] = self._generate_enhanced_cta(
                enhanced_article['title'], 
                enhanced_article.get('focus_keywords', [])
            )
        
        return enhanced_article
    
    def _parse_internal_links(self, internal_links: str) -> Dict[str, str]:
        """Parse internal links configuration"""
        
        link_map = {}
        
        if not internal_links:
            return link_map
        
        # Parse format: "Link Text: /url, Another Link: /another-url"
        for link_entry in internal_links.split(','):
            if ':' in link_entry:
                text, url = link_entry.split(':', 1)
                link_map[text.strip().lower()] = url.strip()
        
        return link_map
    
    def _insert_links_in_content(
        self, 
        content: str, 
        link_map: Dict[str, str], 
        section_keywords: List[str]
    ) -> str:
        """
        Intelligently insert internal links into content
        """
        
        if not link_map:
            return content
        
        enhanced_content = content
        
        # Track inserted links to avoid duplicates
        inserted_links = set()
        
        for link_text, link_url in link_map.items():
            # Skip if already inserted
            if link_url in inserted_links:
                continue
            
            # Find natural insertion points
            insertion_points = self._find_link_insertion_points(
                enhanced_content, 
                link_text, 
                section_keywords
            )
            
            if insertion_points:
                # Choose the best insertion point
                best_point = insertion_points[0]
                
                # Create the link in markdown format
                link_markdown = f'[{best_point["anchor_text"]}]({link_url})'
                
                # Insert the link
                enhanced_content = enhanced_content.replace(
                    best_point["original_text"], 
                    link_markdown, 
                    1  # Replace only first occurrence
                )
                
                inserted_links.add(link_url)
        
        return enhanced_content
    
    def _find_link_insertion_points(
        self, 
        content: str, 
        link_text: str, 
        keywords: List[str]
    ) -> List[Dict[str, str]]:
        """
        Find natural points to insert links based on context
        """
        
        insertion_points = []
        
        # Split into sentences for analysis
        sentences = self._simple_sent_tokenize(content)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Check for direct keyword matches
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                if keyword_lower in sentence_lower:
                    # Found a relevant sentence, create insertion point
                    insertion_points.append({
                        "original_text": keyword,
                        "anchor_text": f"{keyword} (learn more)",
                        "sentence": sentence,
                        "relevance_score": 1.0
                    })
        
        # Check for semantic matches with link text
        link_words = link_text.lower().split()
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Calculate word overlap
            sentence_words = sentence_lower.split()
            overlap = len(set(link_words) & set(sentence_words))
            
            if overlap > 0:
                relevance = overlap / len(link_words)
                if relevance > 0.3:  # At least 30% word overlap
                    # Find the best phrase to link
                    best_phrase = self._find_best_linkable_phrase(sentence, link_words)
                    if best_phrase:
                        insertion_points.append({
                            "original_text": best_phrase,
                            "anchor_text": best_phrase,
                            "sentence": sentence,
                            "relevance_score": relevance
                        })
        
        # Sort by relevance score
        insertion_points.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return insertion_points[:2]  # Return top 2 insertion points
    
    def _find_best_linkable_phrase(self, sentence: str, target_words: List[str]) -> Optional[str]:
        """
        Find the best phrase in a sentence to turn into a link
        """
        
        sentence_lower = sentence.lower()
        
        # Look for exact matches first
        for word in target_words:
            if word in sentence_lower:
                # Find the actual case-preserved word
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                match = pattern.search(sentence)
                if match:
                    return match.group()
        
        return None
    
    def _improve_transitions(self, content: str, section_index: int, total_sections: int) -> str:
        """
        Improve transitions and flow in content
        """
        
        # Add transition phrases for better flow
        transition_phrases = {
            'beginning': [
                "Let's start by exploring",
                "First, it's important to understand",
                "To begin with",
                "Initially"
            ],
            'middle': [
                "Furthermore",
                "Additionally",
                "Building on this concept",
                "Moreover",
                "In addition to this"
            ],
            'end': [
                "Finally",
                "To conclude this section",
                "As a final point",
                "Ultimately"
            ]
        }
        
        # Determine section position
        if section_index == 0:
            position = 'beginning'
        elif section_index == total_sections - 1:
            position = 'end'
        else:
            position = 'middle'
        
        # Check if content already has good transitions
        has_transition = any(
            phrase.lower() in content.lower() 
            for phrases in transition_phrases.values() 
            for phrase in phrases
        )
        
        if not has_transition and len(content) > 50:
            # Add a subtle transition phrase
            phrases = transition_phrases[position]
            selected_phrase = phrases[section_index % len(phrases)]
            
            # Insert at the beginning of the second sentence if possible
            sentences = self._simple_sent_tokenize(content)
            if len(sentences) > 1:
                content = f"{sentences[0]} {selected_phrase}, {sentences[1][0].lower()}{sentences[1][1:]} {' '.join(sentences[2:])}"
        
        return content
    
    def _apply_seo_enhancements(self, article_data: Dict[str, Any], seo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply SEO-specific enhancements to the article
        """
        
        enhanced_article = article_data.copy()
        
        # Enhance title with SEO keywords if needed
        focus_keyword = seo_data.get('focus_keyword')
        if focus_keyword and focus_keyword.lower() not in enhanced_article['title'].lower():
            enhanced_article['seo_title'] = f"{focus_keyword}: {enhanced_article['title']}"
        
        # Ensure meta description includes focus keyword
        if focus_keyword and focus_keyword.lower() not in enhanced_article['meta_description'].lower():
            enhanced_article['meta_description'] = f"Discover {focus_keyword} insights. {enhanced_article['meta_description']}"[:160]
        
        return enhanced_article
    
    def _fix_malformed_urls(self, content: str) -> str:
        """
        Fix malformed URLs in content that have spaces instead of dots
        Specifically targets URLs like: https://www geeksforgeeks org
        Converts them to: https://www.geeksforgeeks.org
        """
        
        # Pattern to find markdown links with malformed URLs
        # Matches: [text](url with spaces)
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        
        def fix_url(match):
            link_text = match.group(1)
            url = match.group(2).strip()
            
            # Only fix URLs that contain spaces and look like web URLs
            if ' ' in url and ('http' in url.lower() or 'www' in url.lower()):
                
                # Check if it's a malformed web URL pattern
                # Pattern: protocol://domain with spaces
                if '://' in url:
                    parts = url.split('://', 1)
                    if len(parts) == 2:
                        protocol = parts[0]
                        rest = parts[1]
                        
                        # Split by forward slash to separate domain from path
                        path_parts = rest.split('/', 1)
                        domain = path_parts[0]
                        path = '/' + path_parts[1] if len(path_parts) > 1 else ''
                        
                        # Only fix domain part if it has spaces - replace spaces with dots
                        if ' ' in domain:
                            # Replace spaces with dots in domain
                            fixed_domain = domain.replace(' ', '.')
                            fixed_url = f"{protocol}://{fixed_domain}{path}"
                            return f"[{link_text}]({fixed_url})"
                
                # Pattern: www domain with spaces (no protocol)
                elif url.lower().startswith('www '):
                    # Replace spaces with dots and add https protocol
                    fixed_url = url.replace(' ', '.')
                    if not fixed_url.startswith('https://'):
                        fixed_url = f"https://{fixed_url}"
                    return f"[{link_text}]({fixed_url})"
                
                # Pattern: domain with spaces that looks like a website
                elif '.' in url and len(url.split()) >= 2:
                    # Check if it looks like a domain (has common TLDs)
                    common_tlds = [' com', ' org', ' net', ' edu', ' gov', ' io', ' co ']
                    if any(tld in url.lower() for tld in common_tlds):
                        fixed_url = url.replace(' ', '.')
                        if not fixed_url.startswith(('http://', 'https://')):
                            fixed_url = f"https://{fixed_url}"
                        return f"[{link_text}]({fixed_url})"
            
            # Return unchanged if no spaces or doesn't look like a web URL
            return match.group(0)
        
        # Apply the fix to all markdown links
        fixed_content = re.sub(link_pattern, fix_url, content)
        
        # Also fix standalone URLs that aren't in markdown format
        # Pattern for standalone URLs with spaces
        standalone_pattern = r'(https?://[^\s\)]+(?:\s+[^\s\)\.,!?]+)+)'
        
        def fix_standalone_url(match):
            url = match.group(1)
            # Only fix if it looks like a domain with spaces
            if ' ' in url and ('www' in url or any(tld in url for tld in [' com', ' org', ' net', ' edu', ' gov'])):
                return url.replace(' ', '.')
            return url
        
        fixed_content = re.sub(standalone_pattern, fix_standalone_url, fixed_content)
        
        # Additional safety check - fix any remaining malformed URLs in parentheses
        # Pattern: (https://domain with spaces)
        paren_url_pattern = r'\((https?://[^)]+)\)'
        
        def fix_paren_url(match):
            url = match.group(1)
            if ' ' in url and ('www' in url or any(tld in url for tld in [' com', ' org', ' net', ' edu', ' gov'])):
                fixed_url = url.replace(' ', '.')
                return f'({fixed_url})'
            return match.group(0)
        
        fixed_content = re.sub(paren_url_pattern, fix_paren_url, fixed_content)
        
        # Final comprehensive check for any remaining space-separated domains
        # This catches patterns like "geeksforgeeks org" or "www example com"
        domain_pattern = r'\b((?:https?://)?(?:www\s+)?[a-zA-Z0-9-]+(?:\s+[a-zA-Z0-9-]+)*\s+(?:com|org|net|edu|gov|io|co|uk|de|fr))\b'
        
        def fix_domain_spaces(match):
            domain = match.group(1)
            # Replace spaces with dots
            fixed_domain = domain.replace(' ', '.')
            # Add protocol if missing
            if not fixed_domain.startswith(('http://', 'https://')):
                fixed_domain = f'https://{fixed_domain}'
            return fixed_domain
        
        fixed_content = re.sub(domain_pattern, fix_domain_spaces, fixed_content, flags=re.IGNORECASE)
        
        return fixed_content
    
    def _generate_enhanced_cta(self, title: str, keywords: List[str]) -> str:
        """
        Generate an enhanced call-to-action
        """
        
        primary_keyword = keywords[0] if keywords else "this topic"
        
        cta_templates = [
            f"Ready to dive deeper into {primary_keyword}? Explore our comprehensive resources and expert insights to enhance your understanding.",
            f"Want to stay ahead in {primary_keyword}? Subscribe to our newsletter for the latest updates, tips, and industry analysis.",
            f"Looking for personalized {primary_keyword} guidance? Our team of experts is ready to help you achieve your goals.",
            f"Interested in learning more about {primary_keyword}? Check out our related articles and comprehensive guides."
        ]
        
        # Choose based on title hash for consistency
        return cta_templates[hash(title) % len(cta_templates)]
    
    def analyze_content_quality(self, content: str) -> Dict[str, Any]:
        """
        Analyze content quality metrics
        """
        
        try:
            # Basic metrics
            word_count = len(content.split())
            sentence_count = len(self._simple_sent_tokenize(content))
            paragraph_count = len([p for p in content.split('\n\n') if p.strip()])
            
            # Calculate readability (simplified)
            avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
            
            # Keyword density analysis
            words = [word.lower() for word in self._simple_word_tokenize(content) if word.isalpha()]
            word_freq = Counter(words)
            
            return {
                'word_count': word_count,
                'sentence_count': sentence_count,
                'paragraph_count': paragraph_count,
                'avg_sentence_length': round(avg_sentence_length, 1),
                'unique_words': len(set(words)),
                'readability_score': min(100, max(0, 100 - (avg_sentence_length * 2))),  # Simplified score
                'top_words': dict(word_freq.most_common(10))
            }
            
        except Exception as e:
            print(f"Content quality analysis failed: {e}")
            return {
                'word_count': len(content.split()),
                'sentence_count': 1,
                'paragraph_count': 1,
                'avg_sentence_length': 15,
                'unique_words': 0,
                'readability_score': 75,
                'top_words': {}
            }