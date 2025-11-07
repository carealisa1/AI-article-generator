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
    
    def extract_multiple_urls_content(self, urls: List[str], max_urls: int = 5) -> List[Dict[str, Any]]:
        """
        Batch process multiple URLs for content extraction with enhanced error handling
        
        Args:
            urls: List of URLs to process
            max_urls: Maximum number of URLs to process
            
        Returns:
            List of extracted content dictionaries
        """
        
        extracted_contents = []
        
        for i, url in enumerate(urls[:max_urls]):
            try:
                print(f"Processing URL {i+1}/{min(len(urls), max_urls)}: {url}")
                
                # Extract content from single URL
                content = self.extract_url_content(url)
                
                if content and content.get('main_content'):
                    # Add batch processing metadata
                    content['batch_index'] = i
                    content['total_in_batch'] = min(len(urls), max_urls)
                    content['processing_success'] = True
                    extracted_contents.append(content)
                else:
                    print(f"Warning: Limited content from {url}")
                    
            except Exception as e:
                print(f"Error processing {url}: {e}")
                # Add error entry for tracking
                extracted_contents.append({
                    'url': url,
                    'batch_index': i,
                    'total_in_batch': min(len(urls), max_urls),
                    'processing_success': False,
                    'error': str(e),
                    'title': f"Failed extraction from {url}",
                    'main_content': '',
                    'extraction_method': 'failed'
                })
                continue
        
        return extracted_contents
    
    def combine_extracted_contents(self, extracted_contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combine multiple extracted contents into a unified context for LLM processing
        
        Args:
            extracted_contents: List of extracted content dictionaries
            
        Returns:
            Combined content dictionary optimized for LLM consumption
        """
        
        successful_extractions = [content for content in extracted_contents if content.get('processing_success', False)]
        
        if not successful_extractions:
            return {
                'combined_title': 'Multi-URL Analysis (No successful extractions)',
                'combined_content': 'No content could be extracted from the provided URLs.',
                'source_count': 0,
                'extraction_methods': [],
                'combined_keywords': [],
                'source_summaries': []
            }
        
        # Combine titles
        titles = [content.get('title', 'Unknown') for content in successful_extractions]
        combined_title = f"Analysis from {len(titles)} sources: " + " | ".join(titles[:3])
        
        # Combine main content
        content_parts = []
        for i, content in enumerate(successful_extractions, 1):
            main_content = content.get('main_content', '')[:800]  # Limit each source to 800 chars
            content_parts.append(f"Source {i} ({content.get('title', 'Unknown')}): {main_content}")
        
        combined_content = "\n\n".join(content_parts)
        
        # Combine keywords
        all_keywords = []
        for content in successful_extractions:
            all_keywords.extend(content.get('keywords', []))
        
        # Remove duplicates and limit
        unique_keywords = list(set(all_keywords))[:15]
        
        # Get extraction methods used
        extraction_methods = list(set([content.get('extraction_method', 'unknown') for content in successful_extractions]))
        
        # Create source summaries
        source_summaries = []
        for i, content in enumerate(successful_extractions, 1):
            summary = content.get('content_summary', content.get('title', f'Source {i}'))
            source_summaries.append(f"Source {i}: {summary}")
        
        return {
            'combined_title': combined_title,
            'combined_content': combined_content,
            'source_count': len(successful_extractions),
            'extraction_methods': extraction_methods,
            'combined_keywords': unique_keywords,
            'source_summaries': source_summaries,
            'total_urls_attempted': len(extracted_contents),
            'successful_extractions': len(successful_extractions),
            'success_rate': len(successful_extractions) / len(extracted_contents) * 100 if extracted_contents else 0
        }
    
    def extract_url_content(self, url: str) -> Dict[str, Any]:
        """
        Extract and analyze content from a URL using Jina REST API for better extraction
        """
        
        # Try Jina API first, fallback to BeautifulSoup if failed
        try:
            extracted_data = self._extract_with_jina_api(url)
            if extracted_data:
                return extracted_data
        except Exception as e:
            print(f"Jina API extraction failed for {url}: {e}")
        
        # Fallback to BeautifulSoup method
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
                'content_summary': '',
                'extraction_method': 'beautifulsoup'
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
    
    def _extract_with_jina_api(self, url: str) -> Dict[str, Any]:
        """
        Extract content using Jina REST API for better content extraction
        """
        
        try:
            # Jina Reader API endpoint
            jina_url = f"https://r.jina.ai/{url}"
            
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'AI-Article-Generator/1.0'
            }
            
            # Make request to Jina API
            response = requests.get(jina_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Parse response
            if response.headers.get('content-type', '').startswith('application/json'):
                jina_data = response.json()
            else:
                # If response is plain text, structure it
                content_text = response.text
                jina_data = {
                    'data': {
                        'title': self._extract_title_from_text(content_text),
                        'content': content_text,
                        'description': '',
                        'url': url
                    }
                }
            
            # Extract and structure the data
            extracted_data = self._process_jina_response(jina_data, url)
            extracted_data['extraction_method'] = 'jina_api'
            
            return extracted_data
            
        except requests.exceptions.RequestException as e:
            print(f"Jina API request failed: {e}")
            return None
        except Exception as e:
            print(f"Jina API processing error: {e}")
            return None
    
    def _process_jina_response(self, jina_data: Dict, url: str) -> Dict[str, Any]:
        """
        Process and structure Jina API response
        """
        
        # Extract data from Jina response structure
        if 'data' in jina_data:
            data = jina_data['data']
        else:
            # Handle different response formats
            data = jina_data
        
        # Extract title
        title = data.get('title', '')
        if not title:
            title = self._extract_title_from_text(data.get('content', ''))
        
        # Extract content
        main_content = data.get('content', '')
        description = data.get('description', data.get('summary', ''))
        
        # Extract headings from content
        headings = self._extract_headings_from_text(main_content)
        
        # Extract keywords using NLP
        keywords = self._extract_keywords_nlp(main_content)
        
        structured_data = {
            'title': title,
            'meta_description': description,
            'headings': headings,
            'main_content': main_content[:2000],  # Limit content length
            'keywords': keywords[:10],
            'images': [],  # Jina doesn't provide image extraction in basic plan
            'links': self._extract_links_from_text(main_content, url),
            'url': url,
            'content_summary': ''
        }
        
        # Generate content summary
        structured_data['content_summary'] = self._generate_content_summary(structured_data)
        
        return structured_data
    
    def _extract_title_from_text(self, text: str) -> str:
        """
        Extract title from plain text content
        """
        
        lines = text.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line and len(line) > 10 and len(line) < 100:
                # This looks like a title
                return line
        
        return "Extracted Article"
    
    def _extract_headings_from_text(self, text: str) -> List[Dict[str, str]]:
        """
        Extract headings from plain text using heuristics
        """
        
        headings = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Heuristics for headings:
            # 1. Lines that are all caps and reasonably short
            # 2. Lines that start with numbers (1., 2., etc.)
            # 3. Lines that are followed by empty lines
            # 4. Lines that are significantly shorter than surrounding text
            
            is_heading = False
            level = 2  # Default to h2
            
            # Check if all caps and reasonable length
            if line.isupper() and 10 <= len(line) <= 80:
                is_heading = True
                level = 1
            
            # Check if starts with number
            elif re.match(r'^\d+\.?\s+', line) and len(line) <= 100:
                is_heading = True
                level = 2
            
            # Check if followed by empty line (and not too long)
            elif (i < len(lines) - 1 and 
                  not lines[i + 1].strip() and 
                  10 <= len(line) <= 80 and
                  not line.endswith('.') and
                  not line.endswith(',')):
                is_heading = True
                level = 2
            
            if is_heading:
                headings.append({
                    'level': level,
                    'text': line,
                    'id': ''
                })
        
        return headings[:10]  # Limit to 10 headings
    
    def _extract_links_from_text(self, text: str, base_url: str) -> List[Dict[str, str]]:
        """
        Extract links from plain text
        """
        
        links = []
        
        # Find URLs in text
        url_pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+|[^\s<>"\']+\.[a-z]{2,}(?:/[^\s<>"\']*)?'
        
        urls = re.findall(url_pattern, text, re.IGNORECASE)
        
        for url in urls[:10]:  # Limit to 10 links
            # Clean up URL
            url = url.rstrip('.,!?;)')
            
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Determine if internal or external
            is_internal = self._is_internal_link(url, base_url)
            
            links.append({
                'url': url,
                'text': url,  # For plain text, URL is the text
                'title': '',
                'is_internal': is_internal
            })
        
        return links
    
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
            'content_summary': f"URL analysis from {url}",
            'extraction_method': 'fallback'
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
            # Skip URL fixing for now as it's causing false positives
            fixed_content = section['content']
            
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
        
        # Parse format: "Link Text: /url" (one per line) or "Link Text: /url, Another Link: /another-url"
        # Split by both newlines and commas to handle both formats
        entries = []
        
        # First split by newlines
        for line in internal_links.split('\n'):
            if line.strip():
                # Then split by commas if multiple links per line
                entries.extend([entry.strip() for entry in line.split(',') if entry.strip()])
        
        for link_entry in entries:
            if ':' in link_entry:
                parts = link_entry.split(':', 1)
                if len(parts) == 2:
                    text = parts[0].strip()
                    url = parts[1].strip()
                    
                    # Clean up the URL - remove any extra spaces and fix common issues
                    if url and not url.startswith(('http://', 'https://', '/')):
                        url = '/' + url  # Add leading slash for relative URLs
                    
                    if text and url:
                        # Store with original case for better matching
                        link_map[text] = url
        
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
        links_added = 0
        max_links_per_section = 2  # Limit to 2 links per section for better UX
        
        for link_text, link_url in link_map.items():
            # Skip if already inserted or max links reached
            if link_url in inserted_links or links_added >= max_links_per_section:
                continue
            
            # Try exact match first
            if link_text.lower() in enhanced_content.lower():
                # Find the exact text with proper case
                pattern = re.compile(re.escape(link_text), re.IGNORECASE)
                match = pattern.search(enhanced_content)
                
                if match:
                    original_text = match.group()
                    # Only replace if it's not already a link
                    if not self._is_already_linked(enhanced_content, match.start(), match.end()):
                        link_markdown = f'[{original_text}]({link_url})'
                        enhanced_content = enhanced_content.replace(original_text, link_markdown, 1)
                        inserted_links.add(link_url)
                        links_added += 1
                        continue
            
            # Try semantic matching if exact match fails
            insertion_points = self._find_semantic_link_points(
                enhanced_content, 
                link_text, 
                section_keywords
            )
            
            if insertion_points and links_added < max_links_per_section:
                best_point = insertion_points[0]
                
                # Create natural anchor text
                anchor_text = best_point.get("anchor_text", best_point["original_text"])
                link_markdown = f'[{anchor_text}]({link_url})'
                
                # Insert the link carefully
                enhanced_content = enhanced_content.replace(
                    best_point["original_text"], 
                    link_markdown, 
                    1
                )
                
                inserted_links.add(link_url)
                links_added += 1
        
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
    
    def _is_already_linked(self, content: str, start_pos: int, end_pos: int) -> bool:
        """Check if text is already part of a markdown link"""
        
        # Look backward for opening bracket
        for i in range(start_pos - 1, max(0, start_pos - 100), -1):
            if content[i] == '[':
                # Found opening bracket, check if there's a closing bracket and URL
                bracket_end = content.find(']', start_pos)
                if bracket_end > end_pos and bracket_end < len(content) - 1:
                    if content[bracket_end + 1] == '(':
                        return True  # Already part of a link
                break
            elif content[i] == ']':
                break  # Found closing bracket first, not in a link
        
        return False
    
    def _find_semantic_link_points(
        self, 
        content: str, 
        link_text: str, 
        keywords: List[str]
    ) -> List[Dict[str, str]]:
        """
        Find semantic points to insert links based on context and keywords
        """
        
        insertion_points = []
        sentences = self._simple_sent_tokenize(content)
        
        # Create search terms from link text
        link_words = set(word.lower() for word in link_text.split())
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            sentence_words = set(sentence_lower.split())
            
            # Check for keyword relevance
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                if keyword_lower in sentence_lower:
                    # Found relevant sentence, look for linkable phrase
                    best_phrase = self._extract_linkable_phrase(sentence, keyword, link_text)
                    
                    if best_phrase:
                        relevance = self._calculate_relevance(best_phrase, link_text, keyword)
                        insertion_points.append({
                            "original_text": best_phrase,
                            "anchor_text": best_phrase,
                            "sentence": sentence,
                            "relevance_score": relevance
                        })
            
            # Check for semantic similarity with link text
            word_overlap = len(link_words & sentence_words)
            if word_overlap > 0:
                relevance = word_overlap / len(link_words)
                if relevance > 0.2:  # At least 20% overlap
                    phrase = self._find_best_linkable_phrase(sentence, list(link_words))
                    if phrase:
                        insertion_points.append({
                            "original_text": phrase,
                            "anchor_text": phrase,
                            "sentence": sentence,
                            "relevance_score": relevance
                        })
        
        # Sort by relevance and return top matches
        insertion_points.sort(key=lambda x: x["relevance_score"], reverse=True)
        return insertion_points[:1]  # Return only the best match
    
    def _extract_linkable_phrase(self, sentence: str, keyword: str, link_text: str) -> Optional[str]:
        """Extract the best phrase to link from a sentence"""
        
        sentence_lower = sentence.lower()
        keyword_lower = keyword.lower()
        
        # If keyword appears in sentence, use it
        if keyword_lower in sentence_lower:
            # Find the actual case-preserved keyword
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            match = pattern.search(sentence)
            if match:
                return match.group()
        
        # Look for phrases that match link text words
        link_words = link_text.lower().split()
        for word in link_words:
            if word in sentence_lower and len(word) > 3:
                pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
                match = pattern.search(sentence)
                if match:
                    return match.group()
        
        return None
    
    def _calculate_relevance(self, phrase: str, link_text: str, keyword: str) -> float:
        """Calculate relevance score for link insertion"""
        
        phrase_lower = phrase.lower()
        link_lower = link_text.lower()
        keyword_lower = keyword.lower()
        
        score = 0.0
        
        # Exact match gets highest score
        if phrase_lower == link_lower:
            score += 1.0
        elif phrase_lower == keyword_lower:
            score += 0.9
        
        # Partial matches
        phrase_words = set(phrase_lower.split())
        link_words = set(link_lower.split())
        keyword_words = set(keyword_lower.split())
        
        # Word overlap scores
        link_overlap = len(phrase_words & link_words) / len(link_words) if link_words else 0
        keyword_overlap = len(phrase_words & keyword_words) / len(keyword_words) if keyword_words else 0
        
        score += (link_overlap * 0.6) + (keyword_overlap * 0.4)
        
        return score
    
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
        
        # Final check for space-separated domains - but only in very specific contexts
        # Only match if it's clearly a domain pattern: starts with www or has protocol
        domain_pattern = r'\b((?:https?://\s*)?www\s+[a-zA-Z0-9-]+\s+(?:com|org|net|edu|gov|io|co|uk|de|fr))\b'
        
        def fix_domain_spaces(match):
            domain = match.group(1)
            # Replace spaces with dots
            fixed_domain = domain.replace(' ', '.')
            # Add protocol if missing
            if not fixed_domain.startswith(('http://', 'https://')):
                fixed_domain = f'https://{fixed_domain}'
            return fixed_domain
        
        # Only apply this fix if the pattern clearly looks like a broken URL
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