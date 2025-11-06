import re
import math
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter
import json
from datetime import datetime

class SEOTools:
    """
    Advanced SEO optimization and analysis tools
    Handles meta generation, keyword density, readability analysis
    """
    
    def __init__(self):
        """Initialize SEO tools with optimization parameters"""
        
        # SEO best practices thresholds
        self.optimal_title_length = (50, 60)
        self.optimal_meta_length = (150, 160)
        self.optimal_keyword_density = (1.0, 2.5)  # Percentage
        self.optimal_readability_score = (60, 80)
        
        # Stop words for keyword analysis
        self.stop_words = set([
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'would', 'you', 'your', 'this', 'they',
            'we', 'our', 'can', 'have', 'been', 'were', 'their', 'said', 'each'
        ])
        
        # LSI (Latent Semantic Indexing) keyword suggestions
        self.lsi_keywords = {
            'bitcoin': ['cryptocurrency', 'blockchain', 'digital currency', 'crypto', 'satoshi'],
            'trading': ['investment', 'market', 'portfolio', 'broker', 'strategy'],
            'health': ['wellness', 'fitness', 'nutrition', 'medical', 'healthcare'],
            'technology': ['innovation', 'digital', 'software', 'tech', 'development'],
            'business': ['company', 'corporate', 'enterprise', 'commercial', 'professional'],
            'marketing': ['advertising', 'promotion', 'branding', 'campaign', 'digital marketing'],
            'education': ['learning', 'training', 'academic', 'course', 'knowledge'],
            'finance': ['money', 'financial', 'investment', 'banking', 'economic']
        }
    
    def optimize_content(
        self, 
        article_data: Dict[str, Any], 
        keywords: str = "", 
        focus_keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive SEO optimization of article content
        
        Args:
            article_data: The generated article data
            keywords: Comma-separated target keywords
            focus_keyword: Primary keyword for optimization
            
        Returns:
            Dictionary containing SEO analysis and optimized data
        """
        
        # Parse keywords
        keyword_list = [k.strip().lower() for k in keywords.split(",") if k.strip()] if keywords else []
        primary_keyword = focus_keyword or (keyword_list[0] if keyword_list else None)
        
        # Collect all content for analysis
        full_content = self._collect_full_content(article_data)
        
        # Perform comprehensive SEO analysis
        seo_data = {
            'focus_keyword': primary_keyword,
            'target_keywords': keyword_list,
            'keyword_analysis': self._analyze_keywords(full_content, keyword_list, primary_keyword),
            'readability_analysis': self._analyze_readability(full_content),
            'title_analysis': self._analyze_title(article_data.get('title', ''), primary_keyword),
            'meta_analysis': self._analyze_meta_description(article_data.get('meta_description', ''), primary_keyword),
            'content_structure': self._analyze_content_structure(article_data),
            'seo_score': 0,  # Will be calculated
            'recommendations': [],
            'lsi_suggestions': self._get_lsi_suggestions(keyword_list),
            'optimization_date': datetime.now().isoformat()
        }
        
        # Calculate overall SEO score
        seo_data['seo_score'] = self._calculate_seo_score(seo_data)
        
        # Generate recommendations
        seo_data['recommendations'] = self._generate_recommendations(seo_data)
        
        # Add derived metrics
        seo_data.update({
            'word_count': seo_data['readability_analysis']['word_count'],
            'keyword_density': seo_data['keyword_analysis'].get('primary_density', 0),
            'readability_score': seo_data['readability_analysis']['flesch_score'],
            'links': self._extract_links_data(article_data)
        })
        
        return seo_data
    
    def _collect_full_content(self, article_data: Dict[str, Any]) -> str:
        """Collect all textual content from the article"""
        
        content_parts = []
        
        # Add title
        if article_data.get('title'):
            content_parts.append(article_data['title'])
        
        # Add meta description
        if article_data.get('meta_description'):
            content_parts.append(article_data['meta_description'])
        
        # Add all section content
        for section in article_data.get('sections', []):
            if section.get('heading'):
                content_parts.append(section['heading'])
            if section.get('content'):
                # Clean HTML tags for analysis
                clean_content = re.sub(r'<[^>]+>', ' ', section['content'])
                content_parts.append(clean_content)
        
        # Add CTA
        if article_data.get('cta'):
            content_parts.append(article_data['cta'])
        
        return ' '.join(content_parts)
    
    def _analyze_keywords(
        self, 
        content: str, 
        target_keywords: List[str], 
        primary_keyword: Optional[str]
    ) -> Dict[str, Any]:
        """
        Analyze keyword usage and density
        """
        
        content_lower = content.lower()
        content_words = self._extract_words(content)
        total_words = len(content_words)
        
        keyword_analysis = {
            'total_words': total_words,
            'primary_keyword': primary_keyword,
            'primary_count': 0,
            'primary_density': 0.0,
            'keyword_distribution': {},
            'keyword_positions': {},
            'missing_keywords': [],
            'overused_keywords': []
        }
        
        if not target_keywords:
            return keyword_analysis
        
        # Analyze each keyword
        for keyword in target_keywords:
            keyword_lower = keyword.lower()
            
            # Count occurrences
            count = content_lower.count(keyword_lower)
            density = (count / total_words * 100) if total_words > 0 else 0
            
            # Find positions (simplified)
            positions = self._find_keyword_positions(content_lower, keyword_lower)
            
            keyword_analysis['keyword_distribution'][keyword] = {
                'count': count,
                'density': round(density, 2),
                'positions': positions
            }
            
            # Check if primary keyword
            if keyword == primary_keyword:
                keyword_analysis['primary_count'] = count
                keyword_analysis['primary_density'] = round(density, 2)
            
            # Identify issues
            if count == 0:
                keyword_analysis['missing_keywords'].append(keyword)
            elif density > self.optimal_keyword_density[1]:
                keyword_analysis['overused_keywords'].append(keyword)
        
        return keyword_analysis
    
    def _extract_words(self, text: str) -> List[str]:
        """Extract meaningful words from text"""
        
        # Remove HTML tags and special characters
        clean_text = re.sub(r'<[^>]+>', ' ', text)
        clean_text = re.sub(r'[^\w\s]', ' ', clean_text)
        
        # Extract words
        words = clean_text.lower().split()
        
        # Filter out stop words and short words
        meaningful_words = [
            word for word in words 
            if len(word) > 2 and word not in self.stop_words
        ]
        
        return meaningful_words
    
    def _find_keyword_positions(self, content: str, keyword: str) -> List[str]:
        """Find keyword positions in content (simplified)"""
        
        positions = []
        
        # Check in first 100 characters (introduction)
        if keyword in content[:100]:
            positions.append('introduction')
        
        # Check in headings (simplified - look for common heading indicators)
        heading_patterns = [r'##\s+.*' + re.escape(keyword), r'#\s+.*' + re.escape(keyword)]
        for pattern in heading_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                positions.append('heading')
                break
        
        # Check in last 100 characters (conclusion)
        if keyword in content[-100:]:
            positions.append('conclusion')
        
        return positions
    
    def _analyze_readability(self, content: str) -> Dict[str, Any]:
        """
        Analyze content readability using multiple metrics
        """
        
        try:
            # Clean content for analysis
            clean_content = re.sub(r'<[^>]+>', ' ', content)
            clean_content = re.sub(r'\s+', ' ', clean_content).strip()
            
            # Basic metrics
            sentences = self._count_sentences(clean_content)
            words = len(clean_content.split())
            syllables = self._count_syllables(clean_content)
            
            # Calculate Flesch Reading Ease Score
            flesch_score = self._calculate_flesch_score(sentences, words, syllables)
            
            # Additional metrics
            avg_sentence_length = words / sentences if sentences > 0 else 0
            avg_syllables_per_word = syllables / words if words > 0 else 0
            
            return {
                'word_count': words,
                'sentence_count': sentences,
                'syllable_count': syllables,
                'avg_sentence_length': round(avg_sentence_length, 1),
                'avg_syllables_per_word': round(avg_syllables_per_word, 2),
                'flesch_score': round(flesch_score, 1),
                'reading_level': self._get_reading_level(flesch_score),
                'readability_grade': self._get_readability_grade(avg_sentence_length, avg_syllables_per_word)
            }
            
        except Exception as e:
            print(f"Readability analysis failed: {e}")
            # Return default values
            return {
                'word_count': len(content.split()),
                'sentence_count': 10,
                'syllable_count': 200,
                'avg_sentence_length': 15.0,
                'avg_syllables_per_word': 1.5,
                'flesch_score': 75.0,
                'reading_level': 'Standard',
                'readability_grade': 8
            }
    
    def _count_sentences(self, text: str) -> int:
        """Count sentences in text"""
        sentence_endings = re.findall(r'[.!?]+', text)
        return max(1, len(sentence_endings))
    
    def _count_syllables(self, text: str) -> int:
        """Estimate syllable count (simplified)"""
        words = text.lower().split()
        syllable_count = 0
        
        for word in words:
            # Simple syllable counting heuristic
            vowels = 'aeiouy'
            word_syllables = 0
            prev_was_vowel = False
            
            for char in word:
                if char in vowels:
                    if not prev_was_vowel:
                        word_syllables += 1
                    prev_was_vowel = True
                else:
                    prev_was_vowel = False
            
            # Adjust for silent e
            if word.endswith('e'):
                word_syllables -= 1
            
            # Ensure at least 1 syllable per word
            word_syllables = max(1, word_syllables)
            syllable_count += word_syllables
        
        return syllable_count
    
    def _calculate_flesch_score(self, sentences: int, words: int, syllables: int) -> float:
        """Calculate Flesch Reading Ease Score"""
        
        if sentences == 0 or words == 0:
            return 0
        
        avg_sentence_length = words / sentences
        avg_syllables_per_word = syllables / words
        
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        return max(0, min(100, score))
    
    def _get_reading_level(self, flesch_score: float) -> str:
        """Convert Flesch score to reading level"""
        
        if flesch_score >= 90:
            return "Very Easy"
        elif flesch_score >= 80:
            return "Easy"
        elif flesch_score >= 70:
            return "Fairly Easy"
        elif flesch_score >= 60:
            return "Standard"
        elif flesch_score >= 50:
            return "Fairly Difficult"
        elif flesch_score >= 30:
            return "Difficult"
        else:
            return "Very Difficult"
    
    def _get_readability_grade(self, avg_sentence_length: float, avg_syllables: float) -> int:
        """Estimate grade level"""
        
        # Simplified Flesch-Kincaid Grade Level
        grade = (0.39 * avg_sentence_length) + (11.8 * avg_syllables) - 15.59
        return max(1, min(16, round(grade)))
    
    def _analyze_title(self, title: str, primary_keyword: Optional[str]) -> Dict[str, Any]:
        """Analyze title SEO effectiveness"""
        
        title_length = len(title)
        
        analysis = {
            'title': title,
            'length': title_length,
            'optimal_length': self.optimal_title_length[0] <= title_length <= self.optimal_title_length[1],
            'contains_primary_keyword': False,
            'keyword_position': None,
            'recommendations': []
        }
        
        if primary_keyword:
            title_lower = title.lower()
            keyword_lower = primary_keyword.lower()
            
            if keyword_lower in title_lower:
                analysis['contains_primary_keyword'] = True
                # Find position (beginning, middle, end)
                keyword_pos = title_lower.find(keyword_lower)
                if keyword_pos < len(title) * 0.33:
                    analysis['keyword_position'] = 'beginning'
                elif keyword_pos < len(title) * 0.66:
                    analysis['keyword_position'] = 'middle'
                else:
                    analysis['keyword_position'] = 'end'
        
        # Generate recommendations
        if title_length < self.optimal_title_length[0]:
            analysis['recommendations'].append("Title is too short. Consider expanding to 50-60 characters.")
        elif title_length > self.optimal_title_length[1]:
            analysis['recommendations'].append("Title is too long. Consider shortening to under 60 characters.")
        
        if primary_keyword and not analysis['contains_primary_keyword']:
            analysis['recommendations'].append(f"Include the primary keyword '{primary_keyword}' in the title.")
        elif primary_keyword and analysis['keyword_position'] != 'beginning':
            analysis['recommendations'].append("Consider placing the primary keyword closer to the beginning of the title.")
        
        return analysis
    
    def _analyze_meta_description(self, meta_description: str, primary_keyword: Optional[str]) -> Dict[str, Any]:
        """Analyze meta description SEO effectiveness"""
        
        meta_length = len(meta_description)
        
        analysis = {
            'meta_description': meta_description,
            'length': meta_length,
            'optimal_length': self.optimal_meta_length[0] <= meta_length <= self.optimal_meta_length[1],
            'contains_primary_keyword': False,
            'recommendations': []
        }
        
        if primary_keyword:
            meta_lower = meta_description.lower()
            keyword_lower = primary_keyword.lower()
            analysis['contains_primary_keyword'] = keyword_lower in meta_lower
        
        # Generate recommendations
        if meta_length < self.optimal_meta_length[0]:
            analysis['recommendations'].append("Meta description is too short. Expand to 150-160 characters.")
        elif meta_length > self.optimal_meta_length[1]:
            analysis['recommendations'].append("Meta description is too long. Shorten to under 160 characters.")
        
        if primary_keyword and not analysis['contains_primary_keyword']:
            analysis['recommendations'].append(f"Include the primary keyword '{primary_keyword}' in the meta description.")
        
        return analysis
    
    def _analyze_content_structure(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content structure for SEO"""
        
        sections = article_data.get('sections', [])
        
        structure_analysis = {
            'total_sections': len(sections),
            'has_introduction': bool(sections),
            'has_conclusion': len(sections) > 2,
            'heading_structure': [],
            'section_lengths': [],
            'content_balance': 'good'
        }
        
        # Analyze each section
        word_counts = []
        for i, section in enumerate(sections):
            heading = section.get('heading', f'Section {i+1}')
            content = section.get('content', '')
            word_count = len(content.split())
            
            structure_analysis['heading_structure'].append({
                'index': i,
                'heading': heading,
                'word_count': word_count
            })
            
            structure_analysis['section_lengths'].append(word_count)
            word_counts.append(word_count)
        
        # Analyze balance
        if word_counts:
            avg_length = sum(word_counts) / len(word_counts)
            variance = sum((x - avg_length) ** 2 for x in word_counts) / len(word_counts)
            
            if variance > avg_length * 0.5:
                structure_analysis['content_balance'] = 'uneven'
            elif all(wc < 50 for wc in word_counts):
                structure_analysis['content_balance'] = 'too_short'
            elif any(wc > 300 for wc in word_counts):
                structure_analysis['content_balance'] = 'sections_too_long'
        
        return structure_analysis
    
    def _calculate_seo_score(self, seo_data: Dict[str, Any]) -> int:
        """Calculate overall SEO score (0-100)"""
        
        score = 0
        max_score = 100
        
        # Title optimization (20 points)
        title_analysis = seo_data.get('title_analysis', {})
        if title_analysis.get('optimal_length'):
            score += 10
        if title_analysis.get('contains_primary_keyword'):
            score += 10
        
        # Meta description optimization (15 points)
        meta_analysis = seo_data.get('meta_analysis', {})
        if meta_analysis.get('optimal_length'):
            score += 8
        if meta_analysis.get('contains_primary_keyword'):
            score += 7
        
        # Keyword optimization (25 points)
        keyword_analysis = seo_data.get('keyword_analysis', {})
        primary_density = keyword_analysis.get('primary_density', 0)
        if self.optimal_keyword_density[0] <= primary_density <= self.optimal_keyword_density[1]:
            score += 15
        elif primary_density > 0:
            score += 8
        
        missing_keywords = keyword_analysis.get('missing_keywords', [])
        if len(missing_keywords) == 0:
            score += 10
        elif len(missing_keywords) <= 2:
            score += 5
        
        # Readability (20 points)
        readability = seo_data.get('readability_analysis', {})
        flesch_score = readability.get('flesch_score', 0)
        if self.optimal_readability_score[0] <= flesch_score <= self.optimal_readability_score[1]:
            score += 20
        elif flesch_score >= 50:
            score += 12
        elif flesch_score >= 30:
            score += 8
        
        # Content structure (20 points)
        structure = seo_data.get('content_structure', {})
        if structure.get('total_sections', 0) >= 3:
            score += 8
        if structure.get('content_balance') == 'good':
            score += 12
        elif structure.get('content_balance') in ['uneven', 'sections_too_long']:
            score += 6
        
        return min(max_score, max(0, score))
    
    def _generate_recommendations(self, seo_data: Dict[str, Any]) -> List[str]:
        """Generate actionable SEO recommendations"""
        
        recommendations = []
        
        # Collect recommendations from individual analyses
        for analysis_key in ['title_analysis', 'meta_analysis']:
            analysis = seo_data.get(analysis_key, {})
            recommendations.extend(analysis.get('recommendations', []))
        
        # Keyword recommendations
        keyword_analysis = seo_data.get('keyword_analysis', {})
        
        missing_keywords = keyword_analysis.get('missing_keywords', [])
        if missing_keywords:
            recommendations.append(f"Consider adding these missing keywords: {', '.join(missing_keywords[:3])}")
        
        overused_keywords = keyword_analysis.get('overused_keywords', [])
        if overused_keywords:
            recommendations.append(f"Reduce usage of overused keywords: {', '.join(overused_keywords[:2])}")
        
        primary_density = keyword_analysis.get('primary_density', 0)
        if primary_density == 0:
            recommendations.append("Add the primary keyword throughout the content naturally.")
        elif primary_density < self.optimal_keyword_density[0]:
            recommendations.append("Increase primary keyword usage slightly for better optimization.")
        elif primary_density > self.optimal_keyword_density[1]:
            recommendations.append("Reduce primary keyword usage to avoid over-optimization.")
        
        # Readability recommendations
        readability = seo_data.get('readability_analysis', {})
        flesch_score = readability.get('flesch_score', 75)
        
        if flesch_score < 60:
            recommendations.append("Improve readability by using shorter sentences and simpler words.")
        elif flesch_score < 30:
            recommendations.append("Content is very difficult to read. Significantly simplify language and structure.")
        
        # Structure recommendations
        structure = seo_data.get('content_structure', {})
        if structure.get('total_sections', 0) < 3:
            recommendations.append("Add more sections to improve content structure and SEO.")
        
        if structure.get('content_balance') == 'uneven':
            recommendations.append("Balance section lengths for better content flow.")
        elif structure.get('content_balance') == 'too_short':
            recommendations.append("Expand sections to provide more valuable content.")
        
        return recommendations[:8]  # Limit to top 8 recommendations
    
    def _get_lsi_suggestions(self, keywords: List[str]) -> List[str]:
        """Get LSI keyword suggestions"""
        
        suggestions = []
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Find matching LSI keywords
            for base_keyword, lsi_list in self.lsi_keywords.items():
                if base_keyword in keyword_lower or keyword_lower in base_keyword:
                    suggestions.extend(lsi_list)
        
        # Remove duplicates and limit
        unique_suggestions = list(set(suggestions))
        return unique_suggestions[:10]
    
    def _extract_links_data(self, article_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract link data from article content"""
        
        links = []
        
        # Extract links from all sections
        for section in article_data.get('sections', []):
            content = section.get('content', '')
            
            # Find HTML links
            link_pattern = r'<a\s+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
            matches = re.findall(link_pattern, content, re.IGNORECASE)
            
            for url, text in matches:
                links.append({
                    'url': url,
                    'text': text,
                    'type': 'internal' if url.startswith('/') else 'external'
                })
        
        return links
    
    def generate_slug(self, title: str, max_length: int = 50) -> str:
        """Generate SEO-friendly URL slug"""
        
        slug = title.lower()
        
        # Replace spaces and special characters
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        
        # Limit length
        if len(slug) > max_length:
            # Try to break at word boundaries
            words = slug.split('-')
            truncated_slug = ""
            for word in words:
                if len(truncated_slug + word + '-') <= max_length:
                    truncated_slug += word + '-'
                else:
                    break
            slug = truncated_slug.rstrip('-')
        
        return slug or 'article'
    
    def generate_schema_markup(self, article_data: Dict[str, Any], seo_data: Dict[str, Any]) -> str:
        """Generate JSON-LD schema markup for the article"""
        
        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": article_data.get('title', ''),
            "description": article_data.get('meta_description', ''),
            "author": {
                "@type": "Organization",
                "name": "AI Article Generator"
            },
            "publisher": {
                "@type": "Organization", 
                "name": "AI Article Generator"
            },
            "datePublished": datetime.now().isoformat(),
            "dateModified": datetime.now().isoformat(),
            "wordCount": seo_data.get('word_count', 0),
            "keywords": seo_data.get('target_keywords', [])
        }
        
        return json.dumps(schema, indent=2)