import requests
import re
from typing import Dict, List, Any
from urllib.parse import urlparse
import time
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ContentTools:
    """
    Minimal content extraction - returns raw Jina API response
    """
    
    def __init__(self):
        pass
    
    def extract_multiple_urls_content(self, urls: List[str], max_urls: int = 5) -> List[Dict[str, Any]]:
        """Extract content from multiple URLs - raw responses only"""
        extracted_contents = []
        
        for i, url in enumerate(urls[:max_urls]):
            try:
                print(f"📄 Processing URL {i+1}/{min(len(urls), max_urls)}: {url}")
                content = self.extract_url_content(url)
                
                if content:
                    content['batch_index'] = i
                    content['processing_success'] = True
                    extracted_contents.append(content)
                    print(f"✅ Extracted content from {url}")
                    
            except Exception as e:
                print(f"❌ Error processing {url}: {e}")
                extracted_contents.append({
                    'url': url,
                    'batch_index': i,
                    'processing_success': False,
                    'error': str(e),
                    'title': f"Failed: {url}",
                    'main_content': f"Failed to extract from {url}",
                })
        
        return extracted_contents
    
    def combine_extracted_contents(self, extracted_contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine contents - minimal processing"""
        successful = [c for c in extracted_contents if c.get('processing_success', False)]
        
        if not successful:
            return {
                'combined_title': 'No Content Extracted',
                'combined_content': 'No content could be extracted from URLs.',
                'source_count': 0,
                'total_urls_attempted': len(extracted_contents),
                'successful_extractions': 0,
                'success_rate': 0.0,
                'combined_keywords': [],
                'source_summaries': [],
                'extraction_methods': []
            }
        
        # Just combine raw content
        titles = [c.get('title', 'Unknown') for c in successful]
        combined_title = " | ".join(titles[:3])
        
        content_parts = []
        for content in successful:
            main_content = content.get('main_content', '')
            title = content.get('title', 'Content')
            content_parts.append(f"From {title}:\n{main_content}")
        
        return {
            'combined_title': combined_title,
            'combined_content': "\n\n---\n\n".join(content_parts),
            'source_count': len(successful),
            'total_urls_attempted': len(extracted_contents),
            'successful_extractions': len(successful),
            'success_rate': len(successful) / len(extracted_contents) * 100 if extracted_contents else 0,
            'combined_keywords': [],  # Simple placeholder - GPT will handle keyword extraction
            'source_summaries': [c.get('title', 'Unknown') for c in successful],
            'extraction_methods': ['jina_gpt_cleaned'] if successful else []
        }
    
    def _remove_all_links(self, content: str) -> str:
        """Remove all types of links, images, and markdown patterns"""
        if not content:
            return content
        
        # Remove markdown images: ![alt text](url)
        content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
        
        # Remove markdown links: [text](url) 
        content = re.sub(r'\[.*?\]\(.*?\)', '', content)
        
        # Remove standalone URLs (http/https)
        content = re.sub(r'https?://[^\s\)\]]+', '', content)
        
        # Remove www URLs
        content = re.sub(r'www\.[^\s\)\]]+', '', content)
        
        # Remove Image references: "Image X:"
        content = re.sub(r'Image \d+:', '', content)
        
        # Clean up multiple spaces and empty lines
        content = re.sub(r'\s+', ' ', content)  # Multiple spaces to single space
        content = re.sub(r'\n\s*\n', '\n', content)  # Multiple newlines to single
        
        return content.strip()
    
    def _extract_article_only(self, content: str) -> str:
        """Use GPT to extract only the main article content"""
        if not content or len(content) < 100:
            return content
        
        try:
            # Set up OpenAI client with explicit API key loading
            api_key = os.getenv('OPENAI_API_KEY')
            
            # Fallback: try to load from .env file directly if not found
            if not api_key:
                try:
                    with open('.env', 'r') as f:
                        for line in f:
                            if line.strip().startswith('OPENAI_API_KEY='):
                                api_key = line.strip().split('=', 1)[1]
                                break
                except:
                    pass
            
            if not api_key:
                print("⚠️ No OpenAI API key found - skipping GPT content extraction")
                return content
            
            client = openai.OpenAI(api_key=api_key)
            print(f"🔑 Using OpenAI API key: {api_key[:8]}...")
            
            prompt = """This is the COMPLETE TEXT from a news/article webpage. Your task is to extract ONLY the actual article content in ANY language.

CONTEXT: This text contains everything from the webpage - the main article mixed with website navigation, menus, ads, and other page elements. You need to identify and extract just the core article content.

EXTRACT the main article content which typically includes:
- Article title and headline
- Article body paragraphs and content
- Quotes, analysis, and reporting
- Technical details and data mentioned in the article

REMOVE all website elements:
- Navigation menus, headers, footers
- "More articles", "Related content", "You might like" sections
- Advertisements and promotional content  
- Cookie/privacy policies and legal notices
- Social sharing buttons and author bios
- Comment sections and subscription prompts
- Price tickers and trading widgets (unless part of the actual article)
- Website branding and company information

IMPORTANT: This is raw webpage text, so identify what is the actual news article vs website navigation. Keep all article content in its original language exactly as written - do not translate, rewrite, or summarize.

Complete webpage text to process:"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting article content from complete webpage text. You understand that webpage text contains both the actual article and website navigation elements mixed together. Your job is to intelligently separate the actual news/article content from the website interface elements. Always preserve the original language and exact text of the article content."},
                    {"role": "user", "content": f"{prompt}\n\n{content}"}
                ],
                temperature=0,
                max_tokens=4000
            )
            
            cleaned_content = response.choices[0].message.content.strip()
            print(f"🤖 GPT content reduction: {len(content)} → {len(cleaned_content)} chars")
            
            return cleaned_content if cleaned_content else content
            
        except Exception as e:
            print(f"⚠️ GPT content extraction failed: {e}, returning original content")
            return content
    
    def extract_url_content(self, url: str) -> Dict[str, Any]:
        """Extract content - raw Jina API response with link filtering"""
        try:
            # Jina API call
            jina_url = f"https://r.jina.ai/{url}"
            headers = {'Accept': 'application/json'}
            
            print(f"🌐 Calling Jina API for {url}")
            response = requests.get(jina_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Return completely raw response with link filtering
            if response.headers.get('content-type', '').startswith('application/json'):
                jina_data = response.json()
                
                # Extract only basic structure, keep content raw but filter links
                if 'data' in jina_data:
                    data = jina_data['data']
                else:
                    data = jina_data
                
                raw_content = data.get('content', '')
                filtered_content = self._remove_all_links(raw_content)
                article_content = self._extract_article_only(filtered_content)
                
                return {
                    'title': data.get('title', 'Extracted Content'),
                    'main_content': article_content,  # Clean article content only
                    'url': url,
                    'extraction_method': 'jina_gpt_cleaned'
                }
            else:
                # Plain text response
                raw_text = response.text
                filtered_text = self._remove_all_links(raw_text)
                article_content = self._extract_article_only(filtered_text)
                
                return {
                    'title': 'Raw Content',
                    'main_content': article_content,  # Clean article content only
                    'url': url,
                    'extraction_method': 'jina_text_gpt_cleaned'
                }
                
        except Exception as e:
            print(f"❌ Jina extraction failed: {e}")
            return {
                'title': f"Failed: {urlparse(url).netloc}",
                'main_content': f"Could not extract content from {url}. Error: {str(e)}",
                'url': url,
                'extraction_method': 'failed'
            }
    
    def enhance_content(self, article_data: Dict[str, Any], internal_links: str = "", seo_data=None) -> Dict[str, Any]:
        """No enhancement - return as-is"""
        return article_data